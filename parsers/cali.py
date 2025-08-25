# parsers/cali.py
import re
from typing import List, Dict, Tuple, Optional

MONEY_RE = re.compile(r"\$\s*([\d\.]+)")

def _to_int_money(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    return int(s.replace(".", "").replace(",", ""))

def _parse_line(line: str) -> Dict:
    s = " ".join(line.split())
    m = re.match(r"^\s*(\d+)\s+([A-Z0-9]{5,7})\s+(D?\d{17,20})\s+(\d{2}/\d{2}/\d{4})\s+([A-Z]\d{2,3})\s+", s)
    if not m:
        return {
            "plataforma": "CALI",
            "numero_comparendo": None,
            "placa": None,
            "fecha_imposicion": None,
            "codigo_infraccion": None,
            "descripcion_infraccion": None,
            "fecha_resolucion": None,
            "valor_interes": None,
            "valor": None,
            "valor_a_pagar": None,
            "raw_line": line,
        }

    _id, placa, num_compa, fecha_imp, codigo = m.groups()
    tail = s[m.end():]

    money = list(MONEY_RE.finditer(tail))
    valor = total = None
    middle = tail
    if len(money) >= 2:
        a1, a2 = money[-2], money[-1]
        valor = _to_int_money(a1.group(1))
        total = _to_int_money(a2.group(1))
        middle = tail[:a1.start()].strip()

    descripcion = None
    fecha_resolucion = None
    valor_interes = None

    mdate = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", middle)
    if mdate:
        fecha_resolucion = mdate.group(1)

    minter = MONEY_RE.search(middle)
    if minter:
        valor_interes = _to_int_money(minter.group(1))

    tmp = middle.replace("No aplica", "").strip()
    tmp = re.sub(r"\b\d{2}/\d{2}/\d{4}\b", "", tmp)
    tmp = MONEY_RE.sub("", tmp)
    tmp = " ".join(tmp.split()).strip()
    if tmp:
        descripcion = tmp

    return {
        "plataforma": "CALI",
        "numero_comparendo": num_compa,  # conservar letra si trae
        "placa": placa.replace(" ", "").upper(),
        "fecha_imposicion": fecha_imp,
        "codigo_infraccion": codigo,
        "descripcion_infraccion": descripcion,
        "fecha_resolucion": fecha_resolucion,
        "valor_interes": valor_interes,
        "valor": valor,
        "valor_a_pagar": total,
        "raw_line": line,
    }

def parse_cali_text(raw_text: str) -> Tuple[List[Dict], str]:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    records: List[Dict] = []
    dbg = []
    for i, ln in enumerate(lines, start=1):
        rec = _parse_line(ln)
        rec["__line_idx"] = i
        records.append(rec)
        dbg.append(f"[L{i}] num={rec.get('numero_comparendo')} placa={rec.get('placa')} valor={rec.get('valor')} total={rec.get('valor_a_pagar')}")
    return records, "\n".join(dbg)
