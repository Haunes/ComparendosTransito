import pandas as pd
from aggregator import aggregate_by_comparendo

def test_aggregate_with_leading_letter_and_union():
    df = pd.DataFrame([
        {"numero_comparendo":"05001000000012345678","fecha_imposicion":"2024-01-01","fecha_notificacion":"","placa":"AAA111","plataforma":"SIMIT"},
        {"numero_comparendo":"D05001000000012345678","fecha_imposicion":"","fecha_notificacion":"2024-01-05","placa":"AAA111","plataforma":"FENIX"},
    ])
    out = aggregate_by_comparendo(df, platform_order=["SIMIT","FENIX"])
    assert len(out) == 1
    r = out.iloc[0]
    # Prefiere mostrar con letra si existe
    assert r["numero_comparendo"] == "D05001000000012345678"
    assert r["plataformas"] == "SIMIT-FENIX" or r.get("plataforma","") == "SIMIT-FENIX"
    assert r["numero_veces"] == 2
