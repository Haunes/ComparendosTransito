# parsers/medellin.py

import re

SECTION = "MEDELLIN"

# ID: opcional letra + 17+ dígitos
_ID_RE    = re.compile(r"^[A-Z]?\d{17,}$")
# Placa: 3 letras + 3 dígitos
_PLATE_RE = re.compile(r"^[A-Z]{3}\d{3}$")

def parse(text: str):
    """
    Cada línea tipo:
      Identificación Placa NroComparendo Fecha ... (resto)
    Ejemplo:
      901354352 LCM709 D05001000000048247110 17/06/2025 C29 ...
    Devuelve dicts con:
      { "id": "<NroComparendo>", "placa": "<Placa>" }
    """
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) < 3:
            continue

        placa = parts[1]
        rid   = parts[2]

        if not _PLATE_RE.match(placa):
            continue
        if not _ID_RE.match(rid):
            continue

        yield {"id": rid, "placa": placa}
