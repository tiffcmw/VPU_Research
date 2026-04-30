
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
) {	// L3
  for (int v3 = 0; v3 < 16; v3++) {	// L7
    v2[v3] = 0;	// L7
  }
  l_S_i_0_i_outer: for (int i_outer = 0; i_outer < 4; i_outer++) {	// L8
  #pragma HLS pipeline II=1
    l_i_inner: for (int i_inner = 0; i_inner < 4; i_inner++) {	// L9
    #pragma HLS unroll
      int v6 = (i_inner + (i_outer * 4));	// L10
      int8_t v7 = v0[v6];	// L11
      int16_t v8 = v7;	// L12
      int16_t a_w;	// L13
      a_w = v8;	// L14
      int8_t v10 = v1[v6];	// L15
      int16_t v11 = v10;	// L16
      int16_t b_w;	// L17
      b_w = v11;	// L18
      int16_t v13 = a_w;	// L19
      int16_t v14 = b_w;	// L20
      ap_int<17> v15 = v13;	// L21
      ap_int<17> v16 = v14;	// L22
      ap_int<17> v17 = v15 + v16;	// L23
      int16_t v18 = v17;	// L24
      int16_t s;	// L25
      s = v18;	// L26
      int16_t v20 = s;	// L27
      int8_t v21 = v20;	// L28
      v2[v6] = v21;	// L29
    }
  }
}

