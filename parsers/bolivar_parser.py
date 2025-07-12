"""
bolivar_parser.py
-----------------
Ejemplo de bloque:

13683001000049160635
24/02/2025

NO
603.930

• El número de comparendo está en cualquier línea que contenga
  solo dígitos (≥14) —puede haber varias filas así en el bloque.
"""

import re
from typing import List

RE_ID = re.compile(r"^\d{14,}$")      # solo dígitos, 14 o más

def parse(block_text: str) -> List[str]:
    ids: List[str] = []
    for linea in block_text.splitlines():
        if RE_ID.fullmatch(linea.strip()):
            ids.append(linea.strip())
    return ids
