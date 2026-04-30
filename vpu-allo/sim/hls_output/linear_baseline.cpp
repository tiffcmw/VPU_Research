
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
    l_S_k_0_k: for (int k = 0; k < 16; k++) {	// L7
      int8_t v6 = v0[i][k];	// L8
      int32_t v7 = v6;	// L9
      int32_t w_w;	// L10
      w_w = v7;	// L11
      int8_t v9 = v1[k];	// L12
      int32_t v10 = v9;	// L13
      int32_t x_w;	// L14
      x_w = v10;	// L15
      int32_t v12 = w_w;	// L16
      int32_t v13 = x_w;	// L17
      int64_t v14 = v12;	// L18
      int64_t v15 = v13;	// L19
      int64_t v16 = v14 * v15;	// L20
      int32_t v17 = v2[i];	// L21
      ap_int<65> v18 = v17;	// L22
      ap_int<65> v19 = v16;	// L23
      ap_int<65> v20 = v18 + v19;	// L24
      int32_t v21 = v20;	// L25
      v2[i] = v21;	// L26
    }
  }
}

