
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
) {	// L2
  for (int v4 = 0; v4 < 16; v4++) {	// L5
    v3[v4] = 0;	// L5
  }
  l_S_i_0_i: for (int i = 0; i < 16; i++) {	// L6
    int8_t v6 = v0[i];	// L7
    int32_t v7 = v6;	// L8
    int32_t a_w;	// L9
    a_w = v7;	// L10
    int8_t v9 = v1[i];	// L11
    int32_t v10 = v9;	// L12
    int32_t b_w;	// L13
    b_w = v10;	// L14
    int32_t v12 = v2[i];	// L15
    int32_t v13 = a_w;	// L16
    int32_t v14 = b_w;	// L17
    int64_t v15 = v13;	// L18
    int64_t v16 = v14;	// L19
    int64_t v17 = v15 * v16;	// L20
    ap_int<65> v18 = v12;	// L21
    ap_int<65> v19 = v17;	// L22
    ap_int<65> v20 = v18 + v19;	// L23
    int32_t v21 = v20;	// L24
    v3[i] = v21;	// L25
  }
}

