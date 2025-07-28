# parsers/simit.py

import re

SECTION = "SIMIT"

# 1) ID al inicio de línea (17+ dígitos, opcional letra)
_ID_LINE_RE        = re.compile(r"^\s*([A-Z]?\d{17,})\b")
# 2) Captura la fecha de imposición en esa línea
_FECHA_IMPO_RE     = re.compile(r"Fecha\s+imposición:\s*([\d/]{10})", flags=re.I)
# 3) Captura fecha de notificación (formato DD/MM/AAAA después de la fecha de imposición)
_FECHA_NOTIF_RE    = re.compile(r"Fecha\s+imposición:\s*[\d/]{10}([\d/]{10})", flags=re.I)
# 4) Placa fallback si no la encontramos explícita
_PLATE_FALLBACK_RE = re.compile(r"\b([A-Z]{3}\d{3})\b")
# 5) Formato de fecha válida DD/MM/AAAA
_DATE_FORMAT_RE    = re.compile(r"^\d{2}/\d{2}/\d{4}$")

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
        "fecha_imposicion": "dd/mm/yyyy",
        "fecha_notif": "dd/mm/yyyy"
      }
    """
    for rid, buf in _iter_blocks(text):
        placa = ""
        fecha_imposicion = ""
        fecha_notif = ""

        # Buscamos en todas las líneas del bloque
        full_text = " ".join(buf)
        
        # Buscar fecha de imposición
        match_impo = _FECHA_IMPO_RE.search(full_text)
        if match_impo:
            fecha_imposicion = match_impo.group(1)
        
        # Buscar fecha de notificación usando el patrón mejorado
        # Primero buscamos la línea que contiene "Fecha imposición"
        for line in buf:
            if "Fecha imposición" in line:
                # Extraemos todas las fechas de esta línea
                fechas = re.findall(r'\d{2}/\d{2}/\d{4}', line)
                if len(fechas) >= 1:
                    fecha_imposicion = fechas[0]
                if len(fechas) >= 2:
                    fecha_notif = fechas[1]
                
                # Buscar placa en esta línea también
                placa_match = _PLATE_FALLBACK_RE.search(line)
                if placa_match:
                    placa = placa_match.group(1)
                break

        # Si no encontramos placa en la línea principal, buscar en todo el bloque
        if not placa:
            joined = "\n".join(buf)
            placa_match = _PLATE_FALLBACK_RE.search(joined)
            if placa_match:
                placa = placa_match.group(1)

        # Validar que las fechas tengan el formato correcto
        if not _DATE_FORMAT_RE.match(fecha_imposicion):
            fecha_imposicion = ""
        if not _DATE_FORMAT_RE.match(fecha_notif):
            fecha_notif = ""

        yield {
            "id": rid,
            "placa": placa,
            "fecha_imposicion": fecha_imposicion,
            "fecha_notif": fecha_notif,
        }
