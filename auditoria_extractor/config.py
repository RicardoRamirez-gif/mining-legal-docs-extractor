# auditoria_extractor/config.py

"""
config.py
Configuración central del extractor de documentos mineros.
"""

import os

# Carpeta base del proyecto (mining-legal-docs-extractor/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Carpeta donde se guardarán resultados (CSV, logs, etc.)
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# Carpeta con PDFs de prueba
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")

# Extensiones de archivo que aceptamos como entrada
VALID_INPUT_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".tiff"]

# Configuración del motor OCR (Tesseract)
OCR_CONFIG = {
    "lang": "spa",   # idioma: español (puedes agregar "eng+spa" si quieres bilingüe)
    "psm": 6,        # page segmentation mode (6 = bloques de texto)
    "oem": 3,        # OCR Engine Mode (3 = default)
}

# Opcional: configuración simple de logging
LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG / INFO / WARNING / ERROR
}
