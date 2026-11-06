#!/usr/bin/env python3
"""Warmtebalans en fan-werkpunt van een run. Gebruik: balans.py <rundir> [N laatste iteraties]"""
import re
import sys
from pathlib import Path

import numpy as np

CP, TA, HTC_AV = 1006.0, 323.0, 81 * 100.0

run = Path(sys.argv[1])
n = int(sys.argv[2]) if len(sys.argv) > 2 else 200


def series(name):
    path = next((run / "postProcessing" / name).glob("*/*.dat"))
    return np.loadtxt(path, comments="#")[:, 1]


vol = float(re.search(r"selected \d+ cell\(s\) with volume ([\d.]+)", (run / "log.foamRun").read_text()).group(1))
vol_total = 2 * vol
intT = series("bundleTL") + series("bundleTR")
q_bundle = HTC_AV * (TA * vol_total - intT)
flux = series("fluxTSides") + series("fluxTTop")
mass = series("massSides") + series("massTop")
t_mean = intT / vol_total

log = (run / "log.foamRun").read_text()
fan = np.array([[float(a), float(b)] for a, b in re.findall(r"^fan 0 Q = (\S+) dp = (\S+)", log, re.M)])
air_in = 288.0
q_air = CP * (flux - mass * air_in)


def tail(x):
    return x[-n:]


print(f"iteraties: {len(q_bundle)}, venster {n}")
print(f"Q fan     {tail(fan[:, 0]).mean():8.1f} m3/s  spreiding {np.ptp(tail(fan[:, 0])):.1f}")
print(f"dp fan    {tail(fan[:, 1]).mean():8.1f} Pa")
print(f"Q bundels {tail(q_bundle).mean() / 1e6:8.2f} MW    spreiding {np.ptp(tail(q_bundle)) / tail(q_bundle).mean() * 100:.2f} %")
print(f"Q lucht   {tail(q_air).mean() / 1e6:8.2f} MW    balansfout {(tail(q_air).mean() / tail(q_bundle).mean() - 1) * 100:.1f} %")
print(f"netto massa {tail(mass).mean():.2f} kg/s, T bundel gem. {tail(t_mean).mean():.2f} K")
