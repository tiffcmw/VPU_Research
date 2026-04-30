"""
schedules/schedule_opt.py — Optimised schedules for all VPU kernels.

SIMD kernels (vadd, vmac, relu):
  split("i", LANES) → i.outer + i.inner
  unroll("i.inner") → fully unrolled lane loop
  pipeline("i.outer") → II=1

Linear layer:
  buffer_at(Y, axis="i") — row accumulator at i (outermost loop, valid).
                            Do NOT reorder first: after reorder("k","i"), i
                            becomes innermost and buffer_at rejects it with
                            "Cannot buffer at the inner-most loop".
  pipeline("k")           — pipeline the reduction body

Fused linear+relu:
  pipeline("k") — same as linear, ReLU inlined after accumulation
"""

import argparse, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import allo
from kernels.vadd   import vadd_i8, VL, LANES
from kernels.vmac   import vmac_i8
from kernels.linear import linear_i8, M, K
from kernels.relu   import relu_i8, linear_relu_i8


def opt_vadd():
    s = allo.customize(vadd_i8)
    s.split("i", factor=LANES)
    s.unroll("i.inner")
    s.pipeline("i.outer")
    return s


def opt_vmac():
    s = allo.customize(vmac_i8)
    s.split("i", factor=LANES)
    s.unroll("i.inner")
    s.pipeline("i.outer")
    return s


def opt_linear():
    s = allo.customize(linear_i8)
    s.buffer_at(s.Y, axis="i")   # i is outermost — valid
    s.pipeline("k")
    return s


def opt_relu():
    s = allo.customize(relu_i8)
    s.split("i", factor=LANES)
    s.unroll("i.inner")
    s.pipeline("i.outer")
    return s


def opt_linear_relu():
    s = allo.customize(linear_relu_i8)
    s.pipeline("k")
    return s


KERNELS = {
    "vadd":        opt_vadd,
    "vmac":        opt_vmac,
    "linear":      opt_linear,
    "relu":        opt_relu,
    "linear_relu": opt_linear_relu,
}


def print_all_hls():
    for name, build_fn in KERNELS.items():
        print(f"\n{'='*60}\n  Optimised HLS — {name}\n{'='*60}")
        print(str(build_fn().build(target="vhls")))


def generate_all_projects(project_dir: str, mode: str = "csim"):
    os.makedirs(project_dir, exist_ok=True)
    results = {}
    for name, build_fn in KERNELS.items():
        prj_path = os.path.join(project_dir, f"{name}_opt.prj")
        print(f"[opt] {name} → {prj_path}  (mode={mode})")
        mod = build_fn().build(target="vivado_hls", mode=mode, project=prj_path)
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