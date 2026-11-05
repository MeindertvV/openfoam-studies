"""Gedeelde helpers voor de post-processing."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e5e4e0"
OVERFLOW = "#898781"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
          "#e87ba4", "#008300", "#6250d6", "#e34948"]
# Een veld houdt in elke grafiek dezelfde kleur
SLOTS = {"Ux": 0, "Uy": 1, "Uz": 2, "p": 3, "p_rgh": 3, "k": 4, "epsilon": 5, "omega": 5,
         "nuTilda": 6, "T": 7, "h": 7, "e": 7,
         "Fx": 0, "Fy": 1, "Fz": 2, "Mx": 0, "My": 1, "Mz": 2,
         "Cd": 0, "Cl": 1, "Cm": 2}


def find_case(arg):
    """Geef de casemap bij een studienaam, studiemap, casemap of smoke-map."""
    path = Path(arg)
    if not path.is_dir():
        path = REPO_ROOT / "studies" / arg
    for candidate in (path, path / "case"):
        if (candidate / "system" / "controlDict").is_file():
            return candidate.resolve()
    sys.exit(f"FOUT: geen case gevonden bij {arg}")


def study_label(case):
    """Naam voor in een titel: de studie, met de map erbij als dat niet case/ is."""
    if not (case.parent / "case.yaml").is_file():
        return case.name
    return case.parent.name if case.name == "case" else f"{case.parent.name} ({case.name})"


def output_path(case, stem, ext, override=None):
    """Standaard <studie>/results/<stem>[_smoke].<ext>; zonder studie in <case>/results/."""
    if override:
        path = Path(override)
    else:
        root = case.parent if (case.parent / "case.yaml").is_file() else case
        suffix = "" if case.name == "case" or root == case else f"_{case.name}"
        path = root / "results" / f"{stem}{suffix}.{ext}"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def colors_for(names):
    """Geef per naam een vaste kleur; wat niet in de acht slots past wordt grijs."""
    used = {SLOTS[n] for n in names if n in SLOTS}
    free = [i for i in range(len(SERIES)) if i not in used]
    colors = {}
    for name in names:
        if name in SLOTS:
            colors[name] = SERIES[SLOTS[name]]
        else:
            colors[name] = SERIES[free.pop(0)] if free else OVERFLOW
    return colors


def style_axes(ax, xlabel, ylabel):
    ax.set_facecolor(SURFACE)
    ax.set_xlabel(xlabel, color=INK_SECONDARY)
    ax.set_ylabel(ylabel, color=INK_SECONDARY)
    ax.tick_params(which="both", colors=INK_SECONDARY, length=0)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)


def add_legend(ax, ncol=1):
    ax.legend(frameon=False, ncol=ncol, labelcolor=INK_SECONDARY,
              loc="lower left", bbox_to_anchor=(0, 1), borderaxespad=0.2)
