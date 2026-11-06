#!/usr/bin/env python3
"""Warmtebalans over een controlebox rond de unit, met dezelfde upwind-T als de solver,
plus debiet en drukval over de bundels.

Gebruik: cv_balans.py <rundir> [tijd]; de mesh komt uit <rundir>/constant/polyMesh.
"""
import re
import sys
from pathlib import Path

import numpy as np

CP = 1006.0
HTC_AV = 8100.0
TA = 323.0
BOX = np.array([[-7.5, -7.5, 43.0], [7.5, 7.5, 59.5]])
T_BUNDEL = 0.5
NORMAAL = {"bundleL": np.array([0.866025, 0, -0.5]), "bundleR": np.array([0.866025, 0, 0.5])}

run = Path(sys.argv[1])
tijd = sys.argv[2] if len(sys.argv) > 2 else max(
    (p.name for p in run.iterdir() if re.fullmatch(r"[\d.]+", p.name)), key=float)
mesh = run / "constant/polyMesh"


def lijst(pad, soort):
    tekst = Path(pad).read_text()
    if soort == "veld":
        m = re.search(r"internalField\s+nonuniform List<\w+>\s*\n?(\d+)\s*\n?\(", tekst)
    else:
        m = re.search(r"\n(\d+)\s*\n\(", tekst)
    n, rest = int(m.group(1)), tekst[m.end():]
    return n, rest


def scalars(pad, soort="veld"):
    n, rest = lijst(pad, soort)
    return np.array(rest.split(None, n)[:n], float)


def vectors(pad, soort="veld"):
    n, rest = lijst(pad, soort)
    return np.array(re.findall(r"\(([-\d.e+]+) ([-\d.e+]+) ([-\d.e+]+)\)", rest)[:n], float)


def labels(pad):
    return scalars(pad, "mesh").astype(int)


def zone(naam):
    tekst = (mesh / "cellZones").read_text()
    i = tekst.index(naam + "\n")
    m = re.search(r"cellLabels\s+List<label>\s*\n?(\d+)\s*\n?\(", tekst[i:])
    n = int(m.group(1))
    return np.array(tekst[i + m.end():].split(None, n)[:n], int)


punten = vectors(mesh / "points", "mesh")
_, rest = lijst(mesh / "faces", "mesh")
vlakken = [np.array(x.split(), int) for x in re.findall(r"\d+\(([\d ]+)\)", rest)]
eigenaar, buur = labels(mesh / "owner"), labels(mesh / "neighbour")
ncel = max(eigenaar.max(), buur.max()) + 1
nint = len(buur)

fc = np.array([punten[f].mean(axis=0) for f in vlakken])
som, aantal = np.zeros((ncel, 3)), np.zeros(ncel)
for k in range(3):
    som[:, k] = np.bincount(eigenaar, fc[:, k], ncel) + np.bincount(buur, fc[:nint, k], ncel)
aantal = np.bincount(eigenaar, minlength=ncel) + np.bincount(buur, minlength=ncel)
C = som / aantal[:, None]

t = run / tijd
phi = scalars(t / "phi")
T = scalars(t / "T")
U = vectors(t / "U")
p = scalars(t / "p_rgh")

binnen = np.all((C > BOX[0]) & (C < BOX[1]), axis=1)
o, b = eigenaar[:nint], buur
rand = binnen[o] != binnen[b]
uit = np.where(binnen[o[rand]], phi[rand], -phi[rand])      # positief = de box uit
T_up = np.where(phi[rand] > 0, T[o[rand]], T[b[rand]])
massa = uit.sum()
T_ref = T_up[uit < 0] @ (-uit[uit < 0]) / -uit[uit < 0].sum()
q_lucht = CP * (uit * (T_up - T_ref)).sum()
print(f"tijd {tijd}: controlebox, {rand.sum()} vlakken")
print(f"  massa in {-uit[uit < 0].sum():.1f}, uit {uit[uit > 0].sum():.1f}, netto {massa:.3f} kg/s")
print(f"  T in {T_ref:.2f} K, T uit {T_up[uit > 0] @ uit[uit > 0] / uit[uit > 0].sum():.2f} K")
print(f"  Q lucht {q_lucht / 1e6:.3f} MW")

q_b, Vt, q_bund = 0, 0, 0
for naam, n in NORMAAL.items():
    z = zone(naam)
    # Volumes uit cellengte: alle bundelcellen hebben hetzelfde niveau.
    w = np.full(len(z), 47.39 / len(z))
    un = U[z] @ n
    q = (w * np.abs(un)).sum() / T_BUNDEL
    q_b += q
    Vt += w.sum()
    q_bund += HTC_AV * (w * (TA - T[z])).sum()
    print(f"  {naam}: |Un| gem {np.abs(un).mean():.2f}, max {np.abs(un).max():.2f} m/s, tangentieel gem "
          f"{np.linalg.norm(U[z] - np.outer(un, n), axis=1).mean():.2f} m/s, debiet {q:.1f} m3/s")
print(f"  debiet bundels {q_b:.1f} m3/s, Q bundels {q_bund / 1e6:.3f} MW, balansfout {(q_lucht / q_bund - 1) * 100:.2f} %")
pl = binnen & (np.abs(C[:, 0]) < 3) & (np.abs(C[:, 1]) < 4) & (C[:, 2] > 47) & (C[:, 2] < 50)
ui = (np.abs(C[:, 0]) > 6.8) & (np.abs(C[:, 0]) < 7.5) & (np.abs(C[:, 1]) < 4) & (C[:, 2] > 50) & (C[:, 2] < 54)
print(f"  p_rgh plenum {p[pl].mean():.1f} Pa, buiten bundel {p[ui].mean():.1f} Pa, verschil {p[pl].mean() - p[ui].mean():.1f} Pa")
