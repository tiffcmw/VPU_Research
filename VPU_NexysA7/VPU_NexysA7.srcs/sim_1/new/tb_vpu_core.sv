`timescale 1ns/1ps
import formats::*;

module tb_vpu_core;

  // -----------------------------
  // Parameters
  // -----------------------------
  localparam int LANES = 4;

  // -----------------------------
  // Declarations
  // -----------------------------
  logic clk;
  logic rst;

  logic cmd_valid;
  logic cmd_ready;
  formats::cmd_t cmd;

  logic busy;
  logic done;
  
  

  // TB preload interface to vpu_top
  logic tb_sp_load_en;
  logic tb_sp_we;
  logic [0:0]  tb_sp_bank;   // SP_BANKS=2 -> 1 bit
  logic [10:0] tb_sp_addr;   // SP_DEPTH=2048 -> 11 bits
  logic [31:0] tb_sp_wdata;

  // Test vectors
  byte A    [0:15];
  byte B    [0:15];
  byte Yexp [0:15];

  int errors;
  int w;
  logic [31:0] outw;
  logic [7:0] o0, o1, o2, o3;

  // -----------------------------
  // Clock generation
  // -----------------------------
  initial clk = 1'b0;
  always #5 clk = ~clk;

  // -----------------------------
  // DUT
  // -----------------------------
  vpu_top #(.LANES(LANES)) dut (
    .clk(clk),
    .rst(rst),
    .cmd_valid(cmd_valid),
    .cmd_ready(cmd_ready),
    .cmd(cmd),
    .busy(busy),
    .done(done),

    .tb_sp_load_en(tb_sp_load_en),
    .tb_sp_we(tb_sp_we),
    .tb_sp_bank(tb_sp_bank),
    .tb_sp_addr(tb_sp_addr),
    .tb_sp_wdata(tb_sp_wdata)
  );

  // -----------------------------
  // Task: write one scratchpad word through TB mux
  // -----------------------------
  
    task automatic write_sp(
    input int bank,
    input int addr,
    input logic [31:0] data
    );
    begin
      // setup
      @(posedge clk);
      tb_sp_bank  = bank[0:0];
      tb_sp_addr  = addr[10:0];
      tb_sp_wdata = data;
      tb_sp_we    = 1'b0;
    
      // write (stable addr/data)
      @(posedge clk);
      tb_sp_we = 1'b1;
    
      // deassert
      @(posedge clk);
      tb_sp_we = 1'b0;
    end
    endtask
        

  // -----------------------------
  // Test sequence
  // -----------------------------
  initial begin
    // init defaults
    rst = 1'b1;
    cmd_valid = 1'b0;
    cmd = '0;
    errors = 0;

    // defaults
    tb_sp_load_en = 1'b0;
    tb_sp_we      = 1'b0;
    tb_sp_bank    = '0;
    tb_sp_addr    = '0;
    tb_sp_wdata   = '0;
    
    rst = 1'b1;
    
    // init vectors
    for (int i = 0; i < 16; i++) begin
      A[i]    = byte'(i);
      B[i]    = byte'(2*i);
      Yexp[i] = byte'(A[i] + B[i]);
    end
    
    repeat (2) @(posedge clk);
    
    // -------------------------------------------------
    // Preload scratchpad (TB has exclusive control)
    // -------------------------------------------------
    
    // Assert TB ownership and wait a full cycle
    tb_sp_load_en = 1'b1;
    @(posedge clk);
    
    // preload A and B
    for (int w = 0; w < 4; w++) begin
      write_sp(0, w,
        {A[4*w+3], A[4*w+2], A[4*w+1], A[4*w+0]}
      );
      write_sp(0, 16+w,
        {B[4*w+3], B[4*w+2], B[4*w+1], B[4*w+0]}
      );
    end
    
    // wait one full cycle AFTER last write
    @(posedge clk);
    
    // release scratchpad to core
    tb_sp_load_en = 1'b0;
    
    $display("mem[0][0]=%h (expect 03020100-ish)", dut.u_sp.mem[0][0]);
    $display("mem[0][16]=%h (expect 06040200-ish)", dut.u_sp.mem[0][16]);

    
    repeat (5) @(posedge clk);
    rst = 1'b0;



    // Issue VADD command
    cmd.op       = formats::OP_VADD_I8;
    cmd.vl       = 16;
    cmd.srcA     = 0;
    cmd.srcB     = 16;
    cmd.dst      = 32;
    cmd.use_pred = 1'b0;
    cmd.block4   = 1'b0;

    @(posedge clk);
    cmd_valid = 1'b1;
    wait (cmd_ready == 1'b1);
    @(posedge clk);
    cmd_valid = 1'b0;

    
    // Wait long enough for completion
    repeat (300) @(posedge clk);
    
    $display("DST[32]=%h", dut.u_sp.mem[0][32]);
    $display("DST[33]=%h", dut.u_sp.mem[0][33]);
    $display("DST[34]=%h", dut.u_sp.mem[0][34]);
    $display("DST[35]=%h", dut.u_sp.mem[0][35]);
    
    $display("EXP0=%h", {Yexp[3],Yexp[2],Yexp[1],Yexp[0]});
    $display("EXP1=%h", {Yexp[7],Yexp[6],Yexp[5],Yexp[4]});
    $display("EXP2=%h", {Yexp[11],Yexp[10],Yexp[9],Yexp[8]});
    $display("EXP3=%h", {Yexp[15],Yexp[14],Yexp[13],Yexp[12]});
    


    // -----------------------------
    // Check results (peek internal mem for convenience)
    // -----------------------------
    for (w = 0; w < 4; w++) begin
      outw = dut.u_sp.mem[0][32 + w];

      o0 = outw[7:0];
      o1 = outw[15:8];
      o2 = outw[23:16];
      o3 = outw[31:24];

      if (o0 !== Yexp[4*w+0]) errors++;
      if (o1 !== Yexp[4*w+1]) errors++;
      if (o2 !== Yexp[4*w+2]) errors++;
      if (o3 !== Yexp[4*w+3]) errors++;
    end

    if (errors == 0)
      $display("TB PASS: VADD_I8 correct for VL=16, LANES=%0d", LANES);
    else
      $display("TB FAIL: errors=%0d", errors);

    $finish;
  end

endmodule
