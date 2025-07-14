# parsers/bolivar_parser.py
import re

SECTION = "BOLIVAR"

# ID de comparendo: opcional letra + dígitos (17+)
_ID_RE = re.compile(r"^[A-Z]?\d{17,}$")

def parse(text: str):
    """
    Parser para Gobernación de Bolívar.
    El comparendo aparece como bloque de líneas, pero sólo interesa
    el número de comparendo (ID) en la primera línea.

    Devuelve dicts con:
      {"id": "<ID>", "placa": ""}
    """
    for line in text.splitlines():
        line = line.strip()
        if _ID_RE.match(line):
            yield {"id": line, "placa": ""}
