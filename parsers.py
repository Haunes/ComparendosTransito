from __future__ import annotations
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

Record = Dict[str, Any]

DATE_PATTERNS = ["%d/%m/%Y", "%d/%m/%y"]

def normalize_date_or_keep(text: str) -> str:
    """Convierte a YYYY-MM-DD si 'text' es fecha dd/mm/(yy|yyyy). Si no, devuelve el literal tal cual."""
    t = (text or "").strip()
    if not t:
        return ""
    for fmt in DATE_PATTERNS:
        try:
            dt = datetime.strptime(t, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return t  # puede ser 'No aplica', 'En proceso notificación', etc.

def normalize_plate(text: str) -> str:
    """Placa upper sin espacios internos."""
    return re.sub(r"\s+", "", text or "").upper()

def ensure_record(num: str, imp: str, notif: str, placa: str, plataforma: str) -> Record:
    return {
        "numero_comparendo": (num or "").strip(),
        "fecha_imposicion": normalize_date_or_keep(imp),
        "fecha_notificacion": normalize_date_or_keep(notif),
        "placa": normalize_plate(placa),
        "plataforma": plataforma,
    }

# --------------------------------------------------------------------
# SIMIT
# --------------------------------------------------------------------

_ALNUM_INLINE_RE = re.compile(r"[A-Za-z0-9]+")

def _extract_inline_token_with_min_digits(line: str, min_digits: int = 11) -> str:
    """
    Busca en la LÍNEA ORIGINAL (sin quitar espacios/guiones/etc.) el primer token
    contiguo [A-Za-z0-9]+ que contenga al menos `min_digits` dígitos.
    Evita que se peguen trozos de fecha/placa/ciudad.
    """
    if not line:
        return ""
    for m in _ALNUM_INLINE_RE.finditer(line):
        tok = m.group(0)
        if sum(ch.isdigit() for ch in tok) >= min_digits:
            return tok
    return ""
_ALNUM_TOKEN_RE = re.compile(r"[A-Za-z0-9]{11,}")  # candidatos; luego filtramos por dígitos

def _extract_comparendo_token(line: str) -> str:
    """
    Extrae el primer token 'alfa-numérico largo' de la línea,
    tras normalizar separadores. Requiere >= 11 dígitos.
    """
    if not line:
        return ""
    s = re.sub(r"[\s\.\-_/]", "", str(line).strip())
    for m in _ALNUM_TOKEN_RE.finditer(s):
        tok = m.group(0)
        if sum(ch.isdigit() for ch in tok) >= 11:
            return tok
    return ""

# --------------------------------------------------------------
def parse_simit(text: str) -> List[Record]:
    """
    Patrón robusto:
      - La línea del número puede tener letras en cualquier posición (p. ej. 7689000000F47510220).
      - Luego buscamos la línea que inicia con 'Fecha imposición:' para extraer
        fecha_imposicion, fecha_notificacion y placa separadas por tabs o 2+ espacios.
    """
    lines = [l.strip() for l in text.splitlines()]
    records: List[Record] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        # 🔧 EXTRACCIÓN SIN NORMALIZAR SEPARADORES
        numero = _extract_inline_token_with_min_digits(line, min_digits=11)
        if not numero:
            i += 1
            continue

        # Buscar la línea con "Fecha imposición:" hacia abajo
        fecha_imp, notif, placa = "", "", ""
        j = i + 1
        while j < n:
            li = lines[j]
            if li.startswith("Fecha imposición:") or li.startswith("Fecha imposicion:"):
                tail = li.split(":", 1)[1].strip() if ":" in li else ""
                # separa por tabs o por 2+ espacios
                parts = re.split(r"\t+|\s{2,}", tail)
                if parts:
                    fecha_imp = parts[0].strip()
                if len(parts) > 1:
                    notif = parts[1].strip()
                if len(parts) > 2:
                    placa = parts[2].strip()
                break
            j += 1

        records.append(ensure_record(numero, fecha_imp, notif, placa, "SIMIT"))

        # Avanza hasta donde llegamos buscando; evita loops si no se halló la línea
        i = j if j > i else i + 1

    return records


# --------------------------------------------------------------------
# FENIX (robusto a columnas corridas)
# --------------------------------------------------------------------
_PLATE_RE = re.compile(
    r"^(?:[A-Z]{3}\d{3}|[A-Z]{3}\d{2}[A-Z]|[A-Z]{2}\d{3}[A-Z])$",
    flags=re.IGNORECASE,
)
_DATE_TOKEN_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")
_LONG_NUM_RE = re.compile(r"^[A-Z]?\d{11,}$")  # número de comparendo (largo)

def _extract_first_dates(tokens: List[str], start_idx: int) -> Tuple[str, str]:
    """Devuelve (fecha_imp, fecha_notif) buscando tokens con formato fecha a partir de start_idx."""
    dates: List[str] = []
    for t in tokens[start_idx:]:
        if _DATE_TOKEN_RE.match(t.strip()):
            dates.append(t.strip())
        # si llega un token de dinero o algo tipo '$', no forzamos nada; simplemente seguimos
    imp = dates[0] if dates else ""
    notif = dates[1] if len(dates) > 1 else ""
    return imp, notif

def parse_fenix(text: str) -> List[Record]:
    """
    Ejemplo típico (pero con posibles columnas corridas):
    Comparendo - ...   VIGENTE   <numero> <placa> <fecha_imp> <fecha_notif>  $... $... $... $...  <medio>
    Estrategia:
      - Buscar primer número largo como numero_comparendo.
      - Desde ahí, buscar primera placa válida.
      - Después de la placa, tomar fechas en orden: 1a = imposición, 2a = notificación (si existe).
    """
    records: List[Record] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or not line.lower().startswith("comparendo"):
            continue
        # separamos por tabs o por múltiples espacios
        tokens = [t for t in re.split(r"\t+|\s{2,}", line) if t.strip()]
        # fallback: si no hay separadores de 2+ espacios, separamos por 1+ espacios
        if len(tokens) < 2:
            tokens = [t for t in re.split(r"\s+", line) if t.strip()]

        # localizar numero
        num_idx, numero = -1, ""
        for idx, tok in enumerate(tokens):
            if _LONG_NUM_RE.match(tok):
                num_idx, numero = idx, tok
                break
        if not numero:
            continue

        # localizar placa después del número
        placa_idx, placa = -1, ""
        for idx in range(num_idx + 1, len(tokens)):
            if _PLATE_RE.match(tokens[idx].strip()):
                placa_idx, placa = idx, tokens[idx].strip()
                break

        # fechas: buscar desde placa_idx+1 (si hay placa) o desde num_idx+1
        start = (placa_idx + 1) if placa_idx >= 0 else (num_idx + 1)
        imp, notif = _extract_first_dates(tokens, start)

        records.append(ensure_record(numero, imp, notif, placa, "FENIX"))
    return records

def _extract_date_only(line: str) -> str:
    """
    Busca una fecha con patrón YYYY-MM-DD dentro de un string.
    Devuelve la fecha encontrada o '' si no hay.
    """
    if not line:
        return ""
    m = re.search(r"\d{4}-\d{2}-\d{2}", line)
    return m.group(0) if m else ""


def parse_magdalena(text: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not text.strip():
        return rows
    blocks = [b.strip() for b in text.split("# Orden:") if b.strip()]
    for b in blocks:
        try:
            num = b.split()[0]  # primer token después de "# Orden:"
            lines = b.splitlines()
            notif_line = lines[1] if len(lines) > 1 else ""
            fecha_notif = _extract_date_only(notif_line)
            rows.append({
                "numero_comparendo": num,
                "fecha_imposicion": "",
                "fecha_notificacion": fecha_notif,
                "placa": "",
                "plataforma": "Magdalena",
            })
        except Exception:
            continue
    return rows


def parse_soledad(text: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not text.strip():
        return rows
    blocks = [b.strip() for b in text.split("# Orden:") if b.strip()]
    for b in blocks:
        try:
            num = b.split()[0]
            lines = b.splitlines()
            notif_line = lines[1] if len(lines) > 1 else ""
            fecha_notif = _extract_date_only(notif_line)
            rows.append({
                "numero_comparendo": num,
                "fecha_imposicion": "",
                "fecha_notificacion": fecha_notif,
                "placa": "",
                "plataforma": "Soledad",
            })
        except Exception:
            continue
    return rows

# --------------------------------------------------------------------
# Medellín / Bello / Itagüí / Manizales / Cali
# --------------------------------------------------------------------
def parse_line_nit_plate_num_date(line: str) -> Optional[Tuple[str, str, str]]:
    """
    Línea: <NIT> <PLACA> <NUMERO> <FECHA> ...
    """
    toks = [t for t in re.split(r"\s+", line.strip()) if t]
    if len(toks) < 4:
        return None
    nit, placa, numero, fecha = toks[0], toks[1], toks[2], toks[3]
    # validaciones básicas
    if not re.fullmatch(r"[A-Z0-9]+", placa.upper()):
        return None
    if not re.fullmatch(r"[A-Z]?\d{8,}", numero):
        return None
    if not re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2,4}", fecha):
        return None
    return (placa, numero, fecha)

def parse_municipal_like(text: str, platform_name: str) -> List[Record]:
    records: List[Record] = []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        parsed = parse_line_nit_plate_num_date(raw)
        if parsed:
            placa, numero, fecha = parsed
            records.append(ensure_record(numero, fecha, "", placa, platform_name))
    return records

# --------------------------------------------------------------------
# Bolívar
# --------------------------------------------------------------------
def parse_bolivar(text: str) -> List[Record]:
    """
    Bloques típicos:
      <numero>
      <fecha_notificacion>
      (posible línea vacía)
      NO
      <monto>

    Tomamos numero + fecha_notificacion; los demás campos quedan vacíos.
    """
    lines = [l.strip() for l in text.splitlines()]
    records: List[Record] = []
    i = 0
    while i < len(lines):
        if re.fullmatch(r"[A-Z]?\d{8,}", lines[i]):
            numero = lines[i]
            fecha_notif = ""
            j = i + 1
            while j < len(lines):
                li = lines[j]
                if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", li):
                    fecha_notif = li
                    break
                # si aparece otro número de comparendo, cortamos
                if re.fullmatch(r"[A-Z]?\d{8,}", li):
                    break
                j += 1
            # fecha de imposición = "" (no se expone en Bolívar)
            records.append(ensure_record(numero, "", fecha_notif, "", "Bolívar"))
            i = j
        i += 1
    return records


# --------------------------------------------------------------------
# Santa Marta (sin duplicados; ignora .pdf)
# --------------------------------------------------------------------
def parse_santamarta(text: str) -> List[Record]:
    """
    Líneas 'Aviso del comparendo <numero> <fecha_fijacion> <fecha_desfijacion>' y líneas .pdf.
    - Ignoramos cualquier línea que contenga '.pdf'
    - Extraemos el <numero> solo de líneas 'Aviso del comparendo ...' (sin .pdf).
    - Evitamos duplicados por numero.
    """
    records: List[Record] = []
    seen = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or ".pdf" in line.lower():
            continue
        m = re.search(r"Aviso del comparendo\s+([A-Z]?\d{8,})(?=\s|$)", line, flags=re.IGNORECASE)
        if m:
            numero = m.group(1)
            if numero not in seen:
                seen.add(numero)
                records.append(ensure_record(numero, "", "", "", "Santa Marta"))
    return records

# --------------------------------------------------------------------
# Router
# --------------------------------------------------------------------
PARSERS = {
    "SIMIT": parse_simit,
    "FENIX": parse_fenix,
    "Medellín": lambda t: parse_municipal_like(t, "Medellín"),
    "Magdalena": parse_magdalena, 
    "Bello": lambda t: parse_municipal_like(t, "Bello"),
    "Itagüí": lambda t: parse_municipal_like(t, "Itagüí"),
    "Manizales": lambda t: parse_municipal_like(t, "Manizales"),
    "Cali": lambda t: parse_municipal_like(t, "Cali"),
    "Soledad": parse_soledad, 
    "Bolívar": parse_bolivar,
    "Santa Marta": parse_santamarta,
}

def parse_platform(name: str, text: str) -> List[Record]:
    fn = PARSERS.get(name)
    if not fn:
        return []
    return fn(text or "")