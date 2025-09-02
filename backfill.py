# backfill.py
from __future__ import annotations
import pandas as pd
import re
from typing import List, Dict, Any, Optional

EXPECTED_COLS = ["numero_comparendo", "fecha_imposicion", "fecha_notificacion", "placa", "plataforma"]

def _normalize_df_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Intenta mapear columnas heterogéneas a las esperadas.
    Acepta tanto 'plataforma' (singular) como 'plataformas' (agregado).
    """
    colmap = {str(c).strip().lower(): c for c in df.columns}

    def pick(*aliases) -> Optional[str]:
        for a in aliases:
            if a in colmap:
                return colmap[a]
        return None

    c_num  = pick("numero_comparendo", "numero de comparendo", "comparendo", "numero")
    c_imp  = pick("fecha_imposicion", "fecha de imposicion")
    c_not  = pick("fecha_notificacion", "fecha de notificacion")
    c_pla  = pick("placa")
    c_plat = pick("plataforma")
    c_plats= pick("plataformas")

    if c_plat is not None:
        # Hoja "Resumen": ya viene por plataforma
        out = pd.DataFrame({
            "numero_comparendo": df[c_num]  if c_num  is not None else "",
            "fecha_imposicion":  df[c_imp]  if c_imp  is not None else "",
            "fecha_notificacion":df[c_not]  if c_not  is not None else "",
            "placa":             df[c_pla]  if c_pla  is not None else "",
            "plataforma":        df[c_plat].astype(str).str.strip(),
        })
        return out[EXPECTED_COLS]

    if c_plats is not None:
        # Hoja "Conteo": reconstruimos filas por plataforma dividiendo el string 'plataformas'
        rows: List[Dict[str, Any]] = []
        for _, r in df.iterrows():
            plataformas_raw = str(r[c_plats]) if c_plats is not None else ""
            plataformas = [p.strip() for p in re.split(r"[-,/;]+", plataformas_raw) if p.strip()]
            if not plataformas:
                plataformas = [""]  # sin info

            base = {
                "numero_comparendo": r[c_num]  if c_num  is not None else "",
                "fecha_imposicion":  r[c_imp]  if c_imp  is not None else "",
                "fecha_notificacion":r[c_not]  if c_not  is not None else "",
                "placa":             r[c_pla]  if c_pla  is not None else "",
            }
            for p in plataformas:
                rr = dict(base)
                rr["plataforma"] = p
                rows.append(rr)

        out = pd.DataFrame(rows, columns=EXPECTED_COLS)
        return out

    # Fallback vacío (no se reconocen columnas)
    return pd.DataFrame(columns=EXPECTED_COLS)

def read_yesterday_summary(xlsx_file) -> pd.DataFrame:
    """
    Lee el 'Resumen de AYER' de un Excel exportado por la app:
    - Preferimos la hoja cuyo nombre comience por 'Resumen'.
    - Si no existe, tomamos la primera hoja y normalizamos; si es 'Conteo', la reconstruimos por plataforma.
    Devuelve DataFrame con columnas: numero_comparendo, fecha_imposicion, fecha_notificacion, placa, plataforma
    """
    xl = pd.ExcelFile(xlsx_file)
    sheet_name = None
    for s in xl.sheet_names:
        if str(s).strip().lower().startswith("resumen"):
            sheet_name = s
            break
    if sheet_name is None:
        sheet_name = xl.sheet_names[0]  # fallback

    df = pd.read_excel(xl, sheet_name=sheet_name)
    df_norm = _normalize_df_columns(df).copy()

    # Limpieza básica de strings
    for c in ["numero_comparendo", "fecha_imposicion", "fecha_notificacion", "placa", "plataforma"]:
        if c in df_norm.columns:
            df_norm[c] = df_norm[c].astype(str).str.strip()

    # Quita filas totalmente vacías de número
    df_norm = df_norm[df_norm["numero_comparendo"].astype(str).str.strip() != ""].reset_index(drop=True)
    return df_norm[EXPECTED_COLS]

def build_backfill_rows(df_prev: pd.DataFrame, platform_name: str) -> List[Dict[str, Any]]:
    """
    A partir del DF normalizado (una fila por plataforma), devuelve rows tipo parsers
    solo de la plataforma pedida.
    """
    if df_prev is None or df_prev.empty:
        return []
    plat = str(platform_name).strip().lower()
    mask = df_prev["plataforma"].astype(str).str.strip().str.lower() == plat
    subset = df_prev[mask]

    rows: List[Dict[str, Any]] = []
    for _, r in subset.iterrows():
        rows.append({
            "numero_comparendo":   str(r["numero_comparendo"]).strip(),
            "fecha_imposicion":    str(r["fecha_imposicion"]).strip(),
            "fecha_notificacion":  str(r["fecha_notificacion"]).strip(),
            "placa":               str(r["placa"]).strip(),
            "plataforma":          platform_name,
        })
    return rows
