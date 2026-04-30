"""
kernels/vmac.py — INT8 vector multiply-accumulate in the Allo DSL.

Validates the MAC path scaffolded but not exercised in Fall 25 (Section 7).
Y[i] = ACC[i] + (int32)A[i] * (int32)B[i]
"""

import allo
from allo.ir.types import int8, int32
import numpy as np

VL = 16
LANES = 4


def vmac_i8(A: int8[VL], B: int8[VL], ACC: int32[VL]) -> int32[VL]:
    """Element-wise multiply-accumulate. INT8 operands widened to INT32."""
    Y: int32[VL] = 0
    for i in range(VL):
        a_w: int32 = A[i]
        b_w: int32 = B[i]
        Y[i] = ACC[i] + a_w * b_w
    return Y


def build_baseline():
    s = allo.customize(vmac_i8)
    return s.build(target="llvm")


def _opt_schedule():
    """split → unroll inner → pipeline outer (same pattern as vadd)."""
    s = allo.customize(vmac_i8)
    s.split("i", factor=LANES)
    s.unroll("i.inner")
    s.pipeline("i.outer")
    return s


def build_hls_optimized():
    return _opt_schedule()


def get_hls_code() -> str:
    return str(_opt_schedule().build(target="vhls"))


def build_vivado_csim(project: str = "vmac.prj"):
    return _opt_schedule().build(target="vivado_hls", mode="csim", project=project)


def build_vivado_cosim(project: str = "vmac.prj"):
    return _opt_schedule().build(target="vivado_hls", mode="cosim", project=project)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    from models.golden import vmac_i8 as golden_vmac

    a   = np.arange(VL, dtype=np.int8)
    b   = (2 * np.arange(VL)).astype(np.int8)
    acc = np.zeros(VL, dtype=np.int32)
    expected = golden_vmac(a, b, acc)
    mod = build_baseline()
    result = mod(a, b, acc)

    print(f"a:        {a.tolist()}")
    print(f"b:        {b.tolist()}")
    print(f"expected: {expected.tolist()}")
    print(f"allo:     {result.tolist()}")
    if np.array_equal(result, expected):
        print(f"\nPASS: vmac_i8 correct for VL={VL}, LANES={LANES}")
    else:
        print("\nFAIL"); sys.exit(1)

    print("\n=== Generated HLS Code ===")
    print(get_hls_code())