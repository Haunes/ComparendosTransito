import re
RE_ID = re.compile(r"^[A-Z]?\d{14,}$")
def parse(text:str):
    ids=[]
    for ln in text.splitlines():
        cols=ln.split()
        if len(cols)>=3 and RE_ID.match(cols[2]):
            ids.append(cols[2])
    return ids
