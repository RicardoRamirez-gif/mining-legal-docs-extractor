# auditoria_extractor/pdf_loader.py

"""
pdf_loader.py
Carga PDFs y decide por página si usar texto directo o OCR.
"""

import os
from typing import List, Dict, Any, Optional

import fitz  # PyMuPDF
from PIL import Image
import io

from .ocr_engine import ocr_image_to_text


class PDFLoader:
    """Carga un PDF y entrega texto página por página, usando OCR si es necesario."""

    def __init__(self, filepath: str):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"El archivo no existe: {filepath}")

        if not filepath.lower().endswith(".pdf"):
            raise ValueError("PDFLoader solo acepta archivos .pdf")

        self.filepath = filepath
        self.doc = fitz.open(filepath)

    def _page_to_image(self, page_index: int, zoom: float = 2.0) -> Image.Image:
        """Renderiza una página del PDF como imagen PIL para OCR."""
        page = self.doc[page_index]
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        return img

    def get_page_text(self, page_index: int, use_ocr_if_empty: bool = True) -> str:
        """
        Retorna el texto de una página:
        - Si la página tiene texto real → usa ese.
        - Si no tiene texto y use_ocr_if_empty=True → aplica OCR sobre la imagen.
        """
        page = self.doc[page_index]
        raw_text = page.get_text("text") or ""
        clean_text = raw_text.strip()

        # Si hay texto "real" (carácteres seleccionables), lo usamos.
        if clean_text:
            return clean_text

        # Si no hay texto, probamos con OCR (caso páginas escaneadas)
        if use_ocr_if_empty:
            img = self._page_to_image(page_index)
            ocr_text = ocr_image_to_text(img)
            return (ocr_text or "").strip()

        return ""

    def iter_pages(self, use_ocr_if_empty: bool = True) -> List[Dict[str, Any]]:
        """
        Recorre todas las páginas y devuelve una lista de dicts:
        [
          { "page": 1, "text": "...", "source": "digital" | "ocr" },
          ...
        ]
        """
        results: List[Dict[str, Any]] = []

        for i in range(len(self.doc)):
            page = self.doc[i]
            raw_text = page.get_text("text") or ""
            clean_text = raw_text.strip()

            if clean_text:
                results.append(
                    {
                        "page_number": i + 1,
                        "text": clean_text,
                        "mode": "digital",  # texto directo del PDF
                    }
                )
            elif use_ocr_if_empty:
                img = self._page_to_image(i)
                ocr_text = ocr_image_to_text(img) or ""
                results.append(
                    {
                        "page_number": i + 1,
                        "text": ocr_text.strip(),
                        "mode": "ocr",  # texto obtenido vía OCR
                    }
                )
            else:
                results.append(
                    {
                        "page_number": i + 1,
                        "text": "",
                        "mode": "empty",
                    }
                )

        return results
