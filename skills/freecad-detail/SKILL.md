---
name: freecad-detail
description: |
  Generates engineering and architectural CAD details from natural language
  descriptions using the FreeCAD Draft Python API. Writes a Python script,
  runs it headless with FreeCADCmd, and saves the result as a DXF file to
  ~/Documents/CAD/. Use when asked to draw, detail, or produce a CAD file
  for any engineering, architectural, or construction detail.
license: MIT
compatibility: "macOS — FreeCAD Community required (brew install --cask freecad)"
metadata:
  author: "Thomas Ott"
  version: "1.0"
---

# FreeCAD Detail Skill

## Overview

Interprets a plain-language description, maps every component to FreeCAD
Draft Python API calls, writes a complete Python script, executes it headless
with `FreeCADCmd`, and opens the resulting DXF in FreeCAD.

Helper: `scripts/freecad_base.py` — import at the top of every generated script.

**Standards enforced by `freecad_base.py`:**
- Geometry at **1:1 scale** — real-world dimensions, no scale factor
- Leroy text heights: **3 mm** labels/dims · **6 mm** title · **2 mm** secondary
  (equivalent to 0.12 / 0.24 / 0.08 inches)
- Nine standard layers with ACI-equivalent colors, linewidths, and draw styles
- FreeCAD works in **mm** internally; pass `units="in"` to auto-convert from inches

Output: `~/Documents/CAD/<name>.dxf`

## Setup

```bash
brew install --cask freecad    # installs to /Applications/FreeCAD.app
```

Verify headless execution:
```bash
/Applications/FreeCAD.app/Contents/MacOS/FreeCADCmd --version
```

## Invocation

```
/freecad-detail <description>
```

Examples:
```
/freecad-detail W8x31 beam to W12x53 column, single-plate shear tab, 4 A325 3/4" bolts at 3" spacing
/freecad-detail 400x400mm RC column, 8 No.16 bars, 40mm cover, No.10 ties at 150mm
/freecad-detail Residential window sill — 2x6 framing, rigid insulation, brick veneer, aluminum flashing
/freecad-detail 150mm pipe through 200mm concrete sleeve, waterstop ring, non-shrink grout
```

---

## Instructions for the model

### Step 1 — Parse the description

Identify:
1. **Detail type** — connection, section, plan, elevation, pipe/mechanical
2. **Materials** — steel, concrete, wood, masonry, aluminum …
3. **Components** — every named physical element
4. **Dimensions** — all given values; estimate standard sizes for anything unstated
5. **Units** — mm or inches; default **mm** if unspecified
6. **Sheet size** — smallest standard that comfortably fits the geometry:

| Sheet | mm | inches (converted) |
|---|---|---|
| A4 | 297 × 210 | 11.7 × 8.3 |
| A3 | 420 × 297 | 16.5 × 11.7 |
| A2 | 594 × 420 | 23.4 × 16.5 |
| A1 | 841 × 594 | 33.1 × 23.4 |

Before writing code, state briefly:
> "Drawing: [component list], units: mm, sheet: 420×297, origin: centre of plate"

---

### Step 2 — Map geometry to API calls

| Component | Call |
|---|---|
| Plate / wall / section outline | `add_polygon([[x,y],…])` |
| Single line, weld | `add_line(x1,y1, x2,y2)` |
| Bolt hole, pipe cross-section | `circ = add_circle(cx,cy, r)` |
| Curved edge | `add_arc(cx,cy, r, startDeg, endDeg)` |
| Material fill | `add_hatch(boundary, HATCH.*)` |
| Hidden geometry | `add_line()` after `set_layer("HIDDEN")` |
| Centerlines | `add_centerlines(cx,cy, size)` |
| Horizontal/vertical dim | `add_linear_dim(x1,y1, x2,y2, offset, angle)` |
| Radius dim | `add_radius_dim(circle_obj, angle)` |
| Diameter dim | `add_diameter_dim(circle_obj, angle)` |
| Text label | `add_label(text, x, y)` |
| Leader + callout | `add_leader([[x,y],…], text)` |

**Layer rule:** call `set_layer("LAYERNAME")` before any raw `add_line` /
`add_circle` / `add_arc` / `add_polygon`. Hatch, dimension, label, leader,
and centerline helpers set their own layers automatically.

**Important:** `add_circle()` returns the circle object. Store it if you need
to call `add_radius_dim()` or `add_diameter_dim()` on it.

**Layers:**
| Layer | Purpose | Color |
|---|---|---|
| `OUTLINE` | Main object lines | white |
| `HIDDEN` | Dashed / behind-cut lines | green |
| `CENTER` | Centerlines | red |
| `DIMENSION` | Dim lines (auto) | yellow |
| `TEXT` | Labels, leaders (auto) | white |
| `HATCH` | Material fills (auto) | grey |
| `DETAIL` | Secondary geometry | cyan |

**Hatch patterns (FCPAT.pat — bundled with FreeCAD):**
| Material | Constant | Pattern | Default scale |
|---|---|---|---|
| Steel / metal | `HATCH.STEEL` | Diagonal4 — 45° lines | 4 mm |
| Aluminum | `HATCH.ALUMINUM` | Diagonal5 — reverse 45° | 4 mm |
| Concrete | `HATCH.CONCRETE` | Diamond — fine crosshatch | 2 mm |
| Brick / CMU | `HATCH.BRICK` | Horizontal5 — rows | 8 mm |
| Earth / fill | `HATCH.EARTH` | Diamond2 — medium crosshatch | 6 mm |
| Gravel | `HATCH.GRAVEL` | Square — grid | 4 mm |
| Insulation | `HATCH.INSULATION` | Horizontal5 — spaced rows | 4 mm |

Override scale with `add_hatch(pts, HATCH.CONCRETE, scale=1.5)`.

**Dimension offset guide (1:1):**
- mm: first dim 12–15 from geometry, stack 10 apart
- in: converted to mm internally; use 5–8 in drawing units (= 127–203 mm internally)
- `offset` sign: negative = below/left · positive = above/right
- `angle`: 0 = horizontal · 90 = vertical

---

### Step 3 — Write the script

Save to `/tmp/<detail_name>.py`.

```python
# Run:
# /Applications/FreeCAD.app/Contents/MacOS/FreeCADCmd /tmp/<detail_name>.py

import sys
sys.path.insert(0, '/Users/ottt/.pi/agent/skills/freecad-detail/scripts')
from freecad_base import *

new_doc("mm")                        # "mm" or "in"
W, H = 420, 297                      # sheet size in drawing units

# ── GEOMETRY ─────────────────────────────────────────────────────────────────
set_layer("OUTLINE")
# ... add_line / add_circle / add_arc / add_polygon calls ...
# add_hatch() immediately after each material outline

# ── DIMENSIONS ───────────────────────────────────────────────────────────────
# add_linear_dim / add_radius_dim / add_diameter_dim
# typical offset: 12–15 mm from nearest edge

# ── LABELS ───────────────────────────────────────────────────────────────────
# add_label / add_leader

# ── TITLE BLOCK ──────────────────────────────────────────────────────────────
add_border_and_title(W, H, "DETAIL TITLE", "1:1", "mm")

path = save_doc("detail_filename")
print("Done:", path)
```

**Text height constants (mm):**
| Constant | Value | Use |
|---|---|---|
| `TEXT_HEIGHT` | 3.0 | Labels, notes, dim text |
| `TITLE_HEIGHT` | 6.0 | Title block heading |
| `SMALL_HEIGHT` | 2.0 | Drafter / secondary notes |

---

### Step 4 — Execute and view

```bash
/Applications/FreeCAD.app/Contents/MacOS/FreeCADCmd /tmp/<detail_name>.py

open ~/Documents/CAD/<detail_name>.dxf
```

Report: saved path · what was drawn · any estimated dimensions.

---

### Step 5 — Iterate

On user feedback: edit the script, re-run, re-open. Offer a revision tag in
the title block for significant changes.

---

## Reference patterns

All examples use mm at 1:1 scale. For inches, pass `new_doc("in")` and use
inch values — `freecad_base` converts to mm internally.

### Steel shear-tab connection (mm)
```python
# Column flange — 15mm thick × 300mm tall
set_layer("OUTLINE")
add_polygon([[-15,0],[-15,300],[15,300],[15,0]])
add_hatch([[-15,0],[-15,300],[15,300],[15,0]], HATCH.STEEL)

# 10mm shear plate — 150mm tall, welded to flange
add_polygon([[15,75],[15,225],[50,225],[50,75]])
add_hatch([[15,75],[15,225],[50,225],[50,75]], HATCH.STEEL)

# M20 bolts (20mm dia) — 3 at 75mm spacing
for y in [112.5, 150, 187.5]:
    circ = add_circle(32.5, y, 10)
    add_centerlines(32.5, y, 15)

add_linear_dim(-15,0, 15,0,  -15, 0)          # flange thickness
add_linear_dim(50,75, 50,225, 15, 90)          # plate height
add_label("W-SHAPE FLANGE",  -40,  150, TEXT_HEIGHT)
add_label("10mm SHEAR PLATE", 65,  150, TEXT_HEIGHT)
```

### RC column section (mm)
```python
set_layer("OUTLINE")
add_polygon([[0,0],[400,0],[400,400],[0,400]])
add_hatch([[0,0],[400,0],[400,400],[0,400]], HATCH.CONCRETE)

cover = 40 + 8  # 40mm clear + half bar dia
bar_r = 8
bar_pts = [
    [cover,cover],[200,cover],[400-cover,cover],
    [cover,200],[400-cover,200],
    [cover,400-cover],[200,400-cover],[400-cover,400-cover],
]
for bx, by in bar_pts:
    circ = add_circle(bx, by, bar_r)
    add_centerlines(bx, by, bar_r + 4)

add_linear_dim(0,0, 400,0,   -20, 0)
add_linear_dim(0,0, 0,400,   -20, 90)
add_linear_dim(0,0, cover,0, -40, 0)
add_label("400x400 RC COLUMN", 200, 200)
add_label("8-16mm BARS",        200, -30)
```

### Pipe sleeve through concrete wall (mm)
```python
set_layer("OUTLINE")
add_polygon([[0,0],[300,0],[300,250],[0,250]])
add_hatch([[0,0],[300,0],[300,250],[0,250]], HATCH.CONCRETE)

pipe_r   = 75      # 150mm OD pipe
sleeve_r = 100     # 200mm OD sleeve
cx, cy   = 150, 125
pipe_circ   = add_circle(cx, cy, pipe_r)
sleeve_circ = add_circle(cx, cy, sleeve_r)
add_centerlines(cx, cy, sleeve_r + 20)

add_diameter_dim(pipe_circ,   45)
add_diameter_dim(sleeve_circ, 135)
add_linear_dim(0,0, 300,0, -20, 0)
add_leader([[cx+pipe_r+8, cy+pipe_r+8],[cx+pipe_r+40,cy+pipe_r+40]],   "150mm STD. PIPE")
add_leader([[cx-sleeve_r-8,cy+sleeve_r+8],[cx-sleeve_r-40,cy+sleeve_r+40]], "200mm SLEEVE W/ GROUT")
```

---

## Error handling

| Error | Fix |
|---|---|
| FreeCAD not found | `brew install --cask freecad` |
| `No module named 'FreeCAD'` | Script must run via `FreeCADCmd`, not plain `python3` |
| `No module named 'freecad_base'` | Check `sys.path.insert` line points to the correct skill path |
| Hatch not visible | Confirm `wire.MakeFace = True` and `_doc.recompute()` are called inside `add_hatch` |
| Dim shows wrong value | Check that `p3` / `p4` vector is in the right position relative to geometry |
| Dim not given | Use nearest standard value; note it as estimated in the report |
| `ViewObject` errors | Verify `Gui.setupWithoutGUI()` is called before Draft imports |
| Detail too complex | Split into primary + sub-detail scripts |
