"""Assemble the demo: web/index.html + the rule packs it fetches.

    python docs/build_web.py                 # -> ./web/rules/*.json (serve ./web)
    python docs/build_web.py --out <dir>     # -> <dir>/index.html + <dir>/rules/*.json
"""
import argparse
import io
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
for fn in os.listdir(os.path.join(ROOT, "buntai", "rules")):
    if fn.endswith(".json"):
        shutil.copy2(os.path.join(ROOT, "buntai", "rules", fn), os.path.join(a.out, "rules", fn))
        n += 1
# GitHub Pages runs Jekyll, which skips files beginning with an underscore.
# _common.json is exactly that, so the marker file has to ship with the demo.
io.open(os.path.join(a.out, ".nojekyll"), "w", encoding="utf-8").write("")
print("built %s (%d rule packs)" % (a.out, n))
