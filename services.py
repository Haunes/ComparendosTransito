# services.py
from enum import Enum
from typing import List, Dict, Tuple

from parsers.simit import parse_simit_text
from parsers.fenix import parse_fenix_text
from parsers.medellin import parse_medellin_text
from parsers.bello import parse_bello_text
from parsers.itagui import parse_itagui_text
from parsers.manizales import parse_manizales_text
from parsers.cali import parse_cali_text
from parsers.bolivar import parse_bolivar_text
from parsers.santamarta import parse_santamarta_text
from parsers.magdalena import parse_magdalena_text
from parsers.soledad import parse_soledad_text


class SupportedPlatform(str, Enum):
    SIMIT = "SIMIT"
    FENIX = "FENIX"
    MEDELLIN = "MEDELLIN"
    BELLO = "BELLO"
    ITAGUI = "ITAGUI"
    MANIZALES = "MANIZALES"
    CALI = "CALI"
    BOLIVAR = "BOLIVAR"
    SANTAMARTA = "SANTAMARTA"
    MAGDALENA = "MAGDALENA"
    SOLEDAD = "SOLEDAD"

def parse_text_by_platform(platform: str, raw_text: str) -> Tuple[List[Dict], str]:
    p = platform.upper()
    if p == SupportedPlatform.SIMIT.value:
        recs, dbg = parse_simit_text(raw_text)
    elif p == SupportedPlatform.FENIX.value:
        recs, dbg = parse_fenix_text(raw_text)
    elif p == SupportedPlatform.MEDELLIN.value:
        recs, dbg = parse_medellin_text(raw_text)
    elif p == SupportedPlatform.BELLO.value:
        recs, dbg = parse_bello_text(raw_text)
    elif p == SupportedPlatform.ITAGUI.value:
        recs, dbg = parse_itagui_text(raw_text)
    elif p == SupportedPlatform.MANIZALES.value:
        recs, dbg = parse_manizales_text(raw_text)
    elif p == SupportedPlatform.CALI.value:
        recs, dbg = parse_cali_text(raw_text)
    elif p == SupportedPlatform.BOLIVAR.value:
        recs, dbg = parse_bolivar_text(raw_text)
    elif p == SupportedPlatform.SANTAMARTA.value:
        recs, dbg = parse_santamarta_text(raw_text)
    elif p == SupportedPlatform.MAGDALENA.value:
        recs, dbg = parse_magdalena_text(raw_text)
    elif p == SupportedPlatform.SOLEDAD.value:
        recs, dbg = parse_soledad_text(raw_text)
    else:
        recs, dbg = [], f"Plataforma no soportada: {platform}"

    for r in recs:
        r.setdefault("plataforma", p)
    return recs, dbg
