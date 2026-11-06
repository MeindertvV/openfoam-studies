#!/usr/bin/env python3
"""Per fan debiet, drukstap en inlaattemperatuur uit log.foamRun, gemiddeld over de laatste 20
rapportages, en de warmte per unit uit T in de bundels. Schrijft fans.csv.
Gebruik: fans_csv.py <rundir>"""
import csv
import re
import sys
from pathlib import Path

import numpy as np

NX, NY, PITCH = 5, 6, 12.6
run = Path(sys.argv[1])
log = (run / "log.foamRun").read_text()
rijen = re.findall(r"^fan (\d+) Q = (\S+) dp = (\S+) Tin = (\S+)", log, re.M)
data = np.array(rijen, float)
n = NX * NY
data = data[-20 * n:]
with open(run / "fans.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["fan", "i", "j", "Q_m3s", "dp_Pa", "Tin_K"])
    totaal = 0.0
    for k in range(n):
        d = data[data[:, 0] == k]
        q, dp, tin = d[:, 1].mean(), d[:, 2].mean(), d[:, 3].mean()
        totaal += q
        w.writerow([k, k // NY, k % NY, f"{q:.1f}", f"{dp:.1f}", f"{tin:.2f}"])
print(f"totaal debiet {totaal:.0f} m3/s, gemiddeld per fan {totaal / n:.1f}")
