# parsers/magdalena.py
import re

SECTION = "MAGDALENA"

# Línea con '# Orden: <id> Notificado'
_ORDEN_RE = re.compile(r"^#\s*Orden:\s*([A-Z]?\d+)\b", flags=re.I)

def parse(text: str):
    """
    Cada vez que aparece '# Orden: 47745001000032113038 Notificado'
    extrae el número 47745001000032113038 como 'id' y devuelve placa vacía.
    """
    for line in text.splitlines():
        m = _ORDEN_RE.match(line)
        if m:
            rid = m.group(1).strip()
            yield {"id": rid, "placa": ""}
