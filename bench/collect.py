"""Collect real human commit messages from GitHub, one corpus per language.

Only commits authored before 2022-11-30 are taken, which is before general
availability of chat LLMs. That keeps the corpus human written, so a finding on
it counts as a false positive.

    python bench/collect.py            # writes bench/corpus/human_<lang>.json
"""
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "corpus")
CUTOFF = "2022-11-30"

TERMS = {
    "ja": ["修正", "対応", "追加", "リファクタリング", "変更"],
    "ko": ["수정", "추가", "변경", "리팩토링", "버그"],
    "zh": ["修复", "优化", "新增", "重构", "调整"],
    "de": ["behoben", "hinzugefügt", "Anpassung", "Korrektur", "geändert"],
    "fr": ["correction", "ajout", "mise à jour", "corrigé", "suppression"],
    "es": ["corrección", "añadido", "actualización", "arreglado", "eliminado"],
}
SCRIPT = {
    "ja": lambda m: re.search(r"[぀-ゟ゠-ヿ]", m),
    "ko": lambda m: re.search(r"[가-힣]", m),
    "zh": lambda m: re.search(r"[一-鿿]", m) and not re.search(r"[぀-ヿ가-힣]", m),
    "de": lambda m: re.search(r"[a-zA-ZäöüßÄÖÜ]", m),
    "fr": lambda m: re.search(r"[a-zA-Zàâçéèêëîïôûùüÿ]", m),
    "es": lambda m: re.search(r"[a-zA-Záéíóúñü]", m),
}
SKIP = re.compile(r"^(Merge|Revert|Bump |Update dependency|chore\(deps\))", re.I)


def search(term, page=1):
    q = '%s committer-date:<%s' % (term, CUTOFF)
    u = "https://api.github.com/search/commits?q=" + urllib.parse.quote(q) + "&per_page=60&page=%d" % page
    r = urllib.request.Request(u, headers={"User-Agent": "ringi-bench", "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(r, timeout=40))


def main():
    os.makedirs(OUT, exist_ok=True)
    for lang, terms in TERMS.items():
        seen, rows = set(), []
        for t in terms:
            try:
                d = search(t)
            except Exception as e:
                print("  ERR", lang, t, e)
                time.sleep(8)
                continue
            for it in d.get("items", []):
                msg = it["commit"]["message"].replace("\r\n", "\n").strip()
                first = msg.split("\n")[0]
                if SKIP.match(first) or not SCRIPT[lang](msg) or len(first) < 6:
                    continue
                key = first[:60]
                if key in seen:
                    continue
                seen.add(key)
                rows.append({"msg": msg, "repo": it["repository"]["full_name"], "date": it["commit"]["author"]["date"][:10]})
            print("  %s %-16s -> %d" % (lang, t, len(rows)))
            time.sleep(8)
        path = os.path.join(OUT, "human_%s.json" % lang)
        with io.open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        print("%s: %d messages -> %s" % (lang, len(rows), path))


if __name__ == "__main__":
    main()
