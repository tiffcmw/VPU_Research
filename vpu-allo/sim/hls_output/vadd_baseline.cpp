
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
void vadd_i8(
  int8_t v0[16],
  int8_t v1[16],
  int8_t v2[16]
) {	// L2
  for (int v3 = 0; v3 < 16; v3++) {	// L7
    v2[v3] = 0;	// L7
  }
  l_S_i_0_i: for (int i = 0; i < 16; i++) {	// L8
    int8_t v5 = v0[i];	// L9
    int16_t v6 = v5;	// L10
    int16_t a_w;	// L11
    a_w = v6;	// L12
    int8_t v8 = v1[i];	// L13
    int16_t v9 = v8;	// L14
    int16_t b_w;	// L15
    b_w = v9;	// L16
    int16_t v11 = a_w;	// L17
    int16_t v12 = b_w;	// L18
    ap_int<17> v13 = v11;	// L19
    ap_int<17> v14 = v12;	// L20
    ap_int<17> v15 = v13 + v14;	// L21
    int16_t v16 = v15;	// L22
    int16_t s;	// L23
    s = v16;	// L24
    int16_t v18 = s;	// L25
    int8_t v19 = v18;	// L26
    v2[i] = v19;	// L27
  }
}

