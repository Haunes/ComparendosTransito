"""
ui/excel_reader.py

This module provides functionality to read and normalize comparendo data from an
uploaded Excel file. It reads the 'COMPARENDOS' sheet (with header on row 7), forces
all data to text, locates the columns for comparendo number, license plate, and
notification date (according to the web page), and returns a cleaned DataFrame.

Functions:
  - _fmt_date(val) -> str
      Normalize a value into 'dd/mm/YYYY' format or empty string if missing.
  - _find_comp_col(cols: dict[str,str]) -> str|None
      Identify the correct column name for 'Número de Comparendo' excluding any
      date-related columns.
  - _find_notif_col(cols: dict[str,str]) -> str|None
      Locate the notification date column specifically marked 'Según página web',
      excluding any 'imposición' fields.
  - resumen_desde_excel(uploaded) -> pd.DataFrame
      Read the uploaded Excel file, extract and normalize comparendo entries,
      producing a DataFrame with columns:
        * id_key (normalized numeric key)
        * comparendo (original string)
        * placa (license plate, if present)
        * fecha_notif (notification date formatted)
        * fuentes (initialized empty list)
        * veces (initialized zero)
"""
import re
import pandas as pd
from datetime import datetime
from core.clean import id_key

_MISSING = {"", "N/A", "NA", "ND", "N.D", "NO APLICA", "-"}
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")

def _fmt_date(val) -> str:
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
        dtype=str,
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

    resumen = pd.DataFrame({
        "id_key":      claves[mask],
        "comparendo":  raw_cmp[mask],
        "placa":       df_valid[placa_col].fillna("").str.strip() if placa_col else "",
        "fecha_notif": df_valid[notif_col].map(_fmt_date),
    })

    resumen["fuentes"] = [[]] * len(resumen)
    resumen["veces"]   = 0
    return resumen
