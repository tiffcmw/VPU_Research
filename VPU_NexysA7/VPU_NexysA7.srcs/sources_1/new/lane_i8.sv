module lane_i8 (
  input  logic        clk,
  input  logic        rst,
  input  logic        en,

  input  logic [7:0]  a_i8,
  input  logic [7:0]  b_i8,

  input  logic        do_vadd,
  input  logic        do_vmac,
  input  logic        acc_clr,

  output logic [7:0]  y_i8,
  output logic [31:0] acc_i32
);

  // signed views
  logic signed [7:0]  a_s, b_s;
  logic signed [8:0]  sum_s;
  logic signed [31:0] acc_next;

  always_comb begin
    a_s = a_i8;
    b_s = b_i8;
    sum_s = a_s + b_s;
    acc_next = acc_i32 + sum_s;
  end

  always_ff @(posedge clk) begin
    if (rst) begin
      y_i8   <= '0;
      acc_i32 <= '0;
    end else if (acc_clr) begin
      acc_i32 <= '0;
      y_i8    <= '0;
    end else if (en) begin
      if (do_vadd) begin
        y_i8 <= sum_s[7:0];
      end
      if (do_vmac) begin
        acc_i32 <= acc_next;
      end
    end
  end

endmodule
