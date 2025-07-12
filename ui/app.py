import sys, pathlib
# ── añade la carpeta raíz del proyecto al PYTHONPATH ───────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ui/app.py
import sys, pathlib, io
import streamlit as st, pandas as pd
from core import run_extract, PARSERS
from ui.excel_reader import resumen_desde_excel
from ui.email_draft import build_email

# ── ruta raíz al PYTHONPATH ─────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Comparador de comparendos", layout="wide")
st.title("🔍 Comparador de comparendos")

platforms = [p for p in [
    "SIMIT","FENIX","MEDELLIN","MAGDALENA","BELLO","ITAGUI",
    "MANIZALES","CALI","SOLEDAD","BOLIVAR","SANTA MARTA"
] if p in PARSERS]

# 1) bloques
st.header("1️⃣ Pega el texto de cada plataforma")
blocks = {p: st.text_area(f"{p} ⤵️", height=150) for p in platforms}
blocks = {p: t for p, t in blocks.items() if t.strip()}

# 2) Excel viejo
st.header("2️⃣ Sube el Excel de ayer (hoja COMPARENDOS, encabezado fila 7)")
xls_old = st.file_uploader("Excel de ayer (.xlsx)", type=["xlsx"])

# ── Procesar ───────────────────────────
if st.button("▶️ Procesar"):
    if not blocks or not xls_old:
        st.warning("Faltan bloques o Excel."); st.stop()

    # TXT sintético
    tmptxt = pathlib.Path("tmp.txt")
    tmptxt.write_text(
        "\n".join(sum(([p, blocks[p].strip()] for p in platforms if p in blocks), [])),
        encoding="utf-8"
    )

    detalle_new, resumen_new = run_extract(tmptxt)
    resumen_old = resumen_desde_excel(xls_old)

    set_new, set_old = set(resumen_new["id_key"]), set(resumen_old["id_key"])
    comunes, añadidos, eliminados = map(sorted, (set_new & set_old,
                                                 set_new - set_old,
                                                 set_old - set_new))

    # mapa info
    dict_info = (pd.concat([resumen_old, resumen_new])
                   .drop_duplicates("id_key", keep="last")
                   .set_index("id_key")[["comparendo","fuentes"]]
                   .to_dict(orient="index"))

    def df(keys):
        return pd.DataFrame({
            "comparendo": [dict_info[k]["comparendo"] for k in keys],
            "fuentes":    [dict_info[k]["fuentes"]    for k in keys],
        })

    df_mant, df_add, df_del = df(comunes), df(añadidos), df(eliminados)

    # Mostrar
    st.subheader("Resumen de hoy")
    st.dataframe(resumen_new[["comparendo","fuentes","veces"]], use_container_width=True)

    a,b,c = st.columns(3)
    a.metric("Se mantienen", len(df_mant))
    b.metric("Añadidos", len(df_add))
    c.metric("Eliminados", len(df_del))
    with a: st.dataframe(df_mant)
    with b: st.dataframe(df_add)
    with c: st.dataframe(df_del)

    # Borrador de correo
    st.subheader("Borrador de correo")
    st.text_area("Cuerpo", build_email(df_add, df_del, df_mant), height=400)

    # Descargar Excel
    buf = io.BytesIO()
    with pd.ExcelWriter(buf) as xl:
        detalle_new.to_excel(xl, index=False, sheet_name="detallado_hoy")
        resumen_new.to_excel(xl, index=False, sheet_name="resumen_hoy")
        df_mant.to_excel(xl, index=False, sheet_name="mantienen")
        df_add.to_excel(xl, index=False, sheet_name="añadidos")
        df_del.to_excel(xl, index=False, sheet_name="eliminados")

    st.download_button("💾 Descargar Excel completo",
                       data=buf.getvalue(),
                       file_name="comparendos_resultado.xlsx")
else:
    st.info("Pega los bloques y sube el Excel para comenzar.")
