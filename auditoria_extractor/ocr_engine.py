# auditoria_extractor/ocr_engine.py

"""
ocr_engine.py
Envuelve Tesseract OCR para extraer texto desde imágenes.
"""

from typing import Optional

from PIL import Image
import pytesseract

from .config import OCR_CONFIG


def ocr_image_to_text(image: Image.Image) -> Optional[str]:
    """
    Aplica OCR a una imagen PIL y devuelve el texto reconocido (o None si falla).
    """
    if image is None:
        return None

    # Configurar Tesseract: idioma + psm + oem
    tesseract_config = f'-l {OCR_CONFIG["lang"]} --oem {OCR_CONFIG["oem"]} --psm {OCR_CONFIG["psm"]}'

    try:
        text = pytesseract.image_to_string(image, config=tesseract_config)
        return text
    except Exception as e:
        # En una versión más avanzada, podríamos loguear este error
        print(f"[WARN] Error en OCR: {e}")
        return None
