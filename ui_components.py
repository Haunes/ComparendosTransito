
from __future__ import annotations
import streamlit as st
import pandas as pd
from typing import Dict, Any

def inject_local_css(dark_mode: bool) -> None:
    """Tema ligero/oscuro simple via CSS (no cambia el tema global de Streamlit)."""
    if dark_mode:
        st.markdown("""
        <style>
        .app-scope { background-color: #0e1117; color: #eaecef; }
        .app-scope .stTextInput > div > div > input,
        .app-scope .stTextInput textarea { background: #161b22; color: #eaecef; }
        .app-scope .stDataFrame { filter: brightness(0.95); }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .app-scope { background-color: #ffffff; color: #24292f; }
        </style>
        """, unsafe_allow_html=True)

def filters_ui(df: pd.DataFrame, key_prefix: str = "flt") -> pd.DataFrame:
    """Renderiza inputs de filtro por columna y devuelve el DF filtrado (contains, case-insensitive)."""
    if df.empty:
        return df
    st.write("### Filtros")
    c1, c2, c3, c4, c5 = st.columns(5)
    cols = ["numero_comparendo", "fecha_imposicion", "fecha_notificacion", "placa", "plataforma"]
    widgets = {}
    for col, container in zip(cols, [c1, c2, c3, c4, c5]):
        with container:
            widgets[col] = st.text_input(f"{col}", key=f"{key_prefix}_{col}")
    # Aplica filtros contains, case-insensitive, sobre strings
    df_str = df.astype(str)
    mask = pd.Series(True, index=df.index)
    for col, val in widgets.items():
        if val:
            mask = mask & df_str[col].str.contains(val, case=False, na=False)
    return df[mask]

def paginated_table(df: pd.DataFrame, page_size: int = 50, key_prefix: str = "pg") -> None:
    """Tabla con paginación manual."""
    if df.empty:
        st.info("No hay registros para mostrar.")
        return
    total = len(df)
    st.caption(f"Registros: {total}")
    c1, c2, _ = st.columns([1,1,3])
    with c1:
        size = st.number_input("Filas por página", 10, 500, page_size, 10, key=f"{key_prefix}_psize")
    pages = max(1, (total + size - 1) // size)
    with c2:
        page = st.number_input("Página", 1, pages, 1, 1, key=f"{key_prefix}_pnum")
    start = (page - 1) * size
    end = start + size
    st.dataframe(df.iloc[start:end].reset_index(drop=True), use_container_width=True)
    st.caption(f"Página {page}/{pages}")
