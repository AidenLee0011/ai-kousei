# -*- coding: utf-8 -*-
"""Collect real Japanese reports, then measure how they are actually written.

The style guides say what should be done. This says what practitioners do:
sentence endings, fixed phrases, heading vocabulary, sentence length. The
report template in rules/ja.json is checked against these numbers, not against
taste.

Sources are public reports from Japanese organisations (JPCERT/CC quarterly
activity reports and similar). Only measurements are stored, plus short
phrases for frequency counting.

    python sources/fetch_ja_reports.py --limit 8
"""
import argparse
import io
import json
import os
import re
import urllib.parse
from collections import Counter

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "reports")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0 Safari/537.36"}
INDEX = "https://www.jpcert.or.jp/pr/"


def pdf_text(url: str) -> str:
    from pdfminer.high_level import extract_text
    r = requests.get(url, headers=UA, timeout=90)
    r.raise_for_status()
    tmp = os.path.join(OUT, "_tmp.pdf")
    with open(tmp, "wb") as f:
        f.write(r.content)
    try:
        return extract_text(tmp)
    finally:
        os.remove(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=8)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    r = requests.get(INDEX, headers=UA, timeout=40)
    r.encoding = r.apparent_encoding or "utf-8"
    urls = []
    for h in re.findall(r'href="([^"]+\.pdf)"', r.text):
        u = urllib.parse.urljoin(INDEX, h)
        if u not in urls:
            urls.append(u)
    urls = urls[: a.limit]

    saved = []
    for u in urls:
        name = os.path.basename(u).replace(".pdf", ".txt")
        path = os.path.join(OUT, name)
        if os.path.exists(path):
            saved.append(path)
            continue
        try:
            t = pdf_text(u)
            with io.open(path, "w", encoding="utf-8") as f:
                f.write(t)
            saved.append(path)
            print("OK   %-34s %7d chars" % (name, len(t)))
        except Exception as e:
            print("FAIL %-34s %s" % (name, str(e)[:80]))

    corpus = "\n".join(io.open(p, encoding="utf-8").read() for p in saved)
    sents = [s.strip() for s in re.split(r"[。\n]+", corpus) if len(s.strip()) > 4]
    endings = Counter()
    for s in sents:
        if re.search(r"(?:です|ます|ました|ません)$", s):
            endings["敬体"] += 1
        elif re.search(r"(?:である|であった|した|する|ない|た)$", s):
            endings["常体"] += 1
        elif re.search(r"[一-鿿ァ-ヶA-Za-z0-9]$", s):
            endings["体言止め"] += 1
        else:
            endings["その他"] += 1
    phrases = Counter()
    for p in re.findall(r"(?:について|に関する|の件|に係る|のとおり|に伴い|を踏まえ|に基づき|概要|背景|課題|対応|方針|結果|考察|今後|以上|なお|また|ただし)", corpus):
        phrases[p] += 1
    heads = Counter()
    for m in re.finditer(r"^\s*(?:\d+[.．]|第\d+|[（(]\d+[）)]|[ア-ン][.、])\s*([^\n]{2,20})$", corpus, re.M):
        heads[m.group(1).strip()] += 1

    stats = {
        "documents": len(saved),
        "sentences": len(sents),
        "mean_sentence_len": round(sum(len(s) for s in sents) / max(1, len(sents)), 1),
        "ending_distribution": {k: round(100.0 * v / max(1, sum(endings.values())), 1) for k, v in endings.most_common()},
        "fixed_phrases_top": phrases.most_common(20),
        "heading_vocabulary_top": heads.most_common(30),
    }
    with io.open(os.path.join(OUT, "_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    print(json.dumps(stats, ensure_ascii=False, indent=1)[:1800])


if __name__ == "__main__":
    main()
