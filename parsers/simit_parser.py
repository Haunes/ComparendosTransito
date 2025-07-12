import re
from typing import List

RE_ID   = re.compile(r"\b[A-Z]?\d{14,}\b")
RE_COMP = re.compile(r"^\s*Comparendo\s*$", re.I)

def parse(text: str) -> List[str]:
    ids, lines = [], text.splitlines()
    for i, ln in enumerate(lines):
        if RE_COMP.match(ln):
            # mira máximo 2 líneas arriba por el ID
            for up in (1, 2):
                if i - up < 0: break
                m = RE_ID.search(lines[i - up])
                if m: ids.append(m.group(0)); break
    return ids
