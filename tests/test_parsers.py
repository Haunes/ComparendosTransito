import pandas as pd
from parsers import parse_simit, parse_fenix, parse_bolivar, parse_santamarta, parse_municipal_like

def test_simit_basic():
    text = """11001000000042735753
Comparendo
Fecha imposición: 23/08/2024\tNo aplica\tLZN818\tBogota D.C.
"""
    rows = parse_simit(text)
    assert len(rows) == 1
    r = rows[0]
    assert r["numero_comparendo"] == "11001000000042735753"
    assert r["fecha_imposicion"] == "2024-08-23"
    assert r["fecha_notificacion"] == "No aplica"
    assert r["placa"] == "LZN818"
    assert r["plataforma"] == "SIMIT"

def test_fenix_shifted():
    # Falta notificación; aparecen valores monetarios después
    text = "Comparendo - camaras salvavidas  VIGENTE  11001000000039571821  LVV783  12/01/2024  $ 357.700 $ 0 $ 0  $ 357.700  Cámaras salvavidas"
    rows = parse_fenix(text)
    assert len(rows) == 1
    r = rows[0]
    assert r["numero_comparendo"] == "11001000000039571821"
    assert r["fecha_imposicion"] == "2024-01-12"
    assert r["fecha_notificacion"] == ""  # no confunde $ con fecha
    assert r["placa"] == "LVV783"
    assert r["plataforma"] == "FENIX"

def test_bolivar_notif_date():
    text = """13683001000049160635
24/02/2025

NO
603.930
"""
    rows = parse_bolivar(text)
    assert len(rows) == 1
    r = rows[0]
    assert r["fecha_imposicion"] == ""  # imposición vacía
    assert r["fecha_notificacion"] == "2025-02-24"  # notificación en Bolívar
    assert r["plataforma"] == "Bolívar"

def test_santamarta_no_pdf_dup():
    text = """Aviso del comparendo 47001000000038775644\t25/08/2023\t11/09/2023
OC_47001000000038775644.pdf
Aviso del comparendo 47001000000038775644.pdf"""
    rows = parse_santamarta(text)
    assert len(rows) == 1
    assert rows[0]["numero_comparendo"] == "47001000000038775644"
    assert rows[0]["plataforma"] == "Santa Marta"

def test_municipal_like():
    # Medellín / similares: "<NIT> <PLACA> <NUMERO> <FECHA>"
    text = "901354352 KYV691 D05001000000048513677 27/07/2025"
    rows = parse_municipal_like(text, "Medellín")
    assert len(rows) == 1
    r = rows[0]
    assert r["numero_comparendo"] == "D05001000000048513677"
    assert r["fecha_imposicion"] == "2025-07-27"
    assert r["fecha_notificacion"] == ""
    assert r["placa"] == "KYV691"
    assert r["plataforma"] == "Medellín"
