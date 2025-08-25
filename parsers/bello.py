# parsers/bello.py (parser específico para BELLO)
import re
from typing import List, Dict, Tuple, Optional

DATE_RE = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")
MONEY_RE = re.compile(r"\$\s*([\d\.]+)")

def _to_int_money(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    return int(s.replace(".", "").replace(",", ""))

def _parse_line(line: str) -> Dict:
    """
    Formato (todo en UNA línea, separado por espacios), p.ej:
    901354352 LQW001 D05088000000048000836 13/02/2025 C14 No aplica No aplica No aplica $ 604.043 $ 604.043
    901354352 NFV087 D05088000000045561725 02/08/2024 C14 0000715381 04/10/2024 $ 92.652 $ 572.624 $ 665.276

    Regla: tomamos SIEMPRE los dos ÚLTIMOS montos con '$' como:
      - valor (multa)
      - valor_a_pagar (total)
    Y en la “zona media” capturamos opcionalmente:
      - fecha_resolucion (si aparece una fecha dd/mm/yyyy)
      - valor_interes (primer monto con '$' que esté en la zona media, si existe)
      - descripcion_infraccion: si hay un texto distinto de 'No aplica' (sin crear columnas nuevas)
    """
    s = " ".join(line.split())  # normaliza espacios múltiples

    # 1) id, placa, numero, fecha_imposicion, codigo_infraccion
    m = re.match(
        r"^\s*(\d+)\s+([A-Z0-9]{5,7})\s+(D?\d{17,20})\s+(\d{2}/\d{2}/\d{4})\s+([A-Z]\d{2,3})\s+",
        s
    )
    if not m:
        return {
            "plataforma": "BELLO",
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
    tail = s[m.end():]  # resto

    # 2) últimos dos montos => valor y total
    money = list(MONEY_RE.finditer(tail))
    valor = total = None
    middle = tail
    if len(money) >= 2:
        a1, a2 = money[-2], money[-1]
        valor = _to_int_money(a1.group(1))
        total = _to_int_money(a2.group(1))
        middle = tail[:a1.start()].strip()

    # 3) zona media: fecha_resolucion, valor_interes y (si aplica) una descripción
    fecha_res = None
    mdate = DATE_RE.search(middle)
    if mdate:
        fecha_res = mdate.group(1)

    valor_interes = None
    minter = MONEY_RE.search(middle)
    if minter:
        valor_interes = _to_int_money(minter.group(1))

    # descripción: cualquier texto diferente de “No aplica” que no sea fecha ni dinero
    tmp = middle.replace("No aplica", "").strip()
    # elimina fechas y montos de tmp para intentar dejar solo texto descriptivo
    tmp = DATE_RE.sub("", tmp)
    tmp = MONEY_RE.sub("", tmp)
    tmp = " ".join(tmp.split()).strip()
    descripcion = tmp if tmp else None

    return {
        "plataforma": "BELLO",
        "numero_comparendo": num_compa,  # conservar letra si trae
        "placa": placa.replace(" ", "").upper(),
        "fecha_imposicion": fecha_imp,
        "codigo_infraccion": codigo,
        "descripcion_infraccion": descripcion,
        "fecha_resolucion": fecha_res,
        "valor_interes": valor_interes,
        "valor": valor,
        "valor_a_pagar": total,
        "raw_line": line,
    }

def parse_bello_text(raw_text: str) -> Tuple[List[Dict], str]:
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
