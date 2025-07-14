# ui/excel_reader.py

import re
import pandas as pd
from datetime import datetime
from core.clean import id_key

_MISSING = {"", "N/A", "NA", "ND", "N.D", "NO APLICA", "-"}
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")

def _fmt_date(val) -> str:
    """
    - Si es NaN → ""
    - Si ya es datetime → "dd/mm/aaaa"
    - Si es string ISO "YYYY-MM-DD hh:mm:ss" → parse y formatea
    - Si es otro string (p.ej. "25/06/2025") → devuelve tal cual
    """
    if pd.isna(val):
        return ""
    if isinstance(val, datetime):
        return val.strftime("%d/%m/%Y")
    s = str(val).strip()
    if s.upper() in _MISSING:
        return ""
    if _ISO_DATE.match(s):
        try:
            dt = pd.to_datetime(s)
            return dt.strftime("%d/%m/%Y")
        except:
            pass
    return s

def _find_comp_col(cols: dict[str,str]) -> str|None:
    for low, orig in cols.items():
        if "número de comparendo" in low or "numero de comparendo" in low:
            return orig
    for low, orig in cols.items():
        if "comparendo" in low and "fecha" not in low:
            return orig
    return None

def _find_notif_col(cols: dict[str,str]) -> str|None:
    for low, orig in cols.items():
        if "segun pagina web" in low:
            return orig
    for low, orig in cols.items():
        if "notificaci" in low and "imposicion" not in low and "imposición" not in low:
            return orig
    return None

def resumen_desde_excel(uploaded) -> pd.DataFrame:
    df = pd.read_excel(
        uploaded,
        sheet_name="COMPARENDOS",
        header=6,
        engine="openpyxl",
        dtype=str,   # todo a texto
    )

    cols = {c.lower(): c for c in df.columns}
    comp_col  = _find_comp_col(cols)
    placa_col = next((orig for low,orig in cols.items() if "placa" in low), None)
    notif_col = _find_notif_col(cols)

    if comp_col is None:
        raise KeyError("No se encontró la columna de Número de Comparendo.")
    if notif_col is None:
        raise KeyError("No se encontró la columna de Fecha de Notificación (Según página web).")

    raw_cmp = df[comp_col].fillna("").str.strip()
    claves  = raw_cmp.map(id_key)

    mask     = claves.astype(bool)
    df_valid = df.loc[mask]

    # ahora aplicamos _fmt_date a raw strings o ISO strings
    resumen = pd.DataFrame({
        "id_key":      claves[mask],
        "comparendo":  raw_cmp[mask],
        "placa":       df_valid[placa_col].fillna("").str.strip() if placa_col else "",
        "fecha_notif": df_valid[notif_col].map(_fmt_date),
    })

    resumen["fuentes"] = [[]] * len(resumen)
    resumen["veces"]   = 0
    return resumen
