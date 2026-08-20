# -*- coding: utf-8 -*-
"""Measure the pack against two corpora.

    human_<lang>.json  commits authored before 2022-11-30  -> a finding is a false positive
    llm_<lang>.json    commit messages written by an LLM   -> a finding is a true positive

    python bench/run.py --lang ja [--rules]
"""
import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from ai_kousei import lint, load_packs  # noqa: E402


def is_squash(msg):
    """PR squash merges bundle dozens of sub-commits. Kept separate: they are
    human, but they are not hand-written prose."""
    return sum(1 for l in msg.splitlines() if l.strip().startswith("* ")) >= 3


def load(kind, lang):
    p = os.path.join(HERE, "corpus", "%s_%s.json" % (kind, lang))
    if not os.path.exists(p):
        return []
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def run(lang, show_rules=False, show_misses=0):
    packs = load_packs()
    out = {}
    per_rule = {"human": {}, "human_squash": {}, "llm": {}}
    for kind in ("human", "human_squash", "llm"):
        rows = load(kind.split("_")[0], lang)
        if kind == "human":
            rows = [r for r in rows if not is_squash(r["msg"])]
        elif kind == "human_squash":
            rows = [r for r in rows if is_squash(r["msg"])]
        if not rows:
            continue
        flagged = err = 0
        scores = []
        misses = []
        for r in rows:
            res = lint(r["msg"], lang, packs)
            scores.append(res["score"])
            if res["findings"]:
                flagged += 1
            if res["errors"]:
                err += 1
            elif kind == "llm":
                misses.append(r["msg"].split("\n")[0][:70])
            for f in res["findings"]:
                per_rule[kind][f["id"]] = per_rule[kind].get(f["id"], 0) + 1
        out[kind] = dict(n=len(rows), flagged=flagged, err=err,
                         score=sum(scores) / len(scores), misses=misses)
    return out, per_rule


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="ja")
    ap.add_argument("--rules", action="store_true", help="per rule breakdown")
    ap.add_argument("--misses", type=int, default=0, help="print N undetected LLM messages")
    a = ap.parse_args()
    out, per_rule = run(a.lang, a.rules)

    print("corpus            n   any finding   blocks commit   mean score")
    for kind, label in (("human", "human, hand written"), ("human_squash", "human, squash merge"), ("llm", "LLM written")):
        if kind not in out:
            continue
        d = out[kind]
        print("%-18s %4d   %5.1f%%        %5.1f%%          %5.1f"
              % (label, d["n"], 100.0 * d["flagged"] / d["n"], 100.0 * d["err"] / d["n"], d["score"]))
    if "llm" in out and "human" in out:
        print("\ndetection (LLM blocked)   %.1f%%" % (100.0 * out["llm"]["err"] / out["llm"]["n"]))
        print("false positive (human blocked) %.1f%%" % (100.0 * out["human"]["err"] / out["human"]["n"]))

    if a.rules:
        print("\nrule                          human%%   LLM%%")
        hn = max(1, out.get("human", {}).get("n", 1))
        ln = max(1, out.get("llm", {}).get("n", 1))
        ids = sorted(set(per_rule["human"]) | set(per_rule["llm"]),
                     key=lambda i: -(per_rule["llm"].get(i, 0) / ln - per_rule["human"].get(i, 0) / hn))
        for i in ids:
            print("%-30s %5.1f  %5.1f" % (i, 100.0 * per_rule["human"].get(i, 0) / hn,
                                          100.0 * per_rule["llm"].get(i, 0) / ln))
    if a.misses and out.get("llm", {}).get("misses"):
        print("\nundetected LLM messages:")
        for m in out["llm"]["misses"][:a.misses]:
            print("  ", m)


if __name__ == "__main__":
    main()
