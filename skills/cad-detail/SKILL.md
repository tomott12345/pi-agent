---
name: cad-detail
description: |
  Generates engineering and architectural CAD details from natural language
  descriptions using the QCAD simple API. Writes an ECMAScript script, runs it
  headless with QCAD, and saves the result as a DWG file to a configurable
  output directory. Use when asked to draw, detail, or produce a CAD file for any
  engineering, architectural, or construction detail.
license: MIT
compatibility: "macOS — QCAD Professional required (brew install --cask qcad)"
metadata:
  author: "Thomas Ott"
  version: "3.0"
---

# CAD Detail Skill

## Overview

Interprets a plain-language description, maps every component to QCAD simple API
calls, writes a complete ECMAScript script, executes it headless, and opens the
resulting DWG in QCAD.

Helper: `scripts/qcad_base.js` — include at the top of every generated script.

**Standards enforced by `qcad_base.js`:**
- Geometry at **1:1 scale** — real-world dimensions, no scale factor
- Leroy text heights: **0.12** labels/dims · **0.24** title · **0.08** secondary
- Nine standard layers, each with ACI color, linetype, and lineweight

Output: `~/Documents/CAD/<name>.dwg` (DWG write requires QCAD Professional)

## Setup

```bash
brew install --cask qcad    # installs to /Applications/QCAD.app
```

## Invocation

```
/cad-detail <description> [--output-dir <path>]
```

Examples:
```
/cad-detail W8x31 beam to W12x53 column, single-plate shear tab, 4 A325 3/4" bolts at 3" spacing
/cad-detail 400x400mm RC column, 8 No.16 bars, 40mm cover, No.10 ties at 150mm
/cad-detail Residential window sill — 2x6 framing, rigid insulation, brick veneer, aluminum flashing
/cad-detail 150mm pipe through 200mm concrete sleeve, waterstop ring, non-shrink grout
```

Optional parameter:
- `--output-dir <path>`: Specify custom output directory (default: ~/Documents/CAD/)

## Instructions for the model

### Step 1 — Parse the description

Identify:
1. **Detail type** — connection, section, plan, elevation, pipe/mechanical
2. **Materials** — steel, concrete, wood, masonry, aluminum …
3. **Components** — every named physical element
4. **Dimensions** — all given values; estimate standard sizes for anything unstated
5. **Units** — mm or inches; default **inches** if unspecified
6. **Sheet size** — smallest standard that comfortably fits the geometry:

| Sheet | Imperial (in) | Metric (mm) |
|---|---|---|
| Letter | 11 × 8.5 | — |
| A4 | — | 297 × 210 |
| Tabloid | 17 × 11 | — |
| A3 | — | 420 × 297 |
| C-size | 22 × 17 | — |
| A2 | — | 594 × 420 |

Before writing code, state briefly:
> "Drawing: [component list], units: in, sheet: 11×8.5, origin: centre of plate"

---

### Step 2 — Map geometry to API calls

| Component | Call |
|---|---|
| Plate / wall / section outline | `addPolygon([[x,y],…])` |
| Single line, weld | `addLine(x1,y1, x2,y2)` |
| Bolt hole, pipe cross-section | `addCircle(cx,cy, r)` |
| Curved edge | `addArc(cx,cy, r, startDeg, endDeg, false)` |
| Material fill | `addHatchRegion(boundary, HATCH.*)` |
| Hidden geometry | `addLine()` on layer `"HIDDEN"` |
| Centerlines | `addCenterlines(cx,cy, size)` |
| Horizontal/vertical dim | `addLinearDim(x1,y1, x2,y2, offset, angle)` |
| Radius dim | `addRadiusDim(circle_obj, angle)` |
| Diameter dim | `addDiameterDim(circle_obj, angle)` |
| Text label | `addLabel(text, x, y)` |
| Leader + callout | `addLeader([[x,y],…], text)` |

**Layer rule:** call `setCurrentLayer("LAYERNAME")` before any raw `addLine` /
`addCircle` / `addArc` / `addPolygon`. Hatch, dimension, label, and leader helpers set their own layers automatically.

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

**Hatch patterns:**
| Material | Constant | Default scale |
|---|---|---|
| Steel / metal | `HATCH.STEEL` | 0.10 |
| Concrete | `HATCH.CONCRETE` | 0.02 |
| Brick / CMU | `HATCH.BRICK` | 0.04 |
| Earth / fill | `HATCH.EARTH` | 0.06 |
| Gravel | `HATCH.GRAVEL` | 0.04 |
| Insulation | `HATCH.INSULATION` | 0.08 |
| Aluminum | `HATCH.ALUMINUM` | 0.10 |

Scale is applied automatically; override with `addHatchRegion(pts, HATCH.CONCRETE, 0.03)`.

**Dimension offset guide (1:1):**
- Inches: first dim 0.5 from geometry, stack 0.4 apart
- mm: first dim 12 from geometry, stack 10 apart
- `offset` sign: negative = below/left · positive = above/right
- `angle`: 0 = horizontal · 90 = vertical

---

### Step 3 — Write the script

Save to `/tmp/<detail_name>.js`.

```javascript
// Run:
 // /Applications/QCAD.app/Contents/MacOS/QCAD -no-gui -allow-multiple-instances \
  //     -autostart /tmp/<detail_name>.js

 include("/Users/ottt/.pi/agent/skills/cad-detail/scripts/qcad_base.js");

 newDoc("in");                            // "in" or "mm"
 var W = 11, H = 8.5;                    // sheet size in drawing units

 startTransaction(_doc);

 // ── GEOMETRY ─────────────────────────────────────────────────────────────────
 setCurrentLayer("OUTLINE");
 // ... addLine / addCircle / addArc / addPolygon calls ...
 // addHatchRegion() immediately after each material outline

 // ── DIMENSIONS ───────────────────────────────────────────────────────────────
 // addLinearDim / addRadiusDim / addDiameterDim calls
 // offset 0.5 (in) or 12 (mm) from nearest edge

 // ── LABELS ───────────────────────────────────────────────────────────────────
 // addLabel / addLeader calls

 // ── TITLE BLOCK ──────────────────────────────────────────────────────────────
 addBorderAndTitle(W, H, "DETAIL TITLE", "1:1", "in");

 endTransaction();

 var path = saveDoc("detail_filename");
 print("Done: " + path);
```

**Text height constants (inches):**
| Constant | Value | Use |
|---|---|---|
| `TEXT_HEIGHT` | 0.12 | Labels, notes, dim text |
| `TITLE_HEIGHT` | 0.24 | Title block heading |
| `SMALL_HEIGHT` | 0.08 | Drafter / secondary notes |

---

### Step 4 — Execute and view

```bash
/Applications/QCAD.app/Contents/MacOS/QCAD -no-gui -allow-multiple-instances \
    -autostart /tmp/<detail_name>.js

 open ~/Documents/CAD/<detail_name>.dwg
```

Report: saved path · what was drawn · any estimated dimensions.

---

### Step 5 — Iterate

On user feedback: edit the script, re-run, re-open. Offer a revision tag in
the title block for significant changes.

---

## Error handling

| Error | Fix |
|---|---|
| QCAD not found | `brew install --cask qcad` |
| DWG export fails | Confirm QCAD Professional is installed (Community cannot write DWG) |
| Script error | Read the terminal output, fix the offending line, re-run |
| Hatch invisible | Use a supported `HATCH.*` constant; try `HATCH.STEEL` to verify |
| Dimension missing | Check `offset` sign and that points are not coincident |
| Dimension not given | Use nearest standard value; note it as estimated in the report |
| Detail too complex | Split into a primary + sub-detail scripts |

---

## Reference patterns

### Steel shear-tab connection (imperial)
```javascript
// Column flange — 0.6" thick × 12" tall
setCurrentLayer("OUTLINE");
addPolygon([[-0.6,0],[-0.6,12],[0.6,12],[0.6,0]]);
addHatchRegion([[-0.6,0],[-0.6,12],[0.6,12],[0.6,0]], HATCH.STEEL);

 // 3/8" shear plate — 6" tall, welded to flange
 addPolygon([[0.6,3],[0.6,9],[1.975,9],[1.975,3]]);
 addHatchRegion([[0.6,3],[0.6,9],[1.975,9],[1.975,3]], HATCH.STEEL);

 // 3/4" A325 bolts — 3 at 1.5" spacing
 for (var y = 4.5; y <= 7.5; y += 1.5) {
     addCircle(1.2875, y, 0.375);
     addCenterlines(1.2875, y, 0.5);
 }

 addLinearDim(-0.6,0, 0.6,0,  -0.5, 0);          // flange width
 addLinearDim(1.975,3, 1.975,9,  0.5, 90);         // plate height
 addLabel("W-SHAPE FLANGE",  -2, 6, TEXT_HEIGHT, "MR");
 addLabel("3/8\" SHEAR PLATE", 2.5, 6, TEXT_HEIGHT, "ML");
```

### RC column section (imperial)
```javascript
setCurrentLayer("OUTLINE");
addPolygon([[0,0],[16,0],[16,16],[0,16]]);
addHatchRegion([[0,0],[16,0],[16,16],[0,16]], HATCH.CONCRETE);

 var cover = 1.5 + 0.3125, barR = 0.3125;
 var barPts = [[cover,cover],[8,cover],[16-cover,cover],
               [cover,8],[16-cover,8],
               [cover,16-cover],[8,16-cover],[16-cover,16-cover]];
 for (var i = 0; i < barPts.length; i++) {
     addCircle(barPts[i][0], barPts[i][1], barR);
     addCenterlines(barPts[i][0], barPts[i][1], barR);
 }

 addLinearDim(0,0, 16,0, -0.5, 0);
 addLinearDim(0,0, 0,16, -0.5, 90);
 addLinearDim(0,0, cover,0, -1.0, 0);
 addLabel("16x16 RC COLUMN", 8, 8);
 addLabel("8-#5 BARS", 8, -1.5);
```

### Pipe sleeve through concrete wall (imperial)
```javascript
setCurrentLayer("OUTLINE");
addPolygon([[0,0],[12,0],[12,10],[0,10]]);
addHatchRegion([[0,0],[12,0],[12,10],[0,10]], HATCH.CONCRETE);

 var pipeR = 3.3125, sleeveR = 4.3125, cx = 6, cy = 5;
 addCircle(cx, cy, sleeveR);
 addCircle(cx, cy, pipeR);
 addCenterlines(cx, cy, sleeveR + 0.75);

 addDiameterDim(cx, cy, pipeR,   45);
 addDiameterDim(cx, cy, sleeveR, 135);
 addLinearDim(0,0, 12,0, -0.5, 0);
 addLeader([[cx+pipeR+0.3, cy+pipeR+0.3],[cx+pipeR+1.5, cy+pipeR+1.5]], "6\" STD. PIPE");
 addLeader([[cx-sleeveR-0.3,cy+sleeveR+0.3],[cx-sleeveR-1.5,cy+sleeveR+1.5]], "8\" SLEEVE W/ GROUT");
```

---

## Error handling

| Error | Fix |
|---|---|
| QCAD not found | `brew install --cask qcad` |
| DWG export fails | Confirm QCAD Professional is installed (Community cannot write DWG) |
| Script error | Read the terminal output, fix the offending line, re-run |
| Hatch invisible | Use a supported `HATCH.*` constant; try `HATCH.STEEL` to verify |
| Dimension missing | Check `offset` sign and that points are not coincident |
| Dimension not given | Use nearest standard value; note it as estimated in the report |
| Detail too complex | Split into a primary + sub-detail scripts |

---

## Reference patterns

All examples use inches at 1:1 scale. For metric, pass `newDoc("mm")` and use mm values — QCAD handles the conversion internally.

### Steel shear-tab connection (mm)
```javascript
// Column flange — 15mm thick × 300mm tall
setCurrentLayer("OUTLINE");
addPolygon([[-15,0],[-15,300],[15,300],[15,0]]);
addHatchRegion([[-15,0],[-15,300],[15,300],[15,0]], HATCH.STEEL);

 // 10mm shear plate — 150mm tall, welded to flange
 addPolygon([[15,75],[15,225],[50,225],[50,75]]);
 addHatchRegion([[15,75],[15,225],[50,225],[50,75]], HATCH.STEEL);

 // M20 bolts (20mm dia) — 3 at 75mm spacing
 for (var y = 112.5; y <= 150; y += 37.5) {
     addCircle(32.5, y, 10);
     addCenterlines(32.5, y, 15);
 }

 addLinearDim(-15,0, 15,0,  -15, 0);          // flange thickness
 addLinearDim(50,75, 50,225, 15, 90);          // plate height
 addLabel("W-SHAPE FLANGE",  -40,  150, TEXT_HEIGHT);
 addLabel("10mm SHEAR PLATE", 65,  150, TEXT_HEIGHT);
```

### RC column section (mm)
```javascript
setCurrentLayer("OUTLINE");
addPolygon([[0,0],[400,0],[400,400],[0,400]]);
addHatchRegion([[0,0],[400,0],[400,400],[0,400]], HATCH.CONCRETE);

 var cover = 40 + 8  // 40mm clear + half bar dia
 var bar_r = 8;
 var bar_pts = [
     [cover,cover],[200,cover],[400-cover,cover],
     [cover,200],[400-cover,200],
     [cover,400-cover],[200,400-cover],[400-cover,400-cover],
 ];
 for (var i = 0; i < bar_pts.length; i++) {
     var bx = bar_pts[i][0], by = bar_pts[i][1];
     var circ = addCircle(bx, by, bar_r);
     add_centerlines(bx, by, bar_r + 4);
 }

 add_linear_dim(0,0, 400,0,   -20, 0);
 add_linear_dim(0,0, 0,400,   -20, 90);
 add_linear_dim(0,0, cover,0, -40, 0);
 add_label("400x400 RC COLUMN", 200, 200);
 add_label("8-16mm BARS",        200, -30);
```

### Pipe sleeve through concrete wall (mm)
```javascript
set_current_layer("OUTLINE");
add_polygon([[0,0],[300,0],[300,250],[0,250]]);
add_hatch([[0,0],[300,0],[300,250],[0,250]], HATCH.CONCRETE);

 var pipe_r   = 75, sleeve_r = 100, cx = 150, cy = 125;
 pipe_circ   = add_circle(cx, cy, pipe_r);
 sleeve_circ = add_circle(cx, cy, sleeve_r);
 add_centerlines(cx, cy, sleeve_r + 20);

 add_diameter_dim(pipe_circ,   45);
 add_diameter_dim(sleeve_circ, 135);
 add_linear_dim(0,0, 300,0, -20, 0);
 add_leader([[cx+pipe_r+8, cy+pipe_r+8],[cx+pipe_r+40,cy+pipe_r+40]],   "150mm STD. PIPE");
 add_leader([[cx-sleeve_r-8,cy+sleeve_r+8],[cx-sleeve_r-40,cy+sleeve_r+40]], "200mm SLEEVE W/ GROUT");
```

---

## Error handling

| Error | Fix |
|---|---|
| QCAD not found | `brew install --cask qcad` |
| DWG export fails | Confirm QCAD Professional is installed (Community cannot write DWG) |
| Script error | Read the terminal output, fix the offending line, re-run |
| Hatch invisible | Use a supported `HATCH.*` constant; try `HATCH.STEEL` to verify |
| Dimension missing | Check `offset` sign and that points are not coincident |
| Dimension not given | Use nearest standard value; note it as estimated in the report |
| Detail too complex | Split into a primary + sub-detail scripts |

---

## Reference patterns

All examples use inches at 1:1 scale. For metric, pass `newDoc("mm")` and use mm values — QCAD handles the conversion internally.

### Steel shear-tab connection (mm)
```javascript
// Column flange — 15mm thick × 300mm tall
setCurrentLayer("OUTLINE");
addPolygon([[-15,0],[-15,300],[15,300],[15,0]]);
addHatchRegion([[-15,0],[-15,300],[15,300],[15,0]], HATCH.STEEL);

 // 10mm shear plate — 150mm tall, welded to flange
 addPolygon([[15,75],[15,225],[50,225],[50,75]]);
 addHatchRegion([[15,75],[15,225],[50,225],[50,75]], HATCH.STEEL);

 // M20 bolts (20mm dia) — 3 at 75mm spacing
 for (var y = 112.5; y <= 150; y += 37.5) {
     addCircle(32.5, y, 10);
     addCenterlines(32.5, y, 15);
 }

 addLinearDim(-15,0, 15,0,  -15, 0);          // flange thickness
 addLinearDim(50,75, 50,225, 15, 90);          // plate height
 addLabel("W-SHAPE FLANGE",  -40,  150, TEXT_HEIGHT);
 addLabel("10mm SHEAR PLATE", 65,  150, TEXT_HEIGHT);
```

### RC column section (mm)
```javascript
setCurrentLayer("OUTLINE");
addPolygon([[0,0],[400,0],[400,400],[0,400]]);
addHatchRegion([[0,0],[400,0],[400,400],[0,400]], HATCH.CONCRETE);

 var cover = 40 + 8  // 40mm clear + half bar dia
 var bar_r = 8;
 var bar_pts = [
     [cover,cover],[200,cover],[400-cover,cover],
     [cover,200],[400-cover,200],
     [cover,400-cover],[200,400-cover],[400-cover,400-cover],
 ];
 for (var i = 0; i < bar_pts.length; i++) {
     var bx = bar_pts[i][0], by = bar_pts[i][1];
     var circ = addCircle(bx, by, bar_r);
     add_centerlines(bx, by, bar_r + 4);
 }

 add_linear_dim(0,0, 400,0,   -20, 0);
 add_linear_dim(0,0, 0,400,   -20, 90);
 add_linear_dim(0,0, cover,0, -40, 0);
 add_label("400x400 RC COLUMN", 200, 200);
 add_label("8-16mm BARS",        200, -30);
```

### Pipe sleeve through concrete wall (mm)
```javascript
set_current_layer("OUTLINE");
add_polygon([[0,0],[300,0],[300,250],[0,250]]);
add_hatch([[0,0],[300,0],[300,250],[0,250]], HATCH.CONCRETE);

 var pipe_r   = 75, sleeve_r = 100, cx = 150, cy = 125;
 pipe_circ   = add_circle(cx, cy, pipe_r);
 sleeve_circ = add_circle(cx, cy, sleeve_r);
 add_centerlines(cx, cy, sleeve_r + 20);

 add_diameter_dim(pipe_circ,   45);
 add_diameter_dim(sleeve_circ, 135);
 add_linear_dim(0,0, 300,0, -20, 0);
 add_leader([[cx+pipe_r+8, cy+pipe_r+8],[cx+pipe_r+40,cy+pipe_r+40]],   "150mm STD. PIPE");
 add_leader([[cx-sleeve_r-8,cy+sleeve_r+8],[cx-sleeve_r-40,cy+sleeve_r+40]], "200mm SLEEVE W/ GROUT");
```

---

## Error handling

| Error | Fix |
|---|---|
| QCAD not found | `brew install --cask qcad` |
| DWG export fails | Confirm QCAD Professional is installed (Community cannot write DWG) |
| Script error | Read the terminal output, fix the offending line, re-run |
| Hatch invisible | Use a supported `HATCH.*` constant; try `HATCH.STEEL` to verify |
| Dimension missing | Check `offset` sign and that points are not coincident |
| Dimension not given | Use nearest standard value; note it as estimated in the report |
| Detail too complex | Split into a primary + sub-detail scripts |

---

## Reference patterns

All examples use inches at 1:1 scale. For metric, pass `newDoc("mm")` and use mm values — QCAD handles the conversion internally.

### Steel shear-tab connection (mm)
```javascript
// Column flange — 15mm thick × 300mm tall
setCurrentLayer("OUTLINE");
addPolygon([[-15,0],[-15,300],[15,300],[15,0]]);
addHatchRegion([[-15,0],[-15,300],[15,300],[15,0]], HATCH.STEEL);

 // 10mm shear plate — 150mm tall, welded to flange
 addPolygon([[15,75],[15,225],[50,225],[50,75]]);
 addHatchRegion([[15,75],[15,225],[50,225],[50,75]], HATCH.STEEL);

 // M20 bolts (20mm dia) — 3 at 75mm spacing
 for (var y = 112.5; y <= 150; y += 37.5) {
     addCircle(32.5, y, 10);
     addCenterlines(32.5, y, 15);
 }

 addLinearDim(-15,0, 15,0,  -15, 0);          // flange thickness
 addLinearDim(50,75, 50,225, 15, 90);          // plate height
 addLabel("W-SHAPE FLANGE",  -40,  150, TEXT_HEIGHT);
 addLabel("10mm SHEAR PLATE", 65,  150, TEXT_HEIGHT);
```

### RC column section (mm)
```javascript
setCurrentLayer("OUTLINE");
addPolygon([[0,0],[400,0],[400,400],[0,400]]);
addHatchRegion([[0,0],[400,0],[400,400],[0,400]], HATCH.CONCRETE);

 var cover = 40 + 8  // 40mm clear + half bar dia
 var bar_r = 8;
 var bar_pts = [
     [cover,cover],[200,cover],[400-cover,cover],
     [cover,200],[400-cover,200],
     [cover,400-cover],[200,400-cover],[400-cover,400-cover],
 ];
 for (var i = 0; i < bar_pts.length; i++) {
     var bx = bar_pts[i][0], by = bar_pts[i][1];
     var circ = addCircle(bx, by, bar_r);
     add_centerlines(bx, by, bar_r + 4);
 }

 add_linear_dim(0,0, 400,0,   -20, 0);
 add_linear_dim(0,0, 0,400,   -20, 90);
 add_linear_dim(0,0, cover,0, -40, 0);
 add_label("400x400 RC COLUMN", 200, 200);
 add_label("8-16mm BARS",        200, -30);
```

### Pipe sleeve through concrete wall (mm)
```javascript
set_current_layer("OUTLINE");
add_polygon([[0,0],[300,0],[300,250],[0,250]]);
add_hatch([[0,0],[300,0],[300,250],[0,250]], HATCH.CONCRETE);

 var pipe_r   = 75, sleeve_r = 100, cx = 150, cy = 125;
 pipe_circ   = add_circle(cx, cy, pipe_r);
 sleeve_circ = add_circle(cx, cy, sleeve_r);
 add_centerlines(cx, cy, sleeve_r + 20);

 add_diameter_dim(pipe_circ,   45);
 add_diameter_dim(sleeve_circ, 135);
 add_linear_dim(0,0, 300,0, -20, 0);
 add_leader([[cx+pipe_r+8, cy+pipe_r+8],[cx+pipe_r+40,cy+pipe_r+40]],   "150mm STD. PIPE");
 add_leader([[cx-sleeve_r-8,cy+sleeve_r+8],[cx-sleeve_r-40,cy+sleeve_r+40]], "200mm SLEEVE W/ GROUT");
```

---

## Error handling

| Error | Fix |
|---|---|
| QCAD not found | `brew install --cask qcad` |
| DWG export fails | Confirm QCAD Professional is installed (Community cannot write DWG) |
| Script error | Read the terminal output, fix the offending line, re-run |
| Hatch invisible | Use a supported `HATCH.*` constant; try `HATCH.STEEL` to verify |
| Dimension missing | Check `offset` sign and that points are not coincident |
| Dimension not given | Use nearest standard value; note it as estimated in the report |
| Detail too complex | Split into a primary + sub-detail scripts |

---

## Reference patterns

All examples use inches at 1:1 scale. For metric, pass `newDoc("mm")` and use mm values — QCAD handles the conversion internally.

### Steel shear-tab connection (mm)
```javascript
// Column flange — 15mm thick × 300mm tall
setCurrentLayer("OUTLINE");
addPolygon([[-15,0],[-15,300],[15,300],[15,0]]);
addHatchRegion([[-15,0],[-15,300],[15,300],[15,0]], HATCH.STEEL);

 // 10mm shear plate — 150mm tall, welded to flange
 addPolygon([[15,75],[15,225],[50,225],[50,75]]);
 addHatchRegion([[15,75],[15,225],[50,225],[50,75]], HATCH.STEEL);

 // M20 bolts (20mm dia) — 3 at 75mm spacing
 for (var y = 112.5; y <= 150; y += 37.5) {
     addCircle(32.5, y, 10);
     addCenterlines(32.5, y, 15);
 }

 addLinearDim(-15,0, 15,0,  -15, 0);          // flange thickness
 addLinearDim(50,75, 50,225, 15, 90);          // plate height
 addLabel("W-SHAPE FLANGE",  -40,  150, TEXT_HEIGHT);
 addLabel("10mm SHEAR PLATE", 65,  150, TEXT_HEIGHT);
```

### RC column section (mm)
```javascript
setCurrentLayer("OUTLINE");
addPolygon([[0,0],[400,0],[400,400],[0,400]]);
addHatchRegion([[0,0],[400,0],[400,400],[0,400]], HATCH.CONCRETE);

 var cover = 40 + 8  // 40mm clear + half bar dia
 var bar_r = 8;
 var bar_pts = [
     [cover,cover],[200,cover],[400-cover,cover],
     [cover,200],[400-cover,200],
     [cover,400-cover],[200,400-cover],[400-cover,400-cover],
 ];
 for (var i = 0; i < bar_pts.length; i++) {
     var bx = bar_pts[i][0], by = bar_pts[i][1];
     var circ = addCircle(bx, by, bar_r);
     add_centerlines(bx, by, bar_r + 4);
 }

 add_linear_dim(0,0, 400,0,   -20, 0);
 add_linear_dim(0,0, 0,400,   -20, 90);
 add_linear_dim(0,0, cover,0, -40, 0);
 add_label("400x400 RC COLUMN", 200, 200);
 add_label("8-16mm BARS",        200, -30);
```

### Pipe sleeve through concrete wall (mm)
```javascript
set_current_layer("OUTLINE");
add_polygon([[0,0],[300,0],[300,250],[0,250]]);
add_hatch([[0,0],[300,0],[300,250],[0,250]], HATCH.CONCRETE);

 var pipe_r   = 75, sleeve_r = 100, cx = 150, cy = 125;
 pipe_circ   = add_circle(cx, cy, pipe_r);
 sleeve_circ = add_circle(cx, cy, sleeve_r);
 add_centerlines(cx, cy, sleeve_r + 20);

 add_diameter_dim(pipe_circ,   45);
 add_diameter_dim(sleeve_circ, 135);
 add_linear_dim(0,0, 300,0, -20, 0);
 add_leader([[cx+pipe_r+8, cy+pipe_r+8],[cx+pipe_r+40,cy+pipe_r+40]],   "150mm STD. PIPE");
 add_leader([[cx-sleeve_r-8,cy+sleeve_r+8],[cx-sleeve_r-40,cy+sleeve_r+40]], "200mm SLEEVE W/ GROUT");
```

---

## Error handling

| Error | Fix |
|---|---|
| QCAD not found | `brew install --cask qcad` |
| DWG export fails | Confirm QCAD Professional is installed (Community cannot write DWG) |
| Script error | Read the terminal output, fix the offending line, re-run |
| Hatch invisible | Use a supported `HATCH.*` constant; try `HATCH.STEEL` to verify |
| Dimension missing | Check `offset` sign and that points are not coincident |
| Dimension not given | Use nearest standard value; note it as estimated in the report |
| Detail too complex | Split into a primary + sub-detail scripts |

---

## Reference patterns

All examples use inches at 1:1 scale. For metric, pass `newDoc("mm")` and use mm values — QCAD handles the conversion internally.

### Steel shear-tab connection (mm)
```javascript
// Column flange — 15mm thick × 300mm tall
setCurrentLayer("OUTLINE");
addPolygon([[-15,0],[-15,300],[15,300],[15,0]]);
addHatchRegion([[-15,0],[-15,300],[15,300],[15,0]], HATCH.STEEL);

 // 10mm shear plate — 150mm tall, welded to flange
 addPolygon([[15,75],[15,225],[50,225],[50,75]]);
 addHatchRegion([[15,75],[15,225],[50,225],[50,75]], HATCH.STEEL);

 // M20 bolts (20mm dia) — 3 at 75mm spacing
 for (var y = 112.5; y <= 150; y += 37.5) {
     addCircle(32.5, y, 10);
     addCenterlines(32.5, y, 15);
 }

 addLinearDim(-15,0, 15,0,  -15, 0);          // flange thickness
 addLinearDim(50,75, 50,225, 15, 90);          // plate height
 addLabel("W-SHAPE FLANGE",  -40,  150, TEXT_HEIGHT);
 addLabel("10mm SHEAR PLATE", 65,  150, TEXT_HEIGHT);
```

### RC column section (mm)
```javascript
setCurrentLayer("OUTLINE");
addPolygon([[0,0],[400,0],[400,400],[0,400]]);
addHatchRegion([[0,0],[400,0],[400,400],[0,400]], HATCH.CONCRETE);

 var cover = 40 + 8  // 40mm clear + half bar dia
 var bar_r = 8;
 var bar_pts = [
     [cover,cover],[200,cover],[400-cover,cover],
     [cover,200],[400-cover,200],
     [cover,400-cover],[200,400-cover],[400-cover,400-cover],
 ];
 for (var i = 0; i < bar_pts.length; i++) {
     var bx = bar_pts[i][0], by = bar_pts[i][1];
     var circ = addCircle(bx, by, bar_r);
     add_centerlines(bx, by, bar_r + 4);
 }

 add_linear_dim(0,0, 400,0,   -20, 0);
 add_linear_dim(0,0, 0,400,   -20, 90);
 add_linear_dim(0,0, cover,0, -40, 0);
 add_label("400x400 RC COLUMN", 200, 200);
 add_label("8-16mm BARS",        200, -30);
```

### Pipe sleeve through concrete wall (mm)
```javascript
set_current_layer("OUTLINE");
add_polygon([[0,0],[300,0],[300,250],[0,250]]);
add_hatch([[0,0],[300,0],[300,250],[0,250]], HATCH.CONCRETE);

 var pipe_r   = 75, sleeve_r = 100, cx = 150, cy = 125;
 pipe_circ   = add_circle(cx, cy, pipe_r);
 sleeve_circ = add_circle(cx, cy, sleeve_r);
 add_centerlines(cx, cy, sleeve_r + 20);

 add_diameter_dim(pipe_circ,   45);
 add_diameter_dim(sleeve_circ, 135);
 add_linear_dim(0,0, 300,0, -20, 0);
 add_leader([[cx+pipe_r+8, cy+pipe_r+8],[cx+pipe_r+40,cy+pipe_r+40]],   "150mm STD. PIPE");
 add_leader([[cx-sleeve_r-8,cy+sleeve_r+8],[cx-sleeve_r-40,cy+sleeve_r+40]], "200mm SLEEVE W/ GROUT");
```

---

## Error handling

| Error | Fix |
|---|---|
| QCAD not found | `brew install --cask qcad` |
| DWG export fails | Confirm QCAD Professional is installed (Community cannot write DWG) |
| Script error | Read the terminal output, fix the offending line, re-run |
| Hatch invisible | Use a supported `HATCH.*` constant; try `HATCH.STEEL` to verify |
| Dimension missing | Check `offset` sign and that points are not coincident |
| Dimension not given | Use nearest standard value; note it as estimated in the report |
| Detail too complex | Split into a primary + sub-detail scripts |

---

## Reference patterns

All examples use inches at 1:1 scale. For metric, pass `newDoc("mm")` and use mm values — QCAD handles the conversion internally.

### Steel shear-tab connection (mm)
```javascript
// Column flange — 15mm thick × 300mm tall
setCurrentLayer("OUTLINE");
addPolygon([[-15,0],[-15,300],[15,300],[15,0]]);
addHatchRegion([[-15,0],[-15,300],[15,300],[15,0]], HATCH.STEEL);

 // 10mm shear plate — 150mm tall, welded to flange
 addPolygon([[15,75],[15,225],[50,225],[50,75]]);
 addHatchRegion([[15,75],[15,225],[50,225],[50,75]], HATCH.STEEL);

 // M20 bolts (20mm dia) — 3 at 75mm spacing
 for (var y = 112.5; y <= 150; y += 37.5) {
     addCircle(32.5, y, 10);
     addCenterlines(32.5, y, 15);
 }

 addLinearDim(-15,0, 15,0,  -15, 0);          // flange thickness
 addLinearDim(50,75, 50,225, 15, 90);          // plate height
 addLabel("W-SHAPE FLANGE",  -40,  150, TEXT_HEIGHT);
 addLabel("10mm SHEAR PLATE", 65,  150, TEXT_HEIGHT);
```

### RC column section (mm)
```javascript
setCurrentLayer("OUTLINE");
addPolygon([[0,0],[400,0],[400,400],[0,400]]);
addHatchRegion([[0,0],[400,0],[400,400],[0,400]], HATCH.CONCRETE);

 var cover = 40 + 8  // 40mm clear + half bar dia
 var bar_r = 8;
 var bar_pts = [
     [cover,cover],[200,cover],[400-cover,cover],
     [cover,200],[400-cover,200],
     [cover,400-cover],[200,400-cover],[400-cover,400-cover],
 ];
 for (var i = 0; i < bar_pts.length; i++) {
     var bx = bar_pts[i][0], by = bar_pts[i][1];
     var circ = addCircle(bx, by, bar_r);
     add_centerlines(bx, by, bar_r + 4);
 }

 add_linear_dim(0,0, 400,0,   -20, 0);
 add_linear_dim(0,0, 0,400,   -20, 90);
 add_linear_dim(0,0, cover,0, -40, 0);
 add_label("400x400 RC COLUMN", 200, 200);
 add_label("8-16mm BARS",        200, -30);
```

### Pipe sleeve through concrete wall (mm)
```javascript
set_current_layer("OUTLINE");
add_polygon([[0,0],[300,0],[300,250],[0,250]]);
add_hatch([[0,0],[300,0],[300,250],[0,250]], HATCH.CONCRETE);

 var pipe_r   = 75, sleeve_r = 100, cx = 150, cy = 125;
 pipe_circ   = add_circle(cx, cy, pipe_r);
 sleeve_circ = add_circle(cx, cy, sleeve_r);
 add_centerlines(cx, cy, sleeve_r + 20);

 add_diameter_dim(pipe_circ,   45);
 add_diameter_dim(sleeve_circ, 135);
 add_linear_dim(0,0, 300,0, -20, 0);
 add_leader([[cx+pipe_r+8, cy+pipe_r+8],[cx+pipe_r+40,cy+pipe_r+40]],   "150mm STD. PIPE");
 add_leader([[cx-sleeve_r-8,cy+sleeve_r+8],[cx-sleeve_r-40,cy+sleeve_r+40]], "200mm SLEEVE W/ GROUT");
```

---

## Error handling

| Error | Fix |
|---|---|
| QCAD not found | `brew install --cask qcad` |
| DWG export fails | Confirm QCAD Professional is installed (Community cannot write DWG) |
| Script error | Read the terminal output, fix the offending line, re-run |
| Hatch invisible | Use a supported `HATCH.*` constant; try `HATCH.STEEL` to verify |
| Dimension missing | Check `offset` sign and that points are not coincident |
| Dimension not given | Use nearest standard value; note it as estimated in the report |
| Detail too complex | Split into a primary + sub-detail scripts |

---

## Reference patterns

All examples use inches at 1:1 scale. For metric, pass `newDoc("mm")` and use mm values — QCAD handles the conversion internally.

### Steel shear-tab connection (mm)
```javascript
// Column flange — 15mm thick × 300mm tall
setCurrentLayer("OUTLINE");
addPolygon([[-15,0],[-15,300],[15,300],[15,0]]);
addHatchRegion([[-15,0],[-15,300],[15,300],[15,0]], HATCH.STEEL);

 // 10mm shear plate — 150mm tall, welded to flange
 addPolygon([[15,75],[15,225],[50,225],[50,75]]);
 addHatchRegion([[15,75],[15,225],[50,225],[50,75]], HATCH.STEEL);

 // M20 bolts (20mm dia) — 3 at 75mm spacing
 for (var y = 112.5; y <= 150; y += 37.5) {
     addCircle(32.5, y, 10);
     addCenterlines(32.5, y, 15);
 }

 addLinearDim(-15,0, 15,0,  -15, 0);          // flange thickness
 addLinearDim(50,75, 50,225, 15, 90);          // plate height
 addLabel("W-SHAPE FLANGE",  -40,  150, TEXT_HEIGHT);
 addLabel("10mm SHEAR PLATE", 65,  150, TEXT_HEIGHT);
```

### RC column section (mm)
```javascript
setCurrentLayer("OUTLINE");
addPolygon([[0,0],[400,0],[400,400],[0,400]]);
addHatchRegion([[0,0],[400,0],[400,400],[0,400]], HATCH.CONCRETE);

 var cover = 40 + 8  // 40mm clear + half bar dia
 var bar_r = 8;
 var bar_pts = [
     [cover,cover],[200,cover],[400-cover,cover],
     [cover,200],[400-cover,200],
     [cover,400-cover],[200,400-cover],[400-cover,400-cover],
 ];
 for (var i = 0; i < bar_pts.length; i++) {
     var bx = bar_pts[i][0], by = bar_pts[i][1];
     var circ = addCircle(bx, by, bar_r);
     add_centerlines(bx, by, bar_r + 4);
 }

 add_linear_dim(0,0, 400,0,   -20, 0);
 add_linear_dim(0,0, 0,400,   -20, 90);
 add_linear_dim(0,0, cover,0, -40, 0);
 add_label("400x400 RC COLUMN", 200, 200);
 add_label("8-16mm BARS",        200, -30);
```

### Pipe sleeve through concrete wall (mm)
```javascript
set_current_layer("OUTLINE");
add_polygon([[0,0],[300,0],[300,250],[0,250]]);
add_hatch([[0,0],[300,0],[300,250],[0,250]], HATCH.CONCRETE);

 var pipe_r   = 75, sleeve_r = 100, cx = 150, cy = 125;
 pipe_circ   = add_circle(cx, cy, pipe_r);
 sleeve_circ = add_circle(cx, cy, sleeve_r);
 add_centerlines(cx, cy, sleeve_r + 20);

 add_diameter_dim(pipe_circ,   45);
 add_diameter_dim(sleeve_circ, 135);
 add_linear_dim(0,0, 300,0, -20, 0);
 add_leader([[cx+pipe_r+8, cy+pipe_r+8],[cx+pipe_r+40,cy+pipe_r+40]],   "150mm STD. PIPE");
 add_leader([[cx-sleeve_r-8,cy+sleeve_r+8],[cx-sleeve_r-40,cy+sleeve_r+40]], "200mm SLEEVE W/ GROUT");
```

---

## Error handling

| Error | Fix |
|---|---|
| QCAD not found | `brew install --cask qcad` |
| DWG export fails | Confirm QCAD Professional is installed (Community cannot write DWG) |
| Script error | Read the terminal output, fix the offending line, re-run |
| Hatch invisible | Use a supported `HATCH.*` constant; try `HATCH.STEEL` to verify |
| Dimension missing | Check `offset` sign and that points are not coincident |
| Dimension not given | Use nearest standard value; note it as estimated in the report |
| Detail too complex | Split into a primary + sub-detail scripts |

---

## Reference patterns

All examples use inches at 1:1 scale. For metric, pass `newDoc("mm")` and use mm values — QCAD handles the conversion internally.

### Steel shear-tab connection (mm)
```javascript
// Column flange — 15mm thick × 300mm tall
setCurrentLayer("OUTLINE");
addPolygon([[-15,0],[-15,300],[15,300],[15,0]]);
addHatchRegion([[-15,0],[-15,300],[15,300],[15,0]], HATCH.STEEL);

 // 10mm shear plate — 150mm tall, welded to flange
 addPolygon([[15,75],[15,225],[50,225],[50,75]]);
 addHatchRegion([[15,75],[15,225],[50,225],[50,75]], HATCH.STEEL);

 // M20 bolts (20mm dia) — 3 at 75mm spacing
 for (var y = 112.5; y <= 150; y += 37.5) {
     addCircle(32.5, y, 10);
     addCenterlines(32.5, y, 15);
 }

 addLinearDim(-15,0, 15,0,  -15, 0);          // flange thickness
 addLinearDim(50,75, 50,225, 15, 90);          // plate height
 addLabel("W-SHAPE FLANGE",  -40,  150, TEXT_HEIGHT);
 addLabel("10mm SHEAR PLATE", 65,  150, TEXT_HEIGHT);
```

### RC column section (mm)
```javascript
setCurrentLayer("OUTLINE");
addPolygon([[0,0],[400,0],[400,400],[0,400]]);
addHatchRegion([[0,0],[400,0],[400,400],[0,400]], HATCH.CONCRETE);

 var cover = 40 + 8  // 40mm clear + half bar dia
 var bar_r = 8;
 var bar_pts = [
     [cover,cover],[200,cover],[400-cover,cover],
     [cover,200],[400-cover,200],
     [cover,400-cover],[200,400-cover],[400-cover,400-cover],
 ];
 for (var i = 0; i < bar_pts.length; i++) {
     var bx = bar_pts[i][0], by = bar_pts[i][1];
     var circ = addCircle(bx, by, bar_r);
     add_centerlines(bx, by, bar_r + 4);
 }

 add_linear_dim(0,0, 400,0,   -20, 0);
 add_linear_dim(0,0, 0,400,   -20, 90);
 add_linear_dim(0,0, cover,0, -40, 0);
 add_label("400x400 RC COLUMN", 200, 200);
 add_label("8-16mm BARS",        200, -30);
```

### Pipe sleeve through concrete wall (mm)
```javascript
set_current_layer("OUTLINE");
add_polygon([[0,0],[300,0],[300,250],[0,250]]);
add_hatch([[0,0],[300,0],[300,250],[0,250]], HATCH.CONCRETE);

 var pipe_r   = 75, sleeve_r = 100, cx = 150, cy = 125;
 pipe_circ   = add_circle(cx, cy, pipe_r);
 sleeve_circ = add_circle(cx, cy, sleeve_r);
 add_centerlines(cx, cy, sleeve_r + 20);

 add_diameter_dim(pipe_circ,   45);
 add_diameter_dim(sleeve_circ, 135);
 add_linear_dim(0,0, 300,0, -20, 0);
 add_leader([[cx+pipe_r+8, cy+pipe_r+8],[cx+pipe_r+40,cy+pipe_r+40]],   "150mm STD. PIPE");
 add_leader([[cx-sleeve_r-8,cy+sleeve_r+8],[cx-sleeve_r-40,cy+sleeve_r+40]], "200mm SLEEVE W/ GROUT");
```

---

## Error handling

| Error | Fix |
|---|---|
| QCAD not found | `brew install --cask qcad` |
| DWG export fails | Confirm QCAD Professional is installed (Community cannot write DWG) |
| Script error | Read the terminal output, fix the offending line, re-run |
| Hatch invisible | Use a supported `HATCH.*` constant; try `HATCH.STEEL` to verify |
| Dimension missing | Check `offset` sign and that points are not coincident |
| Dimension not given | Use nearest standard value; note it as estimated in the report |
| Detail too complex | Split into a primary + sub-detail scripts |

---

## Reference patterns

All examples use inches at 1:1 scale. For metric, pass `newDoc("mm")` and use mm values — QCAD handles the conversion internally.

### Steel shear-tab connection (mm)
```javascript
// Column flange — 15mm thick × 300mm tall
setCurrentLayer("OUTLINE");
addPolygon([[-15,0],[-15,300],[15,300],[15,0]]);
addHatchRegion([[-15,0],[-15,300],[15,300],[15,0]], HATCH.STEEL);

 // 10mm shear plate — 150mm tall, welded to flange
 addPolygon([[15,75],[15,225],[50,225],[50,75]]);
 addHatchRegion([[15,75],[15,225],[50,225],[50,75]], HATCH.STEEL);

 // M20 bolts (20mm dia) — 3 at 75mm spacing
 for (var y = 112.5; y <= 150; y += 37.5) {
     addCircle(32.5, y, 10);
     addCenterlines(32.5, y, 15);
 }

 addLinearDim(-15,0, 15,0,  -15, 0);          // flange thickness
 addLinearDim(50,75, 50,225, 15, 90);          // plate height
 addLabel("W-SHAPE FLANGE",  -40,  150, TEXT_HEIGHT);
 addLabel("10mm SHEAR PLATE", 65,  150, TEXT_HEIGHT);
```

### RC column section (mm)
```javascript
setCurrentLayer("OUTLINE");
addPolygon([[0,0],[400,0],[400,400],[0,400]]);
addHatchRegion([[0,0],[400,0],[400,400],[0,400]], HATCH.CONCRETE);

 var cover = 40 + 8  // 40mm clear + half bar dia
 var bar_r = 8;
 var bar_pts = [
     [cover,cover],[200,cover],[400-cover,cover],
     [cover,200],[400-cover,200],
     [cover,400-cover],[200,400-cover],[400-cover,400-cover],
 ];
 for (var i = 0; i < bar_pts.length; i++) {
     var bx = bar_pts[i][0], by = bar_pts[i][1];
     var circ = addCircle(bx, by, bar_r);
     add_centerlines(bx, by, bar_r + 4);
 }

 add_linear_dim(0,0, 400,0,   -20, 0);
 add_linear_dim(0,0, 0,400,   -20, 90);
 add_linear_dim(0,0, cover,0, -40, 0);
 add_label("400x400 RC COLUMN", 200, 200);
 add_label("8-16mm BARS",        200, -30);
```

### Pipe sleeve through concrete wall (mm)
```javascript
set_current_layer("OUTLINE");
add_polygon([[0,0],[300,0],[300,250],[0,250]]);
add_hatch([[0,0],[300,0],[300,250],[0,250]], HATCH.CONCRETE);

 var pipe_r   = 75, sleeve_r = 100, cx = 150, cy = 125;
 pipe_circ   = add_circle(cx, cy, pipe_r);
 sleeve_circ = add_circle(cx, cy, sleeve_r);
 add_centerlines(cx, cy, sleeve_r + 20);

 add_diameter_dim(pipe_circ,   45);
 add_diameter_dim(sleeve_circ, 135);
 add_linear_dim(0,0, 300,0, -20, 0);
 add_leader([[cx+pipe_r+8, cy+pipe_r+8],[cx+pipe_r+40,cy+pipe_r+40]],   "150mm STD. PIPE");
 add_leader([[cx-sleeve_r-8,cy+sleeve_r+8],[cx-sleeve_r-40,cy+sleeve_r+40]], "200mm SLEEVE W/ GROUT";
```

---

## Error handling

| Error | Fix |
|---|---|
| QCAD not found | `brew install --cask qcad` |
| DWG export fails | Confirm QCAD Professional is installed (Community cannot write DWG) |
| Script error | Read the terminal output, fix the offending line, re-run |
| Hatch invisible | Use a supported `HATCH.*` constant; try `HATCH.STEEL` to verify |
| Dimension missing | Check `offset` sign and that points are not coincident |
| Dimension not given | Use nearest standard value; note it as estimated in the report |
| Detail too complex | Split into a primary + sub-detail scripts |

---

## Reference patterns

All examples use inches at 1:1 scale. For metric, pass `newDoc("mm")` and use mm values — QCAD handles the conversion internally.

### Steel shear-tab connection (mm)
```javascript
// Column flange — 15mm thick × 300mm tall
setCurrentLayer("OUTLINE");
addPolygon([[-15,0],[-15,300],[15,300],[15,0]]);
addHatchRegion([[-15,0],[-15,300],[15,300],[15,0]], HATCH.STEEL);

 // 10mm shear plate — 150mm tall, welded to flange
 addPolygon([[15,75],[15,225],[50,225],[50,75]]);
 addHatchRegion([[15,75],[15,225],[50,225],[50,75]], HATCH.STEEL);

 // M20 bolts (20mm dia) — 3 at 75mm spacing
 for (var y = 112.5; y <= 150; y += 37.5) {
     addCircle(32.5, y, 10);
     addCenterlines(32.5, y, 15);
 }

 addLinearDim(-15,0, 15,0,  -15, 0);          // flange thickness
 addLinearDim(50,75, 50,225, 15, 90);          // plate height
 addLabel("W-SHAPE FLANGE",  -40,  150, TEXT_HEIGHT);
 addLabel("10mm SHEAR PLATE", 65,  150, TEXT_HEIGHT);
```

### RC column section (mm)
```javascript
setCurrentLayer("OUTLINE");
addPolygon([[0,0],[400,0],[400,400],[0,400]]);
addHatchRegion([[0,0],[400,0],[400,400],[0,400]], HATCH.CONCRETE);

 var cover = 40 + 8  // 40mm clear + half bar dia
 var bar_r = 8;
 var bar_pts = [
     [cover,cover],[200,cover],[400-cover,cover],
     [cover,200],[400-cover,200],
     [cover,400-cover],[200,400-cover],[400-cover,400-cover],
 ];
 for (var i = 0; i < bar_pts.length; i++) {
     var bx = bar_pts[i][0], by = bar_pts[i][1];
     var circ = addCircle(bx, by, bar_r);
     add_centerlines(bx, by, bar_r + 4);
 }

 add_linear_dim(0,0, 400,0,   -20, 0);
 add_linear_dim(0,0, 0,400,   -20, 90);
 add_linear_dim(0,0, cover,0, -40, 0);
 add_label("400x400 RC COLUMN", 200, 200);
 add_label("8-16mm BARS",        200, -30);
```

### Pipe sleeve through concrete wall (mm)
```javascript
set_current_layer("OUTLINE");
add_polygon([[0,0],[300,0],[300,250],[0,250]]);
add_hatch([[0,0],[300,0],[300,250],[0,250]], HATCH.CONCRETE);

 var pipe_r   = 75, sleeve_r = 100, cx = 150, cy = 125;
 pipe_circ   = add_circle(cx, cy, pipe_r);
 sleeve_circ = add_circle(cx, cy, sleeve_r);
 add_centerlines(cx, cy, sleeve_r + 20);

 add_diameter_dim(pipe_circ,   45);
 add_diameter_dim(sleeve_circ, 135);
 add_linear_dim(0,0, 300,0, -20, 0);
 add_leader([[cx+pipe_r+8, cy+pipe_r+8],[cx+pipe_r+40,cy+pipe_r+40]],   "150mm STD. PIPE");
 add_leader([[cx-sleeve_r-8,cy+sleeve_r+8],[cx-sleeve_r-40,cy+sleeve_r+40]], "200mm SLEEVE W/ GROUT";
```

---

## Error handling

| Error | Fix |
|---|---|
| QCAD not found | `brew install --cask qcad` |
| DWG export fails | Confirm QCAD Professional is installed (Community cannot write DWG) |
| Script error | Read the terminal output, fix the offending line, re-run |
| Hatch invisible | Use a supported `HATCH.*` constant; try `HATCH.STEEL` to verify |
| Dimension missing | Check `offset` sign and that points are not coincident |
| Dimension not given | Use nearest standard value; note it as estimated in the report |
| Detail too complex | Split into a primary + sub-detail scripts |

---

## Reference patterns

All examples use inches at 1:1 scale. For metric, pass `newDoc("mm")` and use mm values — QCAD handles the conversion internally.

### Steel shear-tab connection (mm)
```javascript
// Column flange — 15mm thick × 300mm tall
setCurrentLayer("OUTLINE");
addPolygon([[-15,0],[-15,300],[15,300],[15,0]]);
addHatchRegion([[-15,0],[-15,300],[15,300],[15,0]], HATCH.STEEL);

 // 10mm shear plate — 150mm tall, welded to flange
 addPolygon([[15,75],[15,225],[50,225],[50,75]]);
 addHatchRegion([[15,75],[15,225],[50,225],[50,75]], HATCH.STEEL);

 // M20 bolts (20mm dia) — 3 at 75mm spacing
 for (var y = 112.5; y <= 150; y += 37.5) {
     addCircle(32.5, y, 10);
     addCenterlines(32.5, y, 15);
 }

 addLinearDim(-15,0, 15,0,  -15, 0);          // flange thickness
 addLinearDim(50,75, 50,225, 15, 90);          // plate height
 addLabel("W-SHAPE FLANGE",  -40,  150, TEXT_HEIGHT);
 addLabel("10mm SHEAR PLATE", 65,  150, TEXT_HEIGHT);
```

### RC column section (mm)
```javascript
setCurrentLayer("OUTLINE");
addPolygon([[0,0],[400,0],[400,400],[0,400]]);
addHatchRegion([[0,0