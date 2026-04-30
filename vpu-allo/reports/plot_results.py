"""
reports/plot_results.py — Parse all csynth.rpt files and generate
publication-quality matplotlib figures for the Spring 2026 report.

Usage
-----
  python3 reports/plot_results.py --report-dir reports/synth_reports
  python3 reports/plot_results.py --report-dir reports/synth_reports --out-dir reports/figures/

Outputs (saved to --out-dir, default: reports/figures/)
  fig1_latency.pdf        Grouped bar: latency baseline vs opt, all kernels
  fig2_speedup.pdf        Bar: speedup factor per kernel
  fig3_resources.pdf      Grouped bar: DSP / FF / LUT baseline vs opt
  fig4_memory_access.pdf  Bar: output-array accesses per row (linear only)
  fig5_dsp_util.pdf       Stacked bar: DSP utilisation as % of Artix-7 240 DSPs
  summary_table.tex       LaTeX tabular ready to \input into the report
"""

import argparse
import os
import re
import sys
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ---------------------------------------------------------------------------
# Style — clean academic look
# ---------------------------------------------------------------------------

plt.rcParams.update({
    "font.family":       "serif",
    "font.size":         10,
    "axes.titlesize":    11,
    "axes.labelsize":    10,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "legend.fontsize":   9,
    "figure.dpi":        150,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "axes.grid.axis":    "y",
    "grid.alpha":        0.35,
    "grid.linewidth":    0.6,
})

BLUE   = "#185FA5"
GRAY   = "#73726c"
GREEN  = "#1D9E75"
AMBER  = "#BA7517"
CORAL  = "#D85A30"

# Artix-7 100T resource totals (xc7a100tcsg324-1)
ARTIX7_DSP  = 240
ARTIX7_FF   = 126800
ARTIX7_LUT  = 63400
ARTIX7_BRAM = 135

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

KERNEL_ORDER = ["vadd", "vmac", "linear", "relu", "linear_relu"]
SCHEDULES    = ["baseline", "opt"]

KERNEL_LABELS = {
    "vadd":        "vadd\\_i8",
    "vmac":        "vmac\\_i8",
    "linear":      "linear\\_i8",
    "relu":        "relu\\_i8",
    "linear_relu": "linear\\_relu",
}
KERNEL_LABELS_PLAIN = {
    "vadd":        "vadd_i8",
    "vmac":        "vmac_i8",
    "linear":      "linear_i8",
    "relu":        "relu_i8",
    "linear_relu": "linear_relu",
}


def parse_rpt(path: str) -> dict:
    """Parse a Vitis HLS 2025.1 csynth.rpt and return a metrics dict."""
    text = open(path, encoding="utf-8", errors="replace").read()

    # Identify kernel from header
    kern_match = re.search(r"Synthesis Summary Report of '(\w+)'", text)
    kernel_func = kern_match.group(1) if kern_match else "unknown"

    # Top-level module row:
    # |+ funcname | - | slack | latency_cyc | latency_ns | - | interval | - | pipelined | bram | dsp | ff | lut | uram |
    top = re.search(
        r'^\s*\|\+\s+\w+\s*\|[^|]*\|[^|]*\|\s*(\d+)\s*\|[^|]*\|[^|]*\|\s*(\d+)\s*\|'
        r'[^|]*\|[^|]*\|[^|]*\|\s*([\d\-]+)[^|]*\|\s*([\d\-]+)[^|]*\|\s*([\d\-]+)[^|]*\|',
        text, re.MULTILINE,
    )

    result = {
        "func":        kernel_func,
        "latency":     None,
        "interval":    None,
        "dsp":         None,
        "ff":          None,
        "lut":         None,
        "bram":        None,
        "loop_ii":     None,
        "loop_latency": None,
    }

    if top:
        result["latency"]  = int(top.group(1))
        result["interval"] = int(top.group(2))
        dsp_raw = top.group(3).strip()
        ff_raw  = top.group(4).strip()
        lut_raw = top.group(5).strip()
        result["dsp"] = int(dsp_raw) if dsp_raw.isdigit() else 0
        result["ff"]  = int(ff_raw)  if ff_raw.isdigit()  else 0
        result["lut"] = int(lut_raw) if lut_raw.isdigit() else 0

    # BRAM from same row (column before DSP in some formats; search separately)
    bram = re.search(
        r'^\s*\|\+\s+\w+\s*\|[^|]*\|[^|]*\|\s*\d+\s*\|[^|]*\|[^|]*\|\s*\d+\s*\|'
        r'[^|]*\|[^|]*\|\s*([\d\-]+)[^|]*\|\s*[\d\-]',
        text, re.MULTILINE,
    )
    if bram:
        b = bram.group(1).strip()
        result["bram"] = int(b) if b.isdigit() else 0

    # Loop-level II from lines like:  o LOOP_NAME | II | ... | iter | II | count
    loop = re.search(
        r'o\s+\S+\s*\|\s*II\s*\|[^|]*\|[^|]*\|[^|]*\|\s*(\d+)\s*\|\s*(\d+)',
        text,
    )
    if loop:
        result["loop_latency"] = int(loop.group(1))
        result["loop_ii"]      = int(loop.group(2))

    return result


def load_all(report_dir: str) -> dict:
    """
    Load all csynth.rpt files from report_dir/<kernel>_<schedule>/csynth.rpt.
    Returns nested dict: data[kernel][schedule] = metrics dict.
    """
    data = {k: {} for k in KERNEL_ORDER}

    for kernel in KERNEL_ORDER:
        for sched in SCHEDULES:
            path = os.path.join(report_dir, f"{kernel}_{sched}", "csynth.rpt")
            if os.path.isfile(path):
                parsed = parse_rpt(path)
                parsed["found"] = True
                data[kernel][sched] = parsed
                print(f"  OK  {kernel:12s} {sched:8s}  "
                      f"lat={parsed['latency']}  dsp={parsed['dsp']}  "
                      f"ff={parsed['ff']}  lut={parsed['lut']}")
            else:
                data[kernel][sched] = {"found": False}
                print(f"  --  {kernel:12s} {sched:8s}  (not found: {path})")

    return data


# ---------------------------------------------------------------------------
# Figure helpers
# ---------------------------------------------------------------------------

def savefig(fig, path):
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {path}")


def bar_group(ax, values_a, values_b, labels, colors, bar_labels=("Baseline","Optimised"),
              ylabel="", title=""):
    x = np.arange(len(labels))
    w = 0.35
    bars_a = ax.bar(x - w/2, values_a, w, color=colors[0], label=bar_labels[0],
                    zorder=3, linewidth=0)
    bars_b = ax.bar(x + w/2, values_b, w, color=colors[1], label=bar_labels[1],
                    zorder=3, linewidth=0)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(framealpha=0.6)
    # Value labels
    for bar in list(bars_a) + list(bars_b):
        h = bar.get_height()
        if h and h > 0:
            ax.text(bar.get_x() + bar.get_width()/2, h + max(values_a+values_b)*0.01,
                    str(int(h)), ha="center", va="bottom", fontsize=8)
    return bars_a, bars_b


# ---------------------------------------------------------------------------
# Figure 1 — Latency comparison
# ---------------------------------------------------------------------------

def fig_latency(data, out_dir):
    kernels = [k for k in KERNEL_ORDER if data[k].get("baseline", {}).get("found")]
    labels  = [KERNEL_LABELS_PLAIN[k] for k in kernels]
    base_lat = [data[k]["baseline"]["latency"] for k in kernels]
    opt_lat  = [data[k]["opt"]["latency"]      for k in kernels
                if data[k].get("opt", {}).get("found")]

    # Pad opt if missing
    while len(opt_lat) < len(kernels):
        opt_lat.append(0)

    fig, ax = plt.subplots(figsize=(7, 4))
    bar_group(ax, base_lat, opt_lat, labels,
              colors=[GRAY, BLUE],
              ylabel="Latency (clock cycles)",
              title="Synthesis Latency: Baseline vs Optimised Schedule")
    savefig(fig, os.path.join(out_dir, "fig1_latency.pdf"))
    savefig(fig if not plt.fignum_exists(fig.number) else plt.figure(),
            os.path.join(out_dir, "fig1_latency.png"))
    # re-draw for png
    fig2, ax2 = plt.subplots(figsize=(7, 4))
    bar_group(ax2, base_lat, opt_lat, labels,
              colors=[GRAY, BLUE],
              ylabel="Latency (clock cycles)",
              title="Synthesis Latency: Baseline vs Optimised Schedule")
    savefig(fig2, os.path.join(out_dir, "fig1_latency.png"))
    return dict(zip(kernels, zip(base_lat, opt_lat)))


# ---------------------------------------------------------------------------
# Figure 2 — Speedup
# ---------------------------------------------------------------------------

def fig_speedup(data, out_dir):
    kernels  = [k for k in KERNEL_ORDER
                if data[k].get("baseline", {}).get("found")
                and data[k].get("opt", {}).get("found")]
    labels   = [KERNEL_LABELS_PLAIN[k] for k in kernels]
    speedups = []
    for k in kernels:
        b = data[k]["baseline"]["latency"]
        o = data[k]["opt"]["latency"]
        speedups.append(round(b / o, 2) if o else 0)

    colors = [GREEN if s >= 3 else BLUE for s in speedups]

    fig, ax = plt.subplots(figsize=(7, 3.5))
    x = np.arange(len(labels))
    bars = ax.bar(x, speedups, color=colors, zorder=3, linewidth=0, width=0.5)
    ax.axhline(1.0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylabel("Speedup (baseline / optimised)")
    ax.set_title("Latency Speedup from Schedule Optimisation")
    for bar, val in zip(bars, speedups):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f"{val:.2f}×", ha="center", va="bottom", fontsize=9, fontweight="bold")
    savefig(fig, os.path.join(out_dir, "fig2_speedup.pdf"))
    fig2, ax2 = plt.subplots(figsize=(7, 3.5))
    bars2 = ax2.bar(x, speedups, color=colors, zorder=3, linewidth=0, width=0.5)
    ax2.axhline(1.0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=15, ha="right")
    ax2.set_ylabel("Speedup (baseline / optimised)")
    ax2.set_title("Latency Speedup from Schedule Optimisation")
    for bar, val in zip(bars2, speedups):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                 f"{val:.2f}×", ha="center", va="bottom", fontsize=9, fontweight="bold")
    savefig(fig2, os.path.join(out_dir, "fig2_speedup.png"))
    return dict(zip(kernels, speedups))


# ---------------------------------------------------------------------------
# Figure 3 — Resource comparison (DSP, FF, LUT)
# ---------------------------------------------------------------------------

def fig_resources(data, out_dir):
    kernels = [k for k in KERNEL_ORDER
               if data[k].get("baseline", {}).get("found")
               and data[k].get("opt", {}).get("found")]
    labels  = [KERNEL_LABELS_PLAIN[k] for k in kernels]

    fig, axes = plt.subplots(1, 3, figsize=(11, 4))

    for ax, metric, color_b, color_o, title, total in zip(
        axes,
        ["dsp", "ff", "lut"],
        [GRAY,  GRAY,  GRAY],
        [AMBER, BLUE,  GREEN],
        ["DSP Slices", "Flip-Flops (FF)", "Look-Up Tables (LUT)"],
        [ARTIX7_DSP, ARTIX7_FF, ARTIX7_LUT],
    ):
        base_vals = [data[k]["baseline"].get(metric, 0) or 0 for k in kernels]
        opt_vals  = [data[k]["opt"].get(metric, 0) or 0      for k in kernels]
        bar_group(ax, base_vals, opt_vals, labels,
                  colors=[color_b, color_o],
                  ylabel=metric.upper(),
                  title=title)
        # Annotate device total as a horizontal dashed line
        ax.axhline(total, color="red", linewidth=0.8, linestyle=":",
                   alpha=0.6, label=f"Device max ({total:,})")
        ax.legend(framealpha=0.6, fontsize=7)

    fig.suptitle("Resource Utilisation: Baseline vs Optimised (xc7a100tcsg324-1)", y=1.02)
    savefig(fig, os.path.join(out_dir, "fig3_resources.pdf"))

    fig2, axes2 = plt.subplots(1, 3, figsize=(11, 4))
    for ax, metric, color_b, color_o, title, total in zip(
        axes2,
        ["dsp", "ff", "lut"],
        [GRAY,  GRAY,  GRAY],
        [AMBER, BLUE,  GREEN],
        ["DSP Slices", "Flip-Flops (FF)", "Look-Up Tables (LUT)"],
        [ARTIX7_DSP, ARTIX7_FF, ARTIX7_LUT],
    ):
        base_vals = [data[k]["baseline"].get(metric, 0) or 0 for k in kernels]
        opt_vals  = [data[k]["opt"].get(metric, 0) or 0      for k in kernels]
        bar_group(ax, base_vals, opt_vals, labels,
                  colors=[color_b, color_o],
                  ylabel=metric.upper(),
                  title=title)
        ax.axhline(total, color="red", linewidth=0.8, linestyle=":",
                   alpha=0.6, label=f"Device max ({total:,})")
        ax.legend(framealpha=0.6, fontsize=7)
    fig2.suptitle("Resource Utilisation: Baseline vs Optimised (xc7a100tcsg324-1)", y=1.02)
    savefig(fig2, os.path.join(out_dir, "fig3_resources.png"))


# ---------------------------------------------------------------------------
# Figure 4 — DSP utilisation as % of device
# ---------------------------------------------------------------------------

def fig_dsp_pct(data, out_dir):
    kernels = [k for k in KERNEL_ORDER
               if data[k].get("baseline", {}).get("found")]
    labels  = [KERNEL_LABELS_PLAIN[k] for k in kernels]
    base_pct = [round(100*(data[k]["baseline"].get("dsp",0) or 0)/ARTIX7_DSP, 1)
                for k in kernels]
    opt_pct  = [round(100*(data[k]["opt"].get("dsp",0) or 0)/ARTIX7_DSP, 1)
                if data[k].get("opt",{}).get("found") else 0
                for k in kernels]

    fig, ax = plt.subplots(figsize=(7, 3.8))
    bar_group(ax, base_pct, opt_pct, labels,
              colors=[GRAY, AMBER],
              ylabel="DSP utilisation (% of 240 slices)",
              title="DSP Slice Utilisation as % of Artix-7 100T Device")
    savefig(fig, os.path.join(out_dir, "fig4_dsp_pct.pdf"))
    fig2, ax2 = plt.subplots(figsize=(7, 3.8))
    bar_group(ax2, base_pct, opt_pct, labels,
              colors=[GRAY, AMBER],
              ylabel="DSP utilisation (% of 240 slices)",
              title="DSP Slice Utilisation as % of Artix-7 100T Device")
    savefig(fig2, os.path.join(out_dir, "fig4_dsp_pct.png"))


# ---------------------------------------------------------------------------
# Figure 5 — Latency × II scatter
# ---------------------------------------------------------------------------

def fig_latency_ii(data, out_dir):
    fig, ax = plt.subplots(figsize=(6, 4))
    for k in KERNEL_ORDER:
        for sched, marker, color in [("baseline", "o", GRAY), ("opt", "s", BLUE)]:
            d = data[k].get(sched, {})
            if not d.get("found"):
                continue
            lat = d.get("latency")
            ii  = d.get("loop_ii") or d.get("interval")
            if lat and ii:
                ax.scatter(ii, lat, marker=marker, color=color, s=60, zorder=3)
                ax.annotate(f"{KERNEL_LABELS_PLAIN[k]}\n({sched[:3]})",
                            (ii, lat), textcoords="offset points",
                            xytext=(5, 3), fontsize=7, color=color)

    base_patch = mpatches.Patch(color=GRAY,  label="Baseline")
    opt_patch  = mpatches.Patch(color=BLUE,  label="Optimised")
    ax.legend(handles=[base_patch, opt_patch], framealpha=0.6)
    ax.set_xlabel("Initiation Interval (II) — cycles")
    ax.set_ylabel("Total Latency (cycles)")
    ax.set_title("Latency vs Initiation Interval")
    savefig(fig, os.path.join(out_dir, "fig5_design_space.pdf"))
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    for k in KERNEL_ORDER:
        for sched, marker, color in [("baseline", "o", GRAY), ("opt", "s", BLUE)]:
            d = data[k].get(sched, {})
            if not d.get("found"):
                continue
            lat = d.get("latency")
            ii  = d.get("loop_ii") or d.get("interval")
            if lat and ii:
                ax2.scatter(ii, lat, marker=marker, color=color, s=60, zorder=3)
                ax2.annotate(f"{KERNEL_LABELS_PLAIN[k]}\n({sched[:3]})",
                             (ii, lat), textcoords="offset points",
                             xytext=(5, 3), fontsize=7, color=color)
    ax2.legend(handles=[base_patch, opt_patch], framealpha=0.6)
    ax2.set_xlabel("Initiation Interval (II) — cycles")
    ax2.set_ylabel("Total Latency (cycles)")
    ax2.set_title("Latency vs Initiation Interval")
    savefig(fig2, os.path.join(out_dir, "fig5_lat_ii.png"))


# ---------------------------------------------------------------------------
# LaTeX summary table
# ---------------------------------------------------------------------------

def write_latex_table(data, out_dir):
    lines = []
    lines.append(r"\begin{table}[h]")
    lines.append(r"\centering")
    lines.append(r"\caption{Vitis HLS 2025.1 synthesis results on xc7a100tcsg324-1 (Nexys A7 Artix-7 100T). "
                 r"Clock period 10\,ns (100\,MHz). II = initiation interval of the innermost pipelined loop.}")
    lines.append(r"\label{tab:synthesis}")
    lines.append(r"\begin{tabular}{llrrrrrr}")
    lines.append(r"\toprule")
    lines.append(r"Kernel & Schedule & Latency (cyc) & Interval & Loop II & DSP & FF & LUT \\")
    lines.append(r"\midrule")

    for k in KERNEL_ORDER:
        for sched in SCHEDULES:
            d = data[k].get(sched, {})
            if not d.get("found"):
                row = f"{KERNEL_LABELS[k]} & {sched} & --- & --- & --- & --- & --- & --- \\\\"
            else:
                lat  = d.get("latency",  "---")
                ivl  = d.get("interval", "---")
                ii   = d.get("loop_ii",  "---") or "---"
                dsp  = d.get("dsp",  0) or 0
                ff   = d.get("ff",   0) or 0
                lut  = d.get("lut",  0) or 0
                row = (f"\\texttt{{{KERNEL_LABELS_PLAIN[k]}}} & "
                       f"{sched} & {lat} & {ivl} & {ii} & "
                       f"{dsp} & {ff:,} & {lut:,} \\\\")
            lines.append(row)
        lines.append(r"\midrule" if k != KERNEL_ORDER[-1] else "")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    path = os.path.join(out_dir, "synthesis_table.tex")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"  -> {path}")
    return path


# ---------------------------------------------------------------------------
# JSON dump for other tools
# ---------------------------------------------------------------------------

def write_json(data, out_dir):
    # Make serialisable
    clean = {}
    for k, scheds in data.items():
        clean[k] = {}
        for s, d in scheds.items():
            clean[k][s] = {kk: vv for kk, vv in d.items()}
    path = os.path.join(out_dir, "synthesis_data.json")
    with open(path, "w") as f:
        json.dump(clean, f, indent=2)
    print(f"  -> {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Parse csynth.rpt files and generate figures")
    parser.add_argument("--report-dir", default="reports/synth_reports",
                        help="Directory containing <kernel>_<schedule>/csynth.rpt files")
    parser.add_argument("--out-dir", default="reports/figures",
                        help="Directory to write figures and tables into")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    print(f"\nLoading reports from: {args.report_dir}")
    data = load_all(args.report_dir)

    found = sum(1 for k in data for s in data[k] if data[k][s].get("found"))
    print(f"\nFound {found}/10 reports. Generating figures...\n")

    fig_latency(data, args.out_dir)
    fig_speedup(data, args.out_dir)
    fig_resources(data, args.out_dir)
    fig_dsp_pct(data, args.out_dir)
    fig_latency_ii(data, args.out_dir)
    write_latex_table(data, args.out_dir)
    write_json(data, args.out_dir)

    print("\nDone. Figures and tables written to:", args.out_dir)


if __name__ == "__main__":
    main()