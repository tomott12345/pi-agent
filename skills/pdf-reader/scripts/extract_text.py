#!/usr/bin/env python3
"""Multi-method PDF text extraction with optional metadata output."""

import sys
import argparse


def extract_pymupdf(path: str) -> tuple[str, dict]:
    import fitz  # pymupdf
    doc = fitz.open(path)
    pages = []
    for i, page in enumerate(doc, 1):
        text = page.get_text("text")
        if text.strip():
            pages.append(f"--- Page {i} ---\n{text.strip()}")
    metadata = {
        "page_count": len(doc),
        "title": doc.metadata.get("title", ""),
        "author": doc.metadata.get("author", ""),
        "subject": doc.metadata.get("subject", ""),
        "creator": doc.metadata.get("creator", ""),
        "creation_date": doc.metadata.get("creationDate", ""),
    }
    doc.close()
    return "\n\n".join(pages), metadata


def extract_pdfplumber(path: str) -> tuple[str, dict]:
    import pdfplumber
    pages = []
    page_count = 0
    with pdfplumber.open(path) as pdf:
        page_count = len(pdf.pages)
        for i, page in enumerate(pdf.pages, 1):
            parts = []
            text = page.extract_text()
            if text and text.strip():
                parts.append(text.strip())
            for table in page.extract_tables() or []:
                rows = [
                    "\t".join(str(cell) if cell is not None else "" for cell in row)
                    for row in table
                    if row
                ]
                if rows:
                    parts.append("[TABLE]\n" + "\n".join(rows) + "\n[/TABLE]")
            if parts:
                pages.append(f"--- Page {i} ---\n" + "\n\n".join(parts))
    metadata = {"page_count": page_count}
    return "\n\n".join(pages), metadata


def extract_tesseract(path: str) -> tuple[str, dict]:
    import io
    import fitz
    import pytesseract
    from PIL import Image

    doc = fitz.open(path)
    pages = []
    for i, page in enumerate(doc, 1):
        # Render at 2x scale for better OCR accuracy
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img)
        if text.strip():
            pages.append(f"--- Page {i} ---\n{text.strip()}")
    metadata = {
        "page_count": len(doc),
        "method_note": "OCR via tesseract (scanned document)",
    }
    doc.close()
    return "\n\n".join(pages), metadata


EXTRACTORS = {
    "pymupdf": extract_pymupdf,
    "pdfplumber": extract_pdfplumber,
    "tesseract": extract_tesseract,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-method PDF text extraction")
    parser.add_argument("path", help="Path to PDF file")
    parser.add_argument(
        "--method",
        choices=list(EXTRACTORS),
        default="pymupdf",
        help="Extraction method (default: pymupdf)",
    )
    parser.add_argument(
        "--metadata",
        action="store_true",
        help="Print document metadata header before text",
    )
    args = parser.parse_args()

    try:
        text, metadata = EXTRACTORS[args.method](args.path)
    except ImportError as exc:
        print(f"[{args.method}] missing dependency: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"[{args.method}] extraction failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if not text.strip():
        print(f"[{args.method}] no text extracted", file=sys.stderr)
        sys.exit(1)

    print(f"=== Extraction method: {args.method} ===\n")

    if args.metadata:
        print("--- Document Metadata ---")
        for key, value in metadata.items():
            if value:
                print(f"{key}: {value}")
        print()

    print(text)


if __name__ == "__main__":
    main()
