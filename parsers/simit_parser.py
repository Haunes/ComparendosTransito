# parsers/simit.py

import re

SECTION = "SIMIT"

# 1) ID al inicio de línea (17+ dígitos, opcional letra)
_ID_LINE_RE        = re.compile(r"^\s*([A-Z]?\d{17,})\b")
# 2) Captura la fecha de imposición en esa línea (no la usamos como notificación)
_FECHA_IMPO_RE     = re.compile(r"Fecha\s+imposición:\s*([\d/]{10})", flags=re.I)
# 3) Placa fallback si no la encontramos explícita
_PLATE_FALLBACK_RE = re.compile(r"\b([A-Z]{3}\d{3})\b")

def _iter_blocks(text: str):
    """
    Genera (rid, buf) donde buf son las líneas desde el ID
    hasta 'Detalle Pago' o hasta el próximo ID.
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = _ID_LINE_RE.match(lines[i])
        if not m:
            i += 1
            continue

        rid = m.group(1)
        buf = [lines[i]]
        j = i + 1
        while j < len(lines):
            if _ID_LINE_RE.match(lines[j]):
                break
            buf.append(lines[j])
            if lines[j].strip().startswith("Detalle Pago"):
                j += 1
                break
            j += 1

        yield rid, buf
        i = j

def parse(text: str):
    """
    parse(text) -> generator de dicts:
      {
        "id": "<número de comparendo>",
        "placa": "<placa XXX999>",
        "fecha_notif": "dd/mm/yyyy"    # AHORA sí la notificación
      }
    """
    for rid, buf in _iter_blocks(text):
        placa       = ""
        fecha_notif = ""

        # Buscamos la línea con "Fecha imposición"
        for line in buf:
            if "Fecha imposición" in line:
                parts = line.split("\t")
                # parts[0] incluye "Fecha imposición: dd/mm/yyyy"
                # parts[1] es la fecha de NOTIFICACIÓN
                if len(parts) >= 2:
                    fecha_notif = parts[1].strip()
                # parts[2] sería la placa
                if len(parts) >= 3:
                    placa = parts[2].strip()
                break

        # Si no hallamos placa así, fallback por regex
        if not placa:
            joined = "\n".join(buf)
            placa = (_PLATE_FALLBACK_RE.search(joined) or [None, ""])[1]

        yield {
            "id":          rid,
            "placa":       placa,
            "fecha_notif": fecha_notif,
        }
