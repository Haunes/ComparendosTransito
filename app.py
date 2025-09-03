from __future__ import annotations
import streamlit as st
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime

from parsers import parse_platform, PARSERS, parse_simit_coactivos
from aggregator import aggregate_by_comparendo
from comparator import build_three_tables
from export_utils import dfs_to_excel_bytes
from backfill import read_yesterday_summary, build_backfill_rows
from modificados import build_modificados_table
from frontend import (
    load_custom_css, get_icon, render_main_header, render_section_header,
    render_alert, render_metric_cards, render_processing_summary, render_footer
)

APP_KEY = "comparendos_app_state"
PLATFORMS = list(PARSERS.keys())

# -------------------- Estado --------------------
def init_state():
    expected = {
        "inputs": {p: "" for p in PLATFORMS},
        "rows_by_platform": {p: [] for p in PLATFORMS},
        "platform_down": {p: False for p in PLATFORMS},
        "yesterday_summary_df": None,
        "yesterday_any_df": None,
        "df_raw": pd.DataFrame(),
        "df_today": pd.DataFrame(),
        "three_tables": None,
        "df_modificados": pd.DataFrame(),
        "view_mode": "resumen",  # opciones: "resumen", "nuevos", "mantenidos", "eliminados", "modificados",
        "coactivos_simit": [],  # estado para cobros coactivos
    }
    if APP_KEY not in st.session_state or not isinstance(st.session_state[APP_KEY], dict):
        st.session_state[APP_KEY] = expected
        return
    app = st.session_state[APP_KEY]
    for k, v in expected.items():
        if k not in app:
            app[k] = v
    for p in PLATFORMS:
        app["inputs"].setdefault(p, "")
        app["rows_by_platform"].setdefault(p, [])
        app["platform_down"].setdefault(p, False)
    # Limpieza por si cambia PARSERS
    for sub in ("inputs", "rows_by_platform", "platform_down"):
        for old in list(app[sub].keys()):
            if old not in PLATFORMS:
                del app[sub][old]

def replace_platform_rows(platform: str, rows: List[Dict[str, Any]]) -> None:
    st.session_state[APP_KEY]["rows_by_platform"][platform] = rows

def concat_all_rows() -> pd.DataFrame:
    data: List[Dict[str, Any]] = []
    for p in PLATFORMS:
        data.extend(st.session_state[APP_KEY]["rows_by_platform"][p])
    cols = ["numero_comparendo", "fecha_imposicion", "fecha_notificacion", "placa", "plataforma"]
    if not data:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(data)
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols]

def clear_platform(platform: str) -> None:
    st.session_state[APP_KEY]["inputs"][platform] = ""
    st.session_state[APP_KEY]["rows_by_platform"][platform] = []
    st.session_state[APP_KEY]["platform_down"][platform] = False
    # Limpiar widget si existe
    wkey = f"input_{platform}"
    if wkey in st.session_state:
        st.session_state[wkey] = ""

def clear_all() -> None:
    st.session_state[APP_KEY]["inputs"] = {p: "" for p in PLATFORMS}
    st.session_state[APP_KEY]["rows_by_platform"] = {p: [] for p in PLATFORMS}
    st.session_state[APP_KEY]["platform_down"] = {p: False for p in PLATFORMS}
    st.session_state[APP_KEY]["yesterday_summary_df"] = None
    st.session_state[APP_KEY]["yesterday_any_df"] = None
    st.session_state[APP_KEY]["df_raw"] = pd.DataFrame()
    st.session_state[APP_KEY]["df_today"] = pd.DataFrame()
    st.session_state[APP_KEY]["three_tables"] = None
    st.session_state[APP_KEY]["df_modificados"] = pd.DataFrame()
    st.session_state[APP_KEY]["view_mode"] = "resumen"
    st.session_state[APP_KEY]["coactivos_simit"] = []
    # Limpiar widgets de texto
    for p in PLATFORMS:
        wkey = f"input_{p}"
        if wkey in st.session_state:
            st.session_state[wkey] = ""

# -------------------- Proceso unificado --------------------
def run_all() -> None:
    # 1) Parseo HOY (texto pegado)
    for name in PLATFORMS:
        text = st.session_state[APP_KEY]["inputs"][name]
        rows = parse_platform(name, text)
        st.session_state[APP_KEY]["rows_by_platform"][name] = rows
        if name == "SIMIT":
            coactivos = parse_simit_coactivos(text)
            st.session_state[APP_KEY]["coactivos_simit"] = coactivos

    # 2) Backfill si marcaste caídas y cargaste Resumen AYER (hoja 1)
    df_prev = st.session_state[APP_KEY]["yesterday_summary_df"]
    replaced = []
    if df_prev is not None and not getattr(df_prev, "empty", False):
        for p, is_down in st.session_state[APP_KEY]["platform_down"].items():
            if is_down:
                backfill_rows = build_backfill_rows(df_prev, p)
                if backfill_rows:
                    st.session_state[APP_KEY]["rows_by_platform"][p] = backfill_rows
                    replaced.append(p)
    if replaced:
        st.success("Backfill: " + ", ".join(replaced))
    elif any(st.session_state[APP_KEY]["platform_down"].values()) and (df_prev is None or getattr(df_prev, "empty", False)):
        st.warning("Marcaste caídas, pero no subiste el Resumen de AYER.")

    # 3) Crudo + Conteo
    df_raw = concat_all_rows()
    df_today = aggregate_by_comparendo(df_raw, platform_order=PLATFORMS)

    st.session_state[APP_KEY]["df_raw"] = df_raw
    st.session_state[APP_KEY]["df_today"] = df_today

    # 4) Tres tablas (comparativa) si hay Excel AYER cargado
    df_y_any = st.session_state[APP_KEY]["yesterday_any_df"]
    df_prev_summary = st.session_state[APP_KEY]["yesterday_summary_df"]
    counts = {"nuevos": 0, "mantenidos": 0, "eliminados": 0}
    if df_y_any is not None and not getattr(df_y_any, "empty", False) and not df_today.empty:
        try:
            res = build_three_tables(df_today, df_y_any, df_prev_summary=df_prev_summary, )
        except Exception as e:
            st.session_state[APP_KEY]["three_tables"] = None
            st.session_state[APP_KEY]["counts"] = counts
            st.error(f"No fue posible generar comparativa: {e}")
        else:
            st.session_state[APP_KEY]["three_tables"] = res
            counts = {
                "nuevos": len(res["NUEVOS"]),
                "mantenidos": len(res["MANTENIDOS"]),
                "eliminados": len(res["ELIMINADOS"]),
            }
            st.session_state[APP_KEY]["counts"] = counts
    else:
        st.session_state[APP_KEY]["three_tables"] = None
        st.session_state[APP_KEY]["counts"] = counts

    # 5) Modificados (SIMIT vs Excel AYER)
    rows_simit = st.session_state[APP_KEY]["rows_by_platform"].get("SIMIT", [])
    if df_y_any is not None and not getattr(df_y_any, "empty", False) and rows_simit:
        try:
            df_mod = build_modificados_table(rows_simit, df_y_any)
        except Exception as e:
            st.session_state[APP_KEY]["df_modificados"] = pd.DataFrame()
            st.error(f"No fue posible generar 'Modificados': {e}")
        else:
            st.session_state[APP_KEY]["df_modificados"] = df_mod
    else:
        st.session_state[APP_KEY]["df_modificados"] = pd.DataFrame()

# -------------------- UI por pestaña --------------------
def platform_tab_ui(name: str) -> None:
    # Header de la plataforma con icono
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <span style="font-size: 1.5rem; margin-right: 0.5rem;">{get_icon('platform')}</span>
        <h3 style="margin: 0; color: var(--primary-dark);">{name}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Checkbox para plataforma caída
    down_key = f"down_{name}"
    current_down = st.session_state[APP_KEY]["platform_down"].get(name, False)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        down_val = st.checkbox(
            f"{get_icon('warning')} Plataforma caída hoy",
            value=current_down,
            key=down_key,
            help="Si está caída, usaré el Resumen de AYER (hoja 1) para esta plataforma."
        )
        st.session_state[APP_KEY]["platform_down"][name] = bool(down_val)
    
    # Área de texto
    txt_key = f"input_{name}"
    if txt_key not in st.session_state:
        st.session_state[txt_key] = st.session_state[APP_KEY]["inputs"].get(name, "")
    text = st.text_area(
        "📝 Pega aquí el texto:",
        key=txt_key,
        height=200,
        placeholder=f"Pega aquí los datos de {name}..."
    )
    st.session_state[APP_KEY]["inputs"][name] = st.session_state[txt_key]
    
    # Botón de limpiar
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(f"{get_icon('clean')} Limpiar", key=f"clr_{name}", use_container_width=True, type="secondary"):
            clear_platform(name)
            render_alert(f"{name} limpiado correctamente", "success", "success")

# -------------------- Main --------------------
def main():
    st.set_page_config(
        page_title="Extractor de Comparendos", 
        layout="wide",
        page_icon="🚗",
        initial_sidebar_state="collapsed"
    )
    
    load_custom_css()
    init_state()
    render_main_header()

    # === 1) Carga de archivos ===
    render_section_header("📁 Gestión de Archivos")
    
    c_up1, c_up2, c_btns = st.columns([2, 2, 1])

    with c_up1:
        st.markdown("**📊 Resumen de Ayer**")
        resumen = st.file_uploader(
            "Selecciona el archivo Excel del resumen de ayer", 
            type=["xlsx"], 
            key="uploader_resumen",
            help="Archivo Excel con el resumen del día anterior"
        )
        if resumen is not None:
            try:
                df_prev = read_yesterday_summary(resumen)
                st.session_state[APP_KEY]["yesterday_summary_df"] = df_prev
                render_alert(f"Resumen cargado exitosamente: {len(df_prev)} filas procesadas", "success", "success")
            except Exception as e:
                render_alert(f"Error al leer el Resumen de AYER: {e}", "warning", "warning")

    with c_up2:
        st.markdown("**🔍 Excel para Comparativa**")
        comp = st.file_uploader(
            "Selecciona el Excel de ayer para comparar", 
            type=["xlsx"], 
            key="uploader_comp",
            help="Excel del día anterior para generar comparativas"
        )
        if comp is not None:
            try:
                df_any = pd.read_excel(comp, header=None)
                st.session_state[APP_KEY]["yesterday_any_df"] = df_any
                render_alert(f"Excel cargado para comparativa ({len(df_any)} filas)", "info", "info")
            except Exception as e:
                render_alert(f"Error al leer el Excel de AYER: {e}", "warning", "warning")

    with c_btns:
        st.markdown("**⚡ Acciones**")
        if st.button(f"{get_icon('process')} Procesar", type="primary", use_container_width=True):
            with st.spinner("Procesando datos..."):
                run_all()
            render_alert("Datos procesados correctamente", "success", "success")
            
        if st.button(f"{get_icon('clean')} Limpiar Todo", type="secondary", use_container_width=True):
            clear_all()
            render_alert("Todos los datos han sido limpiados", "info", "info")

    st.markdown("---")

    # === 2) Pestañas (texto) ===
    render_section_header("📝 Entrada de Datos por Plataforma")
    
    tabs = st.tabs([f"{get_icon('platform')} {name}" for name in PLATFORMS])
    for tab, name in zip(tabs, PLATFORMS):
        with tab:
            platform_tab_ui(name)

    st.markdown("---")

    # === 2.5) Cobros coactivos (SIMIT) ===
    coact_list = st.session_state[APP_KEY].get("coactivos_simit", [])
    if coact_list:  # Solo mostrar si hay cobros coactivos
        render_section_header("⚖️ Cobros Coactivos (SIMIT)")
        co_cols = ["numero_coactivo","fecha_resolucion","placa","organismo","codigo_infraccion","estado","valor","interes","valor_total","plataforma"]
        df_coact = pd.DataFrame(coact_list, columns=co_cols)
        st.dataframe(df_coact, use_container_width=True, height=300)
        st.markdown("---")

    # === 3) Conteo ===
    render_section_header("📊 Resumen de Conteo")
    
    df_today = st.session_state[APP_KEY]["df_today"]
    if df_today.empty:
        render_alert("Sin datos procesados. Pega el texto en las pestañas y pulsa \"Procesar\" para comenzar.", "info", "info")
    else:
        st.dataframe(df_today, use_container_width=True, height=380)
    
    # === 3.1) KPIs de comparativa ===
    counts = st.session_state[APP_KEY].get("counts", {"nuevos": 0, "mantenidos": 0, "eliminados": 0})
    df_mod = st.session_state[APP_KEY]["df_modificados"]
    
    st.markdown("**📈 Métricas de Comparativa**")
    render_metric_cards(counts, df_mod)
    
    if st.session_state[APP_KEY].get("view_mode", "resumen") != "resumen":
        if st.button("🔙 Volver al Resumen", type="secondary"):
            st.session_state[APP_KEY]["view_mode"] = "resumen"
            st.rerun()
    
    view_mode = st.session_state[APP_KEY].get("view_mode", "resumen")
    three = st.session_state[APP_KEY]["three_tables"]
    
    if view_mode == "resumen":
        # Vista normal - continuar con el flujo normal
        pass
    elif view_mode == "nuevos" and three and "NUEVOS" in three:
        render_section_header("🆕 Comparendos Nuevos")
        st.dataframe(three["NUEVOS"], use_container_width=True, height=400)
        return  # Salir temprano para mostrar solo esta tabla
    elif view_mode == "mantenidos" and three and "MANTENIDOS" in three:
        render_section_header("🔄 Comparendos Mantenidos")
        st.dataframe(three["MANTENIDOS"], use_container_width=True, height=400)
        return  # Salir temprano para mostrar solo esta tabla
    elif view_mode == "eliminados" and three and "ELIMINADOS" in three:
        render_section_header("❌ Comparendos Eliminados")
        st.dataframe(three["ELIMINADOS"], use_container_width=True, height=400)
        return  # Salir temprano para mostrar solo esta tabla
    elif view_mode == "modificados" and not df_mod.empty:
        render_section_header("✏️ Comparendos Modificados")
        st.dataframe(df_mod, use_container_width=True, height=400)
        return  # Salir temprano para mostrar solo esta tabla
    elif view_mode != "resumen":
        render_alert(f"No hay datos disponibles para mostrar {view_mode}. Procesa los datos primero.", "info", "info")
        return

    # === 6) Descarga Excel ===
    render_section_header("💾 Exportación de Resultados")
    
    c_dl1, c_dl2 = st.columns([1, 3])
    with c_dl1:
        df_raw  = st.session_state[APP_KEY]["df_raw"]
        df_today = st.session_state[APP_KEY]["df_today"]
        three   = st.session_state[APP_KEY]["three_tables"]
        df_mod  = st.session_state[APP_KEY]["df_modificados"]

        if not df_today.empty or not df_raw.empty:
            sheets: Dict[str, pd.DataFrame] = {}

            if not df_raw.empty:
                resumen_name = f"Resumen {datetime.now().strftime('%d-%m-%y')}"
                sheets[resumen_name] = df_raw

            if not df_today.empty:
                sheets["Conteo"] = df_today

            if isinstance(three, dict):
                if "NUEVOS" in three and not three["NUEVOS"].empty:
                    sheets["Nuevos"] = three["NUEVOS"]
                if "MANTENIDOS" in three and not three["MANTENIDOS"].empty:
                    sheets["Mantenidos"] = three["MANTENIDOS"]
                if "ELIMINADOS" in three and not three["ELIMINADOS"].empty:
                    sheets["Eliminados"] = three["ELIMINADOS"]

            if isinstance(df_mod, pd.DataFrame) and not df_mod.empty:
                sheets["Modificados"] = df_mod

            # Agregar cobros coactivos al Excel si existen
            coact_list = st.session_state[APP_KEY].get("coactivos_simit", [])
            if coact_list:
                co_cols = ["numero_coactivo","fecha_resolucion","placa","organismo","codigo_infraccion","estado","valor","interes","valor_total","plataforma"]
                df_coact = pd.DataFrame(coact_list, columns=co_cols)
                if not df_coact.empty:
                    sheets["Cobros coactivos"] = df_coact

            if sheets:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                xlsx_bytes = dfs_to_excel_bytes(sheets)
                st.download_button(
                    f"{get_icon('download')} Descargar Reporte Completo",
                    data=xlsx_bytes,
                    file_name=f"reporte_comparendos_{ts}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
            else:
                render_alert("No hay datos procesados para exportar aún.", "info", "info")
        else:
            render_alert("Procesa algunos datos primero para habilitar la exportación.", "info", "info")
    
    with c_dl2:
        if not df_today.empty:
            total_comparendos = len(df_raw) if not df_raw.empty else 0
            total_plataformas = len([p for p in PLATFORMS if st.session_state[APP_KEY]["rows_by_platform"][p]])
            timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            
            render_processing_summary(total_comparendos, total_plataformas, timestamp)

    # Footer
    st.markdown("---")
    render_footer()

if __name__ == "__main__":
    main()
