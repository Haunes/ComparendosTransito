from __future__ import annotations
import re
import pandas as pd
from typing import Dict, Any, List

_DIGITS_RE = re.compile(r"\d+")
def canonical_num(num: str) -> str:
    if not num: return ""
    digits = "".join(_DIGITS_RE.findall(str(num)))
    return digits if len(digits) >= 11 else digits


def has_leading_letter(num: str) -> bool:
    s = (num or "").strip()
    return bool(re.match(r"^[A-Za-z]\d{8,}$", s))

def aggregate_by_comparendo(df: pd.DataFrame, platform_order: List[str]) -> pd.DataFrame:
    """
    Agrega por número canónico (ignora una letra inicial SOLO para equivalencia).
    - numero_comparendo mostrado: si existe versión con letra, se prioriza esa.
    - plataformas: unión única de plataformas (ordenada por platform_order), separadas por '-'.
    - numero_veces: cantidad de plataformas únicas.
    - fecha_imposicion / fecha_notificacion / placa: primeras no vacías encontradas.
    """
    if df.empty:
        return pd.DataFrame(columns=[
            "numero_comparendo","fecha_imposicion","fecha_notificacion","placa","plataformas","numero_veces"
        ])

    order_index = {p: i for i, p in enumerate(platform_order)}
    buckets: Dict[str, Dict[str, Any]] = {}

    for _, row in df.iterrows():
        original_num = str(row.get("numero_comparendo", "")).strip()
        if not original_num:
            continue
        key = canonical_num(original_num)
        bucket = buckets.setdefault(key, {
            "numero_comparendo": "",
            "fecha_imposicion": "",
            "fecha_notificacion": "",
            "placa": "",
            "plataformas_list": [],
            "plataformas_set": set(),
        })

        # Preferir mostrar con letra si aparece
        chosen = bucket["numero_comparendo"]
        if not chosen:
            bucket["numero_comparendo"] = original_num
        else:
            if (not has_leading_letter(chosen)) and has_leading_letter(original_num):
                bucket["numero_comparendo"] = original_num

        fi = str(row.get("fecha_imposicion", "")).strip()
        fn = str(row.get("fecha_notificacion", "")).strip()
        pl = str(row.get("placa", "")).strip()
        if fi and not bucket["fecha_imposicion"]:
            bucket["fecha_imposicion"] = fi
        if fn and not bucket["fecha_notificacion"]:
            bucket["fecha_notificacion"] = fn
        if pl and not bucket["placa"]:
            bucket["placa"] = pl

        # Plataformas únicas con orden estable
        plat = str(row.get("plataforma", "")).strip() or str(row.get("plataformas", "")).strip()
        if plat and plat not in bucket["plataformas_set"]:
            bucket["plataformas_set"].add(plat)
            bucket["plataformas_list"].append(plat)

    rows: List[Dict[str, Any]] = []
    for _, b in buckets.items():
        uniq_plats = sorted(set(b["plataformas_list"]), key=lambda x: order_index.get(x, 10**6))
        rows.append({
            "numero_comparendo": b["numero_comparendo"],
            "fecha_imposicion": b["fecha_imposicion"],
            "fecha_notificacion": b["fecha_notificacion"],
            "placa": b["placa"],
            "plataformas": "-".join(uniq_plats),
            "numero_veces": len(uniq_plats),
        })

    out = pd.DataFrame(rows, columns=[
        "numero_comparendo","fecha_imposicion","fecha_notificacion","placa","plataformas","numero_veces"
    ])
    if not out.empty:
        out = out.sort_values(["numero_comparendo","plataformas"], kind="stable").reset_index(drop=True)
    return out
