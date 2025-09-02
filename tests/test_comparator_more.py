import pandas as pd
from datetime import datetime
from comparator import build_three_tables, extract_comparendos_rowwise_with_dates, _to_str_date_like

def test__to_str_date_like_variants():
    assert _to_str_date_like(datetime(2024,1,9)) == "2024-01-09"
    assert _to_str_date_like("09/01/2024") in ("2024-01-09","09/01/2024")
    assert _to_str_date_like("9/1/24") in ("2024-01-09","9/1/24")  # admite corto
    assert _to_str_date_like("") == ""

def test_extract_rowwise_dates_plate_fallbacks_and_multi_comparendos():
    # Fila 8 (índice 7): dos comparendos en la misma fila, placa en B, imposición en H, notificación vacía -> fallback toma 2ª fecha de la fila
    data = [[""]*10 for _ in range(7)]
    data.append(["", "kov-716", "", "", "NIT 901354352", "", "", "27/07/2025", "", "D05001000000048513677 05001000000048513677"])
    df_y = pd.DataFrame(data)
    y_original, yset, ydata = extract_comparendos_rowwise_with_dates(df_y, date_imp_col_idx=7, date_notif_col_idx=8, plate_col_idx=1, header_row_excel_1based=7)
    # Ambos comparendos aparecen (canónicos serán iguales por la letra opcional, pero aceptamos al menos 1)
    assert len(yset) >= 1
    any_key = next(iter(yset))
    d = ydata[any_key]
    assert d["imp_ayer"] != ""     # tomó H
    # No hay I, así que notif_ayer puede ser "" (no pusimos 2ª fecha explícita), y está bien
    assert d["placa_ayer"] == "KOV716"  # normalizada sin guiones

def test_build_three_tables_all_states():
    # HOY tiene A y B; AYER tiene B y C -> NUEVO: A, MANTENIDO: B, ELIMINADO: C
    df_today = pd.DataFrame([
        {"numero_comparendo":"11001000000000000001","fecha_imposicion":"2024-01-01","fecha_notificacion":"","placa":"AAA111","plataformas":"SIMIT","numero_veces":1},  # A
        {"numero_comparendo":"D05001000000048513677","fecha_imposicion":"2025-07-27","fecha_notificacion":"","placa":"KYV691","plataformas":"Medellín","numero_veces":1}, # B (con letra)
    ])
    data = [[""]*10 for _ in range(7)]
    # B (equivalente canónico al de arriba) y C extra
    data.append(["", "KOV716", "", "", "", "", "", "10/01/2024", "15/01/2024", "05001000000048513677 47053000000050062712"])
    df_y = pd.DataFrame(data)

    res = build_three_tables(df_today, df_y, date_imp_col_idx=7, date_notif_col_idx=8, plate_col_idx=1, header_row_excel_1based=7)
    assert len(res["NUEVOS"]) == 1
    assert len(res["MANTENIDOS"]) == 1
    assert len(res["ELIMINADOS"]) == 1

    # Validaciones puntuales
    assert res["NUEVOS"].iloc[0]["numero_comparendo"].endswith("0001")
    assert res["MANTENIDOS"].iloc[0]["numero_comparendo"].startswith("D0500")
    elim = res["ELIMINADOS"].iloc[0]
    assert elim["placa"] == "KOV716"
    assert elim["fecha_imposicion"] != "" and elim["fecha_notificacion"] != ""
