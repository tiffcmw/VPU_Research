"""
tests/test_kernels.py — Test suites for VMAC, linear, ReLU, and fused linear+ReLU.

Opt-schedule tests verify HLS codegen correctness rather than LLVM execution,
because HLS-specific schedule hints (pipeline, unroll, buffer_at) may not lower
cleanly through the LLVM backend — they're synthesis directives, not CPU ops.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest

from kernels.vadd   import VL, LANES
from kernels.vmac   import vmac_i8, build_baseline as vmac_baseline, build_hls_optimized as vmac_opt_sched
from kernels.linear import M, K, linear_i8, build_baseline as lin_baseline, build_hls_optimized as lin_opt_sched
from kernels.relu   import (
    relu_i8, linear_relu_i8,
    build_relu_baseline, build_relu_hls,
    build_fused_baseline, build_fused_hls,
)
from models.golden import (
    vmac_i8 as golden_vmac,
    relu_i8 as golden_relu,
    linear_i8 as golden_linear,
    linear_relu_i8 as golden_fused,
    pack_i32_to_words,
)


# ============================================================
# VMAC
# ============================================================

class TestVmac:
    @pytest.fixture(scope="class")
    def mod(self):
        return vmac_baseline()

    def test_canonical_inputs(self, mod):
        """Validates the MAC path scaffolded but not exercised in Fall 25."""
        a   = np.arange(VL, dtype=np.int8)
        b   = (2 * np.arange(VL)).astype(np.int8)
        acc = np.zeros(VL, dtype=np.int32)
        np.testing.assert_array_equal(mod(a, b, acc), golden_vmac(a, b, acc))
        print(f"\nPASS: vmac_i8 correct for VL={VL}, LANES={LANES}")

    def test_nonzero_accumulator(self, mod):
        a   = np.ones(VL, dtype=np.int8)
        b   = np.ones(VL, dtype=np.int8)
        acc = np.full(VL, 10, dtype=np.int32)
        np.testing.assert_array_equal(mod(a, b, acc), golden_vmac(a, b, acc))

    def test_zero_operands(self, mod):
        a   = np.zeros(VL, dtype=np.int8)
        b   = np.zeros(VL, dtype=np.int8)
        acc = np.arange(VL, dtype=np.int32)
        np.testing.assert_array_equal(mod(a, b, acc), acc)

    def test_negative_operands(self, mod):
        rng = np.random.default_rng(13)
        a   = rng.integers(-128, 127, VL, dtype=np.int8)
        b   = rng.integers(-128, 127, VL, dtype=np.int8)
        acc = rng.integers(-1000, 1000, VL, dtype=np.int32)
        np.testing.assert_array_equal(mod(a, b, acc), golden_vmac(a, b, acc))

    def test_i32_no_overflow(self, mod):
        a   = np.full(VL, 127, dtype=np.int8)
        b   = np.full(VL, 127, dtype=np.int8)
        acc = np.zeros(VL, dtype=np.int32)
        np.testing.assert_array_equal(mod(a, b, acc), golden_vmac(a, b, acc))

    def test_random_fuzz(self, mod):
        rng = np.random.default_rng(21)
        for _ in range(100):
            a   = rng.integers(-128, 127, VL, dtype=np.int8)
            b   = rng.integers(-128, 127, VL, dtype=np.int8)
            acc = rng.integers(-10000, 10000, VL, dtype=np.int32)
            np.testing.assert_array_equal(mod(a, b, acc), golden_vmac(a, b, acc))

    def test_opt_schedule_hls_codegen(self):
        """Optimised schedule generates valid HLS C++ with expected pragmas."""
        code = str(vmac_opt_sched().build(target="vhls"))
        assert "void vmac_i8" in code
        assert "#pragma HLS" in code


# ============================================================
# Linear layer
# ============================================================

class TestLinear:
    @pytest.fixture(scope="class")
    def mod(self):
        return lin_baseline()

    def test_canonical_inputs(self, mod):
        rng = np.random.default_rng(42)
        W = rng.integers(-5, 5, (M, K), dtype=np.int8)
        x = np.arange(K, dtype=np.int8)
        np.testing.assert_array_equal(mod(W, x), golden_linear(W, x))
        print(f"\nPASS: linear_i8 correct for M={M}, K={K}, LANES={LANES}")

    def test_zero_weight(self, mod):
        W = np.zeros((M, K), dtype=np.int8)
        x = np.arange(K, dtype=np.int8)
        np.testing.assert_array_equal(mod(W, x), np.zeros(M, dtype=np.int32))

    def test_zero_input(self, mod):
        rng = np.random.default_rng(77)
        W = rng.integers(-5, 5, (M, K), dtype=np.int8)
        x = np.zeros(K, dtype=np.int8)
        np.testing.assert_array_equal(mod(W, x), np.zeros(M, dtype=np.int32))

    def test_accumulation_correctness(self, mod):
        """W=all-ones, x=all-ones → Y[i]=K for all i."""
        W = np.ones((M, K), dtype=np.int8)
        x = np.ones(K, dtype=np.int8)
        result = mod(W, x)
        assert result[0] == K, f"Expected {K}, got {result[0]}"
        np.testing.assert_array_equal(result, golden_linear(W, x))

    def test_random_fuzz(self, mod):
        rng = np.random.default_rng(33)
        for _ in range(50):
            W = rng.integers(-10, 10, (M, K), dtype=np.int8)
            x = rng.integers(-128, 127, K, dtype=np.int8)
            np.testing.assert_array_equal(mod(W, x), golden_linear(W, x))

    def test_opt_schedule_hls_codegen(self):
        """Optimised schedule generates valid HLS C++ (buffer_at + pipeline)."""
        code = str(lin_opt_sched().build(target="vhls"))
        assert "void linear_i8" in code
        assert "#pragma HLS" in code


# ============================================================
# ReLU
# ============================================================

class TestRelu:
    @pytest.fixture(scope="class")
    def mod(self):
        return build_relu_baseline()

    def test_all_positive(self, mod):
        x = np.arange(1, VL + 1, dtype=np.int8)
        np.testing.assert_array_equal(mod(x), golden_relu(x))

    def test_all_negative(self, mod):
        x = -np.arange(1, VL + 1, dtype=np.int8)
        np.testing.assert_array_equal(mod(x), np.zeros(VL, dtype=np.int8))

    def test_mixed(self, mod):
        x = np.array([-4,-1,0,2,5,-10,3,7,-3,0,1,9,-7,4,-2,6], dtype=np.int8)
        np.testing.assert_array_equal(mod(x), golden_relu(x))

    def test_zero_passthrough(self, mod):
        x = np.zeros(VL, dtype=np.int8)
        np.testing.assert_array_equal(mod(x), np.zeros(VL, dtype=np.int8))


# ============================================================
# Fused Linear + ReLU
# ============================================================

class TestLinearRelu:
    @pytest.fixture(scope="class")
    def mod(self):
        return build_fused_baseline()

    def test_canonical_inputs(self, mod):
        rng = np.random.default_rng(0)
        W = rng.integers(-5, 5, (M, K), dtype=np.int8)
        x = np.arange(K, dtype=np.int8)
        np.testing.assert_array_equal(mod(W, x), golden_fused(W, x))
        print(f"\nPASS: linear_relu_i8 correct for M={M}, K={K}")

    def test_relu_zeros_negatives(self, mod):
        W = -np.eye(M, K, dtype=np.int8)
        x = np.ones(K, dtype=np.int8)
        result = mod(W, x)
        np.testing.assert_array_equal(result, golden_fused(W, x))
        assert np.all(result >= 0)

    def test_saturation_clip(self, mod):
        W = np.full((M, K), 5, dtype=np.int8)
        x = np.full(K, 5, dtype=np.int8)
        result = mod(W, x)
        np.testing.assert_array_equal(result, golden_fused(W, x))
        assert np.all(result <= 127)

    def test_random_fuzz(self, mod):
        rng = np.random.default_rng(64)
        for _ in range(50):
            W = rng.integers(-5, 5, (M, K), dtype=np.int8)
            x = rng.integers(-128, 127, K, dtype=np.int8)
            np.testing.assert_array_equal(mod(W, x), golden_fused(W, x))

    def test_fused_vs_unfused_golden(self, mod):
        rng = np.random.default_rng(101)
        for _ in range(30):
            W = rng.integers(-5, 5, (M, K), dtype=np.int8)
            x = rng.integers(-128, 127, K, dtype=np.int8)
            np.testing.assert_array_equal(mod(W, x), golden_fused(W, x))

    def test_opt_schedule_hls_codegen(self):
        code = str(build_fused_hls().build(target="vhls"))
        assert "void linear_relu_i8" in code
        assert "#pragma HLS" in code


if __name__ == "__main__":
    import subprocess
    sys.exit(subprocess.call(["pytest", __file__, "-v"]))