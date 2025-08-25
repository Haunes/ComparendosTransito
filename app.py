# app.py
import streamlit as st
import pandas as pd
import io
from datetime import datetime

from ui_front import render_header, render_tabs_and_inputs, render_results_table
from services import parse_text_by_platform
from comparator import load_yesterday_excel, compare_today_vs_yesterday

st.set_page_config(page_title="Comparendos - Reconocedor", layout="wide")
render_header()

# --- Pestañas e ingreso de texto ---
should_process = render_tabs_and_inputs()

all_records = []
debug_lines = []

if should_process:
    inputs = {
        "SIMIT": st.session_state.get("txt_SIMIT", ""),
        "FENIX": st.session_state.get("txt_FENIX", ""),
        "MEDELLIN": st.session_state.get("txt_MEDELLIN", ""),
        "BELLO": st.session_state.get("txt_BELLO", ""),
        "ITAGUI": st.session_state.get("txt_ITAGUI", ""),
        "MANIZALES": st.session_state.get("txt_MANIZALES", ""),
        "CALI": st.session_state.get("txt_CALI", ""),
        "BOLIVAR": st.session_state.get("txt_BOLIVAR", ""),
        "SANTAMARTA": st.session_state.get("txt_SANTAMARTA", ""),
    }
    with st.spinner("Procesando texto de todas las pestañas..."):
        for platform, raw in inputs.items():
            if not raw or not raw.strip():
                continue
            recs, dbg = parse_text_by_platform(platform, raw)
            all_records.extend(recs)
            debug_lines.append(f"== {platform} ==\n{dbg}")

render_results_table(all_records, "\n\n".join(debug_lines) if debug_lines else None)

st.markdown(
    "<div style='margin-top:1rem; opacity:.6'>v0.6 · Comparación con plataformas caídas manual + memoria LAST_SEEN</div>",
    unsafe_allow_html=True,
)

# --- Comparación Hoy vs Ayer ---
st.header("📊 Comparación Hoy vs Ayer")

# Archivo oficial anterior (solo COMPARENDOS)
uploaded_file = st.file_uploader("Sube el Excel del día anterior (COMPARENDOS)", type=["xlsx"])

# Paquete de AYER generado por la app (opcional) para memoria (LAST_SEEN)
prev_pkg = st.file_uploader("Sube el paquete de AYER (opcional, para memoria LAST_SEEN)", type=["xlsx"], key="prev_pkg2")

# Plataformas caídas HOY (selección manual)
PLAT_OPTS = [
    "SIMIT","FENIX","MEDELLIN","BELLO","ITAGUI","MANIZALES","CALI",
    "BOLIVAR","SANTAMARTA","MAGDALENA","SOLEDAD" ]
down_today = st.multiselect("Plataformas caídas hoy (manual)", PLAT_OPTS)

if uploaded_file is not None and all_records:
    xls = pd.ExcelFile(uploaded_file)
    df_ayer = load_yesterday_excel(xls, sheet_name="COMPARENDOS")
    df_hoy = pd.DataFrame(all_records)

    # Cargar LAST_SEEN del paquete de AYER si se proporcionó
    prev_last_seen = None
    if prev_pkg is not None:
        xls_prev = pd.ExcelFile(prev_pkg)
        if "LAST_SEEN" in xls_prev.sheet_names:
            prev_last_seen = pd.read_excel(xls_prev, sheet_name="LAST_SEEN")

    resultados, meta_out, last_seen_out = compare_today_vs_yesterday(
        df_hoy, df_ayer,
        prev_last_seen=prev_last_seen,
        manual_down_today=set(down_today) if down_today else None,
        grace_days=2,
    )

    # Resumen
    counts = {k: len(v) for k, v in resultados.items()}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nuevos", counts.get("nuevos", 0))
    c2.metric("Eliminados", counts.get("eliminados", 0))
    c3.metric("Mantenidos", counts.get("mantenidos", 0))
    c4.metric("Modificados", counts.get("modificados", 0))

    # Tablas
    st.subheader("✅ Nuevos")
    st.dataframe(resultados["nuevos"], use_container_width=True)

    st.subheader("❌ Eliminados (con caídas manuales + LAST_SEEN)")
    st.dataframe(resultados["eliminados"], use_container_width=True)

    st.subheader("📌 Mantenidos")
    st.dataframe(resultados["mantenidos"], use_container_width=True)

    st.subheader("✏️ Modificados (SIMIT)")
    st.dataframe(resultados["modificados"], use_container_width=True)

    # Descargar paquete Excel (Hoy + Comparación + LAST_SEEN)
    df_hoy_full   = df_hoy
    df_nuevos     = resultados["nuevos"]
    df_eliminados = resultados["eliminados"]
    df_mantenidos = resultados["mantenidos"]
    df_modificados= resultados["modificados"]

    resumen_df = pd.DataFrame([{
        "nuevos": len(df_nuevos),
        "eliminados": len(df_eliminados),
        "mantenidos": len(df_mantenidos),
        "modificados": len(df_modificados),
        "hoy_total": len(df_hoy_full),
        "plataformas_caidas_hoy": ", ".join(down_today) if down_today else "",
    }])

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df_hoy_full.to_excel(writer, index=False, sheet_name="HOY_RAW")
        df_nuevos.to_excel(writer, index=False, sheet_name="NUEVOS")
        df_eliminados.to_excel(writer, index=False, sheet_name="ELIMINADOS")
        df_mantenidos.to_excel(writer, index=False, sheet_name="MANTENIDOS")
        df_modificados.to_excel(writer, index=False, sheet_name="MODIFICADOS")
        resumen_df.to_excel(writer, index=False, sheet_name="RESUMEN")
        last_seen_out.to_excel(writer, index=False, sheet_name="LAST_SEEN")

    excel_bytes = buf.getvalue()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    st.download_button(
        label="⬇️ Descargar paquete Excel (Hoy + Comparación + LAST_SEEN)",
        data=excel_bytes,
        file_name=f"comparendos_paquete_{stamp}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
