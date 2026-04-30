"""
reports/parse_reports.py — Extract and compare HLS synthesis reports.

Works with reports produced by either:
  - run_hls_wsl2.sh  →  reports/synth_reports/<kernel>_<schedule>/csynth.rpt
  - generate_hls.py  →  sim/vivado_projects/<kernel>_<schedule>.prj/**/csynth.rpt

Usage
-----
  python3 reports/parse_reports.py                              # Markdown table to stdout
  python3 reports/parse_reports.py --csv                        # CSV to stdout
  python3 reports/parse_reports.py --output reports/table.md   # write to file
"""

import argparse, csv, glob, io, json, os, re, sys

KERNELS   = ["vadd", "vmac", "linear", "relu", "linear_relu"]
SCHEDULES = ["baseline", "opt"]

# ---------------------------------------------------------------------------
# Report location search
# ---------------------------------------------------------------------------

def find_csynth_rpt(report_dir: str, kernel: str, schedule: str) -> str | None:
    """Try both the WSL2-script layout and the generate_hls.py project layout."""
    name = f"{kernel}_{schedule}"

    # Layout 1: reports/synth_reports/<name>/csynth.rpt  (from run_hls_wsl2.sh)
    flat = os.path.join(report_dir, name, "csynth.rpt")
    if os.path.isfile(flat):
        return flat

    # Layout 2: <name>.prj/**/csynth.rpt  (from generate_hls.py vivado projects)
    prj = os.path.join(report_dir, f"{name}.prj")
    if os.path.isdir(prj):
        matches = glob.glob(os.path.join(prj, "**", "csynth.rpt"), recursive=True)
        if matches:
            return matches[0]

    return None

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_csynth(path: str) -> dict:
    with open(path) as f:
        text = f.read()

    result = {"latency_min": None, "latency_max": None, "ii": None,
              "bram": None, "dsp": None, "ff": None, "lut": None}

    # Latency table: top-level function row
    # |+ funcname  |  <min> | ... |  <max> | ... |  <II> | ...
    lat = re.search(
        r"\|\+\s+\w+\s*\|\s*(\d+)\s*\|[^|]*\|\s*(\d+)\s*\|[^|]*\|\s*(\d+)\s*\|",
        text)
    if lat:
        result["latency_min"] = int(lat.group(1))
        result["latency_max"] = int(lat.group(2))
        result["ii"]          = int(lat.group(3))

    # Utilisation summary table: | Total | <BRAM> | <DSP> | <FF> | <LUT> |
    res = re.search(
        r"\|\s*Total\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|",
        text)
    if res:
        result["bram"] = int(res.group(1))
        result["dsp"]  = int(res.group(2))
        result["ff"]   = int(res.group(3))
        result["lut"]  = int(res.group(4))

    return result

# ---------------------------------------------------------------------------
# Table rendering
# ---------------------------------------------------------------------------

COLUMNS = ["kernel", "schedule", "latency_min", "latency_max", "ii",
           "dsp", "bram", "ff", "lut"]
HEADERS = {
    "kernel": "Kernel", "schedule": "Schedule",
    "latency_min": "Lat min (cyc)", "latency_max": "Lat max (cyc)",
    "ii": "II", "dsp": "DSP", "bram": "BRAM", "ff": "FF", "lut": "LUT",
}

def _f(v): return str(v) if v is not None else "—"

def render_markdown(rows):
    w = {c: len(HEADERS[c]) for c in COLUMNS}
    for r in rows:
        for c in COLUMNS:
            w[c] = max(w[c], len(_f(r.get(c))))
    hdr = "| " + " | ".join(HEADERS[c].ljust(w[c]) for c in COLUMNS) + " |"
    sep = "|-" + "-|-".join("-"*w[c] for c in COLUMNS) + "-|"
    body = ["| " + " | ".join(_f(r.get(c)).ljust(w[c]) for c in COLUMNS) + " |"
            for r in rows]
    return "\n".join([hdr, sep] + body)

def render_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in COLUMNS})
    return buf.getvalue()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def collect(report_dir):
    rows = []
    for k in KERNELS:
        for s in SCHEDULES:
            rpt = find_csynth_rpt(report_dir, k, s)
            row = {"kernel": k, "schedule": s}
            if rpt:
                row.update(parse_csynth(rpt))
                row["rpt_path"] = rpt
            rows.append(row)
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default="reports/synth_reports")
    parser.add_argument("--csv",    action="store_true")
    parser.add_argument("--json",   action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    rows = collect(args.project_dir)

    if args.json:
        out = json.dumps(rows, indent=2)
    elif args.csv:
        out = render_csv(rows)
    else:
        out  = "## HLS Synthesis Report Comparison\n\n"
        out += render_markdown(rows)
        out += "\n\n_Generated by parse_reports.py_\n"

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(out)
        print(f"Written to {args.output}")
    else:
        print(out)

    # Always persist JSON for the dashboard
    jpath = os.path.join(os.path.dirname(__file__), "report_data.json")
    with open(jpath, "w") as f:
        json.dump(rows, f, indent=2)

if __name__ == "__main__":
    main()