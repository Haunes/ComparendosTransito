# ui/constants.py
from core import PARSERS

PLATFORMS = [p for p in [
    "SIMIT","FENIX","MEDELLIN","MAGDALENA","BELLO",
    "ITAGUI","MANIZALES","CALI","SOLEDAD","BOLIVAR","SANTA MARTA",
] if p in PARSERS]

TITLE = "🔍 Comparador de comparendos"
