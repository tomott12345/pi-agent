"""
oda_convert.py — DWG/DXF ↔ DXF/DWG converter using ODA File Converter.

Usage:
    python3 oda_convert.py <input> [<output_dir>] [options]

    <input>       Path to a single .dwg/.dxf file, or a folder of files.
    <output_dir>  Destination folder (default: ~/Documents/CAD/converted/).

Options:
    --to          Output format: "DXF" (default) or "DWG"
    --version     DWG/DXF version (default: "ACAD2018" for DXF, "R24" for DWG)
    --recurse     Recurse into subdirectories
    --no-audit    Skip the audit/repair pass (faster, may leave corrupt files)
    --oda PATH    Override the ODA File Converter executable path
    --open        Open the output directory in Finder/Explorer after conversion

Requires:
    ODA File Converter — https://www.opendesign.com/guestfiles/oda_file_converter
    macOS:   /Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter
    Linux:   /usr/bin/ODAFileConverter  (or wherever the package installs it)
    Windows: C:/Program Files/ODA/ODAFileConverter <version>/ODAFileConverter.exe

ODA CLI synopsis:
    ODAFileConverter InputDir OutputDir OutputVersion OutputType Recurse Audit [Filter]

    OutputVersion:  ACAD9, ACAD10, ACAD12, ACAD13, ACAD14,
                    ACAD2000, ACAD2004, ACAD2007, ACAD2010, ACAD2013, ACAD2018
    OutputType:     DWG | DXF | DXB
    Recurse:        0 | 1
    Audit:          0 | 1
    Filter:         (optional) glob, e.g. "*.dwg"
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# ODA executable discovery
# ---------------------------------------------------------------------------

_ODA_CANDIDATES = {
    "Darwin": [
        "/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter",
    ],
    "Linux": [
        "/usr/bin/ODAFileConverter",
        "/usr/local/bin/ODAFileConverter",
        str(Path.home() / "ODAFileConverter" / "ODAFileConverter"),
    ],
    "Windows": [
        r"C:\Program Files\ODA\ODAFileConverter_title\ODAFileConverter.exe",
        r"C:\Program Files (x86)\ODA\ODAFileConverter_title\ODAFileConverter.exe",
    ],
}


def find_oda(override=None):
    """Return path to ODA File Converter executable, or raise if not found."""
    if override:
        if not Path(override).is_file():
            raise FileNotFoundError(f"ODA executable not found at: {override}")
        return override

    # Try PATH first
    found = shutil.which("ODAFileConverter")
    if found:
        return found

    system = platform.system()
    for candidate in _ODA_CANDIDATES.get(system, []):
        # Expand glob-like version tokens (Windows)
        if "*" not in candidate and Path(candidate).is_file():
            return candidate

    raise FileNotFoundError(
        "ODA File Converter not found. Install from "
        "https://www.opendesign.com/guestfiles/oda_file_converter "
        "or pass --oda <path>."
    )


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------

_FORMAT_VERSION_DEFAULT = {
    "DXF": "ACAD2018",
    "DWG": "R24",
    "DXB": "ACAD2018",
}


def convert(input_path, output_dir, to="DXF", version=None, recurse=False,
            audit=True, oda_path=None, file_filter=None):
    """
    Convert DWG/DXF files using ODA File Converter.

    input_path:   str or Path — single file or a directory
    output_dir:   str or Path — destination directory (created if needed)
    to:           "DXF", "DWG", or "DXB"
    version:      ODA version string; None → format default
    recurse:      bool — descend into subdirectories
    audit:        bool — run ODA audit/repair pass
    oda_path:     override ODA executable path
    file_filter:  "*.dwg" style glob passed to ODA (None → ODA picks all)

    Returns list of output file paths (may be empty if nothing was converted).
    """
    oda = find_oda(oda_path)
    to = to.upper()
    version = version or _FORMAT_VERSION_DEFAULT.get(to, "ACAD2018")

    input_path = Path(input_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    single_file = input_path.is_file()
    if single_file:
        # ODA works on directories — put the file in a temp dir and filter by name
        tmp_in = Path(tempfile.mkdtemp())
        try:
            # Symlink avoids copying large files
            (tmp_in / input_path.name).symlink_to(input_path)
            result = _run_oda(oda, tmp_in, output_dir, version, to,
                              recurse=False, audit=audit,
                              file_filter=input_path.name)
        finally:
            shutil.rmtree(tmp_in, ignore_errors=True)
    else:
        if not input_path.is_dir():
            raise FileNotFoundError(f"Input not found: {input_path}")
        result = _run_oda(oda, input_path, output_dir, version, to,
                          recurse=recurse, audit=audit, file_filter=file_filter)

    # Collect output files
    suffix = "." + to.lower()
    out_files = sorted(output_dir.rglob("*" + suffix))
    return out_files


def _run_oda(oda, input_dir, output_dir, version, output_type,
             recurse, audit, file_filter=None):
    """Execute the ODA CLI and stream its stdout/stderr."""
    cmd = [
        str(oda),
        str(input_dir),
        str(output_dir),
        version,
        output_type,
        "1" if recurse else "0",
        "1" if audit else "0",
    ]
    if file_filter:
        cmd.append(file_filter)

    print(f"Running: {' '.join(cmd)}")
    proc = subprocess.run(cmd, capture_output=False, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"ODA File Converter exited with code {proc.returncode}"
        )
    return proc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert DWG/DXF files using ODA File Converter.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input",
                        help="Single file or folder to convert")
    parser.add_argument("output_dir", nargs="?",
                        default=str(Path.home() / "Documents" / "CAD" / "converted"),
                        help="Output directory (default: ~/Documents/CAD/converted/)")
    parser.add_argument("--to", default="DXF", choices=["DXF", "DWG", "DXB"],
                        help="Output format (default: DXF)")
    parser.add_argument("--version",
                        help="DWG/DXF version, e.g. ACAD2018, R24 (default: format-specific)")
    parser.add_argument("--recurse", action="store_true",
                        help="Recurse into subdirectories")
    parser.add_argument("--no-audit", dest="audit", action="store_false",
                        help="Skip audit/repair pass")
    parser.add_argument("--filter",
                        help='Glob filter, e.g. "*.dwg"')
    parser.add_argument("--oda", metavar="PATH",
                        help="Override ODA File Converter executable path")
    parser.add_argument("--open", dest="open_after", action="store_true",
                        help="Open output directory after conversion")
    args = parser.parse_args()

    try:
        out_files = convert(
            input_path=args.input,
            output_dir=args.output_dir,
            to=args.to,
            version=args.version,
            recurse=args.recurse,
            audit=args.audit,
            oda_path=args.oda,
            file_filter=args.filter,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        sys.exit(2)

    if out_files:
        print(f"\nConverted {len(out_files)} file(s):")
        for f in out_files:
            print(f"  {f}")
    else:
        print("\nNo output files found — check ODA output above for errors.")

    if args.open_after:
        out_dir = Path(args.output_dir).expanduser().resolve()
        system = platform.system()
        if system == "Darwin":
            subprocess.run(["open", str(out_dir)])
        elif system == "Linux":
            subprocess.run(["xdg-open", str(out_dir)])
        elif system == "Windows":
            subprocess.run(["explorer", str(out_dir)])


if __name__ == "__main__":
    main()
