"""
kernels/relu.py — INT8 ReLU and fused linear+ReLU in the Allo DSL.
"""

import allo
from allo.ir.types import int8, int32
import numpy as np

VL = 16
M  = 8
K  = 16
LANES = 4


def relu_i8(X: int8[VL]) -> int8[VL]:
    """Element-wise ReLU: Y[i] = max(0, X[i])"""
    Y: int8[VL] = 0
    for i in range(VL):
        if X[i] > 0:
            Y[i] = X[i]
    return Y


def linear_relu_i8(W: int8[M, K], X: int8[K]) -> int8[M]:
    """
    Fused linear + ReLU.
    acc[i] = sum_k(W[i,k]*X[k])  in INT32, then Y[i] = max(0, clip(acc, -128,127))

    acc declared in i-loop scope (outside k-loop) — required by Allo's
    C++-style block scoping: variables declared inside a loop block are not
    visible after that block exits.
    """
    Y: int8[M] = 0
    for i in range(M):
        acc: int32 = 0
        for k in allo.reduction(K):
            w_w: int32 = W[i, k]
            x_w: int32 = X[k]
            acc += w_w * x_w
        clamped: int32 = min(acc, 127)
        relu_val: int32 = max(clamped, 0)
        Y[i] = relu_val
    return Y


def build_relu_baseline():
    s = allo.customize(relu_i8)
    return s.build(target="llvm")


def _relu_opt_schedule():
    s = allo.customize(relu_i8)
    s.split("i", factor=LANES)
    s.unroll("i.inner")
    s.pipeline("i.outer")
    return s


def build_relu_hls():
    return _relu_opt_schedule()


def build_fused_baseline():
    s = allo.customize(linear_relu_i8)
    return s.build(target="llvm")


def _fused_opt_schedule():
    s = allo.customize(linear_relu_i8)
    s.pipeline("k")
    return s


def build_fused_hls():
    return _fused_opt_schedule()


def get_relu_hls_code() -> str:
    return str(_relu_opt_schedule().build(target="vhls"))


def get_fused_hls_code() -> str:
    return str(_fused_opt_schedule().build(target="vhls"))


def build_vivado_csim(project: str = "linear_relu.prj"):
    return _fused_opt_schedule().build(target="vivado_hls", mode="csim", project=project)


def build_vivado_cosim(project: str = "linear_relu.prj"):
    return _fused_opt_schedule().build(target="vivado_hls", mode="cosim", project=project)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    from models.golden import relu_i8 as golden_relu, linear_relu_i8 as golden_fused

    x_relu = np.array([-4,-1,0,2,5,-10,3,7,-3,0,1,9,-7,4,-2,6], dtype=np.int8)
    result_relu = build_relu_baseline()(x_relu)
    expected_relu = golden_relu(x_relu)
    print(f"x:        {x_relu.tolist()}")
    print(f"expected: {expected_relu.tolist()}")
    print(f"allo:     {result_relu.tolist()}")
    if np.array_equal(result_relu, expected_relu):
        print(f"PASS: relu_i8 correct for VL={VL}")
    else:
        print("FAIL"); sys.exit(1)

    print()
    rng = np.random.default_rng(0)
    W = rng.integers(-5, 5, (M, K), dtype=np.int8)
    x = np.arange(K, dtype=np.int8)
    result_fused = build_fused_baseline()(W, x)
    expected_fused = golden_fused(W, x)
    print(f"expected: {expected_fused.tolist()}")
    print(f"allo:     {result_fused.tolist()}")
    if np.array_equal(result_fused, expected_fused):
        print(f"PASS: linear_relu_i8 correct for M={M}, K={K}")
    else:
        print("FAIL"); sys.exit(1)

    print("\n=== Fused HLS Code ===")
    print(get_fused_hls_code())