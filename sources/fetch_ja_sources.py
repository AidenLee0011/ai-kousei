# -*- coding: utf-8 -*-
"""Fetch the Japanese authorities the rule pack is derived from.

Nothing here is invented. Every rule in ai_kousei/rules/ja.json cites one of these
documents, and this script is what pulls them so a reviewer can check the claim.

    python sources/fetch_ja_sources.py

Writes sources/raw/<key>.txt (extracted text) and sources/raw/_index.json.
"""
import io
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

SOURCES = [
    # 文化審議会建議「公用文作成の考え方」2022-01-07 — official Japanese government
    # guidance on writing public documents: headings, one-sentence length, tone.
    ("bunkacho_koyobun", "https://www.bunka.go.jp/seisaku/bunkashingikai/kokugo/hokoku/pdf/93651301_01.pdf", "pdf"),
    ("bunkacho_koyobun_page", "https://www.bunka.go.jp/seisaku/bunkashingikai/kokugo/hokoku/93657201.html", "html"),
    # 日本翻訳連盟 JTF日本語標準スタイルガイド(翻訳用) — the translation industry standard.
    ("jtf_styleguide", "https://www.jtf.jp/pdf/jtf_style_guide.pdf", "pdf"),
    ("jtf_styleguide_page", "https://www.jtf.jp/tips/styleguide", "html"),
    # textlint-ja presets: machine readable distillations, each rule citing its source.
    ("textlint_jtf_style", "https://raw.githubusercontent.com/textlint-ja/textlint-rule-preset-JTF-style/master/README.md", "text"),
    ("textlint_ja_technical", "https://raw.githubusercontent.com/textlint-ja/textlint-rule-preset-ja-technical-writing/master/README.md", "text"),
    ("textlint_ai_writing", "https://raw.githubusercontent.com/textlint-ja/textlint-rule-preset-ai-writing/main/README.md", "text"),
    ("textlint_ja_spacing", "https://raw.githubusercontent.com/textlint-ja/textlint-rule-preset-ja-spacing/master/README.md", "text"),
    # Individual textlint rules that a rule in ja.json cites directly.
    ("rule_weak_phrase", "https://raw.githubusercontent.com/textlint-ja/textlint-rule-ja-no-weak-phrase/master/README.md", "text"),
    ("rule_redundant", "https://raw.githubusercontent.com/textlint-ja/textlint-rule-ja-no-redundant-expression/master/README.md", "text"),
    ("rule_max_ten", "https://raw.githubusercontent.com/textlint-ja/textlint-rule-max-ten/master/README.md", "text"),
    ("rule_kanji_run", "https://raw.githubusercontent.com/textlint-ja/textlint-rule-max-kanji-continuous-len/master/README.md", "text"),
    ("rule_doubled_joshi", "https://raw.githubusercontent.com/textlint-ja/textlint-rule-no-doubled-joshi/master/README.md", "text"),
    ("rule_double_neg", "https://raw.githubusercontent.com/textlint-ja/textlint-rule-no-double-negative-ja/master/README.md", "text"),
    ("rule_ga", "https://raw.githubusercontent.com/textlint-ja/textlint-rule-no-doubled-conjunctive-particle-ga/master/README.md", "text"),
    ("rule_dearu_desumasu", "https://raw.githubusercontent.com/textlint-ja/textlint-rule-no-mix-dearu-desumasu/master/README.md", "text"),
    # J-STAGE search API: research on translationese in Japanese.
    ("jstage_honyakucho", "https://api.jstage.jst.go.jp/searchapi/do?service=3&text=%E7%BF%BB%E8%A8%B3%E8%AA%BF&count=50", "text"),
    ("jstage_honyaku_buntai", "https://api.jstage.jst.go.jp/searchapi/do?service=3&text=%E7%BF%BB%E8%A8%B3%E6%96%87%E4%BD%93&count=50", "text"),
]


def fetch(url: str, kind: str) -> str:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=60)
    r.raise_for_status()
    if kind == "pdf":
        from pdfminer.high_level import extract_text
        tmp = os.path.join(RAW, "_tmp.pdf")
        with open(tmp, "wb") as f:
            f.write(r.content)
        txt = extract_text(tmp)
        os.remove(tmp)
        return txt
    if kind == "html":
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script", "style"]):
            t.decompose()
        return re.sub(r"\n{3,}", "\n\n", soup.get_text("\n"))
    r.encoding = r.encoding or "utf-8"
    return r.text


def main():
    os.makedirs(RAW, exist_ok=True)
    index = []
    for key, url, kind in SOURCES:
        try:
            txt = fetch(url, kind)
            path = os.path.join(RAW, key + ".txt")
            with io.open(path, "w", encoding="utf-8") as f:
                f.write(txt)
            index.append({"key": key, "url": url, "kind": kind, "chars": len(txt), "ok": True})
            print("OK   %-26s %7d chars  %s" % (key, len(txt), url))
        except Exception as e:
            index.append({"key": key, "url": url, "kind": kind, "ok": False, "error": str(e)[:200]})
            print("FAIL %-26s %s  %s" % (key, str(e)[:90], url))
    with io.open(os.path.join(RAW, "_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    ok = sum(1 for i in index if i["ok"])
    print("%d/%d sources fetched" % (ok, len(index)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
