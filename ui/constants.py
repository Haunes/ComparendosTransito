"""
ui/constants.py

This module defines constant values for the Streamlit UI:

- PLATFORMS: a list of platform names (e.g., 'SIMIT', 'FENIX', etc.) that
  are enabled based on the available parsers in core.PARSERS.
- TITLE: the page title displayed at the top of the Streamlit application.
"""

# ui/constants.py
from core import PARSERS

PLATFORMS = [p for p in [
    "SIMIT","FENIX","MEDELLIN","MAGDALENA","BELLO",
    "ITAGUI","MANIZALES","CALI","SOLEDAD","BOLIVAR","SANTA MARTA",
] if p in PARSERS]

TITLE = "🔍 Comparador de comparendos"
