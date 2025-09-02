import pandas as pd
from comparator import build_three_tables

def test_three_tables_eliminados_take_B_H_I():
    # HOY: 1 comparendo (A1) con placa XXY123
    df_today = pd.DataFrame([{
        "numero_comparendo":"11001000000039571821",
        "fecha_imposicion":"2024-01-12",
        "fecha_notificacion":"",
        "placa":"XXY123",
        "plataformas":"SIMIT",
        "numero_veces":1
    }])

    # AYER (header=None): simulamos hoja donde:
    # - Col B (idx=1) tiene placa KOV716
    # - Col H (idx=7) imposición 10/01/2024
    # - Col I (idx=8) notificación 15/01/2024
    # - Misma fila contiene un comparendo distinto (ELIMINADO)
    data = [
        ["hdrA","hdrB","hdrC","hdrD","hdrE","hdrF","hdrG","Imposicion","Notificacion","hdrJ"], # fila 1
        *([[""]*10] * 5), # filas 2..6
        ["","PLACA","", "", "", "", "", "FECHA_IMP", "FECHA_NOT", ""], # fila 7 encabezado semántico
        ["", "KOV716", "", "", "", "", "", "10/01/2024", "15/01/2024", "11001000000000000001"], # fila 8 con comparendo ELIMINADO
    ]
    df_yesterday_any = pd.DataFrame(data)

    res = build_three_tables(
        df_today=df_today,
        df_yesterday_any=df_yesterday_any,
        date_imp_col_idx=7,   # H
        date_notif_col_idx=8, # I
        plate_col_idx=1,      # B
        header_row_excel_1based=7
    )

    elim = res["ELIMINADOS"]
    assert len(elim) == 1
    r = elim.iloc[0]
    assert r["placa"] == "KOV716"
    assert r["fecha_imposicion"] in ("10/01/2024","2024-01-10")  # admitimos ambas normalizaciones
    assert r["fecha_notificacion"] in ("15/01/2024","2024-01-15")
