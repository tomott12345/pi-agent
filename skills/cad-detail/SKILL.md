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
  version: "1.0"
---

# CAD Detail Skill

## Overview

Parses a plain-language description of a detail, deduces the geometry, and writes
a Python script using `ezdxf` and the helper module `scripts/dxf_base.py` to
produce a DXF file importable into AutoCAD, BricsCAD, LibreCAD, or any DXF-compatible
CAD application.

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
5. **Unit system** — metric (mm) or imperial (inches); default to mm if unspecified
6. **Scale** — choose an appropriate drawing scale based on the overall size:
   - Small details (<200mm): 1:5 or 1:2
   - Medium (200–500mm): 1:10
   - Large (>500mm): 1:20 or 1:50
7. **Datum / origin** — place the primary element at or near (0, 0) for clarity

Before writing any code, briefly state what you understood:
> "Drawing: [component list], units: mm, scale: 1:10, origin: centre of column base"

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
| Material | Pattern | Scale (mm) |
|---|---|---|
| Steel plate / metal section | `HATCH.STEEL` ("ANSI31") | 2.5 |
| Concrete (cast-in-place) | `HATCH.CONCRETE` ("AR-CONC") | 0.5 |
| Brick / CMU | `HATCH.BRICK` ("AR-BRSTD") | 1.0 |
| Earth / compacted fill | `HATCH.EARTH` | 1.5 |
| Gravel / crushed stone | `HATCH.GRAVEL` | 1.0 |
| Batt insulation | `HATCH.INSULATION` ("INSUL") | 2.0 |
| Wood (end grain) | `HATCH.STEEL` | 1.5 (45°, fine) |
| Wood (long grain) | two parallel lines spaced ~5mm | — |
| Aluminum | `HATCH.ALUMINUM` ("ANSI38") | 2.5 |

**Dimension placement:**
- Place dimension lines 15–20mm outside the nearest outline
- Stack multiple dimensions 15mm apart
- Use `add_linear_dim(msp, p1, p2, offset)` where `offset` is signed distance from p1/p2 to the dim line
  - Negative offset → below or left of geometry
  - Positive offset → above or right

### Step 3 — Write the Python script

Write the complete script to a temporary file `/tmp/<detail_name>.py` and execute it.

**Script template:**

```python
import sys
sys.path.insert(0, '/Users/ottt/.pi/agent/skills/cad-detail/scripts')
from dxf_base import *

# Document setup
doc, msp = new_doc(units='mm')  # or 'in' for imperial

# ── GEOMETRY ────────────────────────────────────────────────────────────────
# Draw components from bottom to top, back to front.
# Add hatching immediately after the outline for each material region.

# ... geometry code ...

# ── DIMENSIONS ──────────────────────────────────────────────────────────────
# Add all key dimensions. Minimum: overall width, overall height,
# and any critical sub-dimensions (spacing, thickness, cover, etc.)

# ... dimension code ...

# ── ANNOTATIONS ─────────────────────────────────────────────────────────────
# Add material callouts, part labels, and a detail title.

# ... label code ...

# ── TITLE BLOCK ─────────────────────────────────────────────────────────────
add_border_and_title(msp, sheet_w, sheet_h, 'DETAIL TITLE', scale='1:10')

# ── SAVE ────────────────────────────────────────────────────────────────────
path = save_doc(doc, 'detail_filename')
print(f'Saved: {path}')
```

**Sheet size guidelines (mm):**
- Small detail: 250 × 200
- Medium detail: 350 × 280
- Large detail: 500 × 400
- Extra large: 700 × 500

Position geometry so it occupies roughly 70% of the sheet,
centred between the border and title block.

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

### Steel connection (shear tab / clip angle)
```python
# Column flange
msp.add_lwpolyline([(-15, 0),(-15, 300),(15, 300),(15, 0)], close=True, dxfattribs={'layer':'OUTLINE'})
add_hatch_region(msp, [(-15,0),(-15,300),(15,300),(15,0)], HATCH.STEEL)

# Shear plate
msp.add_lwpolyline([(15, 100),(15, 200),(40, 200),(40, 100)], close=True, dxfattribs={'layer':'OUTLINE'})
add_hatch_region(msp, [(15,100),(15,200),(40,200),(40,100)], HATCH.STEEL)

# Bolts as circles
for y in [120, 150, 180]:
    msp.add_circle((27, y), 9, dxfattribs={'layer':'OUTLINE'})
    add_centerlines(msp, (27, y), 12)
```

### Concrete section (with rebar)
```python
# Section outline
msp.add_lwpolyline([(0,0),(400,0),(400,400),(0,400)], close=True, dxfattribs={'layer':'OUTLINE'})
add_hatch_region(msp, [(0,0),(400,0),(400,400),(0,400)], HATCH.CONCRETE)

# Rebar as solid filled circles
cover = 40
bar_dia = 16
for pos in [(cover, cover),(400-cover, cover),(cover, 400-cover),(400-cover, 400-cover)]:
    msp.add_circle(pos, bar_dia/2, dxfattribs={'layer':'OUTLINE'})
    add_centerlines(msp, pos, bar_dia)

# Dimension: cover
add_linear_dim(msp, (0, 0), (cover, 0), offset=-15)
```

### Pipe through wall
```python
# Wall section
msp.add_lwpolyline([(0,0),(300,0),(300,200),(0,200)], close=True, dxfattribs={'layer':'OUTLINE'})
add_hatch_region(msp, [(0,0),(300,0),(300,200),(0,200)], HATCH.CONCRETE)

# Pipe sleeve (hollow circle)
sleeve_r = 100  # half of 200mm sleeve
pipe_r   = 75   # half of 150mm pipe
cx, cy   = 150, 100
msp.add_circle((cx, cy), sleeve_r, dxfattribs={'layer':'OUTLINE'})
msp.add_circle((cx, cy), pipe_r,   dxfattribs={'layer':'OUTLINE'})
add_centerlines(msp, (cx, cy), sleeve_r + 20)

# Grout annulus hatch
# (requires a path with hole — use two separate hatch boundary paths)
h = msp.add_hatch(dxfattribs={'layer':'HATCH'})
h.paths.add_edge_path()  # outer boundary
# ... (draw annulus as needed)

add_diameter_dim(msp, (cx, cy), pipe_r,   angle=45)
add_diameter_dim(msp, (cx, cy), sleeve_r, angle=135)
```

## Error handling

| Issue | Action |
|---|---|
| `ezdxf` not installed | Run `pip install ezdxf` and retry |
| Dimension not given | Use the nearest standard size; note it as estimated |
| Ambiguous geometry | Ask a clarifying question before drawing |
| Very complex detail | Split into a primary detail + one or more sub-details |
| Script execution error | Show the traceback, fix the code, and re-run |
