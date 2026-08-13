"""Generate the README figures. Plain SVG, no dependencies.

Data: GitHub / npm registry, measured 2026-08-13. See README for the queries.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BG = "#ffffff"
INK = "#1f2328"
DIM = "#6e7781"
LINE = "#d0d7de"
HOLE = "#e5534b"
FILL = "#3fb950"
PART = "#d29922"
BAR = "#4c8dff"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def market_svg():
    langs = [
        ("English", "humanizer 35,301 / slopless 319", "covered", "commit + PR: none", "hole"),
        ("Japanese", "textlint-ja ai-writing 1,095", "partial", "commit + PR: none", "hole"),
        ("Korean", "none above 1 star", "hole", "commit + PR: none", "hole"),
        ("Chinese", "none above 1 star", "hole", "commit + PR: none", "hole"),
        ("German", "none above 1 star", "hole", "commit + PR: none", "hole"),
        ("French", "none above 1 star", "hole", "commit + PR: none", "hole"),
        ("Spanish", "none above 1 star", "hole", "commit + PR: none", "hole"),
    ]
    bars = [
        ("blader/humanizer", "EN prose, agent skill", 35301, "35,301 stars"),
        ("textlint-ja ai-writing", "JA prose, textlint", 1095, "1,095 stars / 48,603 npm dl per month"),
        ("berelevant/slopless", "EN prose, deterministic", 319, "319 stars"),
        ("commit or PR, any language", "the gap this fills", 0, "0"),
    ]
    W, H = 1180, 378
    o = io.StringIO()
    o.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="-apple-system,Segoe UI,Roboto,sans-serif">' % (W, H, W, H))
    o.write('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))
    o.write('<text x="28" y="34" font-size="17" font-weight="700" fill="%s">Where the tooling already exists, and where it does not</text>' % INK)
    o.write('<text x="28" y="56" font-size="12.5" fill="%s">GitHub and npm, measured 2026-08-13. De-AI writing tools cluster in English prose. No language has one for commit messages or pull request bodies.</text>' % DIM)

    # left: coverage matrix
    x0, y0, rw, rh = 28, 92, 168, 34
    o.write('<text x="%d" y="%d" font-size="11.5" font-weight="700" fill="%s">COVERAGE</text>' % (x0, y0 - 14, DIM))
    o.write('<text x="%d" y="%d" font-size="11.5" fill="%s">prose de-AI tool</text>' % (x0 + rw + 10, y0 - 14, DIM))
    o.write('<text x="%d" y="%d" font-size="11.5" fill="%s">commit / PR tool</text>' % (x0 + rw + 250, y0 - 14, DIM))
    for i, (lang, prose, pstate, commit, cstate) in enumerate(langs):
        y = y0 + i * rh
        o.write('<text x="%d" y="%d" font-size="13" fill="%s">%s</text>' % (x0, y + 17, INK, lang))
        for j, (label, state) in enumerate(((prose, pstate), (commit, cstate))):
            bx = x0 + rw + 10 + j * 240
            col = {"covered": FILL, "partial": PART, "hole": HOLE}[state]
            o.write('<rect x="%d" y="%d" width="232" height="26" rx="4" fill="%s" fill-opacity="0.10" stroke="%s" stroke-opacity="0.45"/>' % (bx, y, col, col))
            o.write('<text x="%d" y="%d" font-size="11.5" fill="%s">%s</text>' % (bx + 9, y + 17, INK, esc(label)))

    # right: demand bars (log-ish scale by sqrt for readability)
    bx0, by0 = 700, 92
    o.write('<text x="%d" y="%d" font-size="11.5" font-weight="700" fill="%s">DEMAND, MEASURED</text>' % (bx0, by0 - 14, DIM))
    maxv = 35301 ** 0.5
    for i, (name, sub, v, label) in enumerate(bars):
        y = by0 + i * 62
        w = int((v ** 0.5) / maxv * 400) if v else 3
        col = BAR if v else HOLE
        o.write('<text x="%d" y="%d" font-size="12.5" font-weight="600" fill="%s">%s</text>' % (bx0, y + 12, INK, esc(name)))
        o.write('<text x="%d" y="%d" font-size="11" fill="%s">%s</text>' % (bx0 + 260, y + 12, DIM, esc(sub)))
        o.write('<rect x="%d" y="%d" width="%d" height="14" rx="3" fill="%s"/>' % (bx0, y + 20, w, col))
        o.write('<text x="%d" y="%d" font-size="11.5" fill="%s">%s</text>' % (bx0 + w + 8, y + 31, DIM, esc(label)))
    o.write('<text x="%d" y="%d" font-size="11" fill="%s">bar length is square-root scaled</text>' % (bx0, by0 + 4 * 62 + 4, DIM))
    o.write('</svg>')
    return o.getvalue()


def pipeline_svg():
    W, H = 1180, 340
    o = io.StringIO()
    o.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="-apple-system,Segoe UI,Roboto,sans-serif">' % (W, H, W, H))
    o.write('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))
    o.write('<defs><marker id="a" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 z" fill="%s"/></marker></defs>' % DIM)
    o.write('<text x="28" y="34" font-size="17" font-weight="700" fill="%s">One rule file, two runtimes, no network</text>' % INK)
    o.write('<text x="28" y="56" font-size="12.5" fill="%s">The hook and the browser demo read the same JSON, so what you try on the page is what blocks your commit.</text>' % DIM)

    def box(x, y, w, h, title, sub, strong=False):
        o.write('<rect x="%d" y="%d" width="%d" height="%d" rx="7" fill="%s" fill-opacity="%s" stroke="%s"/>'
                % (x, y, w, h, BAR if strong else "#f6f8fa", "0.08" if strong else "1", BAR if strong else LINE))
        o.write('<text x="%d" y="%d" font-size="13" font-weight="600" fill="%s">%s</text>' % (x + 12, y + 24, INK, esc(title)))
        for k, line in enumerate(sub):
            o.write('<text x="%d" y="%d" font-size="11.5" fill="%s">%s</text>' % (x + 12, y + 44 + k * 16, DIM, esc(line)))

    def arrow(x1, y1, x2, y2):
        o.write('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.4" marker-end="url(#a)"/>' % (x1, y1, x2, y2, DIM))

    box(28, 96, 190, 78, "git commit", ["message written by you", "or by an agent"])
    arrow(222, 135, 258, 135)
    box(262, 96, 190, 78, "commit-msg hook", ["merge / squash / fixup", "are skipped"])
    arrow(456, 135, 492, 135)
    box(496, 96, 200, 78, "language detection", ["script for ja / ko / zh", "stopwords for de / fr / es"])
    arrow(700, 135, 736, 135)
    box(740, 96, 200, 78, "rules/_common.json", ["emoji, attribution footer,", "invisible characters"], True)
    box(740, 190, 200, 78, "rules/<lang>.json", ["language tells, structure,", "report template"], True)
    arrow(840, 178, 840, 188)
    arrow(944, 135, 980, 135)
    box(984, 96, 168, 78, "findings + score", ["error blocks the commit", "warning is printed"])
    box(496, 214, 200, 62, "browser demo", ["same JSON, same result"])
    arrow(736, 240, 700, 240)
    o.write('<text x="28" y="300" font-size="12" fill="%s">No model call. No telemetry. Rules load in 4 ms, a message lints in 0.24 ms (measured). Every finding carries the reason and the rewrite in the language being linted.</text>' % DIM)
    o.write('</svg>')
    return o.getvalue()


if __name__ == "__main__":
    for name, fn in (("market.svg", market_svg), ("pipeline.svg", pipeline_svg)):
        path = os.path.join(HERE, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(fn())
        print("wrote", path)
