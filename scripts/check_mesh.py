#!/usr/bin/env python3
"""Toets log.checkMesh aan mesh_drempels uit case.yaml.

Gebruik: check_mesh.py <studie>
Exit 0 als de mesh voldoet, 1 bij falen, 2 als log of drempels ontbreken.
"""
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def find_study(arg):
    path = Path(arg)
    if not path.is_dir():
        path = REPO_ROOT / "studies" / arg
    if path.name == "case":
        path = path.parent
    return path


def parse(text):
    """Geef de relevante getallen uit checkMesh-uitvoer; ontbrekend is None."""
    def first(pattern):
        match = re.search(pattern, text, re.M)
        return float(match.group(1)) if match else None

    return {
        "cells": first(r"^\s*cells:\s+(\d+)"),
        "nonOrtho": first(r"Mesh non-orthogonality Max:\s*([-+\d.eE]+)"),
        "skewness": first(r"Max skewness = ([-+\d.eE]+)"),
        "aspect": first(r"Max aspect ratio = ([-+\d.eE]+)"),
        "failed": first(r"Failed (\d+) mesh checks"),
        "ok": re.search(r"^Mesh OK\.", text, re.M) is not None,
    }


def evaluate(values, limits):
    """Geef een lijst van (naam, waarde, grens, geslaagd)."""
    return [
        ("maxNonOrtho", values["nonOrtho"], limits["maxNonOrtho"],
         values["nonOrtho"] is not None and values["nonOrtho"] <= limits["maxNonOrtho"]),
        ("maxSkewness", values["skewness"], limits["maxSkewness"],
         values["skewness"] is not None and values["skewness"] <= limits["maxSkewness"]),
    ]


def main():
    if len(sys.argv) != 2:
        sys.exit("gebruik: check_mesh.py <studie>")
    study = find_study(sys.argv[1])
    spec_file = study / "case.yaml"
    log_file = study / "case" / "log.checkMesh"
    if not spec_file.is_file():
        print(f"FOUT: geen case.yaml in {study}", file=sys.stderr)
        return 2
    if not log_file.is_file():
        print(f"FOUT: {log_file} ontbreekt; draai eerst mesh.sh", file=sys.stderr)
        return 2

    limits = (yaml.safe_load(spec_file.read_text()) or {}).get("mesh_drempels") or {}
    missing = [k for k in ("maxNonOrtho", "maxSkewness") if limits.get(k) is None]
    if missing:
        print(f"FOUT: mesh_drempels mist {', '.join(missing)}", file=sys.stderr)
        return 2

    values = parse(log_file.read_text(errors="replace"))
    if values["cells"] is not None:
        print(f"cellen: {values['cells']:.0f}")
    if values["aspect"] is not None:
        print(f"max aspect ratio: {values['aspect']:g}")

    results = evaluate(values, limits)
    for name, value, limit, passed in results:
        shown = "niet gevonden" if value is None else f"{value:g}"
        print(f"{'OK  ' if passed else 'FOUT'} {name}: {shown} (grens {limit:g})")

    log_ok = values["ok"] and not values["failed"]
    if not log_ok:
        failed = values["failed"]
        print(f"FOUT checkMesh: {f'{failed:.0f} checks mislukt' if failed else 'geen Mesh OK in de log'}")

    if limits.get("doel_yPlus") is not None:
        print(f"let op: doel-y+ {limits['doel_yPlus']} is pas na de run te toetsen")

    return 0 if log_ok and all(r[3] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
