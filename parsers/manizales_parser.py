# parsers/manizales.py
import re

SECTION = "MANIZALES"

# ID de comparendo: opcional letra + 17+ dígitos
_ID_RE    = re.compile(r"^[A-Z]?\d{17,}$")
# Placa: 3 letras + 3 dígitos
_PLATE_RE = re.compile(r"^[A-Z]{3}\d{3}$")

def parse(text: str):
    """
    Parser para Alcaldía de Manizales.
    Cada línea de interés es:
      Identificación Placa ID Fecha ...
    Ejemplo:
      901354352 NZP448 D17001000000047711823 12/12/2024 D04 ...

    Devuelve dicts con:
      {"id": "<NroComparendo>", "placa": "<Placa>"}
    """
    for line in text.splitlines():
        parts = line.strip().split()
        # Mínimo 3 partes: identificación, placa, comparendo
        if len(parts) < 3:
            continue
        placa = parts[1].strip()
        rid   = parts[2].strip()
        # Validar placa e ID
        if not _PLATE_RE.match(placa):
            continue
        if not _ID_RE.match(rid):
            continue
        yield {"id": rid, "placa": placa}
