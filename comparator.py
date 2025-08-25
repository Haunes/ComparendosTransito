# comparator.py
import pandas as pd
import numpy as np
import re
from typing import Dict, Tuple, Optional
import holidays

# --- Helpers fechas y columnas ---

def _to_date(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce", dayfirst=True)

# --- Calendario hábil Colombia ---

def _co_holidays_for_years(years):
    co = holidays.Colombia(years=years)
    return np.array(sorted(co.keys()), dtype="datetime64[D]")

def _busday_add_co(date: pd.Timestamp, n: int) -> pd.Timestamp:
    if pd.isna(date):
        return pd.NaT
    years = range(date.year - 1, date.year + 3)
    hols = _co_holidays_for_years(years)
    d = np.datetime64(date.date(), "D")
    out = np.busday_offset(d, n, roll="forward", holidays=hols)
    return pd.Timestamp(out)

# --- Carga de Excel AYER (fila de encabezados variable; usa columna I para notificación) ---

def load_yesterday_excel(xlsx_path_or_file, sheet_name: str = "COMPARENDOS") -> pd.DataFrame:
    """
    Lee el Excel de 'ayer' detectando encabezados; la fecha de notificación se toma explícitamente de la columna I.
    Acepta ruta, archivo subido o ExcelFile.
    Devuelve columnas: numero_comparendo, fecha_imposicion, fecha_notificacion
    """
    import unicodedata

    def _norm(s: str) -> str:
        if s is None or (isinstance(s, float) and pd.isna(s)):
            s = ""
        s = str(s).strip().lower()
        s = "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")
        return s

    # leer sin header para detectar fila
    raw = pd.read_excel(xlsx_path_or_file, sheet_name=sheet_name, header=None, dtype=str)

    # detectar fila de encabezado por presencia de "numero" y "comparendo"
    header_row = None
    for i in range(min(60, len(raw))):
        row_norm = [_norm(v) for v in raw.iloc[i].tolist()]
        joined = " | ".join(row_norm)
        if "numero" in joined and "comparendo" in joined:
            header_row = i
            break
    if header_row is None:
        header_row = 6  # fallback típico cuando empieza en C7

    header = raw.iloc[header_row].astype(str).tolist()
    df = raw.iloc[header_row + 1:].copy()
    df.columns = [str(c).strip() for c in header]
    df = df.dropna(axis=1, how="all")

    # localizar columnas
    cols_norm = {_norm(c): c for c in df.columns}

    def _find_col_by_keywords(*keywords) -> str:
        kw = [_norm(k) for k in keywords]
        for norm_name, real in cols_norm.items():
            if all(k in norm_name for k in kw):
                return real
        for norm_name, real in cols_norm.items():
            if any(k in norm_name for k in kw):
                return real
        raise KeyError(f"No encontré una columna que parezca {keywords} en {list(df.columns)}")

    col_num = _find_col_by_keywords("numero","comparendo")
    try:
        col_f_imp = _find_col_by_keywords("fecha","comparendo")
    except KeyError:
        col_f_imp = _find_col_by_keywords("fecha","imposicion")

    # Columna I explícita para notificación (índice 8) + fallback por nombre
    if df.shape[1] > 8:
        serie_f_notif = df.iloc[:, 8]
    else:
        serie_f_notif = df[_find_col_by_keywords("fecha","notificacion")]

    out = pd.DataFrame({
        "numero_comparendo": df[col_num].astype(str).str.strip(),
        "fecha_imposicion": _to_date(df[col_f_imp]),
        "fecha_notificacion": _to_date(serie_f_notif),
    })

    out["numero_comparendo"] = (
        out["numero_comparendo"].replace({r"^\s*(nan|none|null|-)?\s*$": pd.NA}, regex=True)
    )
    out = out[out["numero_comparendo"].notna()].reset_index(drop=True)
    return out

# --- Preparación de HOY (registros crudos de parsers) ---

def prepare_today_df(df_today_raw: pd.DataFrame) -> pd.DataFrame:
    if df_today_raw is None or df_today_raw.empty:
        return pd.DataFrame(columns=["numero_comparendo","fecha_imposicion","fecha_notificacion","plataforma"])
    df = df_today_raw.copy()
    if "fecha_imposicion" in df.columns:
        df["fecha_imposicion"] = _to_date(df["fecha_imposicion"])
    else:
        df["fecha_imposicion"] = pd.NaT
    if "fecha_notificacion" in df.columns:
        df["fecha_notificacion"] = _to_date(df["fecha_notificacion"])
    else:
        df["fecha_notificacion"] = pd.NaT
    if "plataforma" not in df.columns:
        df["plataforma"] = pd.NA
    return df[["numero_comparendo","fecha_imposicion","fecha_notificacion","plataforma"]].copy()

# --- Comparador con memoria (LAST_SEEN) y caídas manuales ---

def compare_today_vs_yesterday(
    df_today_raw: pd.DataFrame,
    df_yesterday: pd.DataFrame,
    prev_last_seen: Optional[pd.DataFrame] = None,   # hoja LAST_SEEN del paquete anterior (opcional)
    manual_down_today: Optional[set[str]] = None,    # plataformas caídas marcadas manualmente
    grace_days: int = 2
) -> tuple[Dict[str, pd.DataFrame], Dict, pd.DataFrame]:
    """
    Devuelve (resultados, meta_out, last_seen_out)
    - resultados: dict con DataFrames 'nuevos','eliminados','mantenidos','modificados'
    - meta_out: {'grace_days': int, 'active_platforms': [...]}
    - last_seen_out: DataFrame actualizado (persistir como hoja LAST_SEEN)
    """
    ORDER = ["SIMIT","FENIX","MEDELLIN","BELLO","ITAGUI","MANIZALES","CALI",
             "BOLIVAR","SANTAMARTA","MAGDALENA","SOLEDAD"]
    LABEL = {
        "SIMIT":"Simit","FENIX":"Fenix","MEDELLIN":"Medellin","BELLO":"Bello","ITAGUI":"Itagui",
        "MANIZALES":"Manizales","CALI":"Cali","BOLIVAR":"Bolivar","SANTAMARTA":"Santa Marta",
        "MAGDALENA":"Magdalena","SOLEDAD":"Soledad"
    }

    def _clean_num_series(s: pd.Series) -> pd.Series:
        return s.astype(str).str.strip().replace({r"^\s*(nan|none|null|-)?\s*$": pd.NA}, regex=True)

    def _key_only_digits(s: pd.Series) -> pd.Series:
        return s.fillna("").astype(str).apply(lambda x: re.sub(r"\D", "", x))

    def _pick_display_num(nums: pd.Series) -> str:
        vals = [str(v) for v in nums.dropna().tolist()]
        with_letter = [v for v in vals if re.search(r"[A-Za-z]", v)]
        return with_letter[0] if with_letter else (vals[0] if vals else None)

    def _agg_platforms_pretty(s: pd.Series) -> str:
        vals = [str(v).upper() for v in s.dropna()]
        out = [LABEL[p] for p in ORDER if p in vals]
        return " - ".join(out) if out else None

    # helpers fechas límite (hábiles CO)
    def _f50(d):  # hasta el día 11 hábil siguiente
        return _busday_add_co(d, 11) if pd.notna(d) else pd.NaT
    def _f25(d):  # hasta el día 26 hábil siguiente
        return _busday_add_co(d, 26) if pd.notna(d) else pd.NaT

    # preparar data
    df_hoy = prepare_today_df(df_today_raw)
    df_ayer = df_yesterday[["numero_comparendo","fecha_imposicion","fecha_notificacion"]].copy()

    df_hoy["numero_comparendo"] = _clean_num_series(df_hoy["numero_comparendo"])
    df_ayer["numero_comparendo"] = _clean_num_series(df_ayer["numero_comparendo"])
    df_hoy = df_hoy[df_hoy["numero_comparendo"].notna()].copy()
    df_ayer = df_ayer[df_ayer["numero_comparendo"].notna()].copy()

    df_hoy["__key"] = _key_only_digits(df_hoy["numero_comparendo"])
    df_ayer["__key"] = _key_only_digits(df_ayer["numero_comparendo"])
    df_hoy["plat_code"] = df_hoy["plataforma"].astype(str).str.upper()

    active_today = set(df_hoy["plat_code"].dropna().unique())
    manual_down_today = set([p.upper() for p in (manual_down_today or set())])

    # LAST_SEEN previo
    prev_last_seen = prev_last_seen if (prev_last_seen is not None and not prev_last_seen.empty) else pd.DataFrame()
    if not prev_last_seen.empty:
        if "__key" not in prev_last_seen.columns and "key" in prev_last_seen.columns:
            prev_last_seen = prev_last_seen.rename(columns={"key":"__key"})
        for col in ["__key","numero_display","last_seen_platforms_codes","last_seen_date"]:
            if col not in prev_last_seen.columns:
                prev_last_seen[col] = pd.NA
        prev_last_seen["__key"] = prev_last_seen["__key"].astype(str)

    def _split_codes(x):
        return set([c.strip().upper() for c in str(x).split(",") if c.strip()])

    last_seen_map = {}
    last_seen_date_map = {}
    if not prev_last_seen.empty:
        last_seen_map = dict(zip(
            prev_last_seen["__key"],
            prev_last_seen["last_seen_platforms_codes"].apply(_split_codes)
        ))
        last_seen_date_map = dict(zip(
            prev_last_seen["__key"],
            pd.to_datetime(prev_last_seen["last_seen_date"], errors="coerce")
        ))

    set_hoy  = set(df_hoy["__key"])
    set_ayer = set(df_ayer["__key"])

    nuevos_keys     = set_hoy - set_ayer
    eliminados_keys = set_ayer - set_hoy
    comunes_keys    = set_hoy & set_ayer

    # ========================
    # NUEVOS (+ fechas límite)
    # ========================
    nuevos_raw = df_hoy[df_hoy["__key"].isin(nuevos_keys)].copy()
    nuevos = (
        nuevos_raw.sort_values(["__key"])
        .groupby("__key", as_index=False)
        .agg({
            "numero_comparendo": _pick_display_num,
            "fecha_imposicion": "first",
            "fecha_notificacion": "first",
            "plataforma": _agg_platforms_pretty,
        })
        .rename(columns={"plataforma":"plataformas"})
        .loc[:,["numero_comparendo","fecha_imposicion","fecha_notificacion","plataformas"]]
        .reset_index(drop=True)
    )
    # >>> aquí se agregan las columnas pedidas <<<
    nuevos["fecha_limite_50"] = nuevos["fecha_notificacion"].apply(_f50)
    nuevos["fecha_limite_25"] = nuevos["fecha_notificacion"].apply(_f25)
    # ordenar columnas (opcional)
    nuevos = nuevos[[
        "numero_comparendo","fecha_imposicion","fecha_notificacion",
        "plataformas","fecha_limite_50","fecha_limite_25"
    ]]

    # ELIMINADOS con filtro manual + LAST_SEEN
    eliminados_raw = df_ayer[df_ayer["__key"].isin(eliminados_keys)].copy()
    if not prev_last_seen.empty and manual_down_today:
        today = pd.Timestamp.today().normalize()
        def _keep_row(row) -> bool:
            key = row["__key"]
            prev_plats = last_seen_map.get(key, set())
            if prev_plats and prev_plats.issubset(manual_down_today):
                last_dt = last_seen_date_map.get(key, pd.NaT)
                if pd.isna(last_dt):
                    return False
                days_gap = (today - last_dt.normalize()).days
                return days_gap > grace_days
            return True
        eliminados_raw = eliminados_raw[eliminados_raw.apply(_keep_row, axis=1)].copy()

    eliminados = (
        eliminados_raw.sort_values(["__key"])
        .groupby("__key", as_index=False)
        .agg({
            "numero_comparendo": _pick_display_num,
            "fecha_imposicion": "first",
            "fecha_notificacion": "first",
        })
        .loc[:,["numero_comparendo","fecha_imposicion","fecha_notificacion"]]
        .reset_index(drop=True)
    )

    # MANTENIDOS
    mantenidos_raw = df_hoy[df_hoy["__key"].isin(comunes_keys)].copy()
    mantenidos = (
        mantenidos_raw.sort_values(["__key"])
        .groupby("__key", as_index=False)
        .agg({
            "numero_comparendo": _pick_display_num,
            "fecha_imposicion": "first",
            "fecha_notificacion": "first",
            "plataforma": _agg_platforms_pretty,
        })
        .rename(columns={"plataforma":"plataformas"})
        .loc[:,["numero_comparendo","fecha_imposicion","fecha_notificacion","plataformas"]]
        .reset_index(drop=True)
    )

    # MODIFICADOS (solo SIMIT)
    simit_hoy = (
        df_hoy[(df_hoy["__key"].isin(comunes_keys)) & (df_hoy["plat_code"]=="SIMIT")]
        .sort_values(["__key"])
        .groupby("__key", as_index=False)
        .agg({"numero_comparendo": _pick_display_num, "fecha_notificacion":"first"})
        .rename(columns={"fecha_notificacion":"fecha_notif_hoy"})
    )
    base_ayer = (
        df_ayer[df_ayer["__key"].isin(comunes_keys)]
        .sort_values(["__key"])
        .groupby("__key", as_index=False)
        .agg({"numero_comparendo": _pick_display_num, "fecha_notificacion":"first"})
        .rename(columns={"fecha_notificacion":"fecha_notif_ayer"})
    )
    cmp = pd.merge(base_ayer, simit_hoy, on="__key", how="inner", suffixes=("_ayer_num","_hoy_num"))

    def _status(row):
        hoy = row["fecha_notif_hoy"]; ayer = row["fecha_notif_ayer"]
        if pd.isna(ayer) and pd.notna(hoy): return "actualizada"
        if pd.notna(ayer) and pd.notna(hoy) and hoy.normalize()!=ayer.normalize(): return "modificada"
        return None

    cmp["estado_notif"] = cmp.apply(_status, axis=1)
    modificados = cmp[cmp["estado_notif"].notna()].copy()

    modificados["fecha_limite_50"] = modificados["fecha_notif_hoy"].apply(_f50)
    modificados["fecha_limite_25"] = modificados["fecha_notif_hoy"].apply(_f25)

    def _disp_num(row):
        return _pick_display_num(pd.Series([row.get("numero_comparendo_ayer_num"), row.get("numero_comparendo_hoy_num")]))
    modificados["numero_comparendo"] = modificados.apply(_disp_num, axis=1)

    modificados = modificados[[
        "numero_comparendo","fecha_notif_ayer","fecha_notif_hoy",
        "estado_notif","fecha_limite_50","fecha_limite_25"
    ]].sort_values("numero_comparendo").reset_index(drop=True)

    # LAST_SEEN actualizado
    today = pd.Timestamp.today().normalize()
    today_map = (
        df_hoy.groupby("__key")
        .agg(num_disp=("numero_comparendo", _pick_display_num),
             plats=("plat_code", lambda s: set([p for p in s.dropna()])))
        .reset_index()
    )
    rows = []
    for _, r in today_map.iterrows():
        codes = sorted(list(r["plats"]))
        rows.append({
            "__key": r["__key"],
            "numero_display": r["num_disp"],
            "last_seen_platforms": " - ".join([LABEL[c] for c in ORDER if c in codes]) if codes else None,
            "last_seen_platforms_codes": ",".join(codes),
            "last_seen_date": today,
        })
    df_today_seen = pd.DataFrame(rows)

    if prev_last_seen is None or prev_last_seen.empty:
        last_seen_out = df_today_seen
    else:
        last_seen_out = prev_last_seen.copy()
        if "__key" not in last_seen_out.columns:
            last_seen_out["__key"] = last_seen_out.get("key", pd.Series(dtype=str))
        last_seen_out = last_seen_out.set_index("__key")
        df_today_seen = df_today_seen.set_index("__key")
        last_seen_out.update(df_today_seen)
        new_keys = df_today_seen.index.difference(last_seen_out.index)
        if len(new_keys) > 0:
            last_seen_out = pd.concat([last_seen_out, df_today_seen.loc[new_keys]], axis=0)
        last_seen_out = last_seen_out.reset_index()

    meta_out = {
        "grace_days": int(grace_days),
        "active_platforms": sorted(list(active_today)),
    }

    return {
        "nuevos": nuevos,
        "eliminados": eliminados,
        "mantenidos": mantenidos,
        "modificados": modificados,
    }, meta_out, last_seen_out
