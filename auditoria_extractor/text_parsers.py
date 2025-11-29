"""
text_parsers.py
Funciones para extraer campos relevantes desde el texto plano
de inscripciones mineras chilenas (inscripciones, publicaciones, etc.).
"""

import regex as re
from typing import Any, Dict, List, Optional
from .number_parser import text_number_to_int


MESES = (
    "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|"
    "octubre|noviembre|diciembre"
)


def extract_basic_inscription_fields(text: str) -> Dict[str, Any]:
    """
    Extrae campos básicos típicos de una inscripción:
    - ROL Nacional
    - Nombre de la concesión
    - Fojas, número, año
    - Conservador
    - Fecha (si aparece en encabezado)
    """

    # ROL Nacional (ej: ROL NACIONAL N° 02201-0380-3)
    rol = re.search(
        r"ROL\s+(?:NAC(?:IONAL)?\s*)?N?[°º]?\s*([\d\.\-\/]+)",
        text,
        flags=re.IGNORECASE
    )

    # Nombre de la concesión (muy genérico, luego lo afinamos con ejemplos reales)
    nombre = re.search(
        r"concesi[oó]n(?:\s+de\s+[a-záéíóúñ]+)?(?:\s+denominada)?\s+[\"“']?([A-Z0-9\s\-]+)[\"”']?",
        text,
        flags=re.IGNORECASE
    )

    # Fojas, número, año (ej: "a fojas 123 número 456 del año 2010")
    fojas = re.search(r"fojas\s+(\d+)", text, flags=re.IGNORECASE)
    numero = re.search(r"n[uú]mero\s+(\d+)", text, flags=re.IGNORECASE)
    anio = re.search(r"(?:a[nñ]o|del a[nñ]o)\s+(\d{4})", text, flags=re.IGNORECASE)

    # Conservador (ej: "Conservador de Minas de Antofagasta")
    conservador = re.search(
        r"Conservador(?: de Minas)? de\s+([A-Za-zÁÉÍÓÚÑ\s]+)",
        text,
        flags=re.IGNORECASE
    )

    # Fecha tipo: "Antofagasta, 15 de marzo de 2010"
    fecha = re.search(
        rf"(\d{{1,2}}\s+de\s+(?:{MESES})\s+de\s+\d{{4}})",
        text,
        flags=re.IGNORECASE
    )

    return {
        "rol_nacional": rol.group(1).strip() if rol else None,
        "nombre_concesion": nombre.group(1).strip() if nombre else None,
        "fojas": int(fojas.group(1)) if fojas else None,
        "numero_inscripcion": int(numero.group(1)) if numero else None,
        "anio_inscripcion": int(anio.group(1)) if anio else None,
        "conservador": conservador.group(1).strip() if conservador else None,
        "fecha_texto": fecha.group(1).strip() if fecha else None,
    }


def _limpiar_numero_coord(cadena: str) -> Optional[float]:
    """
    Limpia un número de coordenadas:
    - Elimina puntos de miles.
    - Convierte coma decimal en punto.
    - Devuelve float o None.
    """
    if not cadena:
        return None
    s = cadena.strip()
    s = s.replace(".", "").replace(" ", "")
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def extract_utm_coordinates(text: str) -> List[Dict[str, Any]]:
    """
    Extrae bloques de coordenadas UTM típicos:

    Ejemplos que intentará capturar:
      - "Norte: 7.012.345 m Este: 312.456 m Huso 19 Sur Datum PSAD-56"
      - "N 7012345 E 312456 Huso 19 Datum WGS84"

    Retorna una lista de vértices (no asume aún polígono cerrado).
    """

    coords: List[Dict[str, Any]] = []

    # Patrón general para pares Norte/Este
    # Buscamos frases donde aparezcan ambas componentes relativamente cerca.
    patron_bloque = re.compile(
        r"""
        (?:
            (?:NORTE|N)\s*[:=]?\s*([\d\.\,]{5,})   # valor norte
            .*?
            (?:ESTE|E)\s*[:=]?\s*([\d\.\,]{5,})    # valor este
        )
        |
        (?:
            (?:ESTE|E)\s*[:=]?\s*([\d\.\,]{5,})    # valor este
            .*?
            (?:NORTE|N)\s*[:=]?\s*([\d\.\,]{5,})   # valor norte
        )
        """,
        flags=re.IGNORECASE | re.DOTALL | re.VERBOSE,
    )

    # Huso
    patron_huso = re.compile(
        r"huso\s+(\d{1,2})",
        flags=re.IGNORECASE
    )

    # Datum (muy genérico: PSAD-56, WGS84, SIRGAS, etc.)
    patron_datum = re.compile(
        r"(PSAD-?56|WGS-?84|SIRGAS(?:\s+2000)?)",
        flags=re.IGNORECASE
    )

    # Buscamos todos los bloques donde aparezcan N/E
    for match in patron_bloque.finditer(text):
        g = match.groups()

        # El patrón tiene 4 grupos opcionales:
        # caso 1: norte, este, None, None
        # caso 2: None, None, este, norte
        if g[0] and g[1]:
            norte_raw, este_raw = g[0], g[1]
        elif g[2] and g[3]:
            este_raw, norte_raw = g[2], g[3]
        else:
            continue

        norte = _limpiar_numero_coord(norte_raw)
        este = _limpiar_numero_coord(este_raw)

        # Buscamos huso y datum cerca del bloque encontrado
        texto_local = text[match.start(): match.end() + 200]  # pequeña ventana después

        huso_m = patron_huso.search(texto_local)
        datum_m = patron_datum.search(texto_local)

        huso = int(huso_m.group(1)) if huso_m else None
        datum = datum_m.group(1).upper().replace(" ", "") if datum_m else None

        coords.append(
            {
                "norte": norte,
                "este": este,
                "huso": huso,
                "datum": datum,
                "fuente": "numerico",
            }
        )

    return coords


def extract_all(text: str) -> Dict[str, Any]:
    """
    Función de alto nivel:
    - Extrae campos básicos de inscripción
    - Extrae coordenadas UTM
    (Más adelante podemos agregar superficie, titular, etc.)
    """
    insc = extract_basic_inscription_fields(text)
    utm = extract_utm_coordinates(text)

    return {
        **insc,
        "utm_vertices": utm,
    }
