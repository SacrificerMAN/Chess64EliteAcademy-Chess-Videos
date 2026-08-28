"""Expand KNOWN map in fix_resolve.py at build time."""
from pathlib import Path
p = Path("fix_resolve.py")
if not p.exists():
    raise SystemExit(0)
t = p.read_text()
extra = '''
    "jan-krzysztof duda": "Polish_fighter3000",
    "jan krzysztof duda": "Polish_fighter3000",
    "duda, jan-krzysztof": "Polish_fighter3000",
    "duda, jan krzysztof": "Polish_fighter3000",
    "duda": "Polish_fighter3000",
    "arjun erigaisi": "GHANDEEVAM2003",
    "erigaisi arjun": "GHANDEEVAM2003",
    "erigaisi, arjun": "GHANDEEVAM2003",
    "erigaisi": "GHANDEEVAM2003",
'''
if "Polish_fighter3000" not in t:
    t = t.replace('"levon aronian": "LevAronian",', '"levon aronian": "LevAronian",' + extra)
    p.write_text(t)
    print("expanded KNOWN with Duda/Erigaisi")
else:
    print("KNOWN already expanded")
