# parsers/fenix.py

import re

SECTION = "FENIX"

# Identifica un ID válido (opcional letra + 17+ dígitos)
_ID_RE      = re.compile(r"^[A-Z]?\d{17,}$")
# Fecha en formato dd/mm/aaaa
_DATE_FULL  = re.compile(r"^\d{2}/\d{2}/\d{4}$")
# Placa estándar XXX999
_PLATE_RE   = re.compile(r"\b([A-Z]{3}\d{3})\b")

def parse(text: str):
    """
    Cada línea es:
      tipo   estado   id   placa   fecha_impo   fecha_notif   saldo   int   moras   total   medio
    Separadas por tabuladores.
    Devuelve dicts con:
      { "id": str,
        "placa": str,
        "fecha_imposicion": str,
        "fecha_notif": str }
    """
    for raw in text.splitlines():
        if not raw.strip():
            continue

        cols = raw.split("\t")
        # Necesitamos al menos 6 columnas para llegar a fecha_notif
        if len(cols) < 6:
            continue

        _, _, rid, placa, f_imp, f_not = cols[:6]
        rid   = rid.strip()
        placa = placa.strip()
        f_imp = f_imp.strip()
        f_not = f_not.strip()

        # Validar ID
        if not _ID_RE.match(rid):
            continue

        # Validar placa (fallback por regex si la columna no encaja)
        if not _PLATE_RE.fullmatch(placa) and (_PLATE_RE.search(raw)):
            placa = _PLATE_RE.search(raw).group(1)

        # Normalizar fecha de imposición
        fecha_imposicion = f_imp if _DATE_FULL.match(f_imp) else ""

        # Normalizar fecha de notificación: debe ser dd/mm/aaaa
        fecha_notif = f_not if _DATE_FULL.match(f_not) else ""

        yield {
            "id": rid,
            "placa": placa,
            "fecha_imposicion": fecha_imposicion,
            "fecha_notif": fecha_notif,
        }
