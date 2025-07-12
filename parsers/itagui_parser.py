"""
itagui_parser.py
----------------
Formato de fila (ejemplo):
901354352  NZQ126  D05360000000049474182  06/06/2025  C14  ...

Regla:
• Divide por espacios/tabs consecutivos.
• Toma la 3.ª columna.
• Patrón: 1 letra opcional + ≥14 dígitos.
"""

import re
from typing import List

RE_ID = re.compile(r"^[A-Z]?\d{14,}$")

def parse(block_text: str) -> List[str]:
    ids: List[str] = []
    for linea in block_text.splitlines():
        cols = linea.strip().split()          # divide por espacios
        if len(cols) >= 3 and RE_ID.match(cols[2]):
            ids.append(cols[2])
    return ids
