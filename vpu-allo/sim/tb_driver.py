"""
sim/tb_driver.py — Scratchpad preload sequence generator.

Generates the same tb_sp_* preload sequences used by last semester's
self-checking SystemVerilog testbench (Fall 25 report Section 5.2).
This allows waveforms from the Allo-generated cosim to be compared
directly against the Fall 25 VPU_NexysA7 XSim screenshots.

The scratchpad layout assumed here is:
  Bank 0 : src_A  starting at word address SRC_A
  Bank 0 : src_B  starting at word address SRC_B
  Bank 0 : dst    starting at word address DST_BASE  (written by VPU core)

These constants match the Fall 25 testbench parameters.

Outputs
-------
  sim/hls_output/tb_preload_<kernel>.txt   — human-readable word-by-word preload log
  sim/hls_output/tb_preload_<kernel>.mem   — Xilinx $readmemh-compatible hex file
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.golden import (
    pack_i8_to_words, pack_i32_to_words,
    vadd_i8, vmac_i8, linear_i8, relu_i8,
)
from kernels.vadd   import VL, LANES
from kernels.linear import M, K

OUT_DIR = os.path.join(os.path.dirname(__file__), "hls_output")

# Scratchpad address layout (matches Fall 25 testbench defaults)
SRC_A    = 0
SRC_B    = SRC_A + VL // 4   # 4 bytes per word
DST_BASE = 32                 # same as Fall 25: dst = 32


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_preload(name: str, addr_data: list[tuple[int, int]]) -> None:
    """
    Write a preload sequence as both a human-readable log and a .mem hex file.

    addr_data : list of (word_address, 32-bit value) tuples.
    """
    os.makedirs(OUT_DIR, exist_ok=True)

    log_path = os.path.join(OUT_DIR, f"tb_preload_{name}.txt")
    mem_path = os.path.join(OUT_DIR, f"tb_preload_{name}.mem")

    with open(log_path, "w") as f_log, open(mem_path, "w") as f_mem:
        # .mem file: one hex word per line, address comments for readability
        # Pad to DST_BASE + output words so readmemh loads a contiguous block
        max_addr = max(a for a, _ in addr_data)
        mem_flat = ["00000000"] * (max_addr + 1)

        for addr, val in addr_data:
            hex_val = f"{val & 0xFFFFFFFF:08x}"
            f_log.write(f"addr={addr:3d}  data={hex_val}\n")
            mem_flat[addr] = hex_val

        for line in mem_flat:
            f_mem.write(line + "\n")

    print(f"  [tb_driver] {log_path}")
    print(f"  [tb_driver] {mem_path}")


# ---------------------------------------------------------------------------
# VADD preload  (regression — mirrors Fall 25 console output exactly)
# ---------------------------------------------------------------------------

def generate_vadd_preload(vl: int = VL) -> None:
    """
    Reproduce the scratchpad preload that the Fall 25 testbench would issue
    for VADD_I8 with a = [0,1,…,15], b = [0,2,…,30].

    Console format matches Fig 5 of the Fall 25 report:
      mem[0][0]=03020100  (expect 03020100-ish)
      idx=0 wordA=03020100 wordB=06040200 y=00 03 06 09
      ...
    """
    a = np.arange(vl, dtype=np.int8)
    b = (2 * np.arange(vl)).astype(np.int8)
    y = vadd_i8(a, b)

    words_a   = pack_i8_to_words(a)
    words_b   = pack_i8_to_words(b)
    words_exp = pack_i8_to_words(y)

    # Print the exact log format from Fig 5
    print(f"\n=== VADD preload log (VL={vl}, LANES={LANES}) ===")
    for i, (wa, wb) in enumerate(zip(words_a, words_b)):
        lane_a = [(wa >> (8*j)) & 0xFF for j in range(4)]
        lane_b = [(wb >> (8*j)) & 0xFF for j in range(4)]
        lane_y = words_exp[i]
        ys = [(words_exp[i] >> (8*j)) & 0xFF for j in range(4)]
        print(f"idx={i*4:2d} wordA={wa:08x} wordB={wb:08x} "
              f"y={ys[0]:02x} {ys[1]:02x} {ys[2]:02x} {ys[3]:02x}")

    # Build preload addr→data list
    entries = []
    for i, w in enumerate(words_a):
        entries.append((SRC_A + i, int(w)))
    for i, w in enumerate(words_b):
        entries.append((SRC_B + i, int(w)))
    # Expected dst (for testbench PASS checking)
    print(f"\nExpected dst words:")
    for i, w in enumerate(words_exp):
        print(f"  DST[{DST_BASE + i}] = {w:08x}  (EXP={w:08x})")
        entries.append((DST_BASE + i, int(w)))

    _write_preload("vadd", entries)


# ---------------------------------------------------------------------------
# VMAC preload
# ---------------------------------------------------------------------------

def generate_vmac_preload(vl: int = VL) -> None:
    a   = np.arange(vl, dtype=np.int8)
    b   = (2 * np.arange(vl)).astype(np.int8)
    acc = np.zeros(vl, dtype=np.int32)
    y   = vmac_i8(a, b, acc)

    words_a   = pack_i8_to_words(a)
    words_b   = pack_i8_to_words(b)
    words_acc = pack_i32_to_words(acc)
    words_exp = pack_i32_to_words(y)

    print(f"\n=== VMAC preload log (VL={vl}, LANES={LANES}) ===")
    for i in range(len(words_exp)):
        print(f"  dst[{i}] expected = {words_exp[i]:08x}  ({y[i]})")

    ACC_BASE = SRC_B + len(words_b)
    entries = []
    for i, w in enumerate(words_a):   entries.append((SRC_A    + i, int(w)))
    for i, w in enumerate(words_b):   entries.append((SRC_B    + i, int(w)))
    for i, w in enumerate(words_acc): entries.append((ACC_BASE + i, int(w)))
    for i, w in enumerate(words_exp): entries.append((DST_BASE + i, int(w)))

    _write_preload("vmac", entries)


# ---------------------------------------------------------------------------
# Linear layer preload
# ---------------------------------------------------------------------------

def generate_linear_preload() -> None:
    rng = np.random.default_rng(42)
    W   = rng.integers(-5, 5, (M, K), dtype=np.int8)
    x   = np.arange(K, dtype=np.int8)
    y   = linear_i8(W, x)

    words_x   = pack_i8_to_words(x)
    words_exp = pack_i32_to_words(y)

    # W is a 2-D matrix; store row-major, each row starts at a new word boundary
    W_words = []
    for row in W:
        W_words.extend(pack_i8_to_words(row).tolist())

    print(f"\n=== LINEAR preload log (M={M}, K={K}) ===")
    for i, yw in enumerate(words_exp):
        print(f"  Y[{i}] = {yw:08x}  ({y[i]})")

    W_BASE  = 0
    X_BASE  = W_BASE + len(W_words)
    entries = []
    for i, w in enumerate(W_words):   entries.append((W_BASE  + i, int(w)))
    for i, w in enumerate(words_x):   entries.append((X_BASE  + i, int(w)))
    for i, w in enumerate(words_exp): entries.append((DST_BASE + i, int(w)))

    _write_preload("linear", entries)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    generate_vadd_preload()
    generate_vmac_preload()
    generate_linear_preload()
    print("\nAll preload files written to", OUT_DIR)