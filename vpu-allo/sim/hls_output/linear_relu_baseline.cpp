
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
void linear_relu_i8(
  int8_t v0[8][16],
  int8_t v1[16],
  int8_t v2[8]
) {	// L2
  for (int v3 = 0; v3 < 8; v3++) {	// L7
    v2[v3] = 0;	// L7
  }
  l_S_i_0_i: for (int i = 0; i < 8; i++) {	// L8
    int32_t acc;	// L11
    acc = 0;	// L12
    l_S_k_0_k: for (int k = 0; k < 16; k++) {	// L13
      int8_t v7 = v0[i][k];	// L14
      int32_t v8 = v7;	// L15
      int32_t w_w;	// L16
      w_w = v8;	// L17
      int8_t v10 = v1[k];	// L18
      int32_t v11 = v10;	// L19
      int32_t x_w;	// L20
      x_w = v11;	// L21
      int32_t v13 = w_w;	// L22
      int32_t v14 = x_w;	// L23
      int64_t v15 = v13;	// L24
      int64_t v16 = v14;	// L25
      int64_t v17 = v15 * v16;	// L26
      int32_t v18 = acc;	// L27
      ap_int<65> v19 = v18;	// L28
      ap_int<65> v20 = v17;	// L29
      ap_int<65> v21 = v19 + v20;	// L30
      int32_t v22 = v21;	// L31
      acc = v22;	// L32
    }
    int32_t v23 = acc;	// L34
    int32_t v24 = min(v23, 127);	// L37
    int32_t clamped;	// L38
    clamped = v24;	// L39
    int32_t v26 = clamped;	// L40
    int32_t v27 = max(v26, 0);	// L43
    int32_t relu_val;	// L44
    relu_val = v27;	// L45
    int32_t v29 = relu_val;	// L46
    int8_t v30 = v29;	// L47
    v2[i] = v30;	// L48
  }
}

