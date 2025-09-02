import pandas as pd
import pytest
from datetime import datetime
from modificados import build_modificados_table, holidays

# ---- Utilidad para fabricar un "Excel AYER" (header=None) con filas desde 8 ----
def make_yesterday_any(rows_after_header):
    """
    rows_after_header: lista de filas (listas) que se colocan a partir del índice 7 (fila 8 de Excel).
    Antes de eso, se rellenan 7 filas vacías tal como espera el extractor.
    """
    data = [[""] * 12 for _ in range(7)]
    data.extend(rows_after_header)
    return pd.DataFrame(data)

# ---- Monkeypatch de festivos (para que las ventanas sean deterministas en test) ----
class _NoHolidays(set):
    def __contains__(self, d):
        return False

@pytest.fixture(autouse=True)
def patch_holidays(monkeypatch):
    # Evita depender del calendario real de Colombia en test:
    # hacemos que holidays.Colombia() devuelva un set vacío (sin festivos),
    # así solo se excluyen fines de semana.
    monkeypatch.setattr(holidays, "Colombia", lambda: _NoHolidays())
    yield


def test_modificados_caso_modificado():
    """
    Ayer: comparendo con notificación 10/01/2024 en columna I (idx=8)
    Hoy (SIMIT): mismo comparendo con notificación 12/01/2024 -> MODIFICADO
    """
    # AYER: placa en B (idx=1) no es necesaria aquí, pero dejamos algo
    df_y = make_yesterday_any([
        ["", "ABC123", "", "", "", "", "", "01/01/2024", "10/01/2024", "11001000000039571821"]
    ])

    # HOY SIMIT
    rows_today_simit = [{
        "numero_comparendo": "11001000000039571821",
        "fecha_imposicion": "2024-01-01",
        "fecha_notificacion": "12/01/2024",
        "placa": "ABC123",
        "plataforma": "SIMIT",
    }]

    df_mod = build_modificados_table(rows_today_simit, df_y)
    assert len(df_mod) == 1
    r = df_mod.iloc[0]
    assert r["estado"] == "MODIFICADO"
    assert r["notif_ayer"] in ("2024-01-10", "10/01/2024")
    assert r["notif_hoy"] in ("2024-01-12", "12/01/2024")
    # Ventanas calculadas (no vacías)
    assert r["50_desc_hasta"] != ""
    assert r["25_desc_desde"] != ""
    assert r["25_desc_hasta"] != ""


def test_modificados_caso_actualizado():
    """
    Ayer: sin notificación
    Hoy (SIMIT): notificación presente -> ACTUALIZADO
    """
    df_y = make_yesterday_any([
        ["", "ABC123", "", "", "", "", "", "", "", "11001000000039571821"]
    ])
    rows_today_simit = [{
        "numero_comparendo": "11001000000039571821",
        "fecha_imposicion": "",
        "fecha_notificacion": "05/02/2024",
        "placa": "ABC123",
        "plataforma": "SIMIT",
    }]

    df_mod = build_modificados_table(rows_today_simit, df_y)
    assert len(df_mod) == 1
    r = df_mod.iloc[0]
    assert r["estado"] == "ACTUALIZADO"
    assert r["notif_ayer"] == ""
    assert r["notif_hoy"] in ("2024-02-05", "05/02/2024")
    assert r["50_desc_hasta"] != "" and r["25_desc_desde"] != "" and r["25_desc_hasta"] != ""


def test_modificados_yer_multi_tokens_in_cell():
    """
    Ayer: dos comparendos en la MISMA celda; el nuestro debe ser reconocido (tokenización).
    """
    df_y = make_yesterday_any([
        ["", "KOV716", "", "", "", "", "", "10/01/2024", "15/01/2024",
         "D05001000000048513677 05001000000048513677"]
    ])
    # HOY traemos el que empieza con D... (canónico debe emparejar)
    rows_today_simit = [{
        "numero_comparendo": "D05001000000048513677",
        "fecha_imposicion": "",
        "fecha_notificacion": "20/01/2024",
        "placa": "KOV716",
        "plataforma": "SIMIT",
    }]

    df_mod = build_modificados_table(rows_today_simit, df_y)
    # Como AYER tenía 15/01/2024 y HOY 20/01/2024, entra como MODIFICADO
    assert len(df_mod) == 1
    r = df_mod.iloc[0]
    assert r["estado"] == "MODIFICADO"
    assert r["notif_ayer"] in ("2024-01-15", "15/01/2024")
    assert r["notif_hoy"] in ("2024-01-20", "20/01/2024")


def test_modificados_no_entry_when_missing_yesterday():
    """
    Si el comparendo no existía AYER, no debe aparecer en Modificados (reglas dadas).
    """
    df_y = make_yesterday_any([
        ["", "AAA111", "", "", "", "", "", "01/01/2024", "10/01/2024", "11001000000000000001"]
    ])
    rows_today_simit = [{
        "numero_comparendo": "47053000000050062712",  # no está en AYER
        "fecha_imposicion": "",
        "fecha_notificacion": "20/01/2024",
        "placa": "XYZ999",
        "plataforma": "SIMIT",
    }]

    df_mod = build_modificados_table(rows_today_simit, df_y)
    assert df_mod.empty
