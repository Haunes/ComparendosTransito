# parsers/soledad.py
import re
from typing import List, Dict, Tuple

HDR_RE = re.compile(r"^\s*#\s*Orden:\s*([A-Za-z0-9]{8,})\b.*$", re.IGNORECASE | re.UNICODE)
ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

def _slice_blocks(text: str) -> List[str]:
    lines = text.splitlines()
    starts: List[int] = []
    for i, ln in enumerate(lines):
        if HDR_RE.match(ln.strip()):
            starts.append(i)
    if not starts:
        return []
    starts.append(len(lines))
    blocks: List[str] = []
    for i in range(len(starts) - 1):
        a, b = starts[i], starts[i + 1]
        blk = "\n".join(lines[a:b]).strip()
        if blk:
            blocks.append(blk)
    return blocks

def _parse_block(block: str) -> Dict:
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    out: Dict = {
        "numero_comparendo": None,
        "fecha_imposicion": None,
        "fecha_notificacion": None,
        "raw_block": block,
    }
    if not lines:
        return out

    # 1) número
    m = HDR_RE.match(lines[0])
    if not m:
        for ln in lines[:3]:
            m = HDR_RE.match(ln)
            if m:
                break
    if m:
        out["numero_comparendo"] = m.group(1)

    # 2) fecha imposición (YYYY-MM-DD)
    joined = "\n".join(lines)
    d = ISO_DATE_RE.search(joined)
    if d:
        out["fecha_imposicion"] = d.group(1)

    return out

def parse_soledad_text(raw_text: str) -> Tuple[List[Dict], str]:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = _slice_blocks(text)

    records: List[Dict] = []
    dbg: List[str] = [f"Bloques detectados: {len(blocks)}"]

    for i, blk in enumerate(blocks, start=1):
        rec = _parse_block(blk)
        rec["__block_idx"] = i
        records.append(rec)
        dbg.append(f"[Bloque {i}] numero={rec.get('numero_comparendo')} fecha_imp={rec.get('fecha_imposicion')}")

    return records, "\n".join(dbg)
