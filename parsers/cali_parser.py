"""
cali_parser.py
--------------
Ejemplo de fila:
901354352 NFX120 D76001000000048872050 14/05/2025 C14 ...

• Divide la línea por espacios/tabs consecutivos.
• Devuelve la 3.ª columna si cumple:
      1 letra opcional + 14 o más dígitos.
"""

import re
from typing import List

RE_ID = re.compile(r"^[A-Z]?\d{14,}$")

def parse(block_text: str) -> List[str]:
    ids: List[str] = []
    for linea in block_text.splitlines():
        cols = linea.strip().split()          # separación por espacios
        if len(cols) >= 3 and RE_ID.match(cols[2]):
            ids.append(cols[2])
    return ids
