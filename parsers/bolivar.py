# parsers/bolivar.py
import re
from typing import List, Dict, Tuple, Optional

DATE_RE = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")
MONEY_RE = re.compile(r"\$?\s*([\d\.]+)")

def _to_int_money(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    return int(s.replace(".", "").replace(",", ""))

def _slice_blocks(text: str) -> List[str]:
    lines = [ln.strip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    blocks = []
    cur = []
    for ln in lines:
        if ln:
            cur.append(ln)
        else:
            if cur:
                blocks.append("\n".join(cur))
                cur = []
    if cur:
        blocks.append("\n".join(cur))
    return blocks

def _parse_block(block: str) -> Dict:
    """
    Esperado por bloque (líneas):
      1) numero_comparendo
      2) fecha (dd/mm/yyyy)
      3) (opcional en blanco)
      4) 'NO' o 'SI' (mandamiento pago)
      5) total (con o sin '$', con puntos de miles)
    """
    lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
    out: Dict = {
        "plataforma": "BOLIVAR",
        "numero_comparendo": None,       # mostrar tal cual (con letra si existe)
        "fecha_imposicion": None,        # usamos esta como 'fecha del comparendo'
        "mandamiento_pago": None,        # 'NO'/'SI'
        "valor": None,                   # alias de total
        "valor_a_pagar": None,           # alias de total
        "raw_block": block,
    }
    if not lines:
        return out

    # 1) número (tal cual)
    out["numero_comparendo"] = lines[0].strip()

    # 2) fecha
    if len(lines) > 1:
        m = DATE_RE.search(lines[1])
        if m:
            out["fecha_imposicion"] = m.group(1)

    # 3) mandamiento pago ('NO'/'SI') y total
    # Recorremos el resto buscando 'NO'/'SI' y primer monto
    mand = None
    total = None
    for ln in lines[2:]:
        s = ln.upper()
        if mand is None and s in ("NO", "SI"):
            mand = s
            continue
        if total is None:
            mm = MONEY_RE.search(ln)
            if mm:
                total = _to_int_money(mm.group(1))

    out["mandamiento_pago"] = mand
    out["valor"] = total
    out["valor_a_pagar"] = total
    return out

def parse_bolivar_text(raw_text: str) -> Tuple[List[Dict], str]:
    blocks = _slice_blocks(raw_text)
    records, dbg = [], []
    for i, blk in enumerate(blocks, start=1):
        rec = _parse_block(blk)
        rec["__block_idx"] = i
        records.append(rec)
        dbg.append(f"[B{i}] num={rec.get('numero_comparendo')} fecha={rec.get('fecha_imposicion')} total={rec.get('valor_a_pagar')} mando={rec.get('mandamiento_pago')}")
    return records, "\n".join(dbg)
