"""
Módulo de utilidades para normalizar texto y generar claves de comparación.

Funciones:
  strip_accents(text: str) -> str
    Elimina los acentos de un texto usando descomposición Unicode (NFD).

  id_key(raw: str) -> str
    Convierte un valor bruto en una clave compuesta únicamente por dígitos:
    1. Elimina acentos y convierte a mayúsculas.
    2. Quita prefijos de letras.
    3. Elimina cualquier carácter no numérico.

  norm(text: str) -> str
    Normaliza cadenas para encabezados de columna:
    1. Convierte a minúsculas.
    2. Elimina espacios al inicio y final.
    3. Quita acentos.
"""


import re, unicodedata as ud

_PFX  = re.compile(r"^[A-Z]+")   # letras iniciales
_NUMS = re.compile(r"[^0-9]")    # no-dígitos

def strip_accents(text: str) -> str:
    return "".join(c for c in ud.normalize("NFD", text) if ud.category(c) != "Mn")

def id_key(raw: str) -> str:
    """Sólo dígitos → clave de comparación"""
    s = strip_accents(str(raw)).upper()
    s = _PFX.sub("", s)          # quita letras iniciales
    return _NUMS.sub("", s)      # deja dígitos

def norm(text: str) -> str:
    """para encabezados de columnas"""
    return strip_accents(text.strip().lower())