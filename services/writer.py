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
