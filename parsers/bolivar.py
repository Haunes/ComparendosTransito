# parsers/bolivar.py
import re
from typing import List, Dict, Tuple, Optional

NUM_RE   = re.compile(r"^\d{17,22}$")           # número de comparendo (solo dígitos, 17-22)
DATE_RE  = re.compile(r"^\d{2}/\d{2}/\d{4}$")   # dd/mm/aaaa
MAND_RE  = re.compile(r"^(NO|SI|SÍ)$", re.IGNORECASE)
MONEY_RE = re.compile(r"^[\$\s]*[\d\.\,]+$")    # 603.930 | $ 603.930 | 603,930 (flexible)

def _norm_money(s: str) -> Optional[int]:
    if not s:
        return None
    # quita $ y espacios, convierte 603.930 -> 603930 ; 603,930 -> 603930
    v = s.replace("$", "").replace(" ", "").replace(".", "").replace(",", "")
    return int(v) if v.isdigit() else None

def parse_bolivar_text(raw_text: str) -> Tuple[List[Dict], str]:
    # normaliza saltos y elimina líneas totalmente vacías
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    records: List[Dict] = []
    dbg: List[str] = []

    current = {
        "numero_comparendo": None,
        "fecha_imposicion": None,
        "mandamiento_pago": None,
        "total": None,
    }

    def _flush():
        nonlocal current
        if current["numero_comparendo"]:
            # construir salida estándar
            rec = {
                "numero_comparendo": current["numero_comparendo"],
                "fecha_imposicion": current["fecha_imposicion"],
                "fecha_notificacion": None,       # Bolívar no la trae
                "mandamiento_pago": current["mandamiento_pago"],
                "total": _norm_money(current["total"]) if current["total"] else None,
            }
            records.append(rec)
            dbg.append(
                f"OK num={rec['numero_comparendo']} f_imp={rec['fecha_imposicion']} "
                f"mand={rec['mandamiento_pago']} total={rec['total']}"
            )
        current = {"numero_comparendo": None, "fecha_imposicion": None, "mandamiento_pago": None, "total": None}

    for ln in lines:
        if NUM_RE.match(ln):
            # si ya había un registro en curso, ciérralo antes de empezar uno nuevo
            if current["numero_comparendo"] or current["fecha_imposicion"] or current["mandamiento_pago"] or current["total"]:
                _flush()
            current["numero_comparendo"] = ln
            continue

        if current["numero_comparendo"] is None:
            # ignora todo hasta ver un número válido
            continue

        if current["fecha_imposicion"] is None and DATE_RE.match(ln):
            current["fecha_imposicion"] = ln
            continue

        if current["mandamiento_pago"] is None and MAND_RE.match(ln):
            current["mandamiento_pago"] = ln.upper().replace("Í", "I")
            continue

        if current["total"] is None and MONEY_RE.match(ln):
            current["total"] = ln
            continue

        # cualquier otra línea se ignora

    # último registro pendiente
    _flush()

    return records, "\n".join(dbg)
