#!/usr/bin/env python3
import argparse, pathlib
from core.manager import run_extract

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("txt", help="Archivo de texto con todas las secciones")
    ap.add_argument("-o", "--out", default="comparendos.xlsx",
                    help="Nombre del Excel/CSV de salida")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    run_extract(pathlib.Path(args.txt), pathlib.Path(args.out), debug=args.debug)
