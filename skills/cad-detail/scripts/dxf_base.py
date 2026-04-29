"""
dxf_base.py — standard CAD document setup for the cad-detail skill.

Standards enforced:
  - All geometry drawn at 1:1 (real-world dimensions)
  - Text style: RomanS (romans.shx) — AutoCAD LT compatible SHX font
  - Default text height: 1.2 drawing units
  - Dimension style: CADD standard, ROMANS style, 1.2 text height
  - Layers: OUTLINE, HIDDEN, CENTER, DIMENSION, TEXT, HATCH, DETAIL,
            CONSTRUCTION, TITLE, BORDER

Usage:
    from dxf_base import new_doc, save_doc, HATCH, add_linear_dim, add_radius_dim

    doc, msp = new_doc(units="in")          # or "mm"
    # ... draw geometry on msp at real-world size (1:1) ...
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
# Global standards
# ---------------------------------------------------------------------------

TEXT_HEIGHT  = 0.12       # Leroy No. 120 — standard engineering notes (Romans, 1:1)
TITLE_HEIGHT = 0.24       # Leroy No. 240 — detail title in title block
SMALL_HEIGHT = 0.08       # Leroy No. 80  — secondary notes / drawn-by field
ARROW_SIZE   = 0.18       # dimension arrowhead size (1.5× TEXT_HEIGHT)
DIM_GAP      = 0.06       # gap between dim line and text (0.5× TEXT_HEIGHT)
DIM_EXT      = 0.12       # extension line beyond dimension line
DIM_OFFSET   = 0.06       # extension line origin offset from measured point
ROMANS_FONT  = "romans.shx"   # AutoCAD LT Romans SHX font filename

# ---------------------------------------------------------------------------
# Standard layer definitions
# ---------------------------------------------------------------------------

LAYERS = {
    # name            color  linetype      lineweight (100ths of mm)
    "OUTLINE":        (7,    "Continuous",  50),   # main object lines — white/black
    "HIDDEN":         (3,    "HIDDEN",      25),   # hidden / dashed lines — green
    "CENTER":         (1,    "CENTER",      18),   # centerlines — red
    "DIMENSION":      (2,    "Continuous",  18),   # dimensions — yellow
    "TEXT":           (7,    "Continuous",  18),   # notes and labels — white/black
    "HATCH":          (253,  "Continuous",   9),   # section hatching — grey
    "DETAIL":         (4,    "Continuous",  35),   # secondary object geometry — cyan
    "CONSTRUCTION":   (8,    "Continuous",   9),   # construction / reference lines — grey
    "TITLE":          (7,    "Continuous",  25),   # title block text — white/black
    "BORDER":         (7,    "Continuous",  70),   # sheet border — white/black
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
    CROSS         = "CROSS"
    DOTS          = "DOTS"

    # Recommended scale values (units = drawing units at 1:1)
    SCALE = {
        "ANSI31":   0.10,   # steel section — fine
        "ANSI32":   0.10,
        "AR-CONC":  0.02,   # concrete aggregate
        "AR-BRSTD": 0.04,
        "EARTH":    0.06,
        "GRAVEL":   0.04,
        "INSUL":    0.08,
    }


# ---------------------------------------------------------------------------
# Document factory
# ---------------------------------------------------------------------------

UNIT_CODES = {"in": 1, "ft": 2, "mm": 4, "cm": 5, "m": 6}


def new_doc(units: str = "in", title: Optional[str] = None) -> tuple:
    """
    Create a new DXF R2010 document with:
      - RomanS (romans.shx) text style
      - Standard layers and linetypes
      - CADD dimension style calibrated to TEXT_HEIGHT = 1.2 at 1:1 scale

    Args:
        units: "in" (inches, default) or "mm"
        title: optional detail title stored in header

    Returns:
        (doc, msp) — the document and its modelspace.
    """
    doc = ezdxf.new("R2010")
    doc.units = UNIT_CODES.get(units, 1)
    doc.header["$INSUNITS"] = UNIT_CODES.get(units, 1)
    doc.header["$ACADVER"]  = "AC1024"  # R2010

    # --- Text style: RomanS ---
    _setup_text_style(doc)

    # --- Linetypes ---
    # Scale dash/gap patterns to drawing units
    s = 1.0 if units == "mm" else (1 / 25.4)
    doc.linetypes.add("HIDDEN",  pattern=[6 * s, -3 * s])
    doc.linetypes.add("CENTER",  pattern=[20 * s, -5 * s, 5 * s, -5 * s])
    doc.linetypes.add("PHANTOM", pattern=[25 * s, -5 * s, 5 * s, -5 * s, 5 * s, -5 * s])
    doc.linetypes.add("DASHDOT", pattern=[15 * s, -5 * s, 0, -5 * s])

    # --- Layers ---
    for name, (color, linetype, lw) in LAYERS.items():
        lt = linetype
        if lt != "Continuous" and lt not in [l.dxf.name for l in doc.linetypes]:
            lt = "Continuous"
        doc.layers.add(name, dxfattribs={"color": color, "linetype": lt, "lineweight": lw})

    # --- Dimension style ---
    _setup_dimstyle(doc)

    return doc, doc.modelspace()


def _setup_text_style(doc) -> None:
    """
    Configure the Standard text style to use RomanS (romans.shx).
    Also registers a named 'ROMANS' style for explicit assignment.
    """
    # Update the built-in Standard style
    try:
        standard = doc.styles.get("Standard")
        standard.dxf.font    = ROMANS_FONT
        standard.dxf.bigfont = ""
        standard.dxf.height  = 0   # 0 = height set per entity
    except Exception:
        pass

    # Named style for explicit use in dimensions and text entities
    try:
        doc.styles.add("ROMANS", font=ROMANS_FONT)
    except ezdxf.DXFTableEntryError:
        pass  # already exists


def _setup_dimstyle(doc) -> None:
    """
    Configure the Standard dimension style for 1:1 drawing with
    TEXT_HEIGHT = 1.2, RomanS font, CADD-standard proportions.
    """
    ds = doc.dimstyles.get("Standard")
    ds.dxf.dimasz  = ARROW_SIZE    # arrowhead size
    ds.dxf.dimtxt  = TEXT_HEIGHT   # dimension text height
    ds.dxf.dimdle  = 0             # dimension line extension past ext lines
    ds.dxf.dimexe  = DIM_EXT       # extension line beyond dim line
    ds.dxf.dimexo  = DIM_OFFSET    # extension line offset from point
    ds.dxf.dimgap  = DIM_GAP       # gap between dim line and text
    ds.dxf.dimclrd = 2             # dimension line color: yellow (layer 2)
    ds.dxf.dimclre = 2             # extension line color: yellow
    ds.dxf.dimclrt = 2             # text color: yellow
    ds.dxf.dimtxsty = "ROMANS"     # RomanS text style for all dim text


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
    Add a linear dimension at 1:1 scale.

    Args:
        p1, p2:  measurement points (real-world coordinates)
        offset:  perpendicular distance from measured geometry to dim line
                 (positive = above/right, negative = below/left)
        angle:   0 = horizontal dimension, 90 = vertical dimension
    """
    if angle == 0:
        base = ((p1[0] + p2[0]) / 2, p1[1] + offset)
    elif angle == 90:
        base = (p1[0] + offset, (p1[1] + p2[1]) / 2)
    else:
        dx = math.cos(math.radians(angle + 90))
        dy = math.sin(math.radians(angle + 90))
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        base = (mx + offset * dx, my + offset * dy)

    dim = msp.add_linear_dim(
        base=base,
        p1=p1,
        p2=p2,
        angle=angle,
        dimstyle="Standard",
        override=override,
        dxfattribs={"layer": layer},
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
    boundary: list,
    pattern: str = HATCH.STEEL,
    scale: Optional[float] = None,
    angle: float = 0,
    layer: str = "HATCH",
) -> None:
    """
    Hatch a closed polygonal region.

    Args:
        boundary: list of (x, y) vertices
        pattern:  hatch pattern name (use HATCH.* constants)
        scale:    pattern scale; if None, uses HATCH.SCALE table default
        angle:    rotation of hatch pattern in degrees
    """
    if scale is None:
        scale = HATCH.SCALE.get(pattern, 0.10)
    h = msp.add_hatch(dxfattribs={"layer": layer})
    h.paths.add_polyline_path(boundary, is_closed=True)
    h.set_pattern_fill(pattern, scale=scale, angle=angle)


def add_label(
    msp,
    text: str,
    position: tuple,
    height: float = TEXT_HEIGHT,
    align: str = "MIDDLE_CENTER",
    layer: str = "TEXT",
    rotation: float = 0,
) -> None:
    """
    Add a text label using RomanS font at TEXT_HEIGHT (1.2).

    Args:
        text:     string to display
        position: (x, y) insertion point
        height:   text height in drawing units (default: 1.2)
        align:    ezdxf TextEntityAlignment name (default: MIDDLE_CENTER)
        layer:    target layer (default: TEXT)
        rotation: text rotation in degrees
    """
    alignment = getattr(
        dxf_enums.TextEntityAlignment,
        align,
        dxf_enums.TextEntityAlignment.MIDDLE_CENTER,
    )
    msp.add_text(
        text,
        dxfattribs={
            "height":   height,
            "layer":    layer,
            "rotation": rotation,
            "style":    "ROMANS",
        },
    ).set_placement(position, align=alignment)


def add_leader(
    msp,
    vertices: list,
    annotation: str,
    text_height: float = TEXT_HEIGHT,
    layer: str = "DIMENSION",
) -> None:
    """
    Add a leader line with annotation text at the last vertex.

    Args:
        vertices:    list of (x, y) points; arrowhead at first point
        annotation:  callout string
        text_height: annotation text height (default: 1.2)
    """
    for i in range(len(vertices) - 1):
        msp.add_line(vertices[i], vertices[i + 1], dxfattribs={"layer": layer})
    end = vertices[-1]
    offset = text_height * 0.5
    msp.add_text(
        annotation,
        dxfattribs={
            "height": text_height,
            "layer":  "TEXT",
            "style":  "ROMANS",
        },
    ).set_placement(
        (end[0] + offset, end[1]),
        align=dxf_enums.TextEntityAlignment.MIDDLE_LEFT,
    )


def add_border_and_title(
    msp,
    width: float,
    height: float,
    title: str,
    scale: str = "1:1",
    drawn_by: str = "",
    units: str = "in",
) -> None:
    """
    Add a sheet border and simple title block using RomanS text.

    Args:
        width, height: sheet extents in drawing units (1:1, real size)
        title:         detail title (shown in upper-case)
        scale:         plot scale string, default "1:1"
        drawn_by:      drafter initials or name (optional)
        units:         "in" or "mm" — controls margin sizes
    """
    m     = 0.5  if units == "in" else 13.0   # margin
    box_h = 0.75 if units == "in" else 19.0   # title box height

    # Outer border
    msp.add_lwpolyline(
        [(m, m), (width - m, m), (width - m, height - m), (m, height - m)],
        close=True,
        dxfattribs={"layer": "BORDER"},
    )

    # Title box at bottom
    msp.add_lwpolyline(
        [(m, m), (width - m, m), (width - m, m + box_h), (m, m + box_h)],
        close=True,
        dxfattribs={"layer": "BORDER"},
    )

    # Vertical divider at 60% of width
    mid_x = m + (width - 2 * m) * 0.60
    msp.add_line((mid_x, m), (mid_x, m + box_h), dxfattribs={"layer": "BORDER"})

    cy = m + box_h / 2   # vertical centre of title box

    # Detail title — left cell, TITLE_HEIGHT
    add_label(
        msp, title.upper(),
        (m + (mid_x - m) / 2, cy + TEXT_HEIGHT * 0.4),
        height=TITLE_HEIGHT,
        layer="TITLE",
    )

    # Scale — right cell, TEXT_HEIGHT
    add_label(
        msp, f"SCALE: {scale}",
        (mid_x + (width - m - mid_x) / 2, cy + TEXT_HEIGHT * 0.5),
        height=TEXT_HEIGHT,
        layer="TITLE",
    )

    # Drafter — right cell, SMALL_HEIGHT
    if drawn_by:
        add_label(
            msp, f"BY: {drawn_by}",
            (mid_x + (width - m - mid_x) / 2, cy - TEXT_HEIGHT * 0.5),
            height=SMALL_HEIGHT,
            layer="TITLE",
        )


# ---------------------------------------------------------------------------
# Save helper
# ---------------------------------------------------------------------------

def save_doc(doc, filename: str, output_dir: Optional[str] = None) -> str:
    """
    Save the DXF document to ~/Documents/CAD/ (or a custom directory).

    Args:
        filename:   base name without extension (e.g. "beam_connection")
        output_dir: override output directory (optional)

    Returns:
        Absolute path of the saved file.
    """
    out = Path(output_dir) if output_dir else OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    safe  = "".join(c if c.isalnum() or c in "-_" else "_" for c in filename)
    path  = out / f"{safe}.dxf"
    doc.saveas(str(path))
    return str(path)
