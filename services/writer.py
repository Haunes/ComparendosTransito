"""
services/writer.py

Generates an in‑memory Excel workbook summarizing comparendo data
across multiple sheets. The workbook includes:

  - detallado_hoy   : raw parsed entries for the current day
  - resumen_hoy     : aggregated summary of comparendos for the current day
  - mantienen       : comparendos que se mantienen de un día a otro
  - añadidos        : comparendos nuevos detectados hoy
  - eliminados      : comparendos eliminados desde el día anterior
  - cambios_fecha   : (opcional) comparendos con cambios en la fecha de notificación

Function:
  build_excel(
      detalle_new: DataFrame,
      resumen_new: DataFrame,
      df_mant:     DataFrame,
      df_add:      DataFrame,
      df_del:      DataFrame,
      df_fecha:    DataFrame | None = None
  ) -> bytes
    - Escribe cada DataFrame en su hoja correspondiente usando openpyxl.
    - Incluye la hoja `cambios_fecha` solo si `df_fecha` no es None y no está vacío.
    - Devuelve el contenido del archivo Excel como bytes listo para descarga.
"""


# services/writer.py
import io, pandas as pd

def build_excel(detalle_new, resumen_new,
                df_mant, df_add, df_del,
                df_fecha: pd.DataFrame | None = None) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xls:
        detalle_new.to_excel(xls, index=False, sheet_name="detallado_hoy")
        resumen_new.to_excel(xls, index=False, sheet_name="resumen_hoy")
        df_mant.to_excel(xls, index=False, sheet_name="mantienen")
        df_add .to_excel(xls, index=False, sheet_name="añadidos")
        df_del .to_excel(xls, index=False, sheet_name="eliminados")
        if df_fecha is not None and not df_fecha.empty:
            df_fecha.to_excel(xls, index=False, sheet_name="cambios_fecha")
    return buf.getvalue()
