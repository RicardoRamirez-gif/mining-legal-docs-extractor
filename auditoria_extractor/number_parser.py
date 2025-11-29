"""
number_parser.py
Conversión de números escritos en español a enteros.
Ej: "cinco millones doscientos mil" -> 5200000
"""

import regex as re

UNIDADES = {
    "cero": 0,
    "un": 1,
    "uno": 1,
    "una": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
}

ESPECIALES = {
    "diez": 10,
    "once": 11,
    "doce": 12,
    "trece": 13,
    "catorce": 14,
    "quince": 15,
    "dieciséis": 16,
    "dieciseis": 16,
    "diecisiete": 17,
    "dieciocho": 18,
    "diecinueve": 19,
}

DECENAS = {
    "veinte": 20,
    "treinta": 30,
    "cuarenta": 40,
    "cincuenta": 50,
    "sesenta": 60,
    "setenta": 70,
    "ochenta": 80,
    "noventa": 90,
}

CENTENAS = {
    "cien": 100,
    "ciento": 100,
    "doscientos": 200,
    "trescientos": 300,
    "cuatrocientos": 400,
    "quinientos": 500,
    "seiscientos": 600,
    "setecientos": 700,
    "ochocientos": 800,
    "novecientos": 900,
}

MULTIPLICADORES = {
    "mil": 1_000,
    "millon": 1_000_000,
    "millón": 1_000_000,
    "millones": 1_000_000,
}


def normalize_text_number(text: str) -> str:
    """Limpia tildes y caracteres innecesarios para el parseo."""
    text = text.lower()
    text = text.replace("á", "a").replace("é", "e").replace("í", "i") \
               .replace("ó", "o").replace("ú", "u").replace("ü", "u")
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def text_number_to_int(text: str) -> int | None:
    """
    Convierte un número en palabras en español a entero.
    Soporta expresiones típicas: "cinco millones doscientos mil", "ciento veinte mil",
    "tres mil cuatrocientos cincuenta y dos", etc.
    """
    if not text:
        return None

    text = normalize_text_number(text)
    if not text:
        return None

    tokens = text.split()

    total = 0
    current = 0

    for token in tokens:
        if token in UNIDADES:
            current += UNIDADES[token]
        elif token in ESPECIALES:
            current += ESPECIALES[token]
        elif token in DECENAS:
            current += DECENAS[token]
        elif token in CENTENAS:
            current += CENTENAS[token]
        elif token == "y":
            # Conector, se ignora ("treinta y dos" -> treinta + dos)
            continue
        elif token in MULTIPLICADORES:
            factor = MULTIPLICADORES[token]
            if current == 0:
                current = 1
            current *= factor
            total += current
            current = 0
        else:
            # Palabra desconocida, dejamos el parser "tolerante"
            continue

    total += current

    return total if total != 0 else None


if __name__ == "__main__":
    ejemplos = [
        "cinco millones doscientos mil",
        "ciento veinte mil",
        "tres mil cuatrocientos cincuenta y dos",
        "un millon",
        "doce mil",
        "novecientos noventa y nueve mil novecientos noventa y nueve",
    ]
    for e in ejemplos:
        print(e, "->", text_number_to_int(e))
