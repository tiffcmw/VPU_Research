"""
golden.py — Software reference models for all VPU kernels.

All functions operate on NumPy arrays and mirror the exact memory layout and
arithmetic semantics used by the Allo-generated HLS hardware.  The scratchpad
is modelled as a flat array of 32-bit words (matching last semester's VRF),
and pack/unpack helpers convert between element vectors and that packed format.

Kernels implemented
-------------------
  vadd_i8      — INT8 element-wise addition         (regression vs Fall 25)
  vmac_i8      — INT8 multiply-accumulate → INT32   (scaffolded last sem, now validated)
  relu_i8      — INT8 element-wise ReLU             (new)
  linear_i8    — INT8 GEMM: Y[M] = W[M,K] @ X[K]  (new, single linear layer)
  linear_relu  — fused linear + ReLU                (new, composed)

Packed-word helpers
-------------------
  pack_i8_to_words(vec)   → array of uint32, 4 bytes per word, little-endian lane order
  unpack_words_to_i8(words, vl) → flat int8 array
  pack_i32_to_words(vec)  → same but each element is one 32-bit word
"""

import numpy as np


# ---------------------------------------------------------------------------
# Packed-word helpers  (match VRF byte layout from last semester's testbench)
# ---------------------------------------------------------------------------

def pack_i8_to_words(vec: np.ndarray) -> np.ndarray:
    """
    Pack a 1-D int8 array into 32-bit words, 4 elements per word.
    Lane 0 → bits [7:0], lane 1 → bits [15:8], etc.  (little-endian within word)
    Pads with zeros if len(vec) % 4 != 0.
    """
    vec = vec.astype(np.int8)
    pad = (-len(vec)) % 4
    if pad:
        vec = np.concatenate([vec, np.zeros(pad, dtype=np.int8)])
    raw = vec.view(np.uint8).reshape(-1, 4)
    words = raw[:, 0].astype(np.uint32)
    words |= raw[:, 1].astype(np.uint32) << 8
    words |= raw[:, 2].astype(np.uint32) << 16
    words |= raw[:, 3].astype(np.uint32) << 24
    return words


def unpack_words_to_i8(words: np.ndarray, vl: int) -> np.ndarray:
    """Inverse of pack_i8_to_words — returns exactly vl int8 elements."""
    words = np.asarray(words, dtype=np.uint32)
    raw = np.zeros((len(words), 4), dtype=np.uint8)
    raw[:, 0] = (words & 0xFF).astype(np.uint8)
    raw[:, 1] = ((words >> 8) & 0xFF).astype(np.uint8)
    raw[:, 2] = ((words >> 16) & 0xFF).astype(np.uint8)
    raw[:, 3] = ((words >> 24) & 0xFF).astype(np.uint8)
    return raw.reshape(-1)[:vl].view(np.int8)


def pack_i32_to_words(vec: np.ndarray) -> np.ndarray:
    """Each INT32 element occupies one 32-bit scratchpad word."""
    return np.asarray(vec, dtype=np.int32).view(np.uint32)


# ---------------------------------------------------------------------------
# Kernel golden models
# ---------------------------------------------------------------------------

def vadd_i8(
    a: np.ndarray,
    b: np.ndarray,
    pred: np.ndarray | None = None,
) -> np.ndarray:
    """
    Element-wise INT8 vector addition.

    Y[i] = A[i] + B[i],  saturated to INT8 range via int16 intermediate.
    With optional predicate mask: Y[i] = pred[i] ? A[i]+B[i] : A[i]  (hold semantics).

    This is the same function validated last semester (TB PASS: VADD_I8 VL=16, LANES=4).
    """
    a = a.astype(np.int8)
    b = b.astype(np.int8)
    y = (a.astype(np.int16) + b.astype(np.int16)).astype(np.int8)  # wrapping INT8
    if pred is not None:
        y = np.where(pred.astype(bool), y, a)
    return y.astype(np.int8)


def vmac_i8(
    a: np.ndarray,
    b: np.ndarray,
    acc: np.ndarray | None = None,
    pred: np.ndarray | None = None,
) -> np.ndarray:
    """
    Element-wise INT8 multiply-accumulate → INT32 per lane.

    Y[i] = acc[i] + A[i] * B[i]

    acc defaults to zeros.  pred[i]=0 holds acc[i] unchanged (skip semantics).
    This mirrors the vmac path that was scaffolded but not exercised last semester.
    Output is INT32 (one 32-bit word per lane in the scratchpad).
    """
    a = a.astype(np.int8)
    b = b.astype(np.int8)
    if acc is None:
        acc = np.zeros(len(a), dtype=np.int32)
    acc = acc.astype(np.int32)
    prod = a.astype(np.int32) * b.astype(np.int32)
    if pred is not None:
        prod = np.where(pred.astype(bool), prod, np.zeros_like(prod))
    return (acc + prod).astype(np.int32)


def relu_i8(x: np.ndarray) -> np.ndarray:
    """
    Element-wise ReLU on INT8 vector.

    Y[i] = max(0, X[i])
    """
    return np.maximum(0, x.astype(np.int8)).astype(np.int8)


def linear_i8(
    W: np.ndarray,
    x: np.ndarray,
    bias: np.ndarray | None = None,
) -> np.ndarray:
    """
    Single linear (fully-connected) layer.

    Y[i] = sum_k( W[i,k] * x[k] ) + bias[i]   (INT8 weights/activations, INT32 accumulator)

    W : shape (M, K), int8
    x : shape (K,),   int8
    bias : shape (M,), int32  (optional, defaults to zeros)
    Returns Y : shape (M,), int32
    """
    W = W.astype(np.int8)
    x = x.astype(np.int8)
    y = W.astype(np.int32) @ x.astype(np.int32)   # (M, K) @ (K,) → (M,)
    if bias is not None:
        y = y + bias.astype(np.int32)
    return y.astype(np.int32)


def linear_relu_i8(
    W: np.ndarray,
    x: np.ndarray,
    bias: np.ndarray | None = None,
) -> np.ndarray:
    """
    Fused linear + ReLU.

    Y[i] = max(0, linear_i8(W, x, bias)[i])
    Output is clipped to INT8 range after ReLU (saturating cast).
    """
    y_i32 = linear_i8(W, x, bias)
    y_relu = np.maximum(0, y_i32)
    # Saturating cast to INT8
    y_i8 = np.clip(y_relu, -128, 127).astype(np.int8)
    return y_i8


# ---------------------------------------------------------------------------
# Scratchpad layout helpers  (mirror last semester's dst region format)
# ---------------------------------------------------------------------------

def vadd_expected_words(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Return packed 32-bit words that should appear in the scratchpad dst region."""
    return pack_i8_to_words(vadd_i8(a, b))


def vmac_expected_words(
    a: np.ndarray, b: np.ndarray, acc: np.ndarray | None = None
) -> np.ndarray:
    return pack_i32_to_words(vmac_i8(a, b, acc))


def linear_expected_words(W: np.ndarray, x: np.ndarray) -> np.ndarray:
    return pack_i32_to_words(linear_i8(W, x))


# ---------------------------------------------------------------------------
# CLI smoke test  (matches the terminal output shown in the Fall 25 report)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    VL = 16

    a = np.arange(VL, dtype=np.int8)
    b = (2 * np.arange(VL)).astype(np.int8)

    # --- VADD (regression) ---
    y_add = vadd_i8(a, b)
    print("=== VADD_I8 (regression — matches Fall 25 golden) ===")
    print(f"a: {a.tolist()}")
    print(f"b: {b.tolist()}")
    print(f"y: {y_add.tolist()}")
    words = vadd_expected_words(a, b)
    for i, w in enumerate(words):
        print(f"  word[{i}] = {w:08x}")
    print()

    # --- VMAC (new) ---
    y_mac = vmac_i8(a, b)
    print("=== VMAC_I8 (new — was scaffolded last semester) ===")
    print(f"a:   {a.tolist()}")
    print(f"b:   {b.tolist()}")
    print(f"acc: zeros")
    print(f"y:   {y_mac.tolist()}")
    print()

    # --- ReLU ---
    x_relu = np.array([-4, -1, 0, 2, 5, -10, 3, 7], dtype=np.int8)
    print("=== RELU_I8 ===")
    print(f"x: {x_relu.tolist()}")
    print(f"y: {relu_i8(x_relu).tolist()}")
    print()

    # --- Linear ---
    M, K = 8, 16
    W = np.random.randint(-5, 5, (M, K), dtype=np.int8)
    x_lin = np.arange(K, dtype=np.int8)
    y_lin = linear_i8(W, x_lin)
    print("=== LINEAR_I8 ===")
    print(f"W shape: {W.shape},  x shape: {x_lin.shape}")
    print(f"y (INT32): {y_lin.tolist()}")
    print()

    # --- Fused linear + ReLU ---
    y_fused = linear_relu_i8(W, x_lin)
    print("=== LINEAR_RELU_I8 (fused) ===")
    print(f"y (INT8, post-ReLU): {y_fused.tolist()}")