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