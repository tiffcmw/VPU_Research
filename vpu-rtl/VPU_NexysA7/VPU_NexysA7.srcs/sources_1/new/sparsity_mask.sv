module sparsity_mask #(
  parameter int LANES = 4
)(
  input  logic [LANES-1:0] pred_bits,   // 1 = active, 0 = skip
  input  logic             use_pred,
  output logic [LANES-1:0] lane_en
);
  always_comb begin
    lane_en = '1;
    if (use_pred) lane_en = pred_bits;
  end
endmodule
