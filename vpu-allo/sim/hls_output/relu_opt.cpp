
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
void relu_i8(
  int8_t v0[16],
  int8_t v1[16]
) {	// L3
  for (int v2 = 0; v2 < 16; v2++) {	// L7
    v1[v2] = 0;	// L7
  }
  l_S_i_0_i_outer: for (int i_outer = 0; i_outer < 4; i_outer++) {	// L8
  #pragma HLS pipeline II=1
    l_i_inner: for (int i_inner = 0; i_inner < 4; i_inner++) {	// L9
    #pragma HLS unroll
      int v5 = (i_inner + (i_outer * 4));	// L10
      int8_t v6 = v0[v5];	// L11
      int32_t v7 = v6;	// L12
      bool v8 = v7 > 0;	// L13
      if (v8) {	// L14
        int8_t v9 = v0[v5];	// L15
        v1[v5] = v9;	// L16
      }
    }
  }
}

