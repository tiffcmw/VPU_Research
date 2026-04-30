"""
schedules/schedule_baseline.py — Unoptimized schedules for all kernels.

No pragmas added — establishes the HLS tool's unguided baseline for comparison.
"""

import argparse, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import allo
from kernels.vadd   import vadd_i8, VL, LANES
from kernels.vmac   import vmac_i8
from kernels.linear import linear_i8, M, K
from kernels.relu   import relu_i8, linear_relu_i8


def baseline_vadd():
    return allo.customize(vadd_i8)

def baseline_vmac():
    return allo.customize(vmac_i8)

def baseline_linear():
    return allo.customize(linear_i8)

def baseline_relu():
    return allo.customize(relu_i8)

def baseline_linear_relu():
    return allo.customize(linear_relu_i8)


KERNELS = {
    "vadd":        baseline_vadd,
    "vmac":        baseline_vmac,
    "linear":      baseline_linear,
    "relu":        baseline_relu,
    "linear_relu": baseline_linear_relu,
}


def print_all_hls():
    for name, build_fn in KERNELS.items():
        print(f"\n{'='*60}")
        print(f"  Baseline HLS — {name}")
        print(f"{'='*60}")
        s = build_fn()
        print(s.build(target="vhls"))


def generate_all_projects(project_dir: str, mode: str = "csim"):
    os.makedirs(project_dir, exist_ok=True)
    results = {}
    for name, build_fn in KERNELS.items():
        prj_path = os.path.join(project_dir, f"{name}_baseline.prj")
        print(f"[baseline] {name} → {prj_path}  (mode={mode})")
        s = build_fn()
        mod = s.build(target="vivado_hls", mode=mode, project=prj_path)
        results[name] = {"project": prj_path, "module": mod}
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default=None)
    parser.add_argument("--mode", default="csim", choices=["csim", "cosim"])
    args = parser.parse_args()

    if args.project_dir:
        generate_all_projects(args.project_dir, mode=args.mode)
    else:
        print_all_hls()