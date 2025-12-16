module vpu_core #(
  parameter int LANES = 4,                 // 4..8
  parameter int SP_WORD_W = 32,
  parameter int SP_DEPTH_WORDS = 2048,
  parameter int SP_BANKS = 2
)(
  input  logic clk,
  input  logic rst,

  // command interface (simple valid/ready)
  input  logic              cmd_valid,
  output logic              cmd_ready,
  input  formats::cmd_t     cmd,

  output logic              busy,
  output logic              done,

  // scratchpad ports (single-ported synchronous)
  output logic              sp_we,
  output logic [$clog2(SP_BANKS)-1:0] sp_bank,
  output logic [$clog2(SP_DEPTH_WORDS)-1:0] sp_addr,
  output logic [SP_WORD_W-1:0] sp_wdata,
  input  logic [SP_WORD_W-1:0] sp_rdata
);

  import formats::*;

  // -----------------------------
  // State machine (adds latch stages for sync RAM)
  // -----------------------------
    typedef enum logic [3:0] {
      S_IDLE,
      S_SET_A,   S_GET_A,
      S_SET_B,   S_GET_B,
      S_PREP,    S_EXEC,
      S_SET_DST, S_GET_DST,
      S_WRITE,
      S_DONE
    } state_t;


  state_t st;

  cmd_t cmd_q;
  logic [7:0] idx;                    // element index
  logic [SP_WORD_W-1:0] wordA, wordB; // latched operands
  logic [31:0] dst_word_q;     // latched destination word for RMW


  // Each 32-bit word holds 4 int8 elements: [7:0]=e0, [15:8]=e1, [23:16]=e2, [31:24]=e3
  function automatic logic [7:0] get_byte(input logic [31:0] w, input int b);
    case (b)
      0: get_byte = w[7:0];
      1: get_byte = w[15:8];
      2: get_byte = w[23:16];
      default: get_byte = w[31:24];
    endcase
  endfunction

  function automatic logic [31:0] set_byte(input logic [31:0] w, input int b, input logic [7:0] v);
    logic [31:0] t;
    begin
      t = w;
      case (b)
        0: t[7:0]   = v;
        1: t[15:8]  = v;
        2: t[23:16] = v;
        default: t[31:24] = v;
      endcase
      return t;
    end
  endfunction

  // -----------------------------
  // Lanes + predicate
  // -----------------------------
  logic [LANES-1:0] lane_en;
  logic [LANES-1:0][7:0] a_lane, b_lane, y_lane;
  logic [LANES-1:0][31:0] acc_lane;
  logic [LANES-1:0] pred_bits;

  sparsity_mask #(.LANES(LANES)) u_mask(
    .pred_bits(pred_bits),
    .use_pred(cmd_q.use_pred),
    .lane_en(lane_en)
  );

  genvar i;
  generate
    for (i=0; i<LANES; i++) begin : G_LANES
      lane_i8 u_lane (
        .clk(clk), .rst(rst),
        .en(lane_en[i]),
        .a_i8(a_lane[i]),
        .b_i8(b_lane[i]),
        .do_vadd(cmd_q.op == OP_VADD_I8),
        .do_vmac(cmd_q.op == OP_VMAC_I8),
        .acc_clr(st == S_IDLE && cmd_valid && cmd_ready),
        .y_i8(y_lane[i]),
        .acc_i32(acc_lane[i])
      );
    end
  endgenerate

  // Bank selection scaffolding
  logic buf_sel;

  // Control outputs
  assign cmd_ready = (st == S_IDLE);
  assign busy      = (st != S_IDLE) && (st != S_DONE);
  assign done      = (st == S_DONE);

  // helpers for Vivado: declare loop temps OUTSIDE procedural blocks
  int k;
  int byte_sel;
  
  always_comb begin
      for (k = 0; k < LANES; k++) begin
        a_lane[k] = get_byte(wordA, k);
        b_lane[k] = get_byte(wordB, k);
      end
    end


  // -----------------------------
  // Main FSM (single driver for sp_*)
  // -----------------------------
  
  always_ff @(posedge clk) begin
  if (rst) begin
    st      <= S_IDLE;
    cmd_q   <= '0;
    idx     <= '0;
    wordA   <= '0;
    wordB   <= '0;
    dst_word_q <= '0;
    buf_sel <= 1'b0;
    pred_bits <= '1;

    sp_we    <= 1'b0;
    sp_bank  <= '0;
    sp_addr  <= '0;
    sp_wdata <= '0;

  end else begin
    // defaults
    sp_we   <= 1'b0;
    sp_bank <= (buf_sel ? 1 : 0);

    case (st)

      S_IDLE: begin
        if (cmd_valid && cmd_ready) begin
          cmd_q <= cmd;
          $display("ACCEPT: vl=%0d (0x%0h) srcA=%0d srcB=%0d dst=%0d",
         cmd.vl, cmd.vl, cmd.srcA, cmd.srcB, cmd.dst);

          idx   <= 0;
          pred_bits <= '1;   // scaffold
          st    <= S_SET_A;
        end
      end

      // --------- READ A (sync read: set addr, then capture next cycle) ----------
      S_SET_A: begin
        sp_addr <= cmd_q.srcA + (idx >> 2);
        st      <= S_GET_A;
      end
      S_GET_A: begin
        wordA <= sp_rdata;
        st    <= S_SET_B;
      end

      // --------- READ B ----------
      S_SET_B: begin
        sp_addr <= cmd_q.srcB + (idx >> 2);
        st      <= S_GET_B;
      end
      S_GET_B: begin
        wordB <= sp_rdata;
        st    <= S_PREP;
      end

      // --------- PREP lanes (one cycle to present stable a_lane/b_lane) ----------
      S_PREP: begin
        // a_lane/b_lane are driven combinationally from wordA/wordB and idx
        // give lane_i8 a full cycle with stable inputs
        st <= S_EXEC;
      end

      // --------- EXEC (lane_i8 captures result on this clock edge) ----------
      S_EXEC: begin
        st <= S_SET_DST;
      end

      // --------- READ DST word for RMW ----------
      S_SET_DST: begin
        sp_addr <= cmd_q.dst + (idx >> 2);
        st      <= S_GET_DST;
      end
      S_GET_DST: begin
        dst_word_q <= sp_rdata;
        st         <= S_WRITE;
      end

      // --------- WRITEBACK ----------
      S_WRITE: begin
        if (cmd_q.op == formats::OP_VADD_I8) begin
          logic [31:0] outw;
          outw = dst_word_q;

          for (int k = 0; k < LANES; k++) begin
            outw = set_byte(outw, k, y_lane[k]);
          end
          
          $display("idx=%0d wordA=%h wordB=%h y=%02h %02h %02h %02h",
         idx, wordA, wordB, y_lane[0], y_lane[1], y_lane[2], y_lane[3]);

          sp_we    <= 1'b1;
          sp_addr  <= cmd_q.dst + (idx >> 2);
          sp_wdata <= outw;
        end

        if (idx + LANES >= cmd_q.vl) begin
          st <= S_DONE;
        end else begin
          idx <= idx + LANES;
          st  <= S_SET_A;
        end
      end

      S_DONE: begin
        st <= S_IDLE;
      end

      default: st <= S_IDLE;
    endcase
  end
end

  


endmodule
