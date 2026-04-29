"""
dxf_base.py — standard CAD document setup for the cad-detail skill.

Usage:
    from dxf_base import new_doc, save_doc, HATCH, add_linear_dim, add_radius_dim

    doc, msp = new_doc(units="mm", title="BEAM CONNECTION")
    # ... draw geometry on msp ...
    path = save_doc(doc, "beam_connection")
"""

import math
import os
from pathlib import Path
from typing import Optional

import ezdxf
from ezdxf import enums as dxf_enums

# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path.home() / "Documents" / "CAD"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Standard layer definitions
# ---------------------------------------------------------------------------

LAYERS = {
    # name            color  linetype      lineweight (100ths of mm)
    "OUTLINE":        (7,    "Continuous",  50),   # main object lines
    "HIDDEN":         (3,    "HIDDEN",      25),   # hidden / dashed lines
    "CENTER":         (1,    "CENTER",      18),   # centerlines
    "DIMENSION":      (2,    "Continuous",  18),   # dimensions
    "TEXT":           (7,    "Continuous",  18),   # notes and labels
    "HATCH":          (253,  "Continuous",   9),   # section hatching
    "DETAIL":         (4,    "Continuous",  35),   # secondary object geometry
    "CONSTRUCTION":   (8,    "Continuous",   9),   # construction / reference lines
    "TITLE":          (7,    "Continuous",  25),   # title block text
    "BORDER":         (7,    "Continuous",  70),   # sheet border
}


# ---------------------------------------------------------------------------
# Hatch pattern reference
# ---------------------------------------------------------------------------

class HATCH:
    """Common DXF hatch pattern names with typical CAD uses."""
    STEEL         = "ANSI31"   # 45° diagonal lines — steel, metal sections
    STEEL_CROSS   = "ANSI32"   # steel (alternating diagonals)
    BRASS         = "ANSI33"
    PLASTIC       = "ANSI34"
    FIREBRICK     = "ANSI35"
    MARBLE        = "ANSI36"
    LEAD          = "ANSI37"
    ALUMINUM      = "ANSI38"
    CONCRETE      = "AR-CONC"  # aggregate concrete
    BRICK         = "AR-BRSTD"
    SAND          = "AR-SAND"
    EARTH         = "EARTH"    # earth / soil fill
    GRAVEL        = "GRAVEL"
    INSULATION    = "INSUL"    # batt insulation
    WOOD_END      = "ANSI31"   # end grain — same as steel but smaller scale
    WOOD_LONG     = "ANSI32"   # longitudinal grain
    CROSS         = "CROSS"    # general crosshatch
    DOTS          = "DOTS"

    # Recommended scale values for architectural details (units = mm)
    SCALE = {
        "ANSI31":   2.5,   # steel section — fine
        "ANSI32":   2.5,
        "AR-CONC":  0.5,   # concrete aggregate — keep small
        "AR-BRSTD": 1.0,
        "EARTH":    1.5,
        "GRAVEL":   1.0,
        "INSUL":    2.0,
    }


# ---------------------------------------------------------------------------
# Document factory
# ---------------------------------------------------------------------------

UNIT_CODES = {"in": 1, "ft": 2, "mm": 4, "cm": 5, "m": 6}


def new_doc(units: str = "mm", title: Optional[str] = None) -> tuple:
    """
    Create a new DXF R2010 document with standard layers, linetypes,
    and a dimension style calibrated for the chosen units.

    Returns:
        (doc, msp) — the document and its modelspace.
    """
    doc = ezdxf.new("R2010")
    doc.units = UNIT_CODES.get(units, 4)

    # Store metadata
    doc.header["$INSUNITS"] = UNIT_CODES.get(units, 4)
    if title:
        doc.header["$ACADVER"] = "AC1024"  # R2010

    # --- Linetypes ---
    if units == "mm":
        scale = 1.0
    elif units == "in":
        scale = 1 / 25.4
    else:
        scale = 1.0

    doc.linetypes.add("HIDDEN",  pattern=[6 * scale, -3 * scale])
    doc.linetypes.add("CENTER",  pattern=[20 * scale, -5 * scale, 5 * scale, -5 * scale])
    doc.linetypes.add("PHANTOM", pattern=[25 * scale, -5 * scale, 5 * scale, -5 * scale, 5 * scale, -5 * scale])
    doc.linetypes.add("DASHDOT", pattern=[15 * scale, -5 * scale, 0, -5 * scale])

    # --- Layers ---
    for name, (color, linetype, lw) in LAYERS.items():
        if linetype != "Continuous" and linetype not in [lt.dxf.name for lt in doc.linetypes]:
            linetype = "Continuous"
        doc.layers.add(name, dxfattribs={"color": color, "linetype": linetype, "lineweight": lw})

    # --- Dimension style ---
    _setup_dimstyle(doc, units)

    return doc, doc.modelspace()


def _setup_dimstyle(doc, units: str) -> None:
    """Configure a dimension style appropriate for the unit system."""
    if units == "mm":
        arrow_size = 3.5
        text_height = 3.5
        offset = 2.0
        ext_beyond = 2.0
        ext_offset = 1.5
    else:  # inches
        arrow_size = 0.125
        text_height = 0.125
        offset = 0.0625
        ext_beyond = 0.0625
        ext_offset = 0.0625

    ds = doc.dimstyles.get("Standard")
    ds.dxf.dimasz  = arrow_size
    ds.dxf.dimtxt  = text_height
    ds.dxf.dimdle  = 0
    ds.dxf.dimexe  = ext_beyond
    ds.dxf.dimexo  = ext_offset
    ds.dxf.dimgap  = offset
    ds.dxf.dimclrd = 2   # dimension line: yellow
    ds.dxf.dimclre = 2   # extension line: yellow
    ds.dxf.dimclrt = 2   # text: yellow


# ---------------------------------------------------------------------------
# Dimension helpers
# ---------------------------------------------------------------------------

def add_linear_dim(
    msp,
    p1: tuple,
    p2: tuple,
    offset: float,
    angle: float = 0,
    layer: str = "DIMENSION",
    override: Optional[dict] = None,
) -> None:
    """
    Add a linear dimension.

    Args:
        p1, p2:  measurement points
        offset:  perpendicular distance from p1/p2 to the dimension line
                 (negative = below/left)
        angle:   0 = horizontal, 90 = vertical
    """
    attrs = {"layer": layer}
    if angle == 0:
        base = ((p1[0] + p2[0]) / 2, p1[1] + offset)
    elif angle == 90:
        base = (p1[0] + offset, (p1[1] + p2[1]) / 2)
    else:
        # General case: offset perpendicular to measurement direction
        dx, dy = math.cos(math.radians(angle + 90)), math.sin(math.radians(angle + 90))
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        base = (mx + offset * dx, my + offset * dy)

    dim = msp.add_linear_dim(
        base=base,
        p1=p1,
        p2=p2,
        angle=angle,
        dimstyle="Standard",
        override=override,
        dxfattribs=attrs,
    )
    dim.render()


def add_radius_dim(
    msp,
    center: tuple,
    radius: float,
    angle: float = 45,
    layer: str = "DIMENSION",
) -> None:
    """Add a radial dimension at the given angle (degrees from +X)."""
    dim = msp.add_radius_dim(
        center=center,
        radius=radius,
        angle=angle,
        dimstyle="Standard",
        dxfattribs={"layer": layer},
    )
    dim.render()


def add_diameter_dim(
    msp,
    center: tuple,
    radius: float,
    angle: float = 45,
    layer: str = "DIMENSION",
) -> None:
    """Add a diameter dimension at the given angle."""
    dim = msp.add_diameter_dim(
        center=center,
        radius=radius,
        angle=angle,
        dimstyle="Standard",
        dxfattribs={"layer": layer},
    )
    dim.render()


# ---------------------------------------------------------------------------
# Common geometry helpers
# ---------------------------------------------------------------------------

def add_centerlines(msp, center: tuple, size: float, layer: str = "CENTER") -> None:
    """Draw crosshair centerlines through a point (e.g., hole center)."""
    x, y = center
    msp.add_line((x - size, y), (x + size, y), dxfattribs={"layer": layer})
    msp.add_line((x, y - size), (x, y + size), dxfattribs={"layer": layer})


def add_hatch_region(
    msp,
    boundary: list[tuple],
    pattern: str = HATCH.STEEL,
    scale: Optional[float] = None,
    angle: float = 0,
    layer: str = "HATCH",
) -> None:
    """
    Hatch a closed polygonal region.

    Args:
        boundary: list of (x, y) vertices (open or closed — auto-closed)
        pattern:  hatch pattern name (use HATCH.* constants)
        scale:    pattern scale; defaults to HATCH.SCALE table or 2.5
        angle:    rotation of hatch pattern in degrees
    """
    if scale is None:
        scale = HATCH.SCALE.get(pattern, 2.5)
    h = msp.add_hatch(dxfattribs={"layer": layer})
    h.paths.add_polyline_path(boundary, is_closed=True)
    h.set_pattern_fill(pattern, scale=scale, angle=angle)


def add_label(
    msp,
    text: str,
    position: tuple,
    height: float = 3.5,
    align: str = "MIDDLE_CENTER",
    layer: str = "TEXT",
    rotation: float = 0,
) -> None:
    """Add a text label at the given position."""
    alignment = getattr(dxf_enums.TextEntityAlignment, align, dxf_enums.TextEntityAlignment.LEFT)
    msp.add_text(
        text,
        dxfattribs={"height": height, "layer": layer, "rotation": rotation},
    ).set_placement(position, align=alignment)


def add_leader(
    msp,
    vertices: list[tuple],
    annotation: str,
    text_height: float = 3.0,
    layer: str = "DIMENSION",
) -> None:
    """Add a leader line with annotation text at the last vertex."""
    for i in range(len(vertices) - 1):
        msp.add_line(vertices[i], vertices[i + 1], dxfattribs={"layer": layer})
    # Small arrow head at the start
    msp.add_line(vertices[0], vertices[1], dxfattribs={"layer": layer})
    # Text at the end
    end = vertices[-1]
    msp.add_text(
        annotation,
        dxfattribs={"height": text_height, "layer": "TEXT"},
    ).set_placement((end[0] + 2, end[1]), align=dxf_enums.TextEntityAlignment.MIDDLE_LEFT)


def add_border_and_title(
    msp,
    width: float,
    height: float,
    title: str,
    scale: str = "1:10",
    drawn_by: str = "",
    units: str = "mm",
) -> None:
    """
    Add a simple title block and border.

    Args:
        width, height: sheet extents in drawing units
        title:         detail title
        scale:         e.g. "1:10"
    """
    m = 10 if units == "mm" else 0.5  # margin

    # Border
    msp.add_lwpolyline(
        [(m, m), (width - m, m), (width - m, height - m), (m, height - m)],
        close=True,
        dxfattribs={"layer": "BORDER"},
    )

    # Title box at bottom
    box_h = 20 if units == "mm" else 0.75
    msp.add_lwpolyline(
        [(m, m), (width - m, m), (width - m, m + box_h), (m, m + box_h)],
        close=True,
        dxfattribs={"layer": "BORDER"},
    )
    # Vertical divider
    mid_x = width * 0.6
    msp.add_line((mid_x, m), (mid_x, m + box_h), dxfattribs={"layer": "BORDER"})

    text_h = 4.5 if units == "mm" else 0.18
    small_h = 3.0 if units == "mm" else 0.12
    cy = m + box_h / 2

    add_label(msp, title.upper(),  (m + (mid_x - m) / 2, cy + 2),
              height=text_h, layer="TITLE")
    add_label(msp, f"SCALE: {scale}", (mid_x + (width - m - mid_x) / 2, cy + 3),
              height=small_h, layer="TITLE")
    if drawn_by:
        add_label(msp, f"BY: {drawn_by}", (mid_x + (width - m - mid_x) / 2, cy - 3),
                  height=small_h, layer="TITLE")


# ---------------------------------------------------------------------------
# Save helper
# ---------------------------------------------------------------------------

def save_doc(doc, filename: str, output_dir: Optional[str] = None) -> str:
    """
    Save the DXF document.

    Args:
        filename:   base name without extension (e.g. "beam_connection")
        output_dir: directory to save in; defaults to ~/Documents/CAD/

    Returns:
        Absolute path of the saved file.
    """
    out = Path(output_dir) if output_dir else OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in filename)
    path = out / f"{safe}.dxf"

    doc.saveas(str(path))
    return str(path)
