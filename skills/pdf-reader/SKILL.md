---
name: pdf-reader
description: |
  Reads and analyzes PDF files using multiple extraction and OCR methodologies
  (pdftotext, PyMuPDF, pdfplumber, tesseract). Parses structure, extracts text and
  tables, then uses the LLM to summarize content, identify key information, and answer
  questions about the document. Use when a user needs to read, analyze, summarize,
  or query any PDF — text-based, scanned, or mixed-content.
license: MIT
compatibility: "Linux/macOS (requires poppler; optional: pymupdf, pdfplumber, tesseract)"
metadata:
  author: "Thomas Ott"
  version: "2.0"
---

# PDF Reader Skill

## Overview

This skill extracts content from PDFs using a cascading set of methods, then uses
the model to summarize, extract structured information, or answer questions.

## Setup

Install the tools you need (each layer is optional but recommended):

```bash
# Layer 1 – fast text extraction (text-based PDFs)
brew install poppler            # provides pdftotext

# Layer 2 – enhanced extraction (complex layouts, embedded fonts)
pip install pymupdf

# Layer 3 – table-aware extraction
pip install pdfplumber

# Layer 4 – OCR for scanned / image-only PDFs
brew install tesseract
pip install pytesseract pillow pymupdf   # pymupdf renders pages for tesseract
```

## Invocation

```
/pdf-reader <path-to-pdf> [question or instruction]
```

Examples:
```
/pdf-reader ./report.pdf
/pdf-reader ./contract.pdf "What are the termination clauses?"
/pdf-reader ./invoice.pdf "Extract all line items and totals as a table."
/pdf-reader ./scan.pdf --method tesseract
```

## Instructions for the model

When this skill is invoked, follow these steps:

### Step 1 – Extract text

Run the extraction script:

```bash
bash scripts/extract.sh <pdf-path> [--method auto|pdftotext|pymupdf|pdfplumber|tesseract] [--metadata]
```

- Default method is `auto`, which tries each method in cascade order and uses the
  first that yields usable text.
- Add `--metadata` to include title, author, page count, and creation date.
- Report which extraction method succeeded and the page count.

### Step 2 – Assess the content

Before analyzing, note:
- **Document type** (report, contract, invoice, academic paper, form, etc.)
- **Approximate length** (pages, sections)
- **Quality of extracted text** (clean, garbled, low-confidence OCR)
- **Presence of tables, figures, or structured data**

If text quality is poor, suggest rerunning with `--method tesseract`.

### Step 3 – Analyze

Perform whichever of the following the user requested. If no specific instruction was
given, run all four:

#### 3a. Summary
Write a concise summary (3–5 sentences) covering:
- What the document is and its purpose
- The main topic or subject matter
- The most important finding, decision, or conclusion

#### 3b. Key information extraction
Extract and present as structured lists:
- **Main sections / headings**
- **Key facts, figures, and statistics**
- **Named entities** (people, organizations, dates, monetary amounts, locations)
- **Tables** (reproduce with headers if present)
- **Action items, recommendations, or next steps**
- **Definitions or terms of note**

#### 3c. Q&A
If the user asked a specific question, answer it using only information from the
document. Cite the page number(s) where the answer was found.

#### 3d. Critical observations
Note any of the following if present:
- Contradictions or inconsistencies in the document
- Missing sections or obviously incomplete content
- Caveats, disclaimers, or limitation statements
- Dates, deadlines, or time-sensitive information

### Step 4 – Large documents

For documents exceeding approximately 8,000 words or 20 pages:
1. Process section by section or in page-range batches.
2. Summarize each section, then produce a combined overall summary.
3. Compile the key-information extraction across all sections into a unified output.

## Error handling

| Condition | Response |
|---|---|
| File not found | Report the path and ask the user to verify it |
| Password-protected PDF | Inform the user; extraction is not possible without the password |
| All methods fail | List which tools are missing and the install commands |
| Low OCR confidence | Warn the user; suggest `--method tesseract` with a higher DPI scan |
| Empty extraction | Suggest the PDF may be image-only; retry with `--method tesseract` |

## Extraction method cascade

| Order | Method | Best for |
|---|---|---|
| 1 | `pdftotext` | Pure text PDFs; fastest |
| 2 | `pymupdf` | Complex layouts, embedded fonts, mixed content |
| 3 | `pdfplumber` | Table-heavy documents |
| 4 | `tesseract` | Scanned or image-only PDFs |
