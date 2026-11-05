#!/usr/bin/env python3
"""Residuen uit een solverlog of postProcessing naar PNG.

Gebruik: residuals.py <studie|case> [--log bestand] [-o uit.png]
"""
import argparse
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import (INK, SURFACE, add_legend, colors_for, find_case, output_path, study_label,
                    style_axes)

TIME = re.compile(r"^Time = ([-+\d.eE]+?)s?\s*$")
SOLVE = re.compile(r"Solving for (\w+), Initial residual = ([-+\d.eE]+)")


def parse_log(paths):
    """Geef {veld: ([tijd], [eerste initial residual per tijdstap])}."""
    data = {}
    time = None
    seen = set()
    for path in paths:
        with open(path, errors="replace") as f:
            for line in f:
                match = TIME.match(line)
                if match:
                    time = float(match.group(1))
                    seen = set()
                    continue
                match = SOLVE.search(line)
                if match and time is not None and match.group(1) not in seen:
                    seen.add(match.group(1))
                    times, values = data.setdefault(match.group(1), ([], []))
                    times.append(time)
                    values.append(float(match.group(2)))
    return data


def parse_post(paths):
    """Lees postProcessing/residuals*/<start>/residuals.dat."""
    data = {}
    for path in paths:
        columns = []
        with open(path) as f:
            for line in f:
                if line.startswith("# Time"):
                    columns = line.split()[2:]
                elif line.strip() and not line.startswith("#"):
                    parts = line.split()
                    if "N/A" in parts:
                        continue
                    for name, value in zip(columns, parts[1:]):
                        times, values = data.setdefault(name, ([], []))
                        times.append(float(parts[0]))
                        values.append(float(value))
    return data


def load(case, log):
    if log:
        return parse_log([log]), str(log)
    logs = sorted(case.glob("log.foamRun*"), key=lambda p: p.stat().st_mtime)
    data = parse_log(logs) if logs else {}
    if data:
        return data, ", ".join(p.name for p in logs)
    files = sorted(case.glob("postProcessing/residuals*/*/residuals.dat"))
    return parse_post(files), "postProcessing"


def plot(data, title, path):
    colors = colors_for(list(data))
    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=SURFACE)
    for name, (times, values) in data.items():
        positive = [(t, v) for t, v in zip(times, values) if v > 0]
        ax.plot(*zip(*positive), color=colors[name], linewidth=1.6, label=name)
    ax.set_yscale("log")
    style_axes(ax, "Tijd / iteratie", "Initial residual")
    add_legend(ax, ncol=min(len(data), 7))
    ax.set_title(title, color=INK, loc="left", pad=28)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case")
    parser.add_argument("--log", type=Path)
    parser.add_argument("-o", "--output")
    args = parser.parse_args()

    case = find_case(args.case)
    data, source = load(case, args.log)
    if not data:
        sys.exit(f"FOUT: geen residuen gevonden in {case}")

    path = output_path(case, "residuals", "png", args.output)
    plot(data, f"Residuen: {study_label(case)}", path)
    print(f"bron: {source}")
    for name, (times, values) in data.items():
        print(f"{name}: {len(values)} punten, laatste {values[-1]:.3g} bij t={times[-1]:g}")
    print(path)


if __name__ == "__main__":
    main()
