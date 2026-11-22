import re, json
def load_appdb(path):
    s=open(path).read()
    m=re.search(r'const NUTRI_DB = \{(.*?)\n\};', s, re.S)
    db={}
    for k,v in re.findall(r'^\s*"([^"]+)"\s*:\s*\{([^}]*)\}', m.group(1), re.M):
        db[k]={a:float(b) for a,b in re.findall(r'(\w+)\s*:\s*([\d.]+)',v)}
    ex=re.search(r'const NUTRI_EXTRA = \{(.*?)\n\};', s, re.S)
    extra={k:(float(a),float(b)) for k,a,b in re.findall(r'"([^"]+)":\[([\d.]+),([\d.]+)\]', ex.group(1))}
    return db, extra
