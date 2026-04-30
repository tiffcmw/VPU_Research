
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
void linear_i8(
  int8_t v0[8][16],
  int8_t v1[16],
  int32_t v2[8]
) {	// L2
  for (int v3 = 0; v3 < 8; v3++) {	// L5
    v2[v3] = 0;	// L5
  }
  l_S_i_0_i: for (int i = 0; i < 8; i++) {	// L6
    int32_t v5[1];	// L7
    v5[0] = 0;	// L9
    l_S_k_0_k: for (int k = 0; k < 16; k++) {	// L10
    #pragma HLS pipeline II=1
      int8_t v7 = v0[i][k];	// L11
      int32_t v8 = v7;	// L12
      int32_t w_w;	// L13
      w_w = v8;	// L14
      int8_t v10 = v1[k];	// L15
      int32_t v11 = v10;	// L16
      int32_t x_w;	// L17
      x_w = v11;	// L18
      int32_t v13 = w_w;	// L19
      int32_t v14 = x_w;	// L20
      int64_t v15 = v13;	// L21
      int64_t v16 = v14;	// L22
      int64_t v17 = v15 * v16;	// L23
      int32_t v18 = v5[0];	// L24
      ap_int<65> v19 = v18;	// L25
      ap_int<65> v20 = v17;	// L26
      ap_int<65> v21 = v19 + v20;	// L27
      int32_t v22 = v21;	// L28
      v5[0] = v22;	// L29
    }
    int32_t v23 = v5[0];	// L31
    v2[i] = v23;	// L32
  }
}

