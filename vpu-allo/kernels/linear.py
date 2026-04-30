"""
kernels/linear.py — INT8 GEMM (single linear layer) in the Allo DSL.

Y[i] = sum_k( W[i,k] * X[k] )    INT8 weights/activations, INT32 accumulator

Optimised schedule notes
------------------------
The original loop nest is:
  i (range M) → k (reduction K)

After reorder("k", "i"):
  k (reduction K) → i (range M)     ← i is now innermost

buffer_at rules:
  - "Cannot buffer at the inner-most loop" — so after reorder, axis="i"
    is innermost and is rejected.
  - Solution: do NOT reorder. Keep i outer, k inner. Then buffer_at(Y, axis="i")
    places the buffer at the i level (outermost), which is valid.
    The structure becomes: i → [k_init, k_body, k_back] with a row buffer for Y.
  - Then pipeline("k") pipelines the reduction body.

So the correct optimised schedule for linear_i8 is:
  buffer_at(Y, axis="i") — row accumulator buffer, no reorder needed
  pipeline("k")           — pipeline the reduction
"""

import allo
from allo.ir.types import int8, int32
import numpy as np

M = 8
K = 16
LANES = 4


def linear_i8(W: int8[M, K], X: int8[K]) -> int32[M]:
    """INT8 linear layer. Y[i] = sum_k(W[i,k] * X[k]), accumulated in INT32."""
    Y: int32[M] = 0
    for i in range(M):
        for k in allo.reduction(K):
            w_w: int32 = W[i, k]
            x_w: int32 = X[k]
            Y[i] += w_w * x_w
    return Y


def build_baseline():
    s = allo.customize(linear_i8)
    return s.build(target="llvm")


def _opt_schedule():
    """
    buffer_at(Y, axis="i") — on-chip row accumulator at the i level.
                              i is the outer loop so this is valid.
    pipeline("k")           — pipeline the reduction loop (II=1).
    No split/unroll here: the reduction structure after buffer_at creates
    init/body/back loops; further unrolling is left to the HLS tool.
    """
    s = allo.customize(linear_i8)
    s.buffer_at(s.Y, axis="i")
    s.pipeline("k")
    return s


def build_hls_optimized():
    return _opt_schedule()


def get_hls_code() -> str:
    return str(_opt_schedule().build(target="vhls"))


def build_vivado_csim(project: str = "linear.prj"):
    return _opt_schedule().build(target="vivado_hls", mode="csim", project=project)


def build_vivado_cosim(project: str = "linear.prj"):
    return _opt_schedule().build(target="vivado_hls", mode="cosim", project=project)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    from models.golden import linear_i8 as golden_linear

    rng = np.random.default_rng(42)
    W = rng.integers(-5, 5, (M, K), dtype=np.int8)
    x = np.arange(K, dtype=np.int8)
    expected = golden_linear(W, x)
    mod = build_baseline()
    result = mod(W, x)

    print(f"W shape: {W.shape},  x shape: {x.shape}")
    print(f"expected: {expected.tolist()}")
    print(f"allo:     {result.tolist()}")
    if np.array_equal(result, expected):
        print(f"\nPASS: linear_i8 correct for M={M}, K={K}, LANES={LANES}")
    else:
        print("\nFAIL"); sys.exit(1)

    print("\n=== Generated HLS Code ===")
    print(get_hls_code())