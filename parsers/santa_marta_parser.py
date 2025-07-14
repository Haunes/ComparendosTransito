# parsers/santa_marta_parser.py
import re

SECTION = "SANTA MARTA"

# Línea que inicia con 'Aviso del comparendo ' seguida de ID
_SAM_RE = re.compile(r"^Aviso del comparendo\s+([A-Z]?\d{17,})\b")

def parse(text: str):
    """
    Parser para Alcaldía de Santa Marta.
    Lee cada línea, y cuando empieza con 'Aviso del comparendo ',
    extrae el ID de comparendo. No hay placa en esta plataforma.

    Devuelve dicts:
      {"id": "<ID>", "placa": ""}
    """
    for line in text.splitlines():
        m = _SAM_RE.match(line.strip())
        if m:
            yield {"id": m.group(1), "placa": ""}
