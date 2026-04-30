---
name: dwg-to-dxf
description: |
  Converts DWG files to DXF (or any DWG/DXF ↔ DWG/DXF direction) using ODA
  File Converter. Accepts a single file or a folder. Output lands in
  ~/Documents/CAD/converted/ by default. Use when asked to convert, export,
  or batch-process CAD files between DWG and DXF formats.
license: MIT
compatibility: "macOS / Linux / Windows — ODA File Converter required (free download)"
metadata:
  author: "Thomas Ott"
  version: "1.0"
---

# DWG ↔ DXF Converter Skill

## Overview

Converts DWG/DXF files using ODA File Converter (the same engine AutoCAD uses
internally). Handles a single file, a folder, or a recursive folder tree.

Helper: `scripts/oda_convert.py` — can be called directly or imported as a module.

**Defaults:**
- Input format detected automatically from file extension
- Output format: DXF (ACAD2018 / R24)
- Output directory: `~/Documents/CAD/converted/`

## Setup

Download **ODA File Converter** (free):
https://www.opendesign.com/guestfiles/oda_file_converter

macOS — drag to `/Applications/`. Executable lands at:
```
/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter
```

Verify:
```bash
/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter --help
```

## Invocation

```
/dwg-to-dxf <file_or_folder> [output_dir] [options]
```

Examples:
```
/dwg-to-dxf ~/Downloads/plan.dwg
/dwg-to-dxf ~/Downloads/plans/                        # whole folder
/dwg-to-dxf ~/Downloads/plans/ --recurse              # recursive
/dwg-to-dxf ~/Downloads/plan.dxf --to DWG             # DXF → DWG
/dwg-to-dxf ~/Downloads/plans/ --version ACAD2007     # older target version
```

---

## Instructions for the model

### Step 1 — Identify inputs and intent

From the user's message, extract:
1. **Input path** — single file or folder (expand `~`)
2. **Direction** — DWG→DXF (default) or DXF→DWG or other (`--to`)
3. **Version** — if the user mentions a specific AutoCAD version or year
4. **Recurse** — if the user says "all files", "subdirectories", "batch"
5. **Open after** — if the user wants to see the results immediately

If any detail is ambiguous, default to DXF output at ACAD2018.

### Step 2 — Build the command

Direct script invocation:
```bash
python3 /Users/ottt/.pi/agent/skills/dwg-to-dxf/scripts/oda_convert.py \
    <input> [output_dir] \
    [--to DXF|DWG] \
    [--version ACAD2018] \
    [--recurse] \
    [--no-audit] \
    [--filter "*.dwg"] \
    [--oda /path/to/ODAFileConverter] \
    [--open]
```

Or import as a Python module:
```python
from oda_convert import convert

files = convert(
    input_path="~/Downloads/plan.dwg",
    output_dir="~/Documents/CAD/converted",
    to="DXF",
    version="ACAD2018",
    recurse=False,
    audit=True,
)
print(files)   # list of Path objects
```

### Step 3 — Execute and report

Run the command. Report:
- How many files were converted
- Full output paths
- Any errors from ODA stdout

---

## ODA version strings

| Year | DWG version string | Notes |
|---|---|---|
| 2018+ | `ACAD2018` | Default for DXF |
| 2013–2017 | `ACAD2013` | |
| 2010–2012 | `ACAD2010` | |
| 2007–2009 | `ACAD2007` | |
| 2004–2006 | `ACAD2004` | |
| 2000–2003 | `ACAD2000` | |
| R14 | `ACAD14` | |
| R13 | `ACAD13` | |
| R12 | `ACAD12` | Very old — ASCII DXF only |

For DWG output, `R24` = 2010 format (broadly compatible). Use `ACAD2018` when targeting modern AutoCAD.

---

## Error handling

| Error | Fix |
|---|---|
| `ODA File Converter not found` | Download from opendesign.com or pass `--oda <path>` |
| `exited with code 1` | Check ODA's stdout for the specific file that failed |
| Output directory empty | ODA may have silently failed — run with `--no-audit` to test |
| `Permission denied` on macOS | `chmod +x /Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter` |
| DXF opens with wrong entities | Try an older `--version` (e.g. `ACAD2007`) for compatibility |
| Single file → symlink error | ODA requires a directory; the script uses a temp dir + symlink automatically |
