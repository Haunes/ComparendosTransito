"""
services/notif_changes.py

Provides functionality to detect changes in the notification date of comparendos
between two DataFrame summaries (old vs. new). It focuses on two types of valid
transitions, ignoring any shifts to or from non–date statuses:

  - 'dato actualizado': when a comparendo had an empty/N‑A notification date and now has a valid date.
  - 'modificado'      : when a comparendo’s notification date changes from one valid date to a different valid date.

Any transition where the new value is not a strictly formatted date (dd/mm/yyyy),
such as “En proceso notificación” or “No aplica”, is excluded from the results.

Functions:
  _clean(val) -> str
    Normalize a raw cell value to an empty string if missing or in a predefined
    N‑A set, otherwise return the trimmed string.

  _is_date(s) -> bool
    Return True if the string exactly matches the dd/mm/yyyy pattern.

  detect_notif_changes(resumen_old: DataFrame, resumen_new: DataFrame) -> DataFrame
    Compare the 'fecha_notif' column of two DataFrames filtered to maintained
    comparendos, returning a DataFrame with columns:
      - comparendo
      - placa
      - fecha_notif_old
      - fecha_notif_new
      - tipo_cambio  ('dato actualizado' or 'modificado')
"""


# services/notif_changes.py

import re
import pandas as pd

# Tokens que consideramos “vacío” o “no aplica”
_MISSING = {"", "N/A", "NA", "ND", "N.D", "NO APLICA", "-"}

# Regex para detectar fechas en formato dd/mm/aaaa
_DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")

def _clean(val: object) -> str:
    """
    Normaliza la celda:
      - Si está en _MISSING o es NaN → ""
      - Si es texto dd/mm/aaaa → lo deja
      - Si cualquier otra cosa (p.ej. 'En proceso notificación') → lo deja
    """
    s = str(val).strip()
    if not s or s.upper() in _MISSING:
        return ""
    return s

def _is_date(s: str) -> bool:
    """¿Coincide exactamente con dd/mm/aaaa?"""
    return bool(_DATE_RE.fullmatch(s))

def detect_notif_changes(
    resumen_old: pd.DataFrame,
    resumen_new: pd.DataFrame
) -> pd.DataFrame:
    """
    Detecta únicamente transiciones:
      • "" → fecha válida       ⇒ 'dato actualizado'
      • fecha A → fecha B≠A    ⇒ 'modificado'

    Ignora todo lo demás.
    """
    cols = ["id_key", "comparendo", "placa", "fecha_notif"]
    o = resumen_old[cols].drop_duplicates("id_key").copy()
    n = resumen_new[cols].drop_duplicates("id_key").copy()

    df = (
        o.merge(n, on="id_key", suffixes=("_old","_new"), how="inner")
         # limpiamos
         .assign(
             fo=lambda d: d["fecha_notif_old"].map(_clean),
             fn=lambda d: d["fecha_notif_new"].map(_clean),
         )
    )

    def _cls(r):
        old, new = r["fo"], r["fn"]
        # si nuevo NO es fecha válida, descarta
        if not _is_date(new):
            return None
        # "" → fecha
        if old == "" and new:
            return "dato actualizado"
        # fecha A → fecha B distinta
        if _is_date(old) and old != new:
            return "modificado"
        return None

    df["tipo_cambio"] = df.apply(_cls, axis=1)
    df = df[df["tipo_cambio"].notna()].copy()

    # Construimos la tabla final usando solo cadenas limpias
    return (
        pd.DataFrame({
            "comparendo":      df["comparendo_new"],
            "placa":           df["placa_new"],
            "fecha_notif_old": df["fo"],
            "fecha_notif_new": df["fn"],
            "tipo_cambio":     df["tipo_cambio"],
        })
        .reset_index(drop=True)
    )
