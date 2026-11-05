#!/usr/bin/env python3
"""Forces en coefficients uit postProcessing naar PNG en CSV.

Gebruik: forces.py <studie|case> [-o uitmap]
Per functieobject ontstaat <naam>.csv en <naam>.png.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import (INK, SURFACE, add_legend, colors_for, find_case, output_path, study_label,
                    style_axes)

NUMBER = re.compile(r"[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?")


def read_forces(path):
    """Tel pressure, viscous en eventueel porous op tot Fx..Mz."""
    rows = []
    with open(path) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            values = [float(v) for v in NUMBER.findall(line)]
            sets = (len(values) - 1) // 6
            forces = values[1:1 + 3 * sets]
            moments = values[1 + 3 * sets:]
            rows.append([values[0]]
                        + [sum(forces[i::3]) for i in range(3)]
                        + [sum(moments[i::3]) for i in range(3)])
    return ["Time", "Fx", "Fy", "Fz", "Mx", "My", "Mz"], rows


def read_coeffs(path):
    columns, rows = [], []
    with open(path) as f:
        for line in f:
            if line.startswith("# Time"):
                columns = line[1:].split()
            elif line.strip() and not line.startswith("#"):
                rows.append([float(v) for v in line.split()])
    return columns, rows


def collect(files, reader):
    """Voeg herstarts samen; bij dubbele tijden telt de latere start."""
    columns, merged = [], {}
    for path in sorted(files, key=lambda p: float(p.parent.name)):
        columns, rows = reader(path)
        merged.update((row[0], row) for row in rows)
    return columns, [merged[t] for t in sorted(merged)]


def write_csv(path, columns, rows):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)


def panel(ax, columns, rows, names, ylabel):
    times = [row[0] for row in rows]
    colors = colors_for(names)
    for name in names:
        index = columns.index(name)
        ax.plot(times, [row[index] for row in rows],
                color=colors[name], linewidth=1.6, label=name)
    style_axes(ax, "Tijd / iteratie", ylabel)
    add_legend(ax, ncol=len(names))


def plot(path, title, columns, rows):
    forces = [c for c in ("Fx", "Fy", "Fz") if c in columns]
    if forces:
        fig, axes = plt.subplots(2, 1, figsize=(8, 7), sharex=True, facecolor=SURFACE)
        panel(axes[0], columns, rows, forces, "Kracht [N]")
        panel(axes[1], columns, rows, ["Mx", "My", "Mz"], "Moment [N m]")
        axes[0].set_xlabel("")
        top = axes[0]
    else:
        fig, top = plt.subplots(figsize=(8, 4.5), facecolor=SURFACE)
        names = [c for c in ("Cd", "Cl", "Cm") if c in columns]
        panel(top, columns, rows, names, "Coefficient [-]")
    top.set_title(title, color=INK, loc="left", pad=28)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def summarize(name, columns, rows):
    """Print de laatste waarde en het gemiddelde over de laatste 10%."""
    tail = rows[-max(1, len(rows) // 10):]
    for index, column in enumerate(columns[1:], start=1):
        mean = sum(row[index] for row in tail) / len(tail)
        print(f"{name} {column}: laatste {rows[-1][index]:.4g}, gemiddelde laatste 10% {mean:.4g}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case")
    parser.add_argument("-o", "--output-dir", type=Path)
    args = parser.parse_args()

    case = find_case(args.case)
    sources = {}
    for pattern, reader in (("forces.dat", read_forces), ("forceCoeffs.dat", read_coeffs)):
        for file in case.glob(f"postProcessing/*/*/{pattern}"):
            sources.setdefault((file.parent.parent.name, reader), []).append(file)
    if not sources:
        sys.exit(f"FOUT: geen forces.dat of forceCoeffs.dat in {case}/postProcessing")

    for (name, reader), files in sorted(sources.items(), key=lambda item: item[0][0]):
        columns, rows = collect(files, reader)
        if not rows:
            print(f"let op: {name} is leeg")
            continue
        override = args.output_dir / name if args.output_dir else None
        png = output_path(case, name, "png", override and override.with_suffix(".png"))
        out = output_path(case, name, "csv", override and override.with_suffix(".csv"))
        write_csv(out, columns, rows)
        plot(png, f"{name}: {study_label(case)}", columns, rows)
        summarize(name, columns, rows)
        print(png)
        print(out)


if __name__ == "__main__":
    main()
