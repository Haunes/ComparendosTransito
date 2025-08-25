# parsers/santamarta.py
import re
from typing import List, Dict, Tuple

def parse_santamarta_text(raw_text: str) -> Tuple[List[Dict], str]:
    # Estructura:
    # Aviso del comparendo 47001000000038775644\t25/08/2023\t11/09/2023
    # OC_470010... (líneas PDF que se ignoran)
    text = raw_text.replace("\r\n","\n").replace("\r","\n")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    records: List[Dict] = []
    debug = []

    i = 0
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"^Aviso\s+del\s+comparendo\s+([A-Za-z0-9]+)\s*(\t|\s+)?(\d{2}/\d{2}/\d{4})?(\t|\s+)?(\d{2}/\d{2}/\d{4})?$", ln)
        if m:
            num = m.group(1)
            f_imp = m.group(3)
            f_not = m.group(5)
            rec = {
                "numero_comparendo": num,
                "fecha_imposicion": f_imp,
                "fecha_notificacion": f_not,
                "plataforma": "SANTAMARTA",
            }
            records.append(rec)
            debug.append(f"OK: {num} {f_imp} {f_not}")
            # saltar posibles 1-2 líneas de PDFs
            i += 1
            while i < len(lines) and lines[i].lower().endswith(".pdf"):
                i += 1
            continue
        i += 1

    return records, "\n".join(debug)
