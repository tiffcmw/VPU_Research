"""
kernels/vadd.py — INT8 vector addition in the Allo DSL.

Schedule notes
--------------
unroll() alone on a single loop does NOT create i.outer/i.inner sub-loops —
it just unrolls in place.  To get a named i.outer loop to pipeline, we must
first split("i", factor=LANES) which creates i.outer + i.inner, then
unroll("i.inner") and pipeline("i.outer").
"""

import allo
from allo.ir.types import int8, int16
import numpy as np

VL = 16
LANES = 4
assert VL % LANES == 0


def vadd_i8(A: int8[VL], B: int8[VL]) -> int8[VL]:
    """Element-wise INT8 addition: Y[i] = A[i] + B[i]"""
    Y: int8[VL] = 0
    for i in range(VL):
        a_w: int16 = A[i]
        b_w: int16 = B[i]
        s: int16 = a_w + b_w
        Y[i] = s
    return Y


def build_baseline():
    s = allo.customize(vadd_i8)
    return s.build(target="llvm")


def _opt_schedule():
    """
    split("i", LANES)  → creates i.outer (VL/LANES iters) + i.inner (LANES iters)
    unroll("i.inner")  → fully unrolls the inner lane loop
    pipeline("i.outer") → II=1 on the outer loop
    """
    s = allo.customize(vadd_i8)
    s.split("i", factor=LANES)
    s.unroll("i.inner")
    s.pipeline("i.outer")
    return s


def build_hls_optimized():
    return _opt_schedule()


def get_hls_code() -> str:
    return str(_opt_schedule().build(target="vhls"))


def build_vivado_csim(project: str = "vadd.prj"):
    s = _opt_schedule()
    return s.build(target="vivado_hls", mode="csim", project=project)


def build_vivado_cosim(project: str = "vadd.prj"):
    s = _opt_schedule()
    return s.build(target="vivado_hls", mode="cosim", project=project)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    from models.golden import vadd_i8 as golden_vadd

    a = np.arange(VL, dtype=np.int8)
    b = (2 * np.arange(VL)).astype(np.int8)
    expected = golden_vadd(a, b)
    mod = build_baseline()
    result = mod(a, b)

    print(f"a:        {a.tolist()}")
    print(f"b:        {b.tolist()}")
    print(f"expected: {expected.tolist()}")
    print(f"allo:     {result.tolist()}")
    if np.array_equal(result, expected):
        print(f"\nPASS: vadd_i8 correct for VL={VL}, LANES={LANES}")
    else:
        print("\nFAIL"); sys.exit(1)

    print("\n=== Generated HLS Code ===")
    print(get_hls_code())