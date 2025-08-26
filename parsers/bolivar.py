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
    # Limpieza de líneas
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]  # <== aquí eliminas los vacíos

    out = {
        "numero_comparendo": None,
        "fecha_imposicion": None,
        "mandamiento_pago": None,
        "total": None,
        "raw_block": block,
    }
    if not lines:
        return out

    # 1) número
    out["numero_comparendo"] = lines[0]

    # 2) fecha imposición (línea 2)
    if len(lines) > 1:
        out["fecha_imposicion"] = lines[1]

    # 3) mandamiento pago (línea 3)
    if len(lines) > 2:
        out["mandamiento_pago"] = lines[2]

    # 4) valor (línea 4)
    if len(lines) > 3:
        try:
            out["total"] = float(lines[3].replace(".", "").replace(",", "."))
        except:
            out["total"] = lines[3]

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
