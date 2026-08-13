"""Assemble the demo: web/index.html + the rule packs it fetches.

    python docs/build_web.py                 # -> ./web/rules/*.json (serve ./web)
    python docs/build_web.py --out <dir>     # -> <dir>/index.html + <dir>/rules/*.json
"""
import argparse
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ap = argparse.ArgumentParser()
ap.add_argument("--out", default=os.path.join(ROOT, "web"))
a = ap.parse_args()

os.makedirs(os.path.join(a.out, "rules"), exist_ok=True)
src_html = os.path.join(ROOT, "web", "index.html")
dst_html = os.path.join(a.out, "index.html")
if os.path.abspath(src_html) != os.path.abspath(dst_html):
    shutil.copy2(src_html, dst_html)
n = 0
for fn in os.listdir(os.path.join(ROOT, "natc", "rules")):
    if fn.endswith(".json"):
        shutil.copy2(os.path.join(ROOT, "natc", "rules", fn), os.path.join(a.out, "rules", fn))
        n += 1
print("built %s (%d rule packs)" % (a.out, n))
