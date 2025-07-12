# core/manager.py
import pkgutil, importlib, inspect, pathlib
import pandas as pd
from .clean import id_key           # ⚑ sólo dígitos

# ── descubrir parsers en /parsers --------------------------------------
def _discover():
    import parsers
    out = {}
    for _, modname, _ in pkgutil.iter_modules(parsers.__path__):
        mod = importlib.import_module(f"parsers.{modname}")
        if not (hasattr(mod, "parse") and inspect.isfunction(mod.parse)):
            continue
        key = modname.removesuffix("_parser").replace("_", " ").upper()
        key = getattr(mod, "SECTION", key).upper()
        out[key] = mod.parse
    return out

PARSERS = _discover()

# ── partir el texto en secciones ---------------------------------------
def _sections(txt: str):
    title, buff = None, []
    for ln in txt.splitlines():
        cand = ln.strip().upper()
        if cand in PARSERS:
            if title: yield title, "\n".join(buff)
            title, buff = cand, []
        elif title:
            buff.append(ln)
    if title:
        yield title, "\n".join(buff)

# ── API principal -------------------------------------------------------
def run_extract(txt_path: pathlib.Path):
    text = txt_path.read_text(encoding="utf-8-sig", errors="ignore")
    rows = [
        {"id_raw": rid, "id_key": id_key(rid), "fuente": tit}
        for tit, block in _sections(text)
        for rid in PARSERS[tit](block)
    ]
    if not rows:
        raise ValueError("No se encontró ningún comparendo")

    detalle = pd.DataFrame(rows)

    resumen = (detalle.groupby("id_key")
                 .agg(comparendo=("id_raw", "first"),
                      fuentes   =("fuente", lambda s: " - ".join(sorted(set(s)))),
                      veces     =("fuente", "size"))
                 .reset_index())          # deja id_key como columna
    return detalle, resumen
