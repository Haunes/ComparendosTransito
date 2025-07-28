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
  6. Calculate discount‐deadline dates based on Colombian business days (holidays included):
     - 50% discount: 1 to 11 business days after notification
     - 25% discount: 12 to 26 business days after notification
  7. Offer a download of the complete comparison report as an Excel file.

Usage:
    streamlit run ui/app.py
"""
#!/usr/bin/env python3
import sys
import pathlib

# ── Bootstrapping: añade la carpeta raíz al PYTHONPATH ────────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import holidays
from pandas.tseries.offsets import CustomBusinessDay

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

def calcular_fechas_descuento(df, fecha_col="fecha_notif"):
    """Calcula fechas de vencimiento para descuentos 50% y 25%"""
    if df.empty or fecha_col not in df.columns:
        return df
    
    df_copy = df.copy()
    
    # Filtrar solo las filas que tienen fecha válida
    mask_fecha = df_copy[fecha_col].str.match(r'^\d{2}/\d{2}/\d{4}$', na=False)
    df_con_fecha = df_copy[mask_fecha].copy()
    
    if df_con_fecha.empty:
        return df_copy
    
    # Convertir a datetime
    df_con_fecha["_dt"] = pd.to_datetime(
        df_con_fecha[fecha_col],
        format="%d/%m/%Y",
        dayfirst=True
    )
    
    # Cargar feriados de Colombia para los años involucrados
    years = sorted(df_con_fecha["_dt"].dt.year.unique().tolist())
    co_holidays = holidays.CountryHoliday("CO", years=years)
    cbd = CustomBusinessDay(holidays=list(co_holidays.keys()))
    
    # Sumar días hábiles
    df_con_fecha["Fecha 50% descuento"] = df_con_fecha["_dt"].apply(
        lambda d: (d + 11 * cbd).strftime("%d/%m/%Y")
    )
    df_con_fecha["Fecha 25% descuento"] = df_con_fecha["_dt"].apply(
        lambda d: (d + 26 * cbd).strftime("%d/%m/%Y")
    )
    
    # Eliminar columna auxiliar
    df_con_fecha.drop(columns=["_dt"], inplace=True)
    
    # Actualizar el DataFrame original
    df_copy.loc[mask_fecha, "Fecha 50% descuento"] = df_con_fecha["Fecha 50% descuento"]
    df_copy.loc[mask_fecha, "Fecha 25% descuento"] = df_con_fecha["Fecha 25% descuento"]
    
    # Llenar con vacío las filas sin fecha
    if "Fecha 50% descuento" not in df_copy.columns:
        df_copy["Fecha 50% descuento"] = ""
    if "Fecha 25% descuento" not in df_copy.columns:
        df_copy["Fecha 25% descuento"] = ""
    
    df_copy.loc[~mask_fecha, "Fecha 50% descuento"] = ""
    df_copy.loc[~mask_fecha, "Fecha 25% descuento"] = ""
    
    return df_copy

page_header(TITLE)

blocks  = input_blocks(PLATFORMS)
xls_old = input_excel()

if st.button("▶️ Procesar"):
    if not blocks or not xls_old:
        st.warning("Faltan bloques de texto o falta subir el Excel.")
        st.stop()

    # 1️⃣ Leer y normalizar el Excel de ayer
    resumen_old = resumen_desde_excel(xls_old)

    # 2️⃣ Extraer los datos nuevos y calcular añadidos/eliminados
    detalle_new, resumen_new, df_mant, df_add, df_del = compare(blocks, xls_old)

    # 3️⃣ Filtrar sólo FENIX y SIMIT para verificar cambios de notificación
    mask_fs = resumen_new["fuentes"].str.contains(r"\b(?:FENIX|SIMIT)\b", regex=True)
    res_fs  = resumen_new[mask_fs].copy()

    # 4️⃣ Detectar "dato actualizado" y "modificado" en fecha_notif
    df_fecha = detect_notif_changes(resumen_old, res_fs)

    # 5️⃣ Calcular fechas de vencimiento para descuentos en cambios de fecha
    if not df_fecha.empty:
        df_fecha = calcular_fechas_descuento(df_fecha, "fecha_notif_new")
        # Renombrar las columnas para que sean más claras
        df_fecha = df_fecha.rename(columns={
            "fecha_notif_new": "fecha_notif_nueva"
        })

    # 6️⃣ Calcular fechas de descuento para comparendos añadidos de SIMIT
    if not df_add.empty and "fecha_notif" in df_add.columns:
        # Identificar filas de SIMIT con fecha de notificación válida
        mask_simit = df_add["fuentes"].str.contains(r"\bSIMIT\b", regex=True)
        mask_notif = df_add["fecha_notif"].str.match(r'^\d{2}/\d{2}/\d{4}

    # ── Presentación ────────────────────────────────────────────────────
    st.subheader("📋 Resumen de todos los comparendos detectados hoy")
    
    # Definir columnas a mostrar
    columnas_mostrar = ["comparendo", "placa", "fuentes", "veces"]
    if "fecha_imposicion" in resumen_new.columns:
        columnas_mostrar.insert(-2, "fecha_imposicion")
    if "fecha_notif" in resumen_new.columns:
        columnas_mostrar.insert(-2, "fecha_notif")
    
    st.dataframe(
        resumen_new[columnas_mostrar],
        use_container_width=True,
    )

    show_metrics(df_mant, df_add, df_del)
    show_table("Se mantienen", df_mant, "🟢")
    show_table("Añadidos",     df_add,  "➕")
    show_table("Eliminados",   df_del,  "➖")

    # Mostrar cambios en fechas de notificación
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
    st.info("Pega los bloques y sube el Excel para comenzar."), na=False)
        mask_simit_con_fecha = mask_simit & mask_notif
        
        if mask_simit_con_fecha.any():
            # Calcular fechas de descuento solo para SIMIT con fecha válida
            df_add = calcular_fechas_descuento(df_add, "fecha_notif")

    # ── Presentación ────────────────────────────────────────────────────
    st.subheader("📋 Resumen de todos los comparendos detectados hoy")
    
    # Definir columnas a mostrar
    columnas_mostrar = ["comparendo", "placa", "fuentes", "veces"]
    if "fecha_imposicion" in resumen_new.columns:
        columnas_mostrar.insert(-2, "fecha_imposicion")
    if "fecha_notif" in resumen_new.columns:
        columnas_mostrar.insert(-2, "fecha_notif")
    
    st.dataframe(
        resumen_new[columnas_mostrar],
        use_container_width=True,
    )

    show_metrics(df_mant, df_add, df_del)
    show_table("Se mantienen", df_mant, "🟢")
    show_table("Añadidos",     df_add,  "➕")
    show_table("Eliminados",   df_del,  "➖")

    # Mostrar comparendos nuevos de SIMIT con fechas de descuento
    if not df_add_simit.empty:
        st.subheader("🆕 Comparendos nuevos de SIMIT con fechas de descuento")
        st.dataframe(df_add_simit, use_container_width=True)

    # Mostrar cambios en fechas de notificación
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
            df_fecha if not df_fecha.empty else None,
            df_add_simit if not df_add_simit.empty else None
        ),
        file_name="comparendos_resultado.xlsx",
    )
else:
    st.info("Pega los bloques y sube el Excel para comenzar.")
