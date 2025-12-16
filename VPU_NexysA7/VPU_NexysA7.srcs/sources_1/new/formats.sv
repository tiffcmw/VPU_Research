package formats;

  // Feature flags (compile-time scaffolding)
  parameter bit FEAT_INT8      = 1'b1;   // baseline now
  parameter bit FEAT_FP16_BF16 = 1'b0;   // scaffold later
  parameter bit FEAT_PRED_MASK = 1'b1;   // baseline now
  parameter bit FEAT_BLOCK4    = 1'b0;   // scaffold later
  parameter bit FEAT_DMA       = 1'b0;   // stub now (set 1 later)

  typedef enum logic [2:0] {
    OP_NOP      = 3'd0,
    OP_VADD_I8  = 3'd1, // elementwise int8 add -> int8 (or int16/32 future)
    OP_VMAC_I8  = 3'd2, // int8 multiply-accumulate -> int32
    OP_LOAD     = 3'd3, // scaffold
    OP_STORE    = 3'd4  // scaffold
  } op_t;

  typedef struct packed {
    op_t  op;
    logic [7:0]  vl;        // vector length in elements (per lane strides simplified)
    logic [15:0] srcA;      // scratchpad address (word index)
    logic [15:0] srcB;      // scratchpad address (word index)
    logic [15:0] dst;       // scratchpad address (word index)
    logic [15:0] pred;      // scratchpad address of predicate mask bits (scaffold)
    logic        use_pred;  // enable predication (zero-skip)
    logic        block4;    // enable 4x4 block sparse mode (scaffold)
  } cmd_t;

endpackage
