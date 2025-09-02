# modificados.py
from __future__ import annotations
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd

try:
    import holidays
except ImportError:  # pragma: no cover
    holidays = None  # lo reportamos en la UI

from aggregator import canonical_num

# Token de comparendo dentro de una celda (letra opcional + 11+ dígitos)
_ALNUM_TOKEN_RE = re.compile(r"[A-Za-z0-9]{11,}")

def _iter_comparendos_in_cell(cell_text: str):
    if not cell_text:
        return
    s = str(cell_text)
    s = re.sub(r"[\s\.\-_/]", "", s)  # normaliza separadores
    for m in _ALNUM_TOKEN_RE.finditer(s):
        tok = m.group(0)
        if sum(ch.isdigit() for ch in tok) >= 11:
            yield tok

def _parse_date(s: Any) -> str:
    """Normaliza a YYYY-MM-DD si reconoce fecha; si no, devuelve ''."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    if isinstance(s, (pd.Timestamp, datetime)):
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    txt = str(s).strip()
    if not txt or txt.lower() in ("nan", "none", "no aplica"):
        return ""
    # dd/mm/yyyy o dd/mm/yy
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(txt, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    # yyyy-mm-dd
    try:
        return pd.to_datetime(txt, errors="raise").strftime("%Y-%m-%d")
    except Exception:
        return ""

def _to_date(d: str) -> Optional[datetime]:
    if not d:
        return None
    try:
        return datetime.strptime(d, "%Y-%m-%d")
    except Exception:
        return None

def _col_business_add(start: datetime, n_days: int, co_holidays=None) -> datetime:
    """
    Suma n días hábiles a partir del día siguiente a 'start'.
    n_days=1 => primer día hábil después de start.

    co_holidays: colección con fechas festivas (p. ej., holidays.Colombia()).
                 Si es None, se asume "sin festivos" y solo se excluyen fines de semana.
    """
    if n_days <= 0:
        return start
    if co_holidays is None:
        # Evita errores si no pasamos festivos explícitos
        class _NoHolidays(set):
            def __contains__(self, d):  # noqa: N802
                return False
        co_holidays = _NoHolidays()

    cur = start
    added = 0
    while added < n_days:
        cur += timedelta(days=1)
        if (cur.weekday() < 5) and (cur not in co_holidays):
            added += 1
    return cur


def _calc_windows(notif_hoy: str) -> Tuple[str, str, str]:
    """
    Devuelve (limite_50, desde_25, hasta_25) como YYYY-MM-DD, o '' si no aplica.
    """
    if not notif_hoy or holidays is None:
        return "", "", ""
    d0 = _to_date(notif_hoy)
    if not d0:
        return "", "", ""

    co_holidays = holidays.Colombia()  # festivos Colombia

    # 50%: hasta el día hábil 11 (contado desde el día siguiente a la notificación)
    limit_50 = _col_business_add(d0, 11, co_holidays)

    # 25%: desde el día hábil 12 hasta el 26
    from_25 = _col_business_add(d0, 12, co_holidays)
    to_25   = _col_business_add(d0, 26, co_holidays)

    return limit_50.strftime("%Y-%m-%d"), from_25.strftime("%Y-%m-%d"), to_25.strftime("%Y-%m-%d")


def build_modificados_table(
    rows_today_simit: List[Dict[str, Any]],
    df_yesterday_any: pd.DataFrame,
    header_row_excel_1based: int = 7,  # encabezado en fila 7 => datos desde 8
    notif_col_idx: int = 8,            # I = 9na columna (0-based 8)
) -> pd.DataFrame:
    """
    Compara SIMIT (HOY) vs Excel AYER (personal).
    - 'rows_today_simit' viene de lo pegado hoy (pestaña SIMIT), crudo (sin agregar).
    - 'df_yesterday_any' es el Excel personal sin encabezados (hoja 0, header=None).
    Reglas:
      * Si existe ayer y hoy:
          - notif_ayer != notif_hoy -> MODIFICADO
          - notif_ayer == '' y notif_hoy != '' -> ACTUALIZADO
    Calcula ventanas de descuento 50% y 25% desde notif_hoy (días hábiles Colombia).
    """
    # Mapa AYER: clave canónica -> fecha_notif_ayer (normalizada) + placa si logramos
    y_map: Dict[str, Dict[str, str]] = {}
    n_rows, n_cols = df_yesterday_any.shape if isinstance(df_yesterday_any, pd.DataFrame) else (0, 0)
    start_idx = header_row_excel_1based

    for i in range(min(start_idx, n_rows), n_rows):
        row_vals = df_yesterday_any.iloc[i, :].astype(str).str.strip().tolist()
        notif_ayer = ""
        if notif_col_idx < n_cols:
            notif_ayer = _parse_date(df_yesterday_any.iat[i, notif_col_idx])

        # Extrae todos los comparendos que hubiere en la fila
        comps_in_row: List[str] = []
        for v in row_vals:
            if not v or v.lower() in ("nan", "none"):
                continue
            for token in _iter_comparendos_in_cell(v):
                comps_in_row.append(token)

        for num in comps_in_row:
            key = canonical_num(num)
            if key not in y_map:
                y_map[key] = {"notif_ayer": notif_ayer}

    # Recorre HOY SIMIT
    out_rows: List[Dict[str, Any]] = []
    for r in rows_today_simit:
        num = str(r.get("numero_comparendo", "")).strip()
        if not num:
            continue
        key = canonical_num(num)
        today_notif = _parse_date(r.get("fecha_notificacion", ""))
        if key not in y_map:
            continue  # no existe ayer: no entra a modificados

        notif_ayer = y_map[key].get("notif_ayer", "")
        estado = ""
        if not notif_ayer and today_notif:
            estado = "ACTUALIZADO"
        elif notif_ayer and today_notif and (notif_ayer != today_notif):
            estado = "MODIFICADO"
        else:
            continue  # sin cambio relevante

        limite_50, desde_25, hasta_25 = _calc_windows(today_notif)

        out_rows.append({
            "numero_comparendo": num,
            "placa": str(r.get("placa", "")).strip().upper(),
            "notif_ayer": notif_ayer,
            "notif_hoy": today_notif,
            "estado": estado,
            "50_desc_hasta": limite_50,
            "25_desc_hasta": hasta_25,
        })

    cols = ["numero_comparendo","placa","notif_ayer","notif_hoy","estado","50_desc_hasta","25_desc_hasta"]
    df = pd.DataFrame(out_rows, columns=cols)
    if not df.empty:
        df.sort_values(["estado","numero_comparendo"], kind="stable", inplace=True)
        df.reset_index(drop=True, inplace=True)
    return df
