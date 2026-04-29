"""
freecad_base.py — CAD-detail skill helper using the FreeCAD Draft Python API.

Script structure:

    import sys
    sys.path.insert(0, '/Users/ottt/.pi/agent/skills/freecad-detail/scripts')
    from freecad_base import *

    new_doc("mm")                    # "mm" (default) or "in"

    set_layer("OUTLINE")
    add_polygon([[0,0],[200,0],[200,300],[0,300]])
    add_hatch([[0,0],[200,0],[200,300],[0,300]], HATCH.STEEL)
    circ = add_circle(100, 150, 50)
    add_centerlines(100, 150, 60)
    add_linear_dim(0, 0, 200, 0, -15, 0)     # horizontal, 15 mm below
    add_linear_dim(0, 0, 0, 300, -15, 90)    # vertical, 15 mm left
    add_diameter_dim(circ, 45)
    add_label("PLATE", 100, 150)
    add_border_and_title(420, 297, "DETAIL TITLE", "1:1", "mm")

    path = save_doc("filename")      # ~/Documents/CAD/filename.dxf

Run headless:
    /Applications/FreeCAD.app/Contents/MacOS/FreeCADCmd /tmp/script.py

View:
    open ~/Documents/CAD/filename.dxf

Refs:
    https://wiki.freecad.org/Draft_API
    https://wiki.freecad.org/Headless_FreeCAD
"""

import math
import os
from pathlib import Path

# Gui.setupWithoutGUI() must be called before Draft / importDXF so that
# view providers initialise and layer colours, text size, dim styling work.
import FreeCAD as App
import FreeCADGui as Gui
Gui.setupWithoutGUI()

import Draft
import importDXF

# ---------------------------------------------------------------------------
# Drawing standards  (mm values; inch drawings scale at V())
# ---------------------------------------------------------------------------
TEXT_HEIGHT  = 3.0    # ≈ Leroy No. 120 (0.12 in)
TITLE_HEIGHT = 6.0    # ≈ Leroy No. 240 (0.24 in)
SMALL_HEIGHT = 2.0    # ≈ Leroy No. 80  (0.08 in)

OUTPUT_DIR = Path.home() / "Documents" / "CAD"

# ---------------------------------------------------------------------------
# Hatch patterns — mapped to FCPAT.pat bundles with FreeCAD
# Tuple: (pattern_name, default_scale_mm)
# ---------------------------------------------------------------------------
class HATCH:
    STEEL      = ("Diagonal4",   4.0)   # 45° lines — steel / metal
    ALUMINUM   = ("Diagonal5",   4.0)   # 45° reverse — aluminum
    CONCRETE   = ("Diamond",     2.0)   # fine crosshatch — cast concrete
    BRICK      = ("Horizontal5", 8.0)   # horizontal lines — brick / CMU
    EARTH      = ("Diamond2",    6.0)   # medium crosshatch — earth / fill
    GRAVEL     = ("Square",      4.0)   # square grid — gravel / stone
    INSULATION = ("Horizontal5", 4.0)   # horizontal lines — batt insulation

_PAT_FILE = os.path.join(App.getHomePath(), "data", "Mod", "TechDraw", "PAT", "FCPAT.pat")

# ---------------------------------------------------------------------------
# Layer definitions: name → (line_color RGBA, line_width mm, draw_style)
# draw_style: "Solid" | "Dashed" | "Dashdot" | "Dotted"
# ---------------------------------------------------------------------------
_LAYER_DEFS = {
    "OUTLINE":   ((1.00, 1.00, 1.00, 1.0), 0.50, "Solid"),
    "HIDDEN":    ((0.00, 0.80, 0.00, 1.0), 0.25, "Dashed"),
    "CENTER":    ((0.80, 0.00, 0.00, 1.0), 0.18, "Dashdot"),
    "DIMENSION": ((0.80, 0.80, 0.00, 1.0), 0.18, "Solid"),
    "TEXT":      ((1.00, 1.00, 1.00, 1.0), 0.18, "Solid"),
    "HATCH":     ((0.50, 0.50, 0.50, 1.0), 0.09, "Solid"),
    "DETAIL":    ((0.00, 0.80, 0.80, 1.0), 0.35, "Solid"),
    "TITLE":     ((1.00, 1.00, 1.00, 1.0), 0.25, "Solid"),
    "BORDER":    ((1.00, 1.00, 1.00, 1.0), 0.70, "Solid"),
}

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
_doc    = None
_layers = {}     # name → Draft Layer object
_cur    = "OUTLINE"
_units  = "mm"
_scale  = 1.0    # mm per drawing unit: 1.0 for mm, 25.4 for in

# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------

def new_doc(units="mm"):
    """
    Create a new FreeCAD document with standard layers.
    Call once at the top of every generated script.

    units: "mm" (default) or "in"
    """
    global _doc, _layers, _cur, _units, _scale
    _units = units
    _scale = 25.4 if units == "in" else 1.0
    _doc   = App.newDocument("Detail")
    _layers = {}
    _cur    = "OUTLINE"

    for name, (color, width, style) in _LAYER_DEFS.items():
        lyr = Draft.make_layer(
            name,
            line_color=color,
            shape_color=(0.75, 0.75, 0.75, 1.0),
            line_width=width,
            draw_style=style,
        )
        _layers[name] = lyr

    return _doc


def set_layer(name):
    """Set the current layer for subsequent add_line / add_circle / add_polygon calls."""
    global _cur
    _cur = name


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def V(x, y):
    """User-unit coordinate → FreeCAD mm vector (Z = 0)."""
    return App.Vector(x * _scale, y * _scale, 0.0)


def _place(obj):
    """Add obj to the current layer."""
    lyr = _layers.get(_cur)
    if lyr is not None:
        lyr.Group = lyr.Group + [obj]
    return obj


def _place_on(obj, layer_name):
    """Add obj to a specific layer without touching the current layer."""
    lyr = _layers.get(layer_name)
    if lyr is not None:
        lyr.Group = lyr.Group + [obj]
    return obj


def _style_dim(dim):
    """Apply standard dimension text and arrow styling."""
    if not (hasattr(dim, "ViewObject") and dim.ViewObject):
        return
    try:
        dim.ViewObject.FontSize  = TEXT_HEIGHT * _scale
        dim.ViewObject.ArrowType = "Arrow"
        dim.ViewObject.ArrowSize = TEXT_HEIGHT * _scale * 0.6
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Geometry  (use set_layer() before calling these)
# ---------------------------------------------------------------------------

def add_line(x1, y1, x2, y2):
    """Draw a line on the current layer."""
    return _place(Draft.make_line(V(x1, y1), V(x2, y2)))


def add_circle(cx, cy, r):
    """
    Draw a circle on the current layer.
    Returns the FreeCAD circle object — pass it to add_radius_dim / add_diameter_dim.
    """
    placement = App.Placement(V(cx, cy), App.Rotation())
    return _place(Draft.make_circle(r * _scale, placement=placement))


def add_arc(cx, cy, r, start_deg, end_deg):
    """Draw an arc on the current layer (angles in degrees, CCW from +X)."""
    placement = App.Placement(V(cx, cy), App.Rotation())
    return _place(Draft.make_circle(
        r * _scale, placement=placement,
        startangle=start_deg, endangle=end_deg,
    ))


def add_polygon(points, layer=None):
    """
    Draw a closed polygon outline.
    Uses the current layer unless layer= is given.
    """
    pts  = [V(p[0], p[1]) for p in points]
    wire = Draft.make_wire(pts, closed=True)
    if layer:
        _place_on(wire, layer)
    else:
        _place(wire)
    return wire


def add_centerlines(cx, cy, size):
    """Draw crosshair centerlines on the CENTER layer."""
    h = Draft.make_line(V(cx - size, cy), V(cx + size, cy))
    v = Draft.make_line(V(cx, cy - size), V(cx, cy + size))
    _place_on(h, "CENTER")
    _place_on(v, "CENTER")

# ---------------------------------------------------------------------------
# Hatch  (layer HATCH, applied automatically)
# ---------------------------------------------------------------------------

def add_hatch(points, pattern_tuple, scale=None, angle=0):
    """
    Fill a closed polygonal region with a hatch pattern.

    points:        [[x,y], ...]  — same boundary used for add_polygon
    pattern_tuple: HATCH.STEEL, HATCH.CONCRETE, etc.
    scale:         pattern scale in mm; None → use HATCH default
    angle:         rotation in degrees (default 0)
    """
    pat_name, default_scale = pattern_tuple
    if scale is None:
        scale = default_scale

    pts  = [V(p[0], p[1]) for p in points]
    wire = Draft.make_wire(pts, closed=True)
    wire.MakeFace = True
    _doc.recompute()

    hatch = Draft.make_hatch(wire, _PAT_FILE, pat_name, scale, angle)
    _place_on(hatch, "HATCH")
    return hatch

# ---------------------------------------------------------------------------
# Dimensions  (layer DIMENSION, applied automatically)
# ---------------------------------------------------------------------------

def add_linear_dim(x1, y1, x2, y2, offset, angle=0):
    """
    Horizontal (angle=0) or vertical (angle=90) linear dimension.

    offset: distance from geometry to dimension line
            positive = above / right,  negative = below / left
    """
    if angle == 0:
        p3 = V((x1 + x2) / 2, y1 + offset)
    else:
        p3 = V(x1 + offset, (y1 + y2) / 2)

    dim = Draft.make_dimension(V(x1, y1), V(x2, y2), p3)
    _style_dim(dim)
    _place_on(dim, "DIMENSION")
    return dim


def add_radius_dim(circle_obj, angle=45):
    """
    Radius dimension on a circle.
    circle_obj: the object returned by add_circle().
    angle: leader direction in degrees from +X (default 45).
    """
    edge  = circle_obj.Shape.Edges[0]
    c     = edge.Curve.Center
    r     = edge.Curve.Radius
    rad   = math.radians(angle)
    p4    = App.Vector(c.x + r * 1.5 * math.cos(rad),
                       c.y + r * 1.5 * math.sin(rad), 0.0)
    dim   = Draft.make_dimension(circle_obj, 0, "radius", p4)
    _style_dim(dim)
    _place_on(dim, "DIMENSION")
    return dim


def add_diameter_dim(circle_obj, angle=45):
    """
    Diameter dimension on a circle.
    circle_obj: the object returned by add_circle().
    angle: chord axis in degrees from +X (default 45).
    """
    edge  = circle_obj.Shape.Edges[0]
    c     = edge.Curve.Center
    r     = edge.Curve.Radius
    rad   = math.radians(angle)
    p4    = App.Vector(c.x + r * 1.5 * math.cos(rad),
                       c.y + r * 1.5 * math.sin(rad), 0.0)
    dim   = Draft.make_dimension(circle_obj, 0, "diameter", p4)
    _style_dim(dim)
    _place_on(dim, "DIMENSION")
    return dim

# ---------------------------------------------------------------------------
# Annotations  (layer TEXT / DIMENSION, applied automatically)
# ---------------------------------------------------------------------------

def add_label(text, x, y, height=None, layer="TEXT"):
    """
    Add a text label.
    height: in drawing units (default TEXT_HEIGHT = 3 mm / 0.12 in)
    layer:  "TEXT" (default) or "TITLE"
    """
    height_mm = (height if height is not None else TEXT_HEIGHT) * _scale
    t = Draft.make_text([text], V(x, y))
    if hasattr(t, "ViewObject") and t.ViewObject:
        try:
            t.ViewObject.FontSize = height_mm
        except Exception:
            pass
    _place_on(t, layer)
    return t


def add_leader(pts, text, height=None):
    """
    Draw a leader line with callout text at the tail end.
    pts: [[x,y], ...] — arrowhead at the first point.
    """
    height = height if height is not None else TEXT_HEIGHT
    for i in range(len(pts) - 1):
        ln = Draft.make_line(V(pts[i][0], pts[i][1]), V(pts[i+1][0], pts[i+1][1]))
        _place_on(ln, "DIMENSION")
    end = pts[-1]
    add_label(text, end[0] + height * 0.5, end[1], height, "TEXT")

# ---------------------------------------------------------------------------
# Border and title block
# ---------------------------------------------------------------------------

def add_border_and_title(w, h, title, scale="1:1", units=None, by=""):
    """
    Add a sheet border and simple title block.  Call last, after all geometry.

    w, h:   sheet size in drawing units (1:1, real-world)
    title:  detail title (auto upper-cased)
    scale:  default "1:1"
    units:  "mm" or "in" (inherits from new_doc() if omitted)
    by:     optional drafter initials
    """
    units = units or _units
    m     = 0.5  if units == "in" else 13.0
    box_h = 0.75 if units == "in" else 19.0
    mid_x = m + (w - 2 * m) * 0.60
    cy    = m + box_h / 2

    # Border and title box
    add_polygon([[m, m], [w-m, m], [w-m, h-m], [m, h-m]],   layer="BORDER")
    add_polygon([[m, m], [w-m, m], [w-m, m+box_h], [m, m+box_h]], layer="BORDER")
    ln = Draft.make_line(V(mid_x, m), V(mid_x, m + box_h))
    _place_on(ln, "BORDER")

    # Title text
    add_label(title.upper(),
              m + (mid_x - m) / 2,
              cy + TEXT_HEIGHT * 0.4,
              TITLE_HEIGHT, "TITLE")

    # Scale text
    add_label(f"SCALE: {scale}",
              mid_x + (w - m - mid_x) / 2,
              cy + TEXT_HEIGHT * 0.5,
              TEXT_HEIGHT, "TITLE")

    # Drafter
    if by:
        add_label(f"BY: {by}",
                  mid_x + (w - m - mid_x) / 2,
                  cy - TEXT_HEIGHT * 0.5,
                  SMALL_HEIGHT, "TITLE")

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_doc(filename):
    """
    Recompute, collect all objects from all layers, export to DXF.
    Returns the absolute path of the saved file.
    """
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in filename)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = str(OUTPUT_DIR / f"{safe}.dxf")

    _doc.recompute()

    all_objs = []
    for lyr in _layers.values():
        all_objs.extend(lyr.Group)

    importDXF.export(all_objs, path)
    print(f"Saved: {path}")
    return path
