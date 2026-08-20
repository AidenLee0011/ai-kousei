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
for name in ("index.html", "lint.js"):
    src = os.path.join(ROOT, "web", name)
    dst = os.path.join(a.out, name)
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copy2(src, dst)
n = 0
for fn in os.listdir(os.path.join(ROOT, "ai_kousei", "rules")):
    if fn.endswith(".json"):
        shutil.copy2(os.path.join(ROOT, "ai_kousei", "rules", fn), os.path.join(a.out, "rules", fn))
        n += 1
# GitHub Pages runs Jekyll, which skips files beginning with an underscore.
# _common.json is exactly that, so the marker file has to ship with the demo.
io.open(os.path.join(a.out, ".nojekyll"), "w", encoding="utf-8").write("")
# The npm build shares the same engine file and the same rule packs.
npm = os.path.join(ROOT, "npm")
if os.path.isdir(npm):
    shutil.copy2(os.path.join(ROOT, "web", "lint.js"), os.path.join(npm, "lint.js"))
    os.makedirs(os.path.join(npm, "rules"), exist_ok=True)
    for fn in os.listdir(os.path.join(ROOT, "ai_kousei", "rules")):
        if fn.endswith(".json"):
            shutil.copy2(os.path.join(ROOT, "ai_kousei", "rules", fn), os.path.join(npm, "rules", fn))
print("built %s (%d rule packs)" % (a.out, n))
