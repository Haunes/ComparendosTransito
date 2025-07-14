"""
ui/app.py

Streamlit application entrypoint for the "Comparador de comparendos".

This app provides a web interface to:
  1. Accept raw text blocks pasted from various platforms (SIMIT, FENIX, etc.).
  2. Upload an Excel file from the previous day containing comparendos data.
  3. Extract and compare current data against the Excel to identify:
     - New comparendos
     - Deleted comparendos
     - Maintained comparendos
  4. Filter results for FENIX and SIMIT platforms and detect changes in notification dates:
     - "dato actualizado" when a prior blank/N-A becomes a valid date
     - "modificado" when one valid date changes to another
  5. Display summary tables and metrics using Streamlit components.
  6. Offer a download of the complete comparison report as an Excel file.

Usage:
    streamlit run ui/app.py
"""

#!/usr/bin/env python3
# ui/app.py

import sys
import pathlib

# ── Bootstrapping: añade la carpeta raíz al PYTHONPATH ────────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from ui.constants           import PLATFORMS, TITLE
from ui.layout              import (
    page_header,
    input_blocks,
    input_excel,
    show_metrics,
    show_table,
)
from ui.excel_reader        import resumen_desde_excel
from services.extractor     import compare
from services.notif_changes import detect_notif_changes
from services.writer        import build_excel

# ────────────────────────────────────────────────────────────────────────
page_header(TITLE)

blocks  = input_blocks(PLATFORMS)   # Textos pegados por plataforma
xls_old = input_excel()             # Excel “ayer” (hoja COMPARENDOS)

if st.button("▶️ Procesar"):
    # ── Validación ─────────────────────────────────────────────────────
    if not blocks or not xls_old:
        st.warning("Faltan bloques de texto o falta subir el Excel.")
        st.stop()

    # 1️⃣ Leer y normalizar el Excel de ayer
    resumen_old = resumen_desde_excel(xls_old)

    # 2️⃣ Extraer los datos nuevos y calcular añadidos/eliminados
    detalle_new, resumen_new, df_mant, df_add, df_del = compare(blocks, xls_old)

    # 3️⃣ Filtrar sólo FENIX y SIMIT para verificar cambios de notificación
    mask_fs = resumen_new["fuentes"].str.contains(r"\b(FENIX|SIMIT)\b", regex=True)
    res_fs  = resumen_new[mask_fs].copy()

    # 4️⃣ Detectar “dato actualizado” y “modificado” en fecha_notif
    df_fecha = detect_notif_changes(resumen_old, res_fs)

    # ── Presentación ────────────────────────────────────────────────────
    st.subheader("📋 Resumen de todos los comparendos detectados hoy")
    st.dataframe(
        resumen_new[["comparendo", "placa", "fuentes", "veces"]],
        use_container_width=True,
    )

    show_metrics(df_mant, df_add, df_del)
    show_table("Se mantienen", df_mant, "🟢")
    show_table("Añadidos",     df_add,  "➕")
    show_table("Eliminados",   df_del,  "➖")

    if not df_fecha.empty:
        show_table("Cambios en Fecha de notificación", df_fecha, "✏️")

    # ── Botón de descarga del Excel completo ────────────────────────────
    st.download_button(
        "💾 Descargar Excel completo",
        data=build_excel(
            detalle_new,
            resumen_new,
            df_mant,
            df_add,
            df_del,
            df_fecha if not df_fecha.empty else None
        ),
        file_name="comparendos_resultado.xlsx",
    )
else:
    st.info("Pega los bloques y sube el Excel para comenzar.")
