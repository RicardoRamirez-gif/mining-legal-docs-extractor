# auditoria_extractor/text_parsers.py

"""
text_parsers.py
Funciones para extraer campos relevantes de textos legales mineros
(obtenidos desde PDFs del Conservador de Minas via texto directo u OCR).
"""

from __future__ import annotations

import regex as re
from typing import Any, Dict, List, Optional, Tuple

from .number_parser import text_number_to_int


# -----------------------------
# Utilidades generales
# -----------------------------

def _normalize_spaces(text: str) -> str:
    """Colapsa espacios múltiples y normaliza saltos de línea simples."""
    # Reemplaza saltos de línea por espacios en algunas búsquedas
    return re.sub(r"\s+", " ", text, flags=re.UNICODE).strip()


# -----------------------------
# Parsers de la carátula (certificado Conservador)
# -----------------------------

def extract_conservador(text: str) -> Optional[str]:
    """
    Intenta extraer el nombre del Conservador de Minas, por ejemplo:
    'CONSERVADOR DE MINAS DE VALPARAÍSO'
    """
    # Usamos versión con y sin tildes
    patrones = [
        r"CONSERVADOR(?:A)? DE MINAS DE\s+([A-ZÁÉÍÓÚÜÑ ]+)",
        r"CONSERVADOR(?:A)? DE MINAS\s+DE\s+([A-ZÁÉÍÓÚÜÑ ]+)",
    ]

    for pat in patrones:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            lugar = m.group(1).strip()
            # Normalizamos capitalización básica
            lugar_norm = lugar.title()
            return f"Conservador de Minas de {lugar_norm}"
    return None


def extract_nombre_concesion(text: str) -> Optional[str]:
    """
    Busca patrones tipo:
    INSCRIPCION DE MENSURA "CURAUMA 2, 1 AL 15"
    MENSURA "CURAUMA 2, 1 AL 15"
    CONCESIÓN MINERA DE EXPLOTACIÓN CURAUMA 2, 1 AL 15
    """
    # Unificamos espacios
    norm = _normalize_spaces(text)

    # Patrones probables
    patrones = [
        r"INSCRIPCION DE MENSURA\s+\"?([A-Z0-9 ,/º\-]+)\"?",
        r"MENSURA\s+\"?([A-Z0-9 ,/º\-]+)\"?",
        r"CONCESI[ÓO]N MINERA DE EXPLOTACI[ÓO]N\s+\"?([A-Z0-9 ,/º\-]+)\"?",
    ]

    for pat in patrones:
        m = re.search(pat, norm, flags=re.IGNORECASE)
        if m:
            nombre = m.group(1).strip(" \"")
            # evitamos capturar texto genérico muy corto
            if len(nombre) >= 4:
                return nombre.title()

    # fallback: a veces el nombre va entre comillas solo
    m2 = re.search(r"\"([A-Z0-9 ,/º\-]+)\"", norm)
    if m2 and len(m2.group(1)) >= 4:
        return m2.group(1).title()

    return None


def extract_rol_nacional(text: str) -> Optional[str]:
    """
    Extrae el Rol Nacional, p.ej.:
    'ROL NACIONAL N° 02201-01234-3'
    'ROL NACIONAL Nº 2201-1234-3'
    """
    patrones = [
        r"ROL\s+NACIONAL\s+N[°º]\s*([0-9\.\-–]+)",
        r"ROL\s+NACIONAL\s+([0-9\.\-–]+)",
    ]

    for pat in patrones:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def extract_fojas_numero_anio(text: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """
    Extrae:
    - fojas (en letras o números)
    - número de inscripción (en letras o números)
    - año (en letras o números)

    Ejemplos:
    'ROLANTE A FOJAS SIETE VUELTA NUMERO CINCO DEL REGISTRO... DEL AÑO DOS MIL VEINTE'
    """
    norm = _normalize_spaces(text)

    # FOJAS
    fojas_val: Optional[int] = None
    m_fojas_text = re.search(r"FOJAS\s+([A-ZÁÉÍÓÚÜÑ ]+?)(?:\s+NUMERO|\s+N[°º]|\s+DEL\s+REGISTRO)", norm, flags=re.IGNORECASE)
    if m_fojas_text:
        palabra_fojas = m_fojas_text.group(1).strip()
        # Quitamos palabras tipo 'VUELTA'
        palabra_fojas = re.sub(r"\bVUELTA\b", "", palabra_fojas, flags=re.IGNORECASE).strip()
        if palabra_fojas:
            fojas_val = text_number_to_int(palabra_fojas)
    else:
        # backup: FOJAS <número>
        m_fojas_num = re.search(r"FOJAS\s+([0-9\.]+)", norm, flags=re.IGNORECASE)
        if m_fojas_num:
            try:
                fojas_val = int(m_fojas_num.group(1).replace(".", ""))
            except ValueError:
                fojas_val = None

    # NÚMERO INSCRIPCIÓN
    num_val: Optional[int] = None
    m_num_text = re.search(r"NUMERO\s+([A-ZÁÉÍÓÚÜÑ ]+?)(?:\s+DEL\s+REGISTRO|\s+DEL\s+A[NÑ]O|\s+DEL\s+AÑO)", norm, flags=re.IGNORECASE)
    if m_num_text:
        palabra_num = m_num_text.group(1).strip()
        num_val = text_number_to_int(palabra_num)
    else:
        m_num_num = re.search(r"NUMERO\s+([0-9\.]+)", norm, flags=re.IGNORECASE)
        if m_num_num:
            try:
                num_val = int(m_num_num.group(1).replace(".", ""))
            except ValueError:
                num_val = None

    # AÑO
    anio_val: Optional[int] = None
    # primero en letras
    m_anio_text = re.search(
        r"DEL\s+A[NÑ]O\s+([A-ZÁÉÍÓÚÜÑ ]+?)(?:[\,\.;]|$)",
        norm,
        flags=re.IGNORECASE,
    )
    if m_anio_text:
        palabra_anio = m_anio_text.group(1).strip()
        anio_val = text_number_to_int(palabra_anio)
    else:
        m_anio_num = re.search(r"DEL\s+A[NÑ]O\s+([0-9]{4})", norm, flags=re.IGNORECASE)
        if m_anio_num:
            try:
                anio_val = int(m_anio_num.group(1))
            except ValueError:
                anio_val = None

    return fojas_val, num_val, anio_val


def extract_fecha_texto(text: str) -> Optional[str]:
    """
    Extrae la fecha en texto, por ejemplo:
    'TREINTA DE DICIEMBRE DEL AÑO DOS MIL VEINTE'
    Por ahora la devolvemos como string crudo.
    """
    # Permitimos día en letras, mes en letras, resto libre
    meses = (
        "ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE"
    )

    pat = rf"([A-ZÁÉÍÓÚÜÑ ]+?\s+DE\s+(?:{meses})\s+DEL\s+A[NÑ]O\s+[A-ZÁÉÍÓÚÜÑ ]+)"
    m = re.search(pat, text, flags=re.IGNORECASE)
    if m:
        return _normalize_spaces(m.group(1)).title()
    return None


# -----------------------------
# Parsers de coordenadas UTM
# -----------------------------

def extract_utm_from_numbers(text: str) -> List[Dict[str, Any]]:
    """
    Extrae coordenadas UTM cuando están como números, p.ej.:
    N=6.333.850,00  E=313.500,00
    Norte 6.333.850 Este 313.500
    """
    results: List[Dict[str, Any]] = []

    norm = _normalize_spaces(text)

    patrones = [
        r"(N[= ]\s*([0-9\.\,]+).{0,20}E[= ]\s*([0-9\.\,]+))",
        r"(NORTE\s+([0-9\.\,]+).{0,20}(ESTE|E)\s+([0-9\.\,]+))",
    ]

    for pat in patrones:
        for m in re.finditer(pat, norm, flags=re.IGNORECASE):
            # Dependiendo del patrón, tomamos grupos
            nums = [g for g in m.groups()[1:] if g is not None]
            if len(nums) >= 2:
                n_raw, e_raw = nums[0], nums[1]
                try:
                    n_val = float(n_raw.replace(".", "").replace(",", "."))
                    e_val = float(e_raw.replace(".", "").replace(",", "."))
                    results.append({"norte": n_val, "este": e_val, "source": "digits"})
                except ValueError:
                    continue

    return results


def extract_utm_from_words(text: str) -> List[Dict[str, Any]]:
    """
    Extrae coordenadas UTM cuando están en letras, p.ej.:
    'Norte seis millones trescientos treinta y tres mil ochocientos cincuenta coma cero cero metros,
     Este dos millones ciento veinte mil coma cero cero metros'
    """
    results: List[Dict[str, Any]] = []

    norm = _normalize_spaces(text)

    # Patrón simplificado:
    # - Busca 'NORTE <palabras> COMA ... (ESTE|E) <palabras> COMA'
    pat = r"NORTE\s+([a-záéíóúüñ\s]+?)\s+COMA.*?(?:ESTE|E)\s+([a-záéíóúüñ\s]+?)\s+COMA"

    for m in re.finditer(pat, norm, flags=re.IGNORECASE | re.DOTALL):
        norte_txt = m.group(1).strip()
        este_txt = m.group(2).strip()

        n_val = text_number_to_int(norte_txt)
        e_val = text_number_to_int(este_txt)

        if n_val is not None and e_val is not None:
            results.append(
                {
                    "norte": float(n_val),
                    "este": float(e_val),
                    "source": "words",
                }
            )

    return results



def extract_utm_vertices(text: str) -> List[Dict[str, Any]]:
    """Combina extracción numérica y en letras."""
    verts: List[Dict[str, Any]] = []
    verts.extend(extract_utm_from_numbers(text))
    verts.extend(extract_utm_from_words(text))
    return verts


# -----------------------------
# Wrapper principal
# -----------------------------

def extract_all(text: str) -> Dict[str, Any]:
    """
    Parser principal: dado el texto de una página, intenta extraer
    todos los campos relevantes disponibles.
    """
    data: Dict[str, Any] = {}

    # Intentamos siempre, aunque algunas cosas solo estarán en la carátula
    data["rol_nacional"] = extract_rol_nacional(text)
    data["nombre_concesion"] = extract_nombre_concesion(text)

    fojas, num_insc, anio = extract_fojas_numero_anio(text)
    data["fojas"] = fojas
    data["numero_inscripcion"] = num_insc
    data["anio_inscripcion"] = anio

    data["conservador"] = extract_conservador(text)
    data["fecha_texto"] = extract_fecha_texto(text)

    data["utm_vertices"] = extract_utm_vertices(text)

    return data
