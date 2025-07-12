"""
manizales_parser.py
-------------------
Ejemplo de fila:
901354352  NZP448  D17001000000047711823  12/12/2024  D04  ...

• Separa la línea por uno o más espacios o tabuladores.
• Toma la 3.ª columna y la devuelve si coincide con:
      1 letra opcional + 14 o más dígitos.
"""

import re
from typing import List

RE_ID = re.compile(r"^[A-Z]?\d{14,}$")

def parse(block_text: str) -> List[str]:
    ids: List[str] = []
    for linea in block_text.splitlines():
        cols = linea.strip().split()          # espacios consecutivos
        if len(cols) >= 3 and RE_ID.match(cols[2]):
            ids.append(cols[2])
    return ids
