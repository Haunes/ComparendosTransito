from __future__ import annotations
import re
import pandas as pd
from typing import Tuple, List, Dict, Any, Set
from datetime import datetime
from aggregator import canonical_num  # solo dígitos
from collections import defaultdict

# -------------------- Regex auxiliares --------------------
_PLATE_INLINE_RE = re.compile(
    r"([A-Za-z]{3}\d{3}|[A-Za-z]{3}\d{2}[A-Za-z]|[A-Za-z]{2}\d{3}[A-Za-z])"
)
_DATE_INLINE_RE = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b")
_ALNUM_TOKEN_RE = re.compile(r"[A-Za-z0-9]{11,}")

# -------------------- Utils --------------------

def _platforms_map_from_summary(df_prev_summary: pd.DataFrame) -> Dict[str, str]:
    """
    Construye un mapa: clave_canónica -> 'Plataforma1-Plataforma2-...'
    a partir del DataFrame normalizado del Resumen de AYER (una fila por plataforma).
    """
    if df_prev_summary is None or df_prev_summary.empty:
        return {}
    acc: Dict[str, Set[str]] = defaultdict(set)
    for _, r in df_prev_summary.iterrows():
        num = str(r.get("numero_comparendo", "")).strip()
        key = canonical_num(num)
        if not key:
            continue
        plat = str(r.get("plataforma", "")).strip()
        if not plat:
            continue
        acc[key].add(plat)
    # join estable por orden alfabético (insensible a mayúsculas)
    return {k: "-".join(sorted(list(v), key=str.lower)) for k, v in acc.items()}
def _to_str_date_like(v: Any) -> str:
    if pd.isna(v):
        return ""
    if isinstance(v, (pd.Timestamp, datetime)):
        return v.strftime("%Y-%m-%d")
    s = str(v).strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    try:
        return pd.to_datetime(s, errors="raise").strftime("%Y-%m-%d")
    except Exception:
        return s

def _find_plate_in_row(row_vals: List[str]) -> str:
    for raw in row_vals:
        if not raw or str(raw).lower() in ("nan", "none"):
            continue
        s = re.sub(r"[\s\-]", "", str(raw).upper())
        m = _PLATE_INLINE_RE.search(s)
        if m:
            return m.group(1).upper()
    return ""

def _find_dates_in_row(row_vals: List[str]) -> List[str]:
    out: List[str] = []
    for raw in row_vals:
        if not raw:
            continue
        for m in _DATE_INLINE_RE.findall(str(raw)):
            out.append(_to_str_date_like(m))
    return out

def _iter_comparendos_in_cell(cell_text: str):
    """
    - Normaliza removiendo espacios, guiones, puntos, slashes, underscores, etc.
    - Busca tokens alfanuméricos y filtra los que tengan >=11 dígitos.
    """
    if not cell_text:
        return
    s = str(cell_text)
    s = re.sub(r"[\s\.\-_/]", "", s)  # <--- normalización importante
    for m in _ALNUM_TOKEN_RE.finditer(s):
        tok = m.group(0)
        if sum(ch.isdigit() for ch in tok) >= 11:
            yield tok

# -------------------- Extracción AYER --------------------
def extract_comparendos_rowwise_with_dates(
    df_yesterday_any: pd.DataFrame,
    date_imp_col_idx: int = 7,
    date_notif_col_idx: int = 8,
    plate_col_idx: int = 1,
    header_row_excel_1based: int = 7,
) -> Tuple[Dict[str,str], set, Dict[str, Dict[str,str]]]:
    y_original: Dict[str, str] = {}
    yesterday_set = set()
    y_data: Dict[str, Dict[str, str]] = {}

    n_rows, n_cols = df_yesterday_any.shape if isinstance(df_yesterday_any, pd.DataFrame) else (0, 0)
    data_start_idx = header_row_excel_1based

    for i in range(min(data_start_idx, n_rows), n_rows):
        row_vals = df_yesterday_any.iloc[i, :].astype(str).str.strip().tolist()

        comps_in_row: List[str] = []
        for v in row_vals:
            if not v or v.lower() in ("nan", "none"):
                continue
            for token in _iter_comparendos_in_cell(v):
                comps_in_row.append(token)

        if not comps_in_row:
            continue

        imp_ayer = _to_str_date_like(df_yesterday_any.iat[i, date_imp_col_idx]) if date_imp_col_idx < n_cols else ""
        notif_ayer = _to_str_date_like(df_yesterday_any.iat[i, date_notif_col_idx]) if date_notif_col_idx < n_cols else ""

        if not imp_ayer or not notif_ayer:
            dates_inline = _find_dates_in_row(row_vals)
            if not imp_ayer and len(dates_inline) >= 1:
                imp_ayer = dates_inline[0]
            if not notif_ayer and len(dates_inline) >= 2:
                notif_ayer = dates_inline[1]

        placa_ayer = ""
        if plate_col_idx < n_cols:
            val = df_yesterday_any.iat[i, plate_col_idx]
            if not pd.isna(val):
                placa_ayer = re.sub(r"[\s\-]", "", str(val).upper()).strip()
        if not placa_ayer:
            placa_ayer = _find_plate_in_row(row_vals)

        for val in comps_in_row:
            key = canonical_num(val)  # solo dígitos
            if not key:
                continue
            yesterday_set.add(key)
            if key not in y_original:
                y_original[key] = val
            if key not in y_data:
                y_data[key] = {
                    "imp_ayer": imp_ayer,
                    "notif_ayer": notif_ayer,
                    "placa_ayer": placa_ayer,
                }

    return y_original, yesterday_set, y_data

# -------------------- HOY --------------------
def _today_key_set(df_today: pd.DataFrame) -> Tuple[set, Dict[str, Dict[str,str]]]:
    tset = set()
    tdata: Dict[str, Dict[str,str]] = {}
    if df_today is None or df_today.empty:
        return tset, tdata

    for _, r in df_today.iterrows():
        num = str(r.get("numero_comparendo", "")).strip()
        key = canonical_num(num)  # solo dígitos (coherente con AYER)
        if not key:
            continue
        tset.add(key)
        if key not in tdata:
            tdata[key] = {
                "numero_comparendo": num,
                "fecha_imposicion": str(r.get("fecha_imposicion", "")).strip(),
                "fecha_notificacion": str(r.get("fecha_notificacion", "")).strip(),
                "placa": str(r.get("placa", "")).strip(),
                "plataformas": str(r.get("plataformas", r.get("plataforma",""))).strip(),
                "numero_veces": r.get("numero_veces",""),
            }
    return tset, tdata

# -------------------- Construcción de tablas --------------------
def build_three_tables(
    df_today: pd.DataFrame,
    df_yesterday_any: pd.DataFrame,
    date_imp_col_idx: int = 7,
    date_notif_col_idx: int = 8,
    plate_col_idx: int = 1,
    header_row_excel_1based: int = 7,
    df_prev_summary: pd.DataFrame | None = None,
) -> Dict[str, pd.DataFrame]:
    y_original, yesterday_set, y_data = extract_comparendos_rowwise_with_dates(
        df_yesterday_any,
        date_imp_col_idx=date_imp_col_idx,
        date_notif_col_idx=date_notif_col_idx,
        plate_col_idx=plate_col_idx,
        header_row_excel_1based=header_row_excel_1based,
    )
    platmap_ayer: Dict[str, str] = _platforms_map_from_summary(df_prev_summary) if df_prev_summary is not None else {}

    today_set, today_map = _today_key_set(df_today)

    nuevos     = sorted(today_set - yesterday_set)
    eliminados = sorted(yesterday_set - today_set)
    mantenidos = sorted(today_set & yesterday_set)

    cols = ["numero_comparendo","fecha_imposicion","fecha_notificacion","placa","plataformas","numero_veces","estado"]
    rows_nuevos, rows_mant, rows_elim = [], [], []

    for k in nuevos:
        t = today_map.get(k, {})
        rows_nuevos.append({
            "numero_comparendo": t.get("numero_comparendo",""),
            "fecha_imposicion": t.get("fecha_imposicion",""),
            "fecha_notificacion": t.get("fecha_notificacion",""),
            "placa": t.get("placa",""),
            "plataformas": t.get("plataformas",""),
            "numero_veces": t.get("numero_veces",""),
            "estado": "NUEVO",
        })

    for k in mantenidos:
        t = today_map.get(k, {})
        rows_mant.append({
            "numero_comparendo": t.get("numero_comparendo",""),
            "fecha_imposicion": t.get("fecha_imposicion",""),
            "fecha_notificacion": t.get("fecha_notificacion",""),
            "placa": t.get("placa",""),
            "plataformas": t.get("plataformas",""),
            "numero_veces": t.get("numero_veces",""),
            "estado": "MANTENIDO",
        })

    for k in eliminados:
        orig = y_original.get(k, k)
        d = y_data.get(k, {})
        rows_elim.append({
            "numero_comparendo": orig,
            "fecha_imposicion": d.get("imp_ayer",""),
            "fecha_notificacion": d.get("notif_ayer",""),
            "placa": d.get("placa_ayer",""),
            "plataformas": platmap_ayer.get(k, ""),
            "plataformas": "",
            "numero_veces": "",
            "estado": "ELIMINADO",
        })

    df_nuevos = pd.DataFrame(rows_nuevos, columns=cols)
    df_mant   = pd.DataFrame(rows_mant,   columns=cols)
    df_elim   = pd.DataFrame(rows_elim,   columns=cols)

    for dfx in (df_nuevos, df_mant, df_elim):
        if not dfx.empty:
            dfx.sort_values(["numero_comparendo"], kind="stable", inplace=True)
            dfx.reset_index(drop=True, inplace=True)

    return {"NUEVOS": df_nuevos, "MANTENIDOS": df_mant, "ELIMINADOS": df_elim}
