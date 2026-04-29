#!/usr/bin/env bash
# PDF Reader skill – multi-method extraction entry point
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
METHOD="auto"
SHOW_METADATA=""

usage() {
  printf 'Usage: extract.sh <pdf-path> [--method auto|pdftotext|pymupdf|pdfplumber|tesseract] [--metadata]\n' >&2
  exit 1
}

PDF_PATH=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --method)   METHOD="$2"; shift 2 ;;
    --metadata) SHOW_METADATA="--metadata"; shift ;;
    --help|-h)  usage ;;
    -*)         printf 'Unknown option: %s\n' "$1" >&2; usage ;;
    *)          PDF_PATH="$1"; shift ;;
  esac
done

[[ -z "$PDF_PATH" ]] && usage
[[ ! -f "$PDF_PATH" ]] && { printf 'Error: File not found: %s\n' "$PDF_PATH" >&2; exit 2; }

ABS_PATH="$(cd "$(dirname "$PDF_PATH")" && pwd)/$(basename "$PDF_PATH")"

try_pdftotext() {
  command -v pdftotext >/dev/null 2>&1 || { printf '[pdftotext] not installed\n' >&2; return 1; }
  local text
  text=$(pdftotext -layout "$ABS_PATH" - 2>/dev/null) || { printf '[pdftotext] extraction failed\n' >&2; return 1; }
  [[ -z "$(printf '%s' "$text" | tr -d '[:space:]')" ]] && {
    printf '[pdftotext] no text found — PDF may be scanned\n' >&2
    return 1
  }
  printf '=== Extraction method: pdftotext ===\n\n%s\n' "$text"
}

try_python() {
  local method="$1"
  command -v python3 >/dev/null 2>&1 || { printf '[python3] not installed\n' >&2; return 1; }
  # shellcheck disable=SC2086
  python3 "$SCRIPT_DIR/extract_text.py" "$ABS_PATH" --method "$method" $SHOW_METADATA
}

run_auto() {
  local err_log
  err_log=$(mktemp)
  trap 'rm -f "$err_log"' RETURN

  if try_pdftotext 2>"$err_log"; then return 0; fi
  if try_python pymupdf 2>"$err_log"; then return 0; fi
  if try_python pdfplumber 2>"$err_log"; then return 0; fi
  if try_python tesseract 2>"$err_log"; then return 0; fi

  printf 'Error: All extraction methods failed.\n' >&2
  printf 'Last error: %s\n' "$(cat "$err_log")" >&2
  printf '\nInstall missing tools:\n' >&2
  printf '  brew install poppler tesseract\n' >&2
  printf '  pip install pymupdf pdfplumber pytesseract pillow\n' >&2
  return 3
}

case "$METHOD" in
  pdftotext)  try_pdftotext ;;
  pymupdf)    try_python pymupdf ;;
  pdfplumber) try_python pdfplumber ;;
  tesseract)  try_python tesseract ;;
  auto)       run_auto ;;
  *)          printf 'Unknown method: %s\n' "$METHOD" >&2; usage ;;
esac
