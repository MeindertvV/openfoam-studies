#!/usr/bin/env python3
"""Maakt runs/windstil, runs/wind en runs/scherm uit case/. Alleen 0/, constant/ en system/;
de mesh komt op de VM uit case/constant/polyMesh. Gebruik: mkRuns.py (vanuit de studiemap)."""
import re
import shutil
from pathlib import Path

UREF, ZREF, Z0 = 9.0, 45.0, 0.1  # aanname: 9 m/s op dekhoogte, ruwheid 0,1 m
NRAMP = 100                      # iteraties tot de volle inlaatsnelheid
K_SCHERM, T_SCHERM = 10.0, 1.5   # aanname: verliescoefficient, dikte in m
EPS_SCHERM = 0.01   # box iets verschoven: celcentra op +-0.75 maken boxToCell anders willekeurig
ZSCHERM = (5.0, 44.25)
Z3M, X3M = 9.0, 1.5   # onder z=9: cellen van 3 m met centra op +-1.5; de box mist die, dus een rij apart
HALF_X, HALF_Y = 31.5, 37.8

base = Path("case")
ABL = f"""        flowDir         (1 0 0);
        zDir            (0 0 1);
        Uref            {UREF};
        Zref            {ZREF};
        z0              uniform {Z0};
        zGround         uniform 0;
"""
# Zelfde profiel als atmBoundaryLayerInletVelocity, maar in NRAMP iteraties opgebouwd:
# een plotselinge inlaat van 9 m/s op U = 0 laat k en epsilon binnen 5 iteraties ontsporen.
RAMP = f"""        type            codedFixedValue;
        value           uniform (0 0 0);
        name            ablRamp;
        code
        #{{
            const scalar z0 = {Z0}, Uref = {UREF}, Zref = {ZREF};
            const scalar s = min(this->db().time().value()/{NRAMP}.0, 1.0);
            const scalarField z(max(patch().Cf().component(vector::Z), scalar(0)));
            const scalarField Ux(s*Uref*log((z + z0)/z0)/log((Zref + z0)/z0));
            operator==(Ux*vector(1, 0, 0));
        #}};
"""


# ABL-epsilon met nut op de inlaat begrensd via epsilon >= Cmu k^2/nutMax: test in lokaal/wind_nut.
EPSCAP = f"""        type            codedFixedValue;
        value           uniform 0.026;
        name            ablEpsCap;
        code
        #{{
            const scalar z0 = {Z0}, Uref = {UREF}, Zref = {ZREF}, kappa = 0.41, Cmu = 0.09, nutMax = 5;
            const scalar us = kappa*Uref/log((Zref + z0)/z0);
            const scalar k = sqr(us)/sqrt(Cmu);
            const scalarField z(max(patch().Cf().component(vector::Z), scalar(0)));
            operator==(max(pow3(us)/(kappa*(z + z0)), Cmu*sqr(k)/nutMax));
        #}};
"""


def kopie(naam):
    run = Path("runs") / naam
    if run.exists():
        shutil.rmtree(run)
    (run / "constant").mkdir(parents=True)
    shutil.copytree(base / "0", run / "0")
    shutil.copytree(base / "system", run / "system")
    for f in ("fvModels", "g", "momentumTransport", "pRef", "physicalProperties"):
        shutil.copy(base / "constant" / f, run / "constant" / f)
    (run / f"{naam}.foam").touch()
    return run


def rand(pad, wijzig):
    """Vervangt de blokken van open randen in 0/<veld> door wijzig: {patch: inhoud}."""
    s = pad.read_text()
    i = s.index('    "(inlet|outlet|sides')
    j = s.index("}", i) + 1
    blok = "\n\n".join(f"    {p}\n    {{\n{inhoud}    }}" for p, inhoud in wijzig.items())
    pad.write_text(s[:i] + blok + s[j:])


def wind(run):
    z = run / "0"
    slip_grad = "        type            zeroGradient;\n"
    rand(z / "U", {
        "inlet": RAMP,
        "outlet": "        type            pressureInletOutletVelocity;\n        value           uniform (0 0 0);\n",
        '"(sides|top)"': "        type            slip;\n"})
    open_p = "        type            prghTotalHydrostaticPressure;\n        value           $internalField;\n"
    rand(z / "p_rgh", {
        '"(inlet|sides|top)"': "        type            fixedFluxPressure;\n        value           $internalField;\n",
        "outlet": open_p})
    # ph_rgh: fixedFluxPressure zou de inlaatsnelheid in de hydrostatische start trekken
    rand(z / "ph_rgh", {'"(inlet|outlet|sides)"': slip_grad})
    rand(z / "T", {
        "inlet": "        type            fixedValue;\n        value           uniform 288;\n",
        "outlet": "        type            inletOutlet;\n        inletValue      uniform 288;\n        value           uniform 288;\n",
        '"(sides|top)"': slip_grad})
    rand(z / "k", {
        "inlet": "        type            atmBoundaryLayerInletK;\n" + ABL,
        "outlet": "        type            inletOutlet;\n        inletValue      uniform 1.2;\n        value           uniform 1.2;\n",
        '"(sides|top)"': slip_grad})
    rand(z / "epsilon", {
        "inlet": EPSCAP,
        "outlet": "        type            inletOutlet;\n        inletValue      uniform 0.012;\n        value           uniform 0.012;\n",
        '"(sides|top)"': slip_grad})
    s = (z / "nut").read_text()
    a = "    ground\n    {\n        type            nutkWallFunction;\n        value           uniform 0;\n    }"
    assert a in s
    s = s.replace(a, f"    ground\n    {{\n        type            nutkAtmRoughWallFunction;\n        z0              uniform {Z0};\n        value           uniform 0;\n    }}")
    (z / "nut").write_text(s)
    # nut blijft klein tot de inlaat-k binnenkomt, en maxDeltaT begrenst het expliciete
    # dev2(T(grad(U)))-deel: met nut ~ 10 en dt ~ 2 s op 0,375 m-cellen is dat instabiel.
    p = run / "system/fvSolution"
    s = re.sub(r"maxDeltaT\s+[\d.]+;", "maxDeltaT         0.2;", p.read_text())
    s = re.sub(r"maxCo\s+[\d.]+;", "maxCo             0.7;", s)
    s = re.sub(r"rDeltaTSmoothingCoeff\s+[\d.]+;", "rDeltaTSmoothingCoeff 0.05;", s)
    p.write_text(re.sub(r"rDeltaTDampingCoeff\s+[\d.]+;", "rDeltaTDampingCoeff 0.5;", s))
    # Met wind stroomt er lucht door de slechtste cellen: crash in GAMG bij iteratie 217.
    p = run / "system/fvSchemes"
    s = p.read_text().replace("Gauss linear corrected;", "Gauss linear limited corrected 0.33;")
    s = re.sub(r"default(\s+)corrected;", r"default\1limited corrected 0.33;", s)
    p.write_text(s.replace("default         Gauss linear;\n", "default         Gauss linear;\n    grad(U)         cellLimited Gauss linear 1;\n", 1))
    p = run / "system/controlDict"
    s = p.read_text()
    p.write_text(s.replace("functions\n{", 'libs ("libatmosphericModels.so");\n\nfunctions\n{', 1))


def scherm(run):
    (t0, t1) = ZSCHERM
    p = run / "constant/fvModels"
    s = p.read_text()
    f = K_SCHERM / T_SCHERM
    i = s.index("// Fan: ronde drukverhoging")
    s = s[:i] + f"""// Kruisvormig scherm onder het dek: K = {K_SCHERM} over {T_SCHERM} m dikte (aanname).

screen
{{
    type            explicitPorositySource;

    explicitPorositySourceCoeffs
    {{
        cellZone        screen;

        type            DarcyForchheimer;

        d   (0 0 0);
        f   ({f:.3f} {f:.3f} {f:.3f});

        coordinateSystem
        {{
            type    cartesian;
            origin  (0 0 0);
            coordinateRotation
            {{
                type    axesRotation;
                e1      (1 0 0);
                e3      (0 0 1);
            }}
        }}
    }}
}}

""" + s[i:]
    p.write_text(s)
    w = T_SCHERM / 2
    (w0, w1) = (-w - EPS_SCHERM, w - EPS_SCHERM)
    p = run / "system/topoSetDict"
    s = p.read_text()
    i = s.index("actions\n(")
    p.write_text(s[:i] + f"""actions
(
    {{
        name    screenCells;
        type    cellSet;
        action  new;
        source  boxToCell;
        box     ({w0} -{HALF_Y} {t0}) ({w1} {HALF_Y} {t1});
    }}
    {{
        name    screenCells;
        type    cellSet;
        action  add;
        source  boxToCell;
        box     (-{HALF_X} {w0} {t0}) ({HALF_X} {w1} {t1});
    }}
    {{
        name    screenCells;
        type    cellSet;
        action  add;
        source  boxToCell;
        box     ({-X3M - 0.1} -{HALF_Y} {t0}) ({-X3M + 0.1} {HALF_Y} {Z3M});
    }}
    {{
        name    screenCells;
        type    cellSet;
        action  add;
        source  boxToCell;
        box     (-{HALF_X} {-X3M - 0.1} {t0}) ({HALF_X} {-X3M + 0.1} {Z3M});
    }}
    {{
        name    screen;
        type    cellZoneSet;
        action  new;
        source  setToCellZone;
        set     screenCells;
    }}
);

// ************************************************************************* //
""")


kopie("windstil")
wind(kopie("wind"))
r = kopie("scherm")
wind(r)
scherm(r)
