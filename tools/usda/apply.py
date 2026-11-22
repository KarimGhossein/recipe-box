"""Write the generated database (tools/usda/out/*.js) into app/index.html. Run after build_nutri_db.py."""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, '..', '..', 'app', 'index.html')
s = open(APP, encoding='utf8').read()
def put(name, fname, anchor_after):
    global s
    block = open(os.path.join(HERE, 'out', fname), encoding='utf8').read().strip()
    m = re.search(r'(//[^\n]*\n)?const ' + name + r' = \{.*?\};', s, re.S)
    if m: s = s[:m.start()] + block + s[m.end():]
    else:
        i = s.index(anchor_after) + len(anchor_after); s = s[:i] + '\n' + block + s[i:]
put('NUTRI_DB', 'nutri_db.js', '')
put('NUTRI_SOURCE', 'nutri_source.js', '')
nd = re.search(r'const NUTRI_SOURCE = \{.*?\};', s, re.S).group(0)
put('NUTRI_MICRO', 'nutri_micro.js', nd)
open(APP, 'w', encoding='utf8').write(s)
print('app/index.html updated')
