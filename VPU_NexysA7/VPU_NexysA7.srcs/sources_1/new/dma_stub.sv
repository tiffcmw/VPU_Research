module dma_stub #(
  parameter int ADDR_W = 32,
  parameter int LEN_W  = 32
)(
  input  logic clk,
  input  logic rst,

  input  logic        start,
  input  logic [ADDR_W-1:0] src_addr,
  input  logic [ADDR_W-1:0] dst_addr,
  input  logic [LEN_W-1:0]  len_bytes,
  output logic        busy,
  output logic        done
);
  // Stub behavior: immediate completion (for integration scaffolding).
  always_ff @(posedge clk) begin
    if (rst) begin
      busy <= 1'b0;
      done <= 1'b0;
    end else begin
      done <= 1'b0;
      if (start) begin
        busy <= 1'b1;
        // complete next cycle
      end
      if (busy) begin
        busy <= 1'b0;
        done <= 1'b1;
      end
    end
  end
endmodule
