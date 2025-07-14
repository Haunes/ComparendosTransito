# parsers/cali.py
import re

SECTION = "CALI"

# ID de comparendo: opcional letra + 17+ dígitos
_ID_RE    = re.compile(r"^[A-Z]?\d{17,}$")
# Placa: 3 letras + 3 dígitos
_PLATE_RE = re.compile(r"^[A-Z]{3}\d{3}$")

def parse(text: str):
    """
    Parser para Alcaldía de Cali.
    Cada línea de interés es:
      Identificación Placa ID Fecha ...
    Ejemplo:
      901354352 NFX120 D76001000000048872050 14/05/2025 C14 ...

    Devuelve dicts con:
      {"id": "<NroComparendo>", "placa": "<Placa>"}
    """
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) < 3:
            continue
        placa = parts[1].strip()
        rid   = parts[2].strip()
        if not _PLATE_RE.match(placa):
            continue
        if not _ID_RE.match(rid):
            continue
        yield {"id": rid, "placa": placa}
