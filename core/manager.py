"""
core/manager.py

Este módulo proporciona la lógica para descubrir e invocar parsers que extraen
información de comparendos desde bloques de texto, y luego agrupa y resume esos
datos.

Funciones:
  _discover() -> dict[str, Callable]
    Explora el paquete `parsers`, importa cada módulo que defina una función
    `parse` y construye un diccionario que asocia el nombre de la sección
    (SECTION) con dicha función de parseo.

  _sections(txt: str) -> Generator[tuple[str, str], None, None]
    Divide el texto completo en secciones basándose en los títulos que coinciden
    con las claves de PARSERS, emitiendo pares (título, contenido del bloque).

  run_extract(txt_path: pathlib.Path) -> tuple[pd.DataFrame, pd.DataFrame]
    Lee el archivo de texto en `txt_path`, segmenta el contenido en secciones,
    ejecuta el parser adecuado para cada bloque y normaliza la salida en dos
    DataFrames:
      - detalle: filas individuales con campos id_raw, id_key, placa,
        fecha_notif y fuente.
      - resumen: agrupación por id_key que incluye comparendo, placa,
        fecha_notif, lista de fuentes y número de apariciones (veces).
    Lanza ValueError si no se encuentra ningún comparendo en el texto.

Constantes:
  PARSERS: diccionario global resultante de `_discover()`, que mapea cada
           clave de sección a su función `parse`.
"""


# core/manager.py
import pkgutil, importlib, inspect, pathlib, pandas as pd
from .clean import id_key

# ── descubrir parsers ──────────────────────────────────────────────────
def _discover():
    import parsers
    out = {}
    for _, modname, _ in pkgutil.iter_modules(parsers.__path__):
        mod = importlib.import_module(f"parsers.{modname}")
        if hasattr(mod, "parse") and inspect.isfunction(mod.parse):
            key = getattr(mod, "SECTION",
                          modname.removesuffix("_parser").replace("_", " ")).upper()
            out[key] = mod.parse
    return out

PARSERS = _discover()

# ── separar secciones por título ───────────────────────────────────────
def _sections(txt: str):
    title, buf = None, []
    for ln in txt.splitlines():
        cand = ln.strip().upper()
        if cand in PARSERS:
            if title:
                yield title, "\n".join(buf)
            title, buf = cand, []
        elif title:
            buf.append(ln)
    if title:
        yield title, "\n".join(buf)

# ── función principal ─────────────────────────────────────────────────
def run_extract(txt_path: pathlib.Path):
    text = txt_path.read_text(encoding="utf-8-sig", errors="ignore")
    rows = []

    for tit, block in _sections(text):
        for item in PARSERS[tit](block):
            # ── normalizar salida del parser ──────────────────────────
            if isinstance(item, dict):
                rid   = item.get("id")
                placa = item.get("placa", "")
                fnot  = item.get("fecha_notif", "")
            elif isinstance(item, tuple) and len(item) == 3:
                rid, placa, fnot = item
            elif isinstance(item, tuple):                 # (id, placa)
                rid, placa, fnot = item[0], item[1], ""
            else:                                         # sólo id
                rid, placa, fnot = item, "", ""
            rows.append({
                "id_raw":   rid,
                "id_key":   id_key(rid),
                "placa":    placa,
                "fecha_notif": fnot,
                "fuente":   tit,
            })

    if not rows:
        raise ValueError("No se encontró ningún comparendo")

    detalle = pd.DataFrame(rows)

    resumen = (detalle.groupby("id_key")
                 .agg(comparendo=("id_raw", "first"),
                      placa     =("placa",        lambda s: next((p for p in s if p), "")),
                      fecha_notif=("fecha_notif", lambda s: next((d for d in s if d), "")),
                      fuentes   =("fuente",       lambda s: " - ".join(sorted(set(s)))),
                      veces     =("fuente",       "size"))
                 .reset_index())  # id_key queda como columna
    return detalle, resumen
