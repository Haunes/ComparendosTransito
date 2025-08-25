# parsers/medellin.py (parser específico para MEDELLÍN)
import re
from typing import List, Dict, Tuple, Optional

MONEY_RE = re.compile(r"\$\s*([\d\.]+)")

def _to_int_money(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    return int(s.replace(".", "").replace(",", ""))

def _parse_line(line: str) -> Dict:
    """
    Formato (todo en UNA línea, separado por espacios):
    ID  PLACA  NUM_COMPA  FECHA_IMP  CODIGO  <infracción>  <fecha_resolución>  <valor_interes>  $ VALOR_MULTA  $ TOTAL
    En los ejemplos, los 3 campos intermedios suelen ser 'No aplica'.
    """
    s = " ".join(line.split())  # normaliza espacios múltiples

    # 1) id, placa, número, fecha, código
    m = re.match(
        r"^\s*(\d+)\s+([A-Z0-9]{5,7})\s+(D?\d{17,20})\s+(\d{2}/\d{2}/\d{4})\s+([A-Z]\d{2,3})\s+",
        s
    )
    if not m:
        # Retorna lo básico para depurar si no calza
        return {
            "plataforma": "MEDELLIN",
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
    tail = s[m.end():]  # resto de la línea (incluye 3 campos + montos)

    # 2) toma SIEMPRE los dos ÚLTIMOS montos con '$' como valor y total
    money = list(MONEY_RE.finditer(tail))
    valor = total = None
    middle = tail
    if len(money) >= 2:
        a1, a2 = money[-2], money[-1]
        valor = _to_int_money(a1.group(1))
        total = _to_int_money(a2.group(1))
        middle = tail[:a1.start()].strip()  # lo que hay entre código y los montos

    # 3) los 3 campos intermedios (pueden ser 'No aplica')
    #    Convertimos "No aplica" en un solo token para no romper con espacios
    tmp = middle.replace("No aplica", "No_aplica")
    tokens = [t.replace("_", " ") for t in tmp.split()] if tmp else []
    # Si faltan tokens no pasa nada; se quedan como None
    descripcion = tokens[0] if len(tokens) > 0 else None
    fecha_res = tokens[1] if len(tokens) > 1 else None
    valor_interes = None
    if len(tokens) > 2:
        # puede venir 'No aplica' o un monto con $
        if tokens[2].startswith("$"):
            mvi = MONEY_RE.search(tokens[2])
            if mvi:
                valor_interes = _to_int_money(mvi.group(1))
        # si es 'No aplica', dejamos None

    return {
        "plataforma": "MEDELLIN",
        "numero_comparendo": num_compa,  # conservar letra si trae
        "placa": placa.replace(" ", "").upper(),
        "fecha_imposicion": fecha_imp,
        "codigo_infraccion": codigo,
        "descripcion_infraccion": descripcion,  # campo común
        "fecha_resolucion": fecha_res,          # campo común
        "valor_interes": valor_interes,         # campo común
        "valor": valor,                         # valor multa
        "valor_a_pagar": total,                 # total a pagar
        "raw_line": line,
    }

def parse_medellin_text(raw_text: str) -> Tuple[List[Dict], str]:
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
