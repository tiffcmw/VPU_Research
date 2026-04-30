"""
sim/generate_hls.py — HLS code generation and Vivado simulation launcher.

Usage
-----
  python generate_hls.py --hls-only              # dump HLS C++ for all kernels
  python generate_hls.py --mode csim             # Vivado C-sim
  python generate_hls.py --mode cosim            # RTL co-sim (Vivado XSim)
  python generate_hls.py --kernel vadd --hls-only
  python generate_hls.py --list
"""

import argparse, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from kernels.vadd   import VL, LANES
from kernels.linear import M, K

# Schedule builders — each returns a fresh allo.Schedule object
from schedules.schedule_baseline import (
    baseline_vadd, baseline_vmac, baseline_linear,
    baseline_relu, baseline_linear_relu,
)
from schedules.schedule_opt import (
    opt_vadd, opt_vmac, opt_linear, opt_relu, opt_linear_relu,
)

# Golden models
from models.golden import vadd_i8, vmac_i8, linear_i8, linear_relu_i8, relu_i8

# ---------------------------------------------------------------------------
# Input fixtures
# ---------------------------------------------------------------------------

def make_vadd_inputs():
    return np.arange(VL, dtype=np.int8), (2*np.arange(VL)).astype(np.int8)

def make_vmac_inputs():
    return (np.arange(VL, dtype=np.int8),
            (2*np.arange(VL)).astype(np.int8),
            np.zeros(VL, dtype=np.int32))

def make_linear_inputs():
    rng = np.random.default_rng(42)
    return rng.integers(-5, 5, (M, K), dtype=np.int8), np.arange(K, dtype=np.int8)

def make_relu_inputs():
    return (np.array([-4,-1,0,2,5,-10,3,7,-3,0,1,9,-7,4,-2,6], dtype=np.int8),)

def make_linear_relu_inputs():
    return make_linear_inputs()

# ---------------------------------------------------------------------------
# Kernel registry
# ---------------------------------------------------------------------------

KERNELS = {
    "vadd": {
        "baseline": baseline_vadd,
        "opt":      opt_vadd,
        "inputs":   make_vadd_inputs,
        "golden":   lambda *args: vadd_i8(*args),
    },
    "vmac": {
        "baseline": baseline_vmac,
        "opt":      opt_vmac,
        "inputs":   make_vmac_inputs,
        "golden":   lambda *args: vmac_i8(*args),
    },
    "linear": {
        "baseline": baseline_linear,
        "opt":      opt_linear,
        "inputs":   make_linear_inputs,
        "golden":   lambda *args: linear_i8(*args),
    },
    "relu": {
        "baseline": baseline_relu,
        "opt":      opt_relu,
        "inputs":   make_relu_inputs,
        "golden":   lambda *args: relu_i8(*args),
    },
    "linear_relu": {
        "baseline": baseline_linear_relu,
        "opt":      opt_linear_relu,
        "inputs":   make_linear_relu_inputs,
        "golden":   lambda *args: linear_relu_i8(*args),
    },
}

HLS_OUT_DIR = os.path.join(os.path.dirname(__file__), "hls_output")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
PRJ_DIR     = os.path.join(os.path.dirname(__file__), "vivado_projects")

# ---------------------------------------------------------------------------
# HLS code dump
# ---------------------------------------------------------------------------

def dump_hls_code(kernel_name: str, schedule_name: str, schedule_fn) -> str:
    """
    Build the schedule, emit HLS C++ string via .hls_code, write to file.
    Note: s.build(target='vhls') returns an object; .hls_code is the string.
    """
    os.makedirs(HLS_OUT_DIR, exist_ok=True)
    s = schedule_fn()
    hls_mod = s.build(target="vhls")
    code = hls_mod.hls_code          # ← correct attribute
    out_path = os.path.join(HLS_OUT_DIR, f"{kernel_name}_{schedule_name}.cpp")
    with open(out_path, "w") as f:
        f.write(code)
    print(f"  [hls] Wrote {out_path}")
    return code

# ---------------------------------------------------------------------------
# Simulation runner
# ---------------------------------------------------------------------------

def run_kernel(kernel_name: str, schedule_name: str, mode: str) -> dict:
    kspec    = KERNELS[kernel_name]
    build_fn = kspec[schedule_name]
    inputs   = kspec["inputs"]()
    expected = kspec["golden"](*inputs)

    dump_hls_code(kernel_name, schedule_name, build_fn)

    prj_path = os.path.join(PRJ_DIR, f"{kernel_name}_{schedule_name}.prj")
    os.makedirs(PRJ_DIR, exist_ok=True)
    print(f"  [vivado] {kernel_name}/{schedule_name} → {prj_path}  (mode={mode})")

    s   = build_fn()
    mod = s.build(target="vivado_hls", mode=mode, project=prj_path)

    if mode == "csim":
        result = mod(*inputs)
        passed = np.array_equal(result, expected)
    else:
        mod(*inputs)   # cosim: pass/fail in Vivado XSim log
        passed = True

    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {kernel_name}/{schedule_name}")

    record = {"kernel": kernel_name, "schedule": schedule_name,
              "mode": mode, "status": status, "project": prj_path}

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, f"{kernel_name}_{schedule_name}.json"), "w") as f:
        json.dump(record, f, indent=2)
    return record

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate HLS and run Vivado simulation")
    parser.add_argument("--mode", default="csim", choices=["csim", "cosim"])
    parser.add_argument("--kernel", default="all",
                        help="Kernel name or 'all' (default)")
    parser.add_argument("--schedule", default="all",
                        help="baseline, opt, or all (default)")
    parser.add_argument("--hls-only", action="store_true",
                        help="Only dump HLS C++, do not invoke Vivado")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.list:
        print("Available kernels:", ", ".join(KERNELS.keys()))
        return

    kernels   = list(KERNELS.keys())       if args.kernel   == "all" else [args.kernel]
    schedules = ["baseline", "opt"]        if args.schedule == "all" else [args.schedule]

    all_results = []
    for kname in kernels:
        for sname in schedules:
            print(f"\n--- {kname} / {sname} ---")
            if args.hls_only:
                dump_hls_code(kname, sname, KERNELS[kname][sname])
            else:
                all_results.append(run_kernel(kname, sname, args.mode))

    if all_results:
        print("\n=== Summary ===")
        for r in all_results:
            print(f"  {r['kernel']:14s}  {r['schedule']:8s}  {r['status']}")
        os.makedirs(RESULTS_DIR, exist_ok=True)
        with open(os.path.join(RESULTS_DIR, "summary.json"), "w") as f:
            json.dump(all_results, f, indent=2)


if __name__ == "__main__":
    main()