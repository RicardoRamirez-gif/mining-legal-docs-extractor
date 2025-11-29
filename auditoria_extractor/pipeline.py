# auditoria_extractor/pipeline.py

"""
pipeline.py
Orquesta el proceso completo:
- carga el PDF
- obtiene texto por página (digital u OCR)
- aplica parsers para extraer campos legales & coordenadas
"""

from typing import List, Dict, Any
import os

from .pdf_loader import PDFLoader
from .text_parsers import extract_all


def process_pdf(filepath: str) -> List[Dict[str, Any]]:
    """
    Procesa un PDF completo y devuelve una lista de dicts con la información
    extraída por página.

    Cada elemento tiene forma:
    {
        "archivo": "nombre.pdf",
        "pagina": 1,
        "mode": "digital" | "ocr",
        ...campos de extract_all...
    }
    """
    loader = PDFLoader(filepath)
    basename = os.path.basename(filepath)

    page_results: List[Dict[str, Any]] = []

    for page_info in loader.iter_pages(use_ocr_if_empty=True):
        page_text = page_info["text"]
        mode = page_info["mode"]
        page_number = page_info["page_number"]

        if not page_text:
            # página vacía u OCR fallido
            extracted = {}
        else:
            extracted = extract_all(page_text)

        result = {
            "archivo": basename,
            "pagina": page_number,
            "mode": mode,
            **extracted,
        }
        page_results.append(result)

    return page_results
