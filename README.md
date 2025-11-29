# Mining Legal Docs Extractor

**Mining Legal Docs Extractor** is a Python-based toolkit designed to automatically extract and structure key information from Chilean mining legal documents (e.g. Conservador de Minas inscriptions, court resolutions, SERNAGEOMIN publications).

The goal of this project is to support **large-scale mining title audits** (1000+ concessions), reducing manual work for lawyers and mining engineers by combining:

- PDF parsing
- OCR for scanned documents
- Rule-based NLP in Spanish
- Domain-specific extraction (ROL Nacional, concession name, coordinates, surface, etc.)

> ⚠️ Real documents used in production are confidential. This repository contains only the **core engine** and examples based on synthetic/dummy data.

---

## ✨ Main Features (planned)

- 📄 **PDF Ingestion**
  - Detect whether a page has an embedded text layer or is a scanned image.
  - Support for multi-page legal documents.

- 🔍 **OCR for Scanned Documents**
  - Integration with **Tesseract OCR** (Spanish language).
  - Basic image preprocessing (grayscale, thresholding, deskew) to improve OCR quality.

- 🧠 **Domain-Specific Text Extraction (Spanish, Chilean mining context)**
  - Extract key fields such as:
    - ROL Nacional
    - Concession name
    - Type (Exploration / Exploitation)
    - Surface (ha)
    - Fojas, number, year, register, Conservador
    - Basic ownership information (titular)
  - Robust regular expressions that handle variability between different Conservadores de Minas and courts.

- 🔢 **Number Parsing in Spanish**
  - Convert textual numbers such as:
    - `“cinco millones doscientos mil” → 5,200,000`
  - Useful for:
    - UTM coordinates expressed in words
    - Surface values described in letters

- 📐 **Coordinate Extraction**
  - Detect UTM coordinate blocks (Norte, Este, huso, datum).
  - Normalize coordinates into a structured format ready for GIS / further analysis.

- 📊 **Structured Output**
  - Export results to:
    - CSV / Excel (`.csv`, `.xlsx`)
  - Typical fields:
    - `archivo`, `pagina`, `rol_nacional`, `nombre_concesion`,
      `titular`, `superficie`, `fojas`, `numero`, `anio`,
      `conservador`, `tipo_fuente`, `confianza`, `texto_bruto`

- 🧩 **Designed for Integration**
  - Engine-first design:
    - The extraction logic lives in a reusable Python package (`auditoria_extractor`).
  - Ready to be later integrated into:
    - A web dashboard (Laravel / PHP, FastAPI, etc.)
    - Internal mining property management systems.

---

## 🏗️ Project Structure

```text
auditoria_extractor/
    pipeline.py      # Orchestrates the full extraction pipeline
    pdf_loader.py    # Opens PDFs and decides between text vs OCR
    ocr_engine.py    # Handles Tesseract OCR and preprocessing
    text_parsers.py  # Regex + rule-based text extraction
    number_parser.py # Textual-number → integer conversion (Spanish)
    config.py        # Global settings (paths, OCR language, etc.)
scripts/
    run_batch.py     # Simple CLI entry point to process a folder
samples/
    README_samples.md  # Notes about sample data (no real legal docs)
outputs/
    (generated CSV/Excel files)
