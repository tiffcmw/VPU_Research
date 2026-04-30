
//===------------------------------------------------------------*- C++ -*-===//
//
// Automatically generated file for High-level Synthesis (HLS).
//
//===----------------------------------------------------------------------===//
#include <algorithm>
#include <ap_axi_sdata.h>
#include <ap_fixed.h>
#include <ap_int.h>
#include <hls_math.h>
#include <hls_stream.h>
#include <hls_vector.h>
#include <math.h>
#include <stdint.h>
using namespace std;
/// This is top function.
void vmac_i8(
  int8_t v0[16],
  int8_t v1[16],
  int32_t v2[16],
  int32_t v3[16]
) {	// L3
  for (int v4 = 0; v4 < 16; v4++) {	// L6
    v3[v4] = 0;	// L6
  }
  l_S_i_0_i_outer: for (int i_outer = 0; i_outer < 4; i_outer++) {	// L7
  #pragma HLS pipeline II=1
    l_i_inner: for (int i_inner = 0; i_inner < 4; i_inner++) {	// L8
    #pragma HLS unroll
      int v7 = (i_inner + (i_outer * 4));	// L9
      int8_t v8 = v0[v7];	// L10
      int32_t v9 = v8;	// L11
      int32_t a_w;	// L12
      a_w = v9;	// L13
      int8_t v11 = v1[v7];	// L14
      int32_t v12 = v11;	// L15
      int32_t b_w;	// L16
      b_w = v12;	// L17
      int32_t v14 = v2[v7];	// L18
      int32_t v15 = a_w;	// L19
      int32_t v16 = b_w;	// L20
      int64_t v17 = v15;	// L21
      int64_t v18 = v16;	// L22
      int64_t v19 = v17 * v18;	// L23
      ap_int<65> v20 = v14;	// L24
      ap_int<65> v21 = v19;	// L25
      ap_int<65> v22 = v20 + v21;	// L26
      int32_t v23 = v22;	// L27
      v3[v7] = v23;	// L28
    }
  }
}

