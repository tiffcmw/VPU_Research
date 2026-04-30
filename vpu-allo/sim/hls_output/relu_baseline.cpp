
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
) {	// L2
  for (int v2 = 0; v2 < 16; v2++) {	// L7
    v1[v2] = 0;	// L7
  }
  l_S_i_0_i: for (int i = 0; i < 16; i++) {	// L8
    int8_t v4 = v0[i];	// L9
    int32_t v5 = v4;	// L10
    bool v6 = v5 > 0;	// L13
    if (v6) {	// L14
      int8_t v7 = v0[i];	// L15
      v1[i] = v7;	// L16
    }
  }
}

