"""
soledad_parser.py
-----------------
Ejemplo de línea:

# Orden: 08758000000026402107 Notificado

• Captura el número que aparece después de '# Orden:'.
• Patrón: 1 letra opcional + 14 o más dígitos.
"""

import re
from typing import List

RE_ORDEN = re.compile(r"#\s*Orden:\s*([A-Z]?\d{14,})", re.I)

def parse(block_text: str) -> List[str]:
    """Devuelve todos los IDs que siguen a '# Orden:'."""
    return RE_ORDEN.findall(block_text)
