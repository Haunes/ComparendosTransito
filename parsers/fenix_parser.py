"""
fenix_parser.py
---------------
Extrae los números de comparendo de la sección FENIX.

Formato típico de cada línea (tabuladores o múltiples espacios):

Comparendo - …     VIGENTE   11001000000042735753   LZN818   23/08/2024   ….

Regla:
• Tomamos la **tercera columna** (contando desde 1) después de dividir
  la línea por tabuladores ( \t ) **o** por dos/más espacios consecutivos.
• Solo guardamos la celda si tiene 14 dígitos o más (opcional una letra al inicio).
"""

import re
from typing import List

# 1 letra opcional + ≥14 dígitos
RE_ID = re.compile(r"^[A-Z]?\d{14,}$")
SPLIT = re.compile(r"\t|\s{2,}")          # tab o ≥2 espacios

def parse(block_text: str) -> List[str]:
    ids = []
    for ln in block_text.splitlines():
        cols = [c for c in SPLIT.split(ln.strip()) if c]
        if len(cols) >= 3 and RE_ID.match(cols[2]):
            ids.append(cols[2])
    return ids
