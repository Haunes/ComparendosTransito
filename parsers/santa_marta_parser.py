"""
santa_marta_parser.py  (versión corregida)
-----------------------------------------
• Busca líneas que empiezan por 'Aviso del comparendo'
  y NO contienen '.pdf'.
• De esas líneas toma el número inmediatamente después
  de la frase.
"""

import re
from typing import List

RE_LINE = re.compile(r"Aviso del comparendo\s+(\d{14,})", re.I)

def parse(block_text: str) -> List[str]:
    ids: List[str] = []
    for ln in block_text.splitlines():
        if ".pdf" in ln.lower():
            continue                       # descartar líneas de archivos
        m = RE_LINE.search(ln)
        if m:
            ids.append(m.group(1))
    return ids
