# parsers/fenix.py (parser específico para FENIX)
import re
from typing import List, Dict, Tuple, Optional

MONEY_RE = re.compile(r"\$?\s*([\d\.]+)")

def _clean_money(val: str) -> Optional[int]:
    if val is None:
        return None
    m = MONEY_RE.search(val)
    if not m:
        return None
    num = m.group(1).replace(".", "").replace(",", "")
    try:
        return int(num)
    except Exception:
        return None

def _clean(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.strip()
    return s if s != "" else None

def _split_line(line: str) -> List[str]:
    parts = [p.strip() for p in line.split("\t")]
    return parts

def _parse_line(line: str) -> Dict:
    """
    Estructura esperada (11 columnas, algunas pueden venir vacías):
    0 tipo
    1 estado
    2 numero comparendo
    3 placa
    4 fecha imposicion
    5 fecha notificacion
    6 saldo ($)
    7 intereses ($)
    8 intereses_mora ($)
    9 total ($)
    10 medio_imposicion
    """
    parts = _split_line(line)
    if len(parts) < 11:
        parts += [None] * (11 - len(parts))

    tipo = _clean(parts[0])
    estado = _clean(parts[1])
    numero = _clean(parts[2])
    placa = _clean(parts[3])
    fecha_imp = _clean(parts[4])
    fecha_notif = _clean(parts[5])
    saldo = _clean_money(parts[6] or "")
    intereses = _clean_money(parts[7] or "")
    intereses_mora = _clean_money(parts[8] or "")
    total = _clean_money(parts[9] or "")
    medio = _clean(parts[10])

    result = {
        "numero_comparendo": re.sub(r"\D", "", numero) if numero else None,
        "tipo_comparendo": tipo,
        "estado": estado,
        "placa": placa.replace(" ", "").upper() if placa else None,
        "fecha_imposicion": fecha_imp,
        "fecha_notificacion": fecha_notif,
        "saldo": saldo,
        "intereses": intereses,
        "intereses_mora": intereses_mora,
        "total": total,
        "medio_imposicion": medio,
        "valor": saldo,
        "valor_a_pagar": total,
        "secretaria": None,
        "codigo_infraccion": None,
        "descripcion_infraccion": None,
        "detalle_estado": None,
        "raw_line": line,
    }
    return result

def parse_fenix_text(raw_text: str) -> Tuple[List[Dict], str]:
    """
    Parsea texto plano copiado de FENIX (una línea por comparendo, separada por tabs).
    Soporta múltiples líneas.
    """
    debug = []
    lines = [ln for ln in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    cleaned = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if re.search(r"\d{12,}", s):
            cleaned.append(s)
        else:
            debug.append(f"Omitida (sin número de comparendo): {s[:80]}")
    records = []
    for i, ln in enumerate(cleaned, start=1):
        rec = _parse_line(ln)
        rec["__line_idx"] = i
        records.append(rec)
        debug.append(f"[L{i}] numero={rec.get('numero_comparendo')} placa={rec.get('placa')} estado={rec.get('estado')} total={rec.get('total')}")
    return records, "\n".join(debug)
