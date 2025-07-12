"""
magdalena_parser.py
-------------------
Formato típico:

# Orden: 47745001000032113038 Notificado
2021-11-17 - 15:55
...

• El número de comparendo (o "orden") está justo después de la
  cadena "# Orden:" y antes de la palabra "Notificado".
• Puede ser 1 letra opcional + ≥14 dígitos.
"""

import re
from typing import List

RE_ORDEN = re.compile(r"#\s*Orden:\s*([A-Z]?\d{14,})", re.I)

def parse(block_text: str) -> List[str]:
    """
    Devuelve la lista de todos los números que siguen a '# Orden:'.
    Si el mismo ID aparece dos veces, se devuelve dos veces (main.py
    ya unifica según necesites).
    """
    return RE_ORDEN.findall(block_text)
