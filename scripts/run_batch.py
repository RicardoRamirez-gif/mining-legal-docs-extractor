# scripts/run_batch.py

"""
run_batch.py
Ejecuta el pipeline sobre todos los PDFs de una carpeta y
guarda los resultados en un CSV.
"""

import os
import sys
import glob
import json
import pandas as pd

from auditoria_extractor.pipeline import process_pdf
from auditoria_extractor.config import OUTPUT_DIR


def main(input_folder: str):
    pattern = os.path.join(input_folder, "*.pdf")
    files = glob.glob(pattern)

    all_rows = []

    for f in files:
        print(f"[INFO] Procesando {f}...")
        rows = process_pdf(f)
        all_rows.extend(rows)

    if not all_rows:
        print("[WARN] No se encontró información para exportar.")
        return

    # --- CSV ---
    df = pd.DataFrame(all_rows)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    out_path = os.path.join(OUTPUT_DIR, "auditoria_resultados.csv")
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[OK] Resultados guardados en: {out_path}")

    # --- JSON ---
    json_path = os.path.join(OUTPUT_DIR, "auditoria_resultados.json")
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(all_rows, jf, ensure_ascii=False, indent=2)
    print(f"[OK] Resultados JSON guardados en: {json_path}")



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/run_batch.py <carpeta_con_pdfs>")
        sys.exit(1)

    input_dir = sys.argv[1]
    main(input_dir)
