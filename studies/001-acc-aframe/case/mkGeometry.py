#!/usr/bin/env python3
"""Schrijft de STL's van de A-frame-condensor naar constant/geometry.

x = dwars op de nok, y = langs de nok, z = omhoog; maai op z = 0.
nx en ny geven het aantal fan-units; voor het 5x6-grid alleen deze twee aanpassen.
"""
from math import cos, pi, radians, sin
from pathlib import Path

nx, ny = 1, 1        # aantal units
pitch = 12.6         # m, unitmaat in x en y
zDeck = 45.0         # m, bovenkant fan-dek
tDeck = 0.5          # m, dikte dek, tevens dikte fanzone
R, rHub = 4.55, 1.5  # m, fanstraal en naafstraal
zFoot = 48.0         # m, bundelvoet (bovenkant plenumwand)
half = radians(30)   # halve tophoek van de A
xFoot, xTop = 5.9, 0.8  # m, |x| van de bundelhartlijn aan voet en top
tBundle = 0.5        # m, dikte poreuze zone
nCirc = 72

out = Path("constant/geometry")


def box(lo, hi):
    """Asrechte doos, normalen naar buiten."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    return hexa([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                 (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])


def hexa(p):
    """Driehoeken van een zesvlak; p[0:4] onder, p[4:8] boven, tegen de klok in van boven."""
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    tris = []
    for a, b, c, d in quads:
        tris += [(p[a], p[b], p[c]), (p[a], p[c], p[d])]
    return tris


def cylinder(cx, cy, r, z0, z1):
    tris = []
    for i in range(nCirc):
        a0, a1 = 2 * pi * i / nCirc, 2 * pi * (i + 1) / nCirc
        p0 = (cx + r * cos(a0), cy + r * sin(a0))
        p1 = (cx + r * cos(a1), cy + r * sin(a1))
        tris += [((*p0, z0), (*p1, z1), (*p0, z1)), ((*p0, z0), (*p1, z0), (*p1, z1)),
                 ((cx, cy, z1), (*p0, z1), (*p1, z1)), ((cx, cy, z0), (*p1, z0), (*p0, z0))]
    return tris


def deck(cx, cy):
    """Vierkante plaat met rond gat: ring tussen cirkel en vierkant, plus gatwand en rand."""
    h = pitch / 2
    z0, z1 = zDeck - tDeck, zDeck
    tris = []
    for i in range(nCirc):
        a0, a1 = 2 * pi * i / nCirc, 2 * pi * (i + 1) / nCirc
        c0 = (cx + R * cos(a0), cy + R * sin(a0))
        c1 = (cx + R * cos(a1), cy + R * sin(a1))
        s0 = (cos(a0), sin(a0))
        s1 = (cos(a1), sin(a1))
        m0, m1 = h / max(map(abs, s0)), h / max(map(abs, s1))
        o0 = (cx + m0 * s0[0], cy + m0 * s0[1])
        o1 = (cx + m1 * s1[0], cy + m1 * s1[1])
        tris += [((*c0, z1), (*o0, z1), (*o1, z1)), ((*c0, z1), (*o1, z1), (*c1, z1)),
                 ((*c0, z0), (*o1, z0), (*o0, z0)), ((*c0, z0), (*c1, z0), (*o1, z0)),
                 ((*c0, z0), (*c0, z1), (*c1, z1)), ((*c0, z0), (*c1, z1), (*c1, z0)),
                 ((*o0, z0), (*o1, z1), (*o0, z1)), ((*o0, z0), (*o1, z0), (*o1, z1))]
    return tris


def bundle(cx, cy, side):
    """Schuine plaat van voet naar nok; side = -1 links, +1 rechts."""
    h = pitch / 2
    d = (-side * sin(half), cos(half))        # langs de bundel, omhoog
    n = (cos(half), side * sin(half))         # bundelnormaal in xz
    L = (xFoot - xTop) / sin(half) + 0.3      # 0,3 m extra de wand in
    f = (side * xFoot - 0.3 * d[0], zFoot - 0.3 * d[1])
    t = (f[0] + L * d[0], f[1] + L * d[1])
    w = tBundle / 2
    a, b = (f[0] - w * n[0], f[1] - w * n[1]), (f[0] + w * n[0], f[1] + w * n[1])
    c, e = (t[0] + w * n[0], t[1] + w * n[1]), (t[0] - w * n[0], t[1] - w * n[1])
    ys, ye = cy - h + 0.3, cy + h - 0.3
    return hexa([(cx + a[0], ys, a[1]), (cx + b[0], ys, b[1]), (cx + b[0], ye, b[1]), (cx + a[0], ye, a[1]),
                 (cx + e[0], ys, e[1]), (cx + c[0], ys, c[1]), (cx + c[0], ye, c[1]), (cx + e[0], ye, e[1])])


def gable(cx, y0, y1):
    """Driehoekige eindwand, als waaier vanuit het midden."""
    zApex = zFoot + (xFoot - xTop) / sin(half) * cos(half)
    poly = [(-6.2, zDeck), (6.2, zDeck), (6.2, zFoot), (1.2, zApex + 1.2), (-1.2, zApex + 1.2), (-6.2, zFoot)]
    poly = [(cx + x, z) for x, z in poly]
    mid = (cx, zDeck + 5.0)
    tris = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        tris += [((mid[0], y0, mid[1]), (q[0], y0, q[1]), (p[0], y0, p[1])),
                 ((mid[0], y1, mid[1]), (p[0], y1, p[1]), (q[0], y1, q[1])),
                 ((p[0], y0, p[1]), (q[0], y0, q[1]), (q[0], y1, q[1])),
                 ((p[0], y0, p[1]), (q[0], y1, q[1]), (p[0], y1, p[1]))]
    return tris


def structure(cx, cy):
    h = pitch / 2
    zApex = zFoot + (xFoot - xTop) / sin(half) * cos(half)
    tris = deck(cx, cy) + cylinder(cx, cy, rHub, zDeck - tDeck - 1.0, zDeck + 1.0)
    for s in (-1, 1):
        x0, x1 = sorted((cx + s * 5.6, cx + s * 6.2))
        tris += box((x0, cy - h, zDeck - 0.01), (x1, cy + h, zFoot))     # plenumwand
        y0, y1 = sorted((cy + s * 5.9, cy + s * 6.3))
        tris += gable(cx, y0, y1)
    tris += box((cx - 1.2, cy - h, zApex - 1.0), (cx + 1.2, cy + h, zApex + 1.2))  # nok/stoomleiding
    return tris


def write(name, tris):
    with open(out / f"{name}.stl", "w") as f:
        f.write(f"solid {name}\n")
        for a, b, c in tris:
            f.write(" facet normal 0 0 0\n  outer loop\n")
            for p in (a, b, c):
                f.write(f"   vertex {p[0]:.5f} {p[1]:.5f} {p[2]:.5f}\n")
            f.write("  endloop\n endfacet\n")
        f.write(f"endsolid {name}\n")


units = [((i - (nx - 1) / 2) * pitch, (j - (ny - 1) / 2) * pitch) for i in range(nx) for j in range(ny)]
out.mkdir(parents=True, exist_ok=True)
write("structure", [t for u in units for t in structure(*u)])
write("bundleL", [t for u in units for t in bundle(*u, -1)])
write("bundleR", [t for u in units for t in bundle(*u, 1)])
