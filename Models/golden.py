import numpy as np

def vadd_i8(a: np.ndarray, b: np.ndarray, pred: np.ndarray | None = None) -> np.ndarray:
    a = a.astype(np.int8)
    b = b.astype(np.int8)
    y = (a.astype(np.int16) + b.astype(np.int16)).astype(np.int8)
    if pred is not None:
        y = np.where(pred.astype(bool), y, a.astype(np.int8))  # "skip = hold" semantics
    return y

def vmac_i8(a: np.ndarray, b: np.ndarray, pred: np.ndarray | None = None) -> np.ndarray:
    a = a.astype(np.int8)
    b = b.astype(np.int8)
    prod = a.astype(np.int32) * b.astype(np.int32)
    if pred is not None:
        prod = np.where(pred.astype(bool), prod, 0)
    return np.cumsum(prod, dtype=np.int32)  # example; per-lane acc differs

if __name__ == "__main__":
    a = np.arange(16, dtype=np.int8)
    b = (2*np.arange(16)).astype(np.int8)
    y = vadd_i8(a,b)
    print("a:", a)
    print("b:", b)
    print("y:", y)
