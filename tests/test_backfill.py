import pandas as pd
from backfill import build_backfill_rows

def test_backfill_rows_filters_by_platform():
    df_summary = pd.DataFrame([
        {"numero_comparendo":"1","fecha_imposicion":"2024-01-01","fecha_notificacion":"","placa":"abc123","plataforma":"SIMIT"},
        {"numero_comparendo":"2","fecha_imposicion":"2024-01-02","fecha_notificacion":"","placa":"def456","plataforma":"FENIX"},
    ])
    rows = build_backfill_rows(df_summary, "SIMIT")
    assert len(rows) == 1
    r = rows[0]
    assert r["numero_comparendo"] == "1"
    assert r["placa"] == "ABC123"  # normalizada
    assert r["plataforma"] == "SIMIT"

import pandas as pd
from backfill import read_yesterday_summary, build_backfill_rows

def test_read_yesterday_summary_renames_and_filtering(tmp_path):
    df = pd.DataFrame({
        "Numero_Comparendo": ["A1","A2"],
        "FECHA_IMPOSICION": ["2024-01-01","2024-01-02"],
        "fecha_notificacion": ["", "2024-01-05"],
        "Placa": ["abc123"," dEf456 "],
        "PLATAFORMA": ["SIMIT","FENIX"],
        "otra": [1,2],
    })
    p = tmp_path / "resumen.xlsx"
    with pd.ExcelWriter(p) as w:
        df.to_excel(w, index=False, sheet_name="Resumen 01-01-25")
    out = read_yesterday_summary(str(p))
    assert list(out.columns) == ["numero_comparendo","fecha_imposicion","fecha_notificacion","placa","plataforma"]
    assert len(out) == 2

def test_build_backfill_rows_filters_and_normalizes():
    df = pd.DataFrame({
        "numero_comparendo": ["100","200"],
        "fecha_imposicion": ["2024-01-01",""],
        "fecha_notificacion": ["","2024-02-01"],
        "placa": [" abC123 ","ghi-789"],
        "plataforma": ["SIMIT", "FENIX"],
    })
    rows = build_backfill_rows(df, "SIMIT")
    assert len(rows) == 1
    r = rows[0]
    assert r["numero_comparendo"] == "100"
    assert r["placa"] == "ABC123"
    assert r["plataforma"] == "SIMIT"

def test_build_backfill_rows_platform_not_present_returns_empty():
    df = pd.DataFrame({
        "numero_comparendo":["1"],"fecha_imposicion":[""],"fecha_notificacion":[""],"placa":["XYZ111"],"plataforma":["FENIX"]
    })
    rows = build_backfill_rows(df, "SIMIT")
    assert rows == []
