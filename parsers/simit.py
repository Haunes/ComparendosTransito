# parsers/simit.py (parser específico para SIMIT)
import re
from typing import List, Dict, Tuple, Optional

DATE_RE = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")
MONEY_RE = re.compile(r"\$\s*([\d\.]+)")

def _clean_money(val: str) -> Optional[int]:
    if not val:
        return None
    m = MONEY_RE.search(val)
    if not m:
        return None
    num = m.group(1).replace(".", "").replace(",", "")
    try:
        return int(num)
    except Exception:
        return None

def _first_date(s: str) -> Optional[str]:
    if not s:
        return None
    m = DATE_RE.search(s)
    return m.group(1) if m else None

def _extract_num_token(text: str) -> Optional[str]:
    # token alfanumérico largo (14+), soporta letras en cualquier posición
    m = re.search(r"[A-Za-z0-9]{14,}", text.replace(" ", ""))
    return m.group(0) if m else None

def _extract_number_lines(text: str) -> List[int]:
    lines = text.splitlines()
    starts = []
    for i, ln in enumerate(lines):
        if re.fullmatch(r"[A-Za-z0-9]{14,}", ln.strip()):
            starts.append(i)
    if not starts:
        for i, ln in enumerate(lines):
            if re.search(r"[A-Za-z0-9]{8,}", ln):
                nxt = lines[i+1].strip().lower() if i + 1 < len(lines) else ""
                if nxt == "comparendo":
                    starts.append(i)
    return starts

def _slice_blocks(text: str) -> List[str]:
    lines = text.splitlines()
    starts = _extract_number_lines(text)
    if not starts:
        return []
    starts.append(len(lines))
    blocks = []
    for i in range(len(starts) - 1):
        a, b = starts[i], starts[i+1]
        block = "\n".join(lines[a:b]).strip()
        if block:
            blocks.append(block)
    return blocks

def _parse_block(block: str) -> Dict:
    result: Dict = {
        "numero_comparendo": None,
        "tipo_comparendo": None,
        "fecha_imposicion": None,
        "fecha_notificacion": None,
        "placa": None,
        "secretaria": None,
        "codigo_infraccion": None,
        "descripcion_infraccion": None,
        "estado": None,
        "detalle_estado": None,
        "valor": None,
        "valor_a_pagar": None,
        "raw_block": block,
    }

    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    if not lines:
        return result

    # 1) número de comparendo (con letra si trae)
    num = _extract_num_token(lines[0]) or _extract_num_token(block)
    if num:
        result["numero_comparendo"] = num

    # 2) tipo de comparendo
    if len(lines) > 1 and lines[1].lower().startswith("comparendo"):
        result["tipo_comparendo"] = lines[1]
    else:
        for ln in lines[1:4]:
            if ln.lower().startswith("comparendo"):
                result["tipo_comparendo"] = ln
                break

    # 3) fechas, placa, secretaria
    idx_fecha = None
    for i, ln in enumerate(lines):
        if ln.lower().startswith("fecha imposición:") or ln.lower().startswith("fecha imposicion:"):
            idx_fecha = i
            break

    if idx_fecha is not None:
        linea_fecha = lines[idx_fecha]
        payload = linea_fecha.split(":", 1)[-1].strip()
        parts = re.split(r"\t+|\s{2,}", payload)
        parts = [p.strip() for p in parts if p.strip()]
        if parts:
            result["fecha_imposicion"] = _first_date(parts[0])
        if len(parts) > 1:
            maybe_date = _first_date(parts[1])
            result["fecha_notificacion"] = maybe_date or parts[1]
        if len(parts) > 2:
            result["placa"] = parts[2].replace(" ", "").upper()
        if len(parts) > 3:
            result["secretaria"] = " ".join(parts[3:])

    # 4) código infracción
    codigo = None
    for ln in lines:
        if re.match(r"^[A-Z]\d{2}", ln) or "..." in ln:
            codigo = ln
            break
    result["codigo_infraccion"] = codigo

    # 5) descripción infracción
    desc = None
    for ln in lines:
        if ln.lower().startswith("fotodetección") or ln.lower().startswith("fotodeteccion"):
            desc = ln
            break
    result["descripcion_infraccion"] = desc

    # 6) estado y detalle
    estados_posibles = {"pendiente","en firme","pagado","anulado","archivado","en cobro coactivo"}
    estado_idx = None
    for i, ln in enumerate(lines):
        if ln.lower() in estados_posibles:
            estado_idx = i
            break
    if estado_idx is not None:
        result["estado"] = lines[estado_idx]
        if estado_idx + 1 < len(lines):
            result["detalle_estado"] = lines[estado_idx + 1]

    # 7) valores
    valor = None
    valor_pagar = None
    for ln in lines:
        matches = MONEY_RE.findall(ln)
        if len(matches) >= 2:
            valor = _clean_money("$" + matches[0])
            valor_pagar = _clean_money("$" + matches[1])
            break

    if valor is None or valor_pagar is None:
        valores = []
        for ln in lines:
            if MONEY_RE.search(ln):
                val = _clean_money(ln)
                if val is not None:
                    valores.append(val)
        if valores:
            valor = valores[0]
        if len(valores) > 1:
            valor_pagar = valores[1]

    result["valor"] = valor
    result["valor_a_pagar"] = valor_pagar

    return result

def parse_simit_text(raw_text: str) -> Tuple[List[Dict], str]:
    debug_lines = []
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = _slice_blocks(text)
    debug_lines.append(f"Bloques detectados: {len(blocks)}")

    records: List[Dict] = []
    for i, blk in enumerate(blocks, start=1):
        rec = _parse_block(blk)
        rec["__block_idx"] = i
        records.append(rec)
        debug_lines.append(
            f"[Bloque {i}] numero={rec.get('numero_comparendo')} placa={rec.get('placa')} "
            f"valor={rec.get('valor')} valor_a_pagar={rec.get('valor_a_pagar')}"
        )

    debug_info = "\n".join(debug_lines)
    return records, debug_info
