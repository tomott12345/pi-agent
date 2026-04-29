---
name: cad-detail
description: |
  Generates AutoCAD-compatible DXF files from natural language descriptions of
  engineering or architectural details. Interprets geometry, dimensions, materials,
  and annotations from the description, then produces a DXF using ezdxf with
  standard layers, linetypes, hatch patterns, and a title block. Output files are
  saved to ~/Documents/CAD/. Use when asked to draw, detail, or produce a CAD
  file for any engineering, architectural, or construction detail.
license: MIT
compatibility: "Linux/macOS (requires Python 3 and ezdxf: pip install ezdxf)"
metadata:
  author: "Thomas Ott"
  version: "1.1"
---

# CAD Detail Skill

## Overview

Parses a plain-language description of a detail, deduces the geometry, and writes
a Python script using `ezdxf` and the helper module `scripts/dxf_base.py` to
produce a DXF file importable into AutoCAD LT or any DXF-compatible CAD application.

**Drawing standards enforced automatically by `dxf_base.py`:**
- All geometry drawn at **1:1 scale** (real-world dimensions in inches or mm)
- **RomanS font** (`romans.shx`) on all text, labels, and dimension annotations
- **Text height: 1.2** drawing units on all text entities and dimensions
- Standard CADD layers with correct colors, linetypes, and lineweights

Output files are saved to `~/Documents/CAD/<detail_name>.dxf`.

## Setup

```bash
pip install ezdxf
```

## Invocation

```
/cad-detail <description of the detail>
```

Examples:
```
/cad-detail A W8x31 steel beam bolted to a W12x53 column flange with a single-plate shear connection, 4 A325 3/4" bolts, 3" spacing
/cad-detail Reinforced concrete column section 400x400mm with 8 No.16 rebars, 40mm cover, No.10 ties at 150mm spacing
/cad-detail Typical residential window sill detail with 2x6 framing, rigid insulation, brick veneer, and aluminum sill flashing
/cad-detail Pipe sleeve through concrete wall, 150mm diameter pipe, 200mm sleeve, waterstop ring, non-shrink grout
```

## Instructions for the model

### Step 1 — Understand the description

Read the description and identify:

1. **Detail type** — structural connection, section cut, plan detail, elevation detail, pipe/mechanical
2. **Primary material(s)** — steel, concrete, wood, masonry, aluminum, etc.
3. **Components** — list every physical element mentioned
4. **Key dimensions** — extract all given dimensions; estimate reasonable values for any that are standard but not stated
5. **Unit system** — metric (mm) or imperial (inches); default to **inches** if unspecified. Pass `units='in'` or `units='mm'` to `new_doc()`.
6. **Scale** — always **1:1**. Draw every entity at its true real-world dimension. Do not apply any scale factor to geometry. The title block will read `SCALE: 1:1`.
7. **Sheet size** — choose a standard sheet size in the same drawing units:
   - Imperial (inches): 11 × 8.5 (letter), 17 × 11 (tabloid), 22 × 17 (C-size)
   - Metric (mm): 297 × 210 (A4), 420 × 297 (A3), 594 × 420 (A2)
   - Pick the smallest sheet that gives comfortable white space around the geometry
8. **Datum / origin** — place the primary element at or near (0, 0) for clarity; leave room above for the geometry and at the bottom for the title block

Before writing any code, briefly state what you understood:
> "Drawing: [component list], units: in, scale: 1:1, sheet: 11×8.5, origin: centre of plate"

### Step 2 — Plan the geometry

Map each component to DXF entity types:

| Component | Entity |
|---|---|
| Plate, section outline, wall | `add_lwpolyline` (closed) |
| Single line, weld, gap | `add_line` |
| Bolt hole, pipe cross-section | `add_circle` |
| Fillet, curved edge | `add_arc` |
| Material indication | `add_hatch_region` |
| Rebar, bolt shank | `add_line` on OUTLINE or HIDDEN |
| Dimension | `add_linear_dim`, `add_radius_dim`, `add_diameter_dim` |
| Note, label | `add_label` |
| Leader with callout | `add_leader` |
| Centerline through hole | `add_centerlines` |

**Layer assignments:**
- Main visible geometry → `OUTLINE`
- Hidden / behind-cut geometry → `HIDDEN`
- Centerlines → `CENTER`
- All dimensions → `DIMENSION`
- Notes and callouts → `TEXT`
- Section hatching → `HATCH`
- Secondary/background geometry → `DETAIL`

**Hatch patterns:**
| Material | Pattern | Auto scale | Notes |
|---|---|---|---|
| Steel plate / metal section | `HATCH.STEEL` | 0.10 | 45° lines |
| Concrete (cast-in-place) | `HATCH.CONCRETE` | 0.02 | AR-CONC aggregate |
| Brick / CMU | `HATCH.BRICK` | 0.04 | AR-BRSTD |
| Earth / compacted fill | `HATCH.EARTH` | 0.06 | |
| Gravel / crushed stone | `HATCH.GRAVEL` | 0.04 | |
| Batt insulation | `HATCH.INSULATION` | 0.08 | |
| Wood (end grain) | `HATCH.STEEL` | 0.06 | use `angle=45` |
| Wood (long grain) | two parallel lines spaced to suit | — | draw manually |
| Aluminum | `HATCH.ALUMINUM` | 0.10 | ANSI38 |

Scale defaults are set in `HATCH.SCALE` and applied automatically when `scale=None`.
Override with `add_hatch_region(msp, boundary, HATCH.CONCRETE, scale=0.03)` if needed.

**Dimension placement (1:1, inches):**
- Place dimension lines 0.4–0.6 in. outside the nearest outline
- Stack multiple dimensions 0.4 in. apart
- Use `add_linear_dim(msp, p1, p2, offset)` where `offset` is signed distance:
  - Negative → below or left of geometry
  - Positive → above or right
- For mm drawings, use 10–15 mm offsets instead

### Step 3 — Write the Python script

Write the complete script to a temporary file `/tmp/<detail_name>.py` and execute it.

**Script template:**

```python
import sys
sys.path.insert(0, '/Users/ottt/.pi/agent/skills/cad-detail/scripts')
from dxf_base import *

# ── DOCUMENT SETUP ──────────────────────────────────────────────────────────
# units='in' (default) or 'mm'
# All standards applied automatically: RomanS font, 1.2 text height, 1:1 scale
doc, msp = new_doc(units='in')

# Sheet size in drawing units (real-world, 1:1)
sheet_w, sheet_h = 11, 8.5   # e.g. ANSI A letter in inches

# ── GEOMETRY ────────────────────────────────────────────────────────────────
# Draw all components at TRUE real-world dimensions (1:1).
# No scale factors — if a plate is 6 inches wide, coordinates span 6 units.
# Draw from bottom to top, back to front.
# Add hatching immediately after the outline for each material region.

# ... geometry code ...

# ── DIMENSIONS ──────────────────────────────────────────────────────────────
# Add all key dimensions. Minimum: overall width, overall height,
# and any critical sub-dimensions (spacing, thickness, cover, etc.)
# Offset = distance from geometry to dimension line in drawing units.
# Typical offset for inches: 0.4 to 0.6; for mm: 10 to 15.

# ... dimension code ...

# ── ANNOTATIONS ─────────────────────────────────────────────────────────────
# add_label() and add_leader() use RomanS font and TEXT_HEIGHT (1.2) by default.
# Pass height=TITLE_HEIGHT (1.8) for prominent callouts if needed.

# ... label code ...

# ── TITLE BLOCK ─────────────────────────────────────────────────────────────
# scale is always '1:1' — do not change this
add_border_and_title(msp, sheet_w, sheet_h, 'DETAIL TITLE', scale='1:1', units='in')

# ── SAVE ────────────────────────────────────────────────────────────────────
path = save_doc(doc, 'detail_filename')
print(f'Saved: {path}')
```

**Standard sheet sizes:**

| Sheet | Imperial (in) | Metric (mm) |
|---|---|---|
| Small | 11 × 8.5 (letter) | 297 × 210 (A4) |
| Medium | 17 × 11 (tabloid) | 420 × 297 (A3) |
| Large | 22 × 17 (C-size) | 594 × 420 (A2) |
| Extra large | 34 × 22 (D-size) | 841 × 594 (A1) |

Position geometry so it occupies 65–75% of the usable area (inside border,
above title block), centred left-to-right.

**Text height reference (dxf_base constants — Leroy standard, inches):**

| Constant | Value | Leroy size | Use |
|---|---|---|---|
| `TEXT_HEIGHT` | 0.12 | No. 120 | All labels, notes, dimension text (default) |
| `TITLE_HEIGHT` | 0.24 | No. 240 | Detail title in title block |
| `SMALL_HEIGHT` | 0.08 | No. 80 | Secondary notes, drawn-by field |

### Step 4 — Execute and report

Run the script:
```bash
python3 /tmp/<detail_name>.py
```

Report:
- The saved file path
- A brief summary of what was drawn
- Any dimensions that were estimated (not given in the description)
- Suggestion for how the user can open the file (AutoCAD, FreeCAD, etc.)

### Step 5 — Iterate on feedback

If the user requests changes (different dimensions, added components, different scale),
modify the script and regenerate the DXF. Offer to:
- Add a revision indicator to the title block
- Export at a different scale
- Split into multiple details if the description is complex

## Common detail patterns

All examples use inches at 1:1 scale. For mm, multiply inch values by 25.4
and pass `units='mm'` to `new_doc()`.

### Steel connection (shear tab / clip angle) — imperial
```python
# Column flange  (W-shape flange represented as a rectangle, 0.6" thick × 12" tall)
msp.add_lwpolyline([(-0.6,0),(-0.6,12),(0.6,12),(0.6,0)], close=True, dxfattribs={'layer':'OUTLINE'})
add_hatch_region(msp, [(-0.6,0),(-0.6,12),(0.6,12),(0.6,0)], HATCH.STEEL)

# Shear plate  (3/8" × 6" plate welded to flange)
msp.add_lwpolyline([(0.6,3),(0.6,9),(1.975,9),(1.975,3)], close=True, dxfattribs={'layer':'OUTLINE'})
add_hatch_region(msp, [(0.6,3),(0.6,9),(1.975,9),(1.975,3)], HATCH.STEEL)

# 3/4" A325 bolts (3 bolts at 3" spacing)
for y in [4.5, 6.0, 7.5]:
    msp.add_circle((1.2875, y), 0.375, dxfattribs={'layer':'OUTLINE'})  # bolt hole
    add_centerlines(msp, (1.2875, y), 0.5)

# Dimensions
add_linear_dim(msp, (-0.6, 0), (0.6, 0), offset=-0.5)        # flange width
add_linear_dim(msp, (1.975, 3), (1.975, 9), offset=0.5, angle=90)  # plate height
add_label(msp, "W-SHAPE FLANGE", (-2, 6), align="MIDDLE_RIGHT")
add_label(msp, "3/8 SHEAR PLATE", (2.5, 6), align="MIDDLE_LEFT")
```

### Reinforced concrete column section — imperial
```python
# 16"×16" column section
msp.add_lwpolyline([(0,0),(16,0),(16,16),(0,16)], close=True, dxfattribs={'layer':'OUTLINE'})
add_hatch_region(msp, [(0,0),(16,0),(16,16),(0,16)], HATCH.CONCRETE)

# 8 No.5 bars (5/8" dia) at 1.5" clear cover
cover   = 1.5 + 0.625/2   # to bar centre
bar_dia = 0.625
for pos in [(cover,cover),(8,cover),(16-cover,cover),
            (cover,8),(16-cover,8),
            (cover,16-cover),(8,16-cover),(16-cover,16-cover)]:
    msp.add_circle(pos, bar_dia/2, dxfattribs={'layer':'OUTLINE'})
    add_centerlines(msp, pos, bar_dia)

# Dimensions
add_linear_dim(msp, (0,0),  (16,0),  offset=-0.5)              # width
add_linear_dim(msp, (0,0),  (0,16),  offset=-0.5, angle=90)    # height
add_linear_dim(msp, (0,0),  (cover,0), offset=-1.0)            # cover
add_label(msp, "16x16 R.C. COLUMN", (8, 8))
add_label(msp, "8-#5 BARS", (8, -1.5))
```

### Pipe sleeve through concrete wall — imperial
```python
# 12" thick concrete wall
msp.add_lwpolyline([(0,0),(12,0),(12,10),(0,10)], close=True, dxfattribs={'layer':'OUTLINE'})
add_hatch_region(msp, [(0,0),(12,0),(12,10),(0,10)], HATCH.CONCRETE)

# 6" pipe (OD=6.625") inside 8" sleeve (OD=8.625")
pipe_r   = 6.625 / 2
sleeve_r = 8.625 / 2
cx, cy   = 6, 5
msp.add_circle((cx, cy), sleeve_r, dxfattribs={'layer':'OUTLINE'})
msp.add_circle((cx, cy), pipe_r,   dxfattribs={'layer':'OUTLINE'})
add_centerlines(msp, (cx, cy), sleeve_r + 0.75)

# Dimensions
add_diameter_dim(msp, (cx, cy), pipe_r,   angle=45)
add_diameter_dim(msp, (cx, cy), sleeve_r, angle=135)
add_linear_dim(msp,  (0,0), (12,0), offset=-0.5)              # wall thickness
add_label(msp, "6\" STD. PIPE", (cx+pipe_r+0.3, cy+pipe_r+0.3), align="BOTTOM_LEFT")
add_label(msp, "8\" SLEEVE W/ GROUT", (cx-sleeve_r-0.3, cy+sleeve_r+0.3), align="BOTTOM_RIGHT")
```

## Error handling

| Issue | Action |
|---|---|
| `ezdxf` not installed | Run `pip install ezdxf` and retry |
| Dimension not given | Use the nearest standard size; note it as estimated |
| Ambiguous geometry | Ask a clarifying question before drawing |
| Very complex detail | Split into a primary detail + one or more sub-details |
| Script execution error | Show the traceback, fix the code, and re-run |
