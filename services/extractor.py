"""
services/extractor.py

Provides functionality to build a temporary text file from raw text blocks
and compare extracted comparendo data against a reference Excel dataset.

Functions:
  build_tmp_txt(blocks: dict[str, str]) -> pathlib.Path
    Merge named text blocks into a single temporary .txt file, preserving
    section headers for downstream parsing.

  compare(blocks: dict[str, str], xls_old) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]
    1. Builds a merged text file from the provided blocks.
    2. Runs parsers on the text to produce 'detalle_new' (raw entries) and
       'resumen_new' (aggregated summary) DataFrames.
    3. Reads the previous day's summary ('resumen_old') from the given Excel.
    4. Computes maintained, added, and deleted comparendos by comparing
       ID keys between new and old summaries.
    5. Returns a tuple:
       - detalle_new: full parsed rows for today
       - resumen_new: aggregated summary for today
       - df_mant    : maintained comparendos
       - df_add     : newly added comparendos
       - df_del     : deleted comparendos
"""


# services/extractor.py
import pathlib, io
import pandas as pd
from core import run_extract
from ui.excel_reader import resumen_desde_excel

def build_tmp_txt(blocks: dict[str, str]) -> pathlib.Path:
    """Une en un .txt temporal todos los bloques separados por sección."""
    tmp = pathlib.Path("tmp.txt")
    lines = []
    for name, txt in blocks.items():
        lines.extend([name, txt.strip()])
    tmp.write_text("\n".join(lines), encoding="utf-8")
    return tmp

def compare(blocks: dict[str, str], xls_old) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Devuelve: detalle_new, resumen_new, df_mant, df_add, df_del
    """
    tmp_txt = build_tmp_txt(blocks)

    detalle_new, resumen_new = run_extract(tmp_txt)
    resumen_old             = resumen_desde_excel(xls_old)

    set_new, set_old   = set(resumen_new.id_key), set(resumen_old.id_key)
    comunes            = sorted(set_new & set_old)
    añadidos, eliminados = sorted(set_new - set_old), sorted(set_old - set_new)

    # map id_key → info (última versión)
    dict_info = (
        pd.concat([resumen_old, resumen_new])
          .drop_duplicates("id_key", keep="last")
          .set_index("id_key").to_dict(orient="index")
    )

    def _df(keys):
        return pd.DataFrame({
            "comparendo":[dict_info[k]["comparendo"] for k in keys],
            "placa":     [dict_info[k]["placa"]      for k in keys],
            "fuentes":   [dict_info[k]["fuentes"]    for k in keys],
        })

    return detalle_new, resumen_new, _df(comunes), _df(añadidos), _df(eliminados)
