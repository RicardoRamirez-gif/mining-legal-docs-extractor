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

def extract_titular(text: str) -> Optional[str]:
    """
    Extrae el titular de la inscripción.
    Se prioriza:
    - Carátula tipo: INSCRIPCION DE MENSURA "X" DE <TITULAR>, INSCRITA EL...
    - Expresiones: A NOMBRE DE <...>, DE PROPIEDAD DE <...>, TITULAR <...>.
    Intentamos ser más precisos y evitar párrafos largos.
    """
    norm = _normalize_spaces(text)

    candidatos: List[str] = []

    # 1) Patrón típico de carátula: INSCRIPCION DE MENSURA ... DE <TITULAR>, INSCRITA EL ...
    pat_caratula = (
        r"INSCRIPCION DE MENSURA\s+\"[A-Z0-9 ,/º\-]+\"\s+DE\s+"
        r"([A-ZÁÉÍÓÚÜÑ0-9 \.&\-]+?)(?:,|\sINSCRITA|\sROLANTE|\sDEL\s+AÑO|\.)"
    )
    for m in re.finditer(pat_caratula, norm, flags=re.IGNORECASE):
        candidatos.append(m.group(1).strip())

    # 2) A NOMBRE DE <...>
    pat_nombre = r"A\s+NOMBRE\s+DE\s+([A-ZÁÉÍÓÚÜÑ0-9 \.&\-]+?)(?:,|\sINSCRITA|\sROLANTE|\sDEL\s+AÑO|\.)"
    for m in re.finditer(pat_nombre, norm, flags=re.IGNORECASE):
        candidatos.append(m.group(1).strip())

    # 3) DE PROPIEDAD DE <...>
    pat_prop = r"DE\s+PROPIEDAD\s+DE\s+([A-ZÁÉÍÓÚÜÑ0-9 \.&\-]+?)(?:,|\sINSCRITA|\sROLANTE|\sDEL\s+AÑO|\.)"
    for m in re.finditer(pat_prop, norm, flags=re.IGNORECASE):
        candidatos.append(m.group(1).strip())

    # 4) TITULAR <...>
    pat_tit = r"TITULAR\s+([A-ZÁÉÍÓÚÜÑ0-9 \.&\-]+?)(?:,|\sINSCRITA|\sROLANTE|\sDEL\s+AÑO|\.)"
    for m in re.finditer(pat_tit, norm, flags=re.IGNORECASE):
        candidatos.append(m.group(1).strip())

    if not candidatos:
        return None

    # Filtro de calidad de candidatos
    def es_titular_valido(s: str) -> bool:
        s_clean = s.strip(" ,.;")
        if not s_clean:
            return False

        palabras = s_clean.split()
        # Evitar cosas demasiado cortas o demasiado largas
        if len(palabras) < 2 or len(palabras) > 8:
            return False

        # Evitar que empiece con palabras que no son nombre/razón social
        primeras = {"SE", "LA", "EL", "ENTRE", "CINCUENTA", "CIENTO", "CERO", "INTERES"}
        if palabras[0].upper() in primeras:
            return False

        return True

    def score_titular(s: str) -> int:
        """Más puntaje si parece razón social."""
        s_u = s.upper()
        score = 0
        if any(tag in s_u for tag in ["S.A", "LTDA", "LIMITADA", "SPA", "S.P.A"]):
            score += 3
        if any(tag in s_u for tag in ["MINERA", "COMPAÑÍA", "COMPANIA", "SOCIEDAD"]):
            score += 2
        # Bonus por 2+ palabras
        if len(s.split()) >= 2:
            score += 1
        return score

    candidatos_filtrados = [c.strip(" ,.;") for c in candidatos if es_titular_valido(c)]

    if not candidatos_filtrados:
        return None

    # Elegimos el mejor según score
    candidatos_filtrados.sort(key=score_titular, reverse=True)
    titular = candidatos_filtrados[0]
    return titular.title()



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


def extract_fojas_numero_anio(text: str) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[str]]:
    """
    Extrae:
    - fojas (en letras o números)
    - número de inscripción (en letras o números)
    - año (en letras o números)
    - indicador de 'vuelta' (fojas_vuelta): 'vta' o ''

    Ejemplos:
    'ROLANTE A FOJAS SIETE VUELTA NUMERO CINCO DEL REGISTRO... DEL AÑO DOS MIL VEINTE'
    """
    norm = _normalize_spaces(text)

    # ------------------------------------
    # Detectar si dice VUELTA / VTA / VTA.
    # ------------------------------------
    fojas_vuelta: Optional[str] = ""

    # Tomamos un trozo alrededor de la palabra FOJAS
    m_fojas_ctx = re.search(r"FOJAS\s+(.{0,80})", norm, flags=re.IGNORECASE)
    if m_fojas_ctx:
        ctx = m_fojas_ctx.group(1)
        if re.search(r"\b(VTA\.?|VUELTA)\b", ctx, flags=re.IGNORECASE):
            fojas_vuelta = "vta"

    # ------------------------------------
    # FOJAS (número)
    # ------------------------------------
    fojas_val: Optional[int] = None
    m_fojas_text = re.search(
        r"FOJAS\s+([A-ZÁÉÍÓÚÜÑ ]+?)(?:\s+VTA\.?|\s+VUELTA|\s+NUMERO|\s+N[°º]|\s+DEL\s+REGISTRO)",
        norm,
        flags=re.IGNORECASE,
    )
    if m_fojas_text:
        palabra_fojas = m_fojas_text.group(1).strip()
        # Quitamos palabras tipo 'VUELTA' si quedara por error
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

    # ------------------------------------
    # NÚMERO INSCRIPCIÓN
    # ------------------------------------
    num_val: Optional[int] = None
    m_num_text = re.search(
        r"NUMERO\s+([A-ZÁÉÍÓÚÜÑ ]+?)(?:\s+DEL\s+REGISTRO|\s+DEL\s+A[NÑ]O|\s+DEL\s+AÑO)",
        norm,
        flags=re.IGNORECASE,
    )
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

    # ------------------------------------
    # AÑO
    # ------------------------------------
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

    return fojas_val, num_val, anio_val, fojas_vuelta


def extract_fojas_vuelta(text: str) -> str:
    """
    Devuelve 'vta' si el texto menciona que la fojas es vuelta.
    Si no menciona nada, devuelve ''.
    """
    norm = _normalize_spaces(text)

    # Casos reconocidos: VUELTA, VTA, VTA.
    if re.search(r"FOJAS\s+[A-ZÁÉÍÓÚÜÑ0-9 \.,º\-]*(VUELTA|VTA\.?)", norm, flags=re.IGNORECASE):
        return "vta"

    return ""


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

def classify_utm_match(text: str, start_idx: int, end_idx: int) -> str:
    """
    Mira el contexto alrededor del match (±80 caracteres) y trata de
    clasificar el tipo de coordenada: 'hito_mensura', 'vertice', 'lindero', etc.
    """
    window_size = 80
    inicio = max(0, start_idx - window_size)
    fin = min(len(text), end_idx + window_size)
    contexto = text[inicio:fin].upper()

    if "HITO DE MENSURA" in contexto or "H.M." in contexto:
        return "hito_mensura"
    if "VERTICE" in contexto or "VÉRTICE" in contexto or "V-1" in contexto or "V-2" in contexto:
        return "vertice"
    if "LINDERO" in contexto:
        return "lindero"
    return "desconocido"

# -----------------------------
# Parsers de cédulas, domicilios, juzgado, causa rol
# -----------------------------

def extract_cedulas_identidad(text: str) -> List[str]:
    """
    Extrae posibles Cédulas/RUT desde el texto.
    Ejemplos:
    - "CEDULA NACIONAL DE IDENTIDAD N° 12.345.678-9"
    - "RUT 12.345.678-9"
    """
    resultados: List[str] = []
    # Trabajamos sobre el texto tal cual (respetando puntos y guiones)
    patrones = [
        r"CEDULA(?: NACIONAL)? DE IDENTIDAD\s+N[°º]?\s*([\d\.\-kK]+)",
        r"CEDULA(?: NACIONAL)? DE IDENTIDAD\s+NUMERO\s*([\d\.\-kK]+)",
        r"RUT\s*([\d\.\-kK]+)",
    ]

    for pat in patrones:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            ci = m.group(1).strip()
            if ci and ci not in resultados:
                resultados.append(ci)

    return resultados


def extract_domicilios(text: str) -> List[str]:
    """
    Extrae posibles domicilios, buscando frases tipo:
    - 'domiciliado en Avenida ...'
    - 'domiciliada en calle ...'
    - 'con domicilio en ...'
    """
    resultados: List[str] = []
    norm = _normalize_spaces(text)

    patrones = [
        r"DOMICILIAD[OA]\s+EN\s+([^\,\.;]+)",
        r"CON\s+DOMICILIO\s+EN\s+([^\,\.;]+)",
        r"DOMICILIO\s+EN\s+([^\,\.;]+)",
    ]

    for pat in patrones:
        for m in re.finditer(pat, norm, flags=re.IGNORECASE):
            frag = m.group(1).strip()
            if frag:
                # Normalizamos un poco la dirección (capitalización básica)
                dom = frag.strip()
                # Evitamos duplicados
                if dom not in resultados:
                    resultados.append(dom)

    return resultados


def extract_juzgados(text: str) -> List[str]:
    """
    Extrae nombres de juzgados, p.ej.:
    - 'Juzgado de Letras de Valparaíso'
    - 'Segundo Juzgado Civil de Santiago'
    """
    resultados: List[str] = []
    norm = _normalize_spaces(text)

    # Tomamos desde 'JUZGADO' hasta el próximo signo fuerte o salto lógico
    pat = r"(JUZGADO\s+[A-ZÁÉÍÓÚÜÑ0-9\s\-DELCIVILRA\.]+)"
    for m in re.finditer(pat, norm, flags=re.IGNORECASE):
        j = m.group(1).strip()
        if j and j not in resultados:
            resultados.append(j)

    return resultados


def extract_causas_rol(text: str) -> List[str]:
    """
    Extrae posibles 'causa rol', p.ej.:
    - 'causa Rol N° C-1234-2020'
    - 'causa rol 1234-2020'
    Sólo consideramos cuando aparece la palabra 'causa'.
    """
    resultados: List[str] = []
    norm = _normalize_spaces(text)

    patrones = [
        r"CAUSA\s+ROL\s+N[°º]?\s*([A-Z0-9\.\-\/]+)",
        r"CAUSA\s+ROL\s+([A-Z0-9\.\-\/]+)",
    ]

    for pat in patrones:
        for m in re.finditer(pat, norm, flags=re.IGNORECASE):
            rol = m.group(1).strip()
            if rol and rol not in resultados:
                resultados.append(rol)

    return resultados


# -----------------------------
# Parsers de coordenadas UTM
# -----------------------------

def extract_utm_from_numbers(text: str) -> List[Dict[str, Any]]:
    """
    Extrae coordenadas UTM cuando están como números, p.ej.:
    N=6.333.850,00  E=258.350,00
    Norte 6.333.850 metros, Este 258.350 metros
    Coordenadas U.T.M. Norte 6.333.850 Este 258.350
    """
    results: List[Dict[str, Any]] = []

    norm = _normalize_spaces(text)

    patrones = [
        # Caso genérico: Norte primero, luego Este
        r"(?:N(?:ORTE)?)[\s:=]*"
        r"(?P<norte>[0-9\.\,]+)"
        r"(?:\s*(?:METROS|M))?"
        r".{0,80}?"   # ← dejamos espacio para 'metros', 'UTM', etc.
        r"(?:E(?:STE)?)[\s:=]*"
        r"(?P<este>[0-9\.\,]+)",

        # Variante: Este primero, luego Norte (por si acaso)
        r"(?:E(?:STE)?)[\s:=]*"
        r"(?P<este>[0-9\.\,]+)"
        r"(?:\s*(?:METROS|M))?"
        r".{0,80}?"
        r"(?:N(?:ORTE)?)[\s:=]*"
        r"(?P<norte>[0-9\.\,]+)",
    ]

    for pat in patrones:
        for m in re.finditer(pat, norm, flags=re.IGNORECASE):
            n_raw = m.groupdict().get("norte")
            e_raw = m.groupdict().get("este")
            if not n_raw or not e_raw:
                continue
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

    # Campos "clásicos"
    data["rol_nacional"] = extract_rol_nacional(text)
    data["nombre_concesion"] = extract_nombre_concesion(text)

    fojas, num_insc, anio, fojas_vta = extract_fojas_numero_anio(text)

    data["fojas"] = fojas
    data["fojas_vuelta"] = fojas_vta   # 👈 AÑADIDO
    data["numero_inscripcion"] = num_insc
    data["anio_inscripcion"] = anio

    data["conservador"] = extract_conservador(text)
    data["fecha_texto"] = extract_fecha_texto(text)

    
    data["titular"] = extract_titular(text)

    data["utm_vertices"] = extract_utm_vertices(text)

    # 🔹 NUEVOS CAMPOS
    data["cedulas_identidad"] = extract_cedulas_identidad(text)
    data["domicilios"] = extract_domicilios(text)
    data["juzgados"] = extract_juzgados(text)
    data["causas_rol"] = extract_causas_rol(text)

    # (aquí ya estabas llenando "titular" en tu versión actual;
    # si lo tienes en otra función, simplemente asegúrate de seguirlo poniendo aquí)

    return data


