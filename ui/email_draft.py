"""
ui/constants.py

This module defines constant values for the Streamlit UI:

- PLATFORMS: a list of platform names (e.g., 'SIMIT', 'FENIX', etc.) that
  are enabled based on the available parsers in core.PARSERS.
- TITLE: the page title displayed at the top of the Streamlit application.
"""

# ui/email_draft.py
from datetime import date

def _lista(df, intro):
    lines = [
        f"• Placa {row.placa or '[buscar placa en ' + row.fuentes + ']'} "
        f"comparendo No. {row.comparendo}"
        for _, row in df.iterrows()
    ]
    return intro + "\n" + "\n".join(lines) + "\n\n" if lines else ""

def build_email(df_add, df_del, df_mant):
    hoy = date.today().strftime("%d/%m/%Y")
    partes = [
        "Estimados:\n\n",
        f"Adjuntamos la base de revisión con los comparendos encontrados el {hoy}, "
        "junto con las capturas de pantalla de los nuevos.\n\n",
    ]
    partes.append(_lista(df_add, "Se registraron los siguientes comparendos nuevos:")
                  or "No se registraron comparendos nuevos hoy.\n\n")
    partes.append(_lista(df_del, "Se eliminaron los siguientes comparendos:")
                  or "No se evidenciaron comparendos eliminados.\n\n")
    partes.append("Quedamos atentos a cualquier inquietud.\n\nSaludos cordiales,\nEquipo de revisión\n")
    return "".join(partes)
