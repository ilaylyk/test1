# -*- coding: utf-8 -*-
"""AutoCAD-style redraw of a hand-drawn apartment plan (2nd floor, M 1:100).

Source: scanned BTI-style sketch (plan of a 2nd-floor apartment).
Topology and annotations follow the original; wall geometry is rebuilt on a
clean orthogonal grid so the plan closes. Units: meters, INSUNITS = 6.

Design frame: X -> right, Y -> down (screen-like). All entities are emitted
flipped: y_dxf = 14.25 - y, so the DXF has a standard positive Y-up frame.

Outputs:
    plan_kvartiry_2etazh.dxf   -- R2018 DXF, opens in AutoCAD/nanoCAD/etc.
    plan_preview.png           -- quick raster preview for verification
"""
import math

import ezdxf
from ezdxf.enums import TextEntityAlignment

# ----------------------------------------------------------------------
# Design-frame constants (meters)
# ----------------------------------------------------------------------
ET = 0.25          # exterior wall thickness
IT = 0.10          # interior partition thickness
YMAX = 14.25       # outer bottom face of the building (design frame)

OUT_DIR = r"C:\Users\ilayl\.zcode\workspace\draft-032df714-1235-4dc3-80d5-36a4389ed870\apartment-plan-dxf"
DXF_PATH = OUT_DIR + r"\plan_kvartiry_2etazh.dxf"
PNG_PATH = OUT_DIR + r"\plan_preview.png"


def X(x: float) -> float:
    return round(x, 4)


def Y(y: float) -> float:
    """Flip design Y (down) into DXF Y (up)."""
    return round(YMAX - y, 4)


# ----------------------------------------------------------------------
# Document, layers, text style, dimension style
# ----------------------------------------------------------------------
doc = ezdxf.new("R2018", setup=True)
doc.header["$INSUNITS"] = 6       # meters
doc.header["$MEASUREMENT"] = 1    # metric
doc.header["$LTSCALE"] = 1.0
doc.header["$TEXTSIZE"] = 0.25

LAYERS = [
    # name,         color, lineweight (0.01 mm)
    ("Стены",       7, 50),
    ("Окна",        4, 18),
    ("Двери",       2, 18),
    ("Размеры",     3, 13),
    ("Текст",       7, 13),
    ("Сантехника",  5, 13),
    ("Мебель",     30, 13),
]
for name, color, lw in LAYERS:
    doc.layers.add(name, color=color, lineweight=lw)

if "TXT" not in doc.styles:
    doc.styles.add("TXT", font="arial.ttf")

ds = doc.dimstyles.add("PLAN")
ds.dxf.dimtxsty = "TXT"
ds.dxf.dimtxt = 0.18     # text height: 1.8 mm on paper at 1:100
ds.dxf.dimtsz = 0.10     # architectural tick instead of arrow (dimasz=0)
ds.dxf.dimasz = 0.0
ds.dxf.dimexe = 0.08
ds.dxf.dimexo = 0.08
ds.dxf.dimdec = 2
ds.dxf.dimclrt = 3
ds.dxf.dimclrd = 3
ds.dxf.dimclre = 3
ds.dxf.dimscale = 1.0

msp = doc.modelspace()

# ----------------------------------------------------------------------
# Primitive helpers
# ----------------------------------------------------------------------

def rect(x1, y1, x2, y2, layer, closed=True):
    pts = [(X(x1), Y(y1)), (X(x2), Y(y1)), (X(x2), Y(y2)), (X(x1), Y(y2))]
    msp.add_lwpolyline(pts, close=closed, dxfattribs={"layer": layer})


def line(x1, y1, x2, y2, layer):
    msp.add_line((X(x1), Y(y1)), (X(x2), Y(y2)), dxfattribs={"layer": layer})


def circle(x, y, r, layer):
    msp.add_circle((X(x), Y(y)), r, dxfattribs={"layer": layer})


def wall(x1, y1, x2, y2):
    """Wall piece: outlined polyline + solid hatch fill (BTI style)."""
    rect(x1, y1, x2, y2, "Стены")
    h = msp.add_hatch(color=8, dxfattribs={"layer": "Стены"})
    h.paths.add_polyline_path(
        [(X(x1), Y(y1)), (X(x2), Y(y1)), (X(x2), Y(y2)), (X(x1), Y(y2))],
        is_closed=True,
    )


def window(x1, y1, x2, y2):
    """Window opening: thin frame + central glazing line."""
    rect(x1, y1, x2, y2, "Окна")
    if (x2 - x1) >= (y2 - y1):            # horizontal window
        ym = (y1 + y2) / 2.0
        line(x1, ym, x2, ym, "Окна")
        line(x1, y1, x1, y2, "Окна")      # jambs
        line(x2, y1, x2, y2, "Окна")
    else:                                  # vertical window
        xm = (x1 + x2) / 2.0
        line(xm, y1, xm, y2, "Окна")
        line(x1, y1, x2, y1, "Окна")
        line(x1, y2, x2, y2, "Окна")


def door(hinge, leaf_end, jamb):
    """Door leaf (open 90 deg) + quarter-circle swing arc."""
    line(hinge[0], hinge[1], leaf_end[0], leaf_end[1], "Двери")
    cx, cy = X(hinge[0]), Y(hinge[1])
    r = math.hypot(leaf_end[0] - hinge[0], leaf_end[1] - hinge[1])
    p1 = (X(leaf_end[0]), Y(leaf_end[1]))
    p2 = (X(jamb[0]), Y(jamb[1]))
    a1 = math.degrees(math.atan2(p1[1] - cy, p1[0] - cx))
    a2 = math.degrees(math.atan2(p2[1] - cy, p2[0] - cx))
    if (a2 - a1) % 360.0 <= 180.0:
        msp.add_arc((cx, cy), r, a1, a2, dxfattribs={"layer": "Двери"})
    else:
        msp.add_arc((cx, cy), r, a2, a1, dxfattribs={"layer": "Двери"})


def text(x, y, s, h=0.30, layer="Текст",
         align=TextEntityAlignment.MIDDLE_CENTER, rotation=0.0):
    t = msp.add_text(
        s,
        dxfattribs={
            "style": "TXT",
            "height": h,
            "layer": layer,
            "rotation": rotation,
        },
    )
    t.set_placement((X(x), Y(y)), align=align)


def dim(p1, p2, base, angle=0.0, label=None):
    """Linear dimension with architectural ticks (dimstyle PLAN)."""
    fp1 = (X(p1[0]), Y(p1[1]))
    fp2 = (X(p2[0]), Y(p2[1]))
    fbase = (X(base[0]), Y(base[1]))
    kwargs = dict(base=fbase, p1=fp1, p2=fp2, angle=angle, dimstyle="PLAN")
    if label is not None:
        kwargs["text"] = label
    msp.add_linear_dim(**kwargs).render()


# ----------------------------------------------------------------------
# Walls (design frame, y-down). E* = exterior, I* = interior.
# ----------------------------------------------------------------------
WALLS = [
    # E1 top band (y 0..0.25), gaps = windows W1..W3
    (0.00, 0.00, 0.80, 0.25),
    (2.60, 0.00, 3.725, 0.25),
    (5.325, 0.00, 6.25, 0.25),
    (8.25, 0.00, 8.90, 0.25),
    # E2 left band (x 0..0.25), gap = bathroom window W4
    (0.00, 0.25, 0.25, 2.85),
    (0.00, 3.99, 0.25, 5.65),
    # E3 right band (x 8.65..8.90), gap = entrance door
    (8.65, 0.25, 8.90, 6.90),
    (8.65, 7.90, 8.90, 14.25),
    # E4 hall bottom band, right part = 1.16 passage into lobby
    (0.25, 5.65, 3.59, 5.75),
    # E5 neck-left / lobby-left / room-left band
    (3.49, 5.75, 3.59, 14.00),
    # E6 room bottom band, gap = window W5
    (3.49, 14.00, 5.40, 14.25),
    (7.00, 14.00, 8.90, 14.25),
    # I1 kitchen | living1 partition, gap = kitchen doorway
    (3.20, 0.25, 3.30, 1.30),
    (3.20, 2.20, 3.30, 4.45),
    # I2 living1 | living2 partition
    (5.75, 0.25, 5.85, 6.45),
    # I3 kitchen | bathroom partition
    (0.25, 2.25, 3.20, 2.35),
    # I4 bathroom bottom / hall top, gap = bathroom door
    (0.25, 4.04, 2.20, 4.14),
    (3.00, 4.04, 3.20, 4.14),
    # I5 living1 bottom / corridor top, gap = 1.16 opening
    (3.30, 4.35, 3.94, 4.45),
    (5.10, 4.35, 5.85, 4.45),
    # I6 living2 bottom band, gap = living2 door
    (4.75, 6.35, 6.60, 6.45),
    (7.50, 6.35, 8.65, 6.45),
    # I7 lobby bottom / room top, gap = room door
    (3.49, 8.25, 4.00, 8.35),
    (4.90, 8.25, 8.65, 8.35),
    # I8 neck-right wall block (closes corridor/lobby junction)
    (4.75, 5.65, 5.85, 6.35),
]
for w in WALLS:
    wall(*w)

# ----------------------------------------------------------------------
# Windows
# ----------------------------------------------------------------------
WINDOWS = [
    (0.80, 0.00, 2.60, 0.25),      # W1 kitchen, 1.80
    (3.725, 0.00, 5.325, 0.25),    # W2 living 10.7, 1.60
    (6.25, 0.00, 8.25, 0.25),      # W3 living 16.7, 2.00
    (0.00, 2.85, 0.25, 3.99),      # W4 bathroom, 1.14 (left wall)
    (5.40, 14.00, 7.00, 14.25),    # W5 room 13.1, 1.60 (bottom wall)
]
for w in WINDOWS:
    window(*w)

# ----------------------------------------------------------------------
# Doors: (hinge, leaf_end, jamb) in design frame
# ----------------------------------------------------------------------
DOORS = [
    # kitchen -> living1 (opening in I1)
    ((3.20, 1.30), (2.40, 1.30), (3.20, 2.20)),
    # bathroom <- hall (opening in I4)
    ((3.00, 4.04), (3.00, 3.24), (2.20, 4.04)),
    # living2 (16.7) <- lobby (opening in I6)
    ((6.60, 6.35), (6.60, 5.45), (7.50, 6.35)),
    # room 13.1 <- lobby (opening in I7)
    ((4.00, 8.35), (4.00, 9.25), (4.90, 8.35)),
    # entrance door (opening in E3 right wall)
    ((8.65, 6.90), (7.75, 6.90), (8.65, 7.90)),
]
for d in DOORS:
    door(*d)

# ----------------------------------------------------------------------
# Plumbing fixtures
# ----------------------------------------------------------------------
# Kitchen: sink under window + stove at left wall
rect(0.45, 0.35, 1.05, 0.75, "Сантехника")
circle(0.75, 0.55, 0.16, "Сантехника")
rect(0.35, 1.45, 0.95, 2.05, "Сантехника")
for bx, by in [(0.53, 1.63), (0.77, 1.63), (0.53, 1.87), (0.77, 1.87)]:
    circle(bx, by, 0.09, "Сантехника")

# Bathroom: bathtub along left wall, washbasin, toilet
rect(0.35, 2.45, 1.05, 3.95, "Сантехника")
rect(0.43, 2.53, 0.97, 3.87, "Сантехника")
circle(0.70, 3.72, 0.045, "Сантехника")
rect(2.10, 2.45, 2.50, 2.85, "Сантехника")
circle(2.30, 2.65, 0.14, "Сантехника")
rect(2.60, 2.45, 3.00, 2.65, "Сантехника")
circle(2.80, 2.88, 0.16, "Сантехника")

# ----------------------------------------------------------------------
# Furniture: built-in wardrobes
# ----------------------------------------------------------------------
rect(7.00, 7.80, 8.55, 8.25, "Мебель")          # lobby wardrobe
line(7.35, 7.80, 7.35, 8.25, "Мебель")
line(7.70, 7.80, 7.70, 8.25, "Мебель")
line(8.05, 7.80, 8.05, 8.25, "Мебель")

rect(3.64, 8.55, 4.19, 11.05, "Мебель")         # room wardrobe, 2.50 long
line(3.64, 9.55, 4.19, 9.55, "Мебель")
line(3.64, 10.55, 4.19, 10.55, "Мебель")
text(4.55, 9.80, "2,50", h=0.20, layer="Мебель")

# ----------------------------------------------------------------------
# Room labels (name + area, as on the original sketch)
# ----------------------------------------------------------------------
LABELS = [
    (1.70, 1.10, 1.70, 1.42, "КУХНЯ", "6,5"),
    (1.78, 3.00, 1.78, 3.32, "САН. УЗЕЛ", "4,93"),
    (2.40, 4.80, 2.40, 5.12, "ПРИХОЖАЯ", "7,1"),
    (4.50, 2.10, 4.50, 2.42, "ЖИЛАЯ", "10,7"),
    (7.20, 3.20, 7.20, 3.52, "ЖИЛАЯ", "16,7"),
    (6.20, 11.20, 6.20, 11.52, "ЖИЛАЯ", "13,1"),
]
for nx, ny, ax, ay, name, area in LABELS:
    text(nx, ny, name, h=0.28)
    text(ax, ay, area, h=0.24)

# ----------------------------------------------------------------------
# Title block texts
# ----------------------------------------------------------------------
text(4.45, -1.75, "ПЛАН КВАРТИРЫ  М 1:100", h=0.40)
text(2.20, -1.10, "2-й этаж", h=0.28,
     align=TextEntityAlignment.MIDDLE_LEFT)

# ----------------------------------------------------------------------
# Dimensions (as annotated on the sketch)
# ----------------------------------------------------------------------
# Top chain: room widths
dim((0.25, 0.0), (3.20, 0.0), (1.72, -0.55))
dim((3.30, 0.0), (5.75, 0.0), (4.52, -0.55))
dim((5.85, 0.0), (8.65, 0.0), (7.25, -0.55))
# Left: kitchen+bathroom column depth 4.04; bathroom window 1.14
dim((0.0, 0.0), (0.0, 4.04), (-0.60, 2.00), angle=90)
dim((0.0, 2.85), (0.0, 3.99), (-0.28, 3.42), angle=90)
# Right: living2 depth 6.35; room depth 5.65
dim((8.90, 0.0), (8.90, 6.35), (9.45, 3.20), angle=90)
dim((8.90, 8.35), (8.90, 14.00), (9.45, 11.20), angle=90)
# Bottom: room width (annotation kept from sketch)
dim((3.59, 14.25), (8.65, 14.25), (6.10, 14.80), label="4,38")
# Hall width 4.50
dim((0.25, 5.75), (4.75, 5.75), (2.50, 6.45))
# 1.16 openings: living1 -> corridor, corridor -> lobby
dim((3.94, 4.45), (5.10, 4.45), (4.52, 3.90))
dim((3.59, 5.75), (4.75, 5.75), (4.17, 6.10))

# ----------------------------------------------------------------------
# Export
# ----------------------------------------------------------------------
doc.saveas(DXF_PATH)
print("DXF saved:", DXF_PATH)

# Raster preview for verification
try:
    from ezdxf.addons.drawing.matplotlib import qsave
    qsave(msp, PNG_PATH, bg="#FFFFFF", dpi=220)
    print("Preview saved:", PNG_PATH)
except Exception as exc:  # fallback renderer
    print("qsave failed (%s), using manual backend" % exc)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

    fig = plt.figure()
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    Frontend(ctx, MatplotlibBackend(ax)).draw_layout(msp)
    ax.set_aspect("equal")
    fig.savefig(PNG_PATH, dpi=220, facecolor="#FFFFFF")
    plt.close(fig)
    print("Preview saved (fallback):", PNG_PATH)
