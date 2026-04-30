#!/bin/bash
# run_hls_wsl2.sh — Run Vitis HLS synthesis from WSL2 for all VPU kernels.
#
# Usage (from a WSL2 terminal, NOT inside Docker):
#
#   cd "/mnt/c/Users/tiffa/Documents/RPI/VPU_Research/Spring 2026"
#   bash reports/run_hls_wsl2.sh
#
# Output: reports/synth_reports/<kernel>_<schedule>/csynth.rpt
# Then:   python3 reports/parse_reports.py --project-dir reports/synth_reports

# MAY NOT WORK, NOT FULLY TESTED. RAN INTO A LOT OF PROBLEMS RUNNING ON WSL, 
# Use run_hls_windows.ps1 if you're on windows. 

set -e

# ── Vivado 2025.1 paths ──────────────────────────────────────────────────────
# adjust visit settings file path to system
VITIS_SETTINGS="/mnt/c/Xilinx/2025.1/Vitis/settings64.sh"

if [ -f "$VITIS_SETTINGS" ]; then
    source "$VITIS_SETTINGS"
fi

VITIS_HLS_BIN="$(command -v vitis_hls || true)"

if [ -z "$VITIS_HLS_BIN" ]; then
    echo "ERROR: vitis_hls not found in PATH."
    echo "Try:"
    echo "  find /mnt/c/Xilinx/2025.1 -name 'vitis_hls*' 2>/dev/null"
    echo ""
    echo "Also make sure you installed the Linux version of Vitis if running from WSL2."
    exit 1
fi

echo "Using: $VITIS_HLS_BIN"
echo "Version: $("$VITIS_HLS_BIN" -version 2>&1 | head -1)"
echo ""

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HLS_DIR="$PROJECT_ROOT/sim/hls_output"
REPORT_DIR="$PROJECT_ROOT/reports/synth_reports"
mkdir -p "$REPORT_DIR"

# Nexys A7 Artix-7 100T — same part as Fall 25
PART="xc7a100tcsg324-1"
CLOCK_PERIOD="10"   # 10 ns = 100 MHz

# ── Per-kernel synthesis ─────────────────────────────────────────────────────
run_kernel() {
    local CPP="$1"           # e.g. vadd_baseline.cpp
    local NAME="${CPP%.cpp}" # e.g. vadd_baseline
    local OUTDIR="$REPORT_DIR/$NAME"
    mkdir -p "$OUTDIR"

    # Derive top-function name from filename
    case "$NAME" in
        vadd*)        TOPFUNC="vadd_i8" ;;
        vmac*)        TOPFUNC="vmac_i8" ;;
        linear_relu*) TOPFUNC="linear_relu_i8" ;;
        linear*)      TOPFUNC="linear_i8" ;;
        relu*)        TOPFUNC="relu_i8" ;;
        *)            echo "  WARNING: unknown kernel $NAME, skipping"; return ;;
    esac

    local TCL="$OUTDIR/run.tcl"
    cat > "$TCL" << TCL_EOF
open_project "$OUTDIR/proj"
set_top $TOPFUNC
add_files "$HLS_DIR/$CPP"
open_solution "solution1" -reset
set_part {$PART}
create_clock -period $CLOCK_PERIOD -name default
csynth_design
exit
TCL_EOF

    echo "  [$NAME]  top=$TOPFUNC  part=$PART"
    "$VITIS_HLS_BIN" -f "$TCL" > "$OUTDIR/vitis_hls.log" 2>&1
    local RC=$?

    # csynth.rpt lives inside the solution directory
    local RPT
    RPT=$(find "$OUTDIR/proj" -name "csynth.rpt" 2>/dev/null | head -1)

    if [ -n "$RPT" ]; then
        cp "$RPT" "$OUTDIR/csynth.rpt"
        # Extract the one-line summary for quick feedback
        local LAT II DSP LUT
        LAT=$(grep -m1 "Latency" "$RPT" | grep -o '[0-9]*' | head -1)
        echo "    -> done  (csynth.rpt saved)"
    else
        echo "    -> WARNING: csynth.rpt not found — check $OUTDIR/vitis_hls.log"
        if [ $RC -ne 0 ]; then
            echo "    -> vitis_hls exited with code $RC"
        fi
    fi
}

# ── Main ─────────────────────────────────────────────────────────────────────
echo "=== Vitis HLS synthesis  |  Part: $PART  |  Clock: ${CLOCK_PERIOD}ns ==="
echo ""

if [ ! -d "$HLS_DIR" ]; then
    echo "ERROR: HLS output directory not found: $HLS_DIR"
    echo "Run first (inside Docker): python3 sim/generate_hls.py --hls-only"
    exit 1
fi

CPP_COUNT=$(find "$HLS_DIR" -name "*.cpp" | wc -l)
if [ "$CPP_COUNT" -eq 0 ]; then
    echo "ERROR: No .cpp files found in $HLS_DIR"
    exit 1
fi

echo "Found $CPP_COUNT HLS files in $HLS_DIR"
echo ""

for CPP_PATH in "$HLS_DIR"/*.cpp; do
    run_kernel "$(basename "$CPP_PATH")"
done

echo ""
echo "=== Synthesis complete ==="
echo "Reports saved to: $REPORT_DIR"
echo ""
echo "Next — generate the comparison table:"
echo "  python3 reports/parse_reports.py --project-dir reports/synth_reports --output reports/comparison_table.md"
echo ""
echo "Or view raw JSON for the dashboard:"
echo "  python3 reports/parse_reports.py --project-dir reports/synth_reports --json"