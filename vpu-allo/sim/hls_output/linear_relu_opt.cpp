
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
  for (int v3 = 0; v3 < 8; v3++) {	// L6
    v2[v3] = 0;	// L6
  }
  l_S_i_0_i: for (int i = 0; i < 8; i++) {	// L7
    int32_t acc;	// L8
    acc = 0;	// L9
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
      int32_t v18 = acc;	// L24
      ap_int<65> v19 = v18;	// L25
      ap_int<65> v20 = v17;	// L26
      ap_int<65> v21 = v19 + v20;	// L27
      int32_t v22 = v21;	// L28
      acc = v22;	// L29
    }
    int32_t v23 = acc;	// L31
    int32_t v24 = min(v23, 127);	// L33
    int32_t clamped;	// L34
    clamped = v24;	// L35
    int32_t v26 = clamped;	// L36
    int32_t v27 = max(v26, 0);	// L37
    int32_t relu_val;	// L38
    relu_val = v27;	// L39
    int32_t v29 = relu_val;	// L40
    int8_t v30 = v29;	// L41
    v2[i] = v30;	// L42
  }
}

