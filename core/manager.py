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
