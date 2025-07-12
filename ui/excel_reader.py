import sys, pathlib
# ── añade la carpeta raíz del proyecto al PYTHONPATH ───────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ui/excel_reader.py
import pandas as pd
from core.clean import id_key, norm

def resumen_desde_excel(uploaded):
    """
    Lee la hoja COMPARENDOS (encabezado fila 7) y devuelve:
    id_key | comparendo | fuentes | veces
    """
    df = pd.read_excel(uploaded, sheet_name="COMPARENDOS", header=6)

    col = next((c for c in df.columns
                if all(tk in norm(c) for tk in ("numero", "comparendo"))), None)
    if col is None:
        raise ValueError("No hallé la columna 'Número de Comparendo' en fila 7")

    # crea DataFrame temporal con el valor crudo y su clave numérica
    tmp = (df[[col]]
             .rename(columns={col: "comparendo"})
             .assign(comparendo=lambda d: d["comparendo"].astype(str).str.strip(),
                     id_key     =lambda d: d["comparendo"].apply(id_key)))

    # descarta vacíos / nan
    tmp = tmp[tmp["id_key"].ne("") & tmp["id_key"].ne("NAN")]

    resumen = (tmp.groupby("id_key", as_index=False)
                 .agg(comparendo=("comparendo", "first"),
                      veces     =("comparendo", "size"))
                 .assign(fuentes="ANTERIOR"))

    return resumen
