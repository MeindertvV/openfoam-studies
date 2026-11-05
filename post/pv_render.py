#!/usr/bin/env python3
"""Headless render van een veld naar PNG. Draai met pvbatch, niet met python.

Eerst `source scripts/env.sh`; lokaal is een X-server nodig (WSLg).
Gebruik: pvbatch --force-offscreen-rendering post/pv_render.py <studie|case> [--field U]
             [--mode slice|contour] [--origin X Y Z] [--normal X Y Z]
             [--iso WAARDE] [--color VELD] [--time T] [--edges] [-o uit.png]
"""
import argparse
import itertools
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import INK, SURFACE, find_case, output_path

try:
    import paraview.simple as pv
except ImportError:
    # pvbatch uit het Ubuntu-pakket start zonder dist-packages op sys.path
    sys.path.append("/usr/lib/python3/dist-packages")
    import paraview.simple as pv

SEQUENTIAL = ["#cde2fb", "#86b6ef", "#2a78d6", "#1c5cab", "#0d366b"]
DIVERGING = ["#2a78d6", "#f0efec", "#e34948"]
IMAGE_WIDTH = 1600
MAX_HEIGHT = 1000
MARGIN = 40
BAR_HEIGHT = 110


def rgb(hex_color):
    return [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def set_colors(lut, low, high, is_vector):
    """Eén tint voor grootte, twee tinten rond nul voor een veld met beide tekens."""
    if not is_vector and low < 0 < high:
        limit = max(-low, high)
        stops = [-limit, 0, limit]
        ramp = DIVERGING
    else:
        count = len(SEQUENTIAL) - 1
        stops = [low + (high - low) * i / count for i in range(count + 1)]
        ramp = SEQUENTIAL
    lut.RGBPoints = [value for stop, color in zip(stops, ramp) for value in [stop, *rgb(color)]]
    lut.ColorSpace = "Lab"


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def frame_slice(view, bounds, normal, has_bar):
    """Zet een parallelle camera recht op de slice en snij het beeld op de geometrie bij."""
    length = math.sqrt(dot(normal, normal))
    normal = [n / length for n in normal]
    up = [0, 1, 0] if abs(normal[1]) < 0.9 else [0, 0, 1]
    right = cross(up, normal)
    length = math.sqrt(dot(right, right))
    right = [r / length for r in right]
    up = cross(normal, right)

    corners = list(itertools.product(bounds[:2], bounds[2:4], bounds[4:6]))
    along = [dot(corner, right) for corner in corners]
    above = [dot(corner, up) for corner in corners]
    width = max(along) - min(along)
    height = max(above) - min(above)
    centre = [dot(corners[0], normal) * n
              + (max(along) + min(along)) / 2 * r
              + (max(above) + min(above)) / 2 * u
              for n, r, u in zip(normal, right, up)]

    bar = BAR_HEIGHT if has_bar else 0
    pixels = min((IMAGE_WIDTH - 2 * MARGIN) / width,
                 (MAX_HEIGHT - 2 * MARGIN - bar) / height)
    image_height = int(height * pixels) + 2 * MARGIN + bar
    target = [c - u * bar / (2 * pixels) for c, u in zip(centre, up)]

    view.ViewSize = [IMAGE_WIDTH, image_height]
    view.CameraParallelProjection = 1
    view.CameraFocalPoint = target
    view.CameraPosition = [t + n * max(width, height) for t, n in zip(target, normal)]
    view.CameraViewUp = up
    view.CameraParallelScale = image_height / (2 * pixels)
    return [IMAGE_WIDTH, image_height]


def color_by(display, view, result, field):
    """Kleur op een veld met legenda; geeft het bereik terug."""
    array = result.GetDataInformation().GetPointDataInformation().GetArrayInformation(field)
    if array is None:
        sys.exit(f"FOUT: veld {field} niet gevonden in het resultaat")
    is_vector = array.GetNumberOfComponents() > 1
    if is_vector:
        pv.ColorBy(display, ("POINTS", field, "Magnitude"))
    else:
        pv.ColorBy(display, ("POINTS", field))
    low, high = array.GetComponentRange(-1 if is_vector else 0)
    lut = pv.GetColorTransferFunction(field)
    set_colors(lut, low, high, is_vector)

    display.SetScalarBarVisibility(view, True)
    bar = pv.GetScalarBar(lut, view)
    bar.Title = field
    bar.ComponentTitle = "Magnitude" if is_vector else ""
    bar.TitleColor = rgb(INK)
    bar.LabelColor = rgb(INK)
    return low, high, bar


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case")
    parser.add_argument("--field", help="optioneel bij --edges: dan alleen de mesh")
    parser.add_argument("--mode", choices=["slice", "contour"], default="slice")
    parser.add_argument("--origin", type=float, nargs=3)
    parser.add_argument("--normal", type=float, nargs=3, default=[0, 0, 1])
    parser.add_argument("--iso", type=float)
    parser.add_argument("--color", help="veld om de contour mee te kleuren; standaard --field")
    parser.add_argument("--time", type=float, help="standaard de laatste tijd")
    parser.add_argument("--edges", action="store_true", help="toon de celranden")
    parser.add_argument("-o", "--output")
    args = parser.parse_args()
    if args.mode == "contour" and args.iso is None:
        parser.error("--mode contour vereist --iso")
    if args.field is None and (args.mode == "contour" or not args.edges):
        parser.error("--field is verplicht, behalve bij een slice met --edges")
    return args


def main():
    args = parse_args()
    case = find_case(args.case)
    foam_file = case / "case.foam"
    foam_file.touch()

    reader = pv.OpenFOAMReader(FileName=str(foam_file))
    reader.UpdatePipelineInformation()
    times = list(reader.TimestepValues)
    if not times:
        sys.exit(f"FOUT: geen tijdmappen in {case}")
    time = times[-1] if args.time is None else args.time
    if time not in times:
        sys.exit(f"FOUT: tijd {time} bestaat niet; beschikbaar: {times}")
    color_field = args.color or args.field
    reader.CellArrays = sorted({name for name in (args.field, color_field) if name})
    reader.UpdatePipeline(time)

    info = reader.GetDataInformation()
    if args.field and not info.GetPointDataInformation().GetArrayInformation(args.field):
        sys.exit(f"FOUT: veld {args.field} niet gevonden op t={time}")
    bounds = info.GetBounds()
    centre = [(bounds[2 * i] + bounds[2 * i + 1]) / 2 for i in range(3)]

    if args.mode == "slice":
        result = pv.Slice(Input=reader)
        result.SliceType.Origin = args.origin or centre
        result.SliceType.Normal = args.normal
        # Met triangulatie zijn de echte cellen niet meer te zien
        result.Triangulatetheslice = 0
    else:
        result = pv.Contour(Input=reader)
        result.ContourBy = ["POINTS", args.field]
        result.Isosurfaces = [args.iso]
    result.UpdatePipeline(time)

    view = pv.CreateRenderView(ViewSize=[1600, 800])
    view.ViewTime = time
    view.UseColorPaletteForBackground = 0
    view.Background = rgb(SURFACE)
    view.OrientationAxesVisibility = 0
    display = pv.Show(result, view)
    # Geen belichting: de kleur moet exact de waarde weergeven
    display.Ambient = 1.0
    display.Diffuse = 0.0
    if args.edges:
        display.SetRepresentationType("Surface With Edges")
        display.EdgeColor = rgb(INK)

    if color_field:
        low, high, bar = color_by(display, view, result, color_field)
        print(f"t={time:g}, {color_field}: {low:.4g} .. {high:.4g}")
    else:
        display.AmbientColor = rgb(SEQUENTIAL[0])
        display.DiffuseColor = rgb(SEQUENTIAL[0])
        print(f"t={time:g}, mesh")

    size = [IMAGE_WIDTH, 800]
    view.ResetCamera()
    if args.mode == "slice":
        size = frame_slice(view, result.GetDataInformation().GetBounds(), args.normal,
                           bool(color_field))
        if color_field:
            bar.Orientation = "Horizontal"
            bar.WindowLocation = "Any Location"
            bar.Position = [0.35, 0.02]
            bar.ScalarBarLength = 0.3
            bar.ScalarBarThickness = 14

    stem = f"{args.field}_{args.mode}{'_edges' if args.edges else ''}" if args.field else "mesh"
    path = output_path(case, stem, "png", args.output)
    pv.SaveScreenshot(str(path), view, ImageResolution=size)
    print(path)


if __name__ == "__main__":
    main()
