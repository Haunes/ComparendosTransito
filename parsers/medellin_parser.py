"""
medellin_parser.py
------------------
Formato típico de cada fila:

  901354352  NFZ914  D05001000000048242254  12/06/2025  C29  No aplica ...

Regla:
• Columnas separadas por uno o más espacios (no hay tabuladores).
• El **ID** del comparendo es siempre la 3.ª columna (índice 2).
• Patrón: 1 letra opcional + ≥14 dígitos.
"""

import re
from typing import List

RE_ID = re.compile(r"^[A-Z]?\d{14,}$")

def parse(block_text: str) -> List[str]:
    ids: List[str] = []
    for linea in block_text.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        columnas = linea.split()  # división por espacios consecutivos
        if len(columnas) >= 3 and RE_ID.match(columnas[2]):
            ids.append(columnas[2])
    return ids
