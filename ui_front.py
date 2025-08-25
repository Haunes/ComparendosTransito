# ui_front.py
import streamlit as st
import pandas as pd
import re

PLATFORMS = [
    "SIMIT","FENIX","MEDELLIN","BELLO","ITAGUI","MANIZALES","CALI",
    "BOLIVAR","SANTAMARTA","MAGDALENA","SOLEDAD" 
]
LABEL = {
    "SIMIT":"Simit","FENIX":"Fenix","MEDELLIN":"Medellin","BELLO":"Bello","ITAGUI":"Itagui",
    "MANIZALES":"Manizales","CALI":"Cali","BOLIVAR":"Bolivar","SANTAMARTA":"Santa Marta",
    "MAGDALENA":"Magdalena", "SOLEDAD":"Soledad" 
}

def render_header():
    st.title("Comparendos · Reconocedor y Comparador")

def render_tabs_and_inputs() -> bool:
    tabs = st.tabs([LABEL[p] for p in PLATFORMS])
    pressed = False

    for i, p in enumerate(PLATFORMS):
        with tabs[i]:
            st.text_area(f"Texto {LABEL[p]}", key=f"txt_{p}", height=220)
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Procesar", key=f"proc_{p}"):
                    pressed = True
            with col_b:
                if st.button("Limpiar cuadro", key=f"clear_{p}"):
                    st.session_state[f"txt_{p}"] = ""
    return pressed

def render_results_table(all_records, debug_text: str | None):
    st.header("📄 Hoy (tabla combinada)")
    if not all_records:
        st.info("Pega texto en alguna pestaña y pulsa Procesar.")
        return

    df = pd.DataFrame(all_records)
    df["numero_comparendo"] = df["numero_comparendo"].astype(str)

    def _pick_display(nums: pd.Series) -> str:
        vals = [str(v) for v in nums.dropna().tolist()]
        with_letter = [v for v in vals if re.search(r"[A-Za-z]", v)]
        return with_letter[0] if with_letter else (vals[0] if vals else None)

    def _key_only_digits(x: str) -> str:
        return re.sub(r"\D","", str(x) if x is not None else "")

    def _agg_plats(s: pd.Series) -> str:
        vals = [str(v).upper() for v in s.dropna()]
        ordered = [LABEL[p] for p in PLATFORMS if p in vals]
        return " - ".join(ordered) if ordered else None

    df["__key"] = df["numero_comparendo"].apply(_key_only_digits)

    agg = (
        df.sort_values(["__key"])
          .groupby("__key", as_index=False)
          .agg({
              "numero_comparendo": _pick_display,
              "placa": "first",
              "fecha_imposicion": "first",
              "fecha_notificacion": "first",
              "plataforma": _agg_plats,
          })
          .rename(columns={"numero_comparendo":"numero", "plataforma":"plataformas"})
    )
    # conteo de plataformas
    counts = (
        df.groupby(["__key"])["plataforma"].nunique().reset_index(name="plataformas_count")
    )
    out = agg.merge(counts, on="__key", how="left").drop(columns=["__key"])
    st.dataframe(out, use_container_width=True)

    if debug_text:
        with st.expander("Debug"):
            st.text(debug_text)
