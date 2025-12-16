module scratchpad #(
  parameter int WORD_W = 32,
  parameter int DEPTH_WORDS = 2048,
  parameter int BANKS = 2
)(
  input  logic clk,

  input  logic                      we,
  input  logic [$clog2(BANKS)-1:0]   bank,
  input  logic [$clog2(DEPTH_WORDS)-1:0] addr,
  input  logic [WORD_W-1:0]          wdata,
  output logic [WORD_W-1:0]          rdata
);

  logic [WORD_W-1:0] mem [BANKS-1:0][DEPTH_WORDS-1:0];

  // write is synchronous
  always_ff @(posedge clk) begin
    if (we) begin
      mem[bank][addr] <= wdata;
    end
  end

  // read is combinational (SIM MODEL)
  always_comb begin
    rdata = mem[bank][addr];
  end

endmodule
