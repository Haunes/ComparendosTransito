# ui/layout.py
import streamlit as st
import pandas as pd

def page_header(title: str):
    st.set_page_config(page_title=title, layout="wide")
    st.title(title)

def input_blocks(platforms: list[str]) -> dict[str, str]:
    st.header("1️⃣ Pega el texto de cada plataforma")
    raw = {p: st.text_area(f"{p} ⤵️", height=150) for p in platforms}
    return {k: v for k, v in raw.items() if v.strip()}

def input_excel():
    st.header("2️⃣ Sube el Excel de ayer (hoja COMPARENDOS, header fila 7)")
    return st.file_uploader("Archivo .xlsx", type=["xlsx"])

def show_metrics(df_mant, df_add, df_del):
    col1, col2, col3 = st.columns(3)
    col1.metric("Se mantienen", len(df_mant))
    col2.metric("Añadidos",   len(df_add))
    col3.metric("Eliminados", len(df_del))

def show_table(title: str, df: pd.DataFrame, color: str):
    st.subheader(f"{color} {title}")
    st.dataframe(df, use_container_width=True)
