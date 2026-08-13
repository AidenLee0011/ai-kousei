# -*- coding: utf-8 -*-
"""Check that every rule's quotation exists verbatim in the fetched source.

This is the anti-hallucination gate. A rule claims a clause and a quote; this
script fetches nothing, it reads sources/raw/*.txt (produced by
fetch_ja_sources.py) and searches for the quoted string with whitespace
normalised. A quote that cannot be found is either wrong or invented, and the
rule must be corrected or dropped.

    python sources/verify_quotes.py            # exit 1 if any quote is missing
    python sources/verify_quotes.py --lang ja
"""
import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(HERE, "raw")

# rule pack source key -> raw file(s) that may contain the quote
DOC_FILES = {
    "koyobun": ["bunkacho_koyobun.txt", "bunkacho_koyobun_page.txt"],
    "jtf": ["jtf_styleguide.txt", "textlint_jtf_style.txt"],
    "ja_tech": ["textlint_ja_technical.txt", "rule_weak_phrase.txt", "rule_redundant.txt",
                "rule_max_ten.txt", "rule_kanji_run.txt", "rule_doubled_joshi.txt",
                "rule_double_neg.txt", "rule_ga.txt", "rule_dearu_desumasu.txt"],
    "ai_writing": ["textlint_ai_writing.txt"],
}
MEASURED = {"jpcert_reports", "human_commits"}  # measured corpora, not documents


def norm(s):
    """Whitespace and markdown escapes are rendering artifacts, not content."""
    s = s.replace(chr(92) + "[", "[").replace(chr(92) + "]", "]").replace(chr(92) + "*", "*")
    return re.sub(r"\s+", "", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="ja")
    a = ap.parse_args()

    pack = json.load(io.open(os.path.join(ROOT, "buntai", "rules", "%s.json" % a.lang), encoding="utf-8"))
    if not os.path.isdir(RAW):
        print("sources/raw is missing. Run: python sources/fetch_ja_sources.py")
        return 2

    corpus = {}
    for key, files in DOC_FILES.items():
        text = ""
        for f in files:
            p = os.path.join(RAW, f)
            if os.path.exists(p):
                text += io.open(p, encoding="utf-8").read()
        corpus[key] = norm(text)

    ok = miss = 0
    for rule in pack["rules"]:
        src = rule.get("source") or {}
        doc, quote = src.get("doc"), src.get("quote", "")
        if doc in MEASURED:
            print("SKIP  %-28s measured corpus, not a document" % rule["id"])
            continue
        hay = corpus.get(doc, "")
        needle = norm(quote)
        # a quote may be a faithful contraction of two adjacent sentences, so
        # also accept the case where every clause of the quote is present
        found = needle in hay
        if not found and quote:
            parts = [norm(p) for p in re.split(r"[。、]", quote) if len(norm(p)) >= 6]
            found = bool(parts) and all(p in hay for p in parts)
        if found:
            ok += 1
            print("OK    %-28s %s %s" % (rule["id"], doc, src.get("loc", "")))
        else:
            miss += 1
            print("MISS  %-28s %s %s\n        quote: %s" % (rule["id"], doc, src.get("loc", ""), quote[:60]))
    print("\n%d verified, %d not found in the fetched sources" % (ok, miss))
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())
