# -*- coding: utf-8 -*-
"""Ask an LLM to write commit messages, with no hint about style.

This is the positive half of the benchmark: messages a coding agent would
actually produce. The prompts say nothing about tone, length or AI tells, so a
finding here counts as a true positive.

    python bench/generate.py --lang ja
"""
import argparse
import io
import json
import os
import sys
import time

sys.path.insert(0, "D:/SH_DA_Agent_202602")
from da_backend.utils import llm_router  # noqa: E402

MODEL = "gemini-3.5-flash"
NATIVE_MODEL = "gemini-2.5-flash"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "corpus")

LANG_NAME = {"ja": "Japanese", "ko": "Korean", "zh": "Simplified Chinese",
             "de": "German", "fr": "French", "es": "Spanish"}

CHANGES = [
    "payment retry loop was unbounded; retry_max is now fixed at 3 and the overflow goes to a dead-letter queue",
    "added a Redis cache in front of the product detail API; TTL 300 seconds",
    "the login session cookie was missing SameSite=Lax; added it and bumped the session library",
    "removed the legacy CSV export endpoint, nobody has called it in six months",
    "N+1 query in the order list page: added a join and one prefetch",
    "the nightly batch died when the source table was empty; it now exits 0 with a log line",
    "renamed the config key api_timeout to api_timeout_ms and kept a fallback for one release",
    "upgraded the chart library to v5 and rewrote the two custom tooltips",
    "the search index rebuild now runs in parallel over four shards",
    "fixed a race between the file upload handler and the virus scanner",
]
STYLES = [
    "Write a commit message for this change in {lang}.",
    "Write a commit message with a body in {lang} explaining this change.",
    "Write a short pull request description in {lang} for this change: summary, background and how it was verified.",
]


def ask(prompt):
    """Router first, native Gemini when the router has no credit."""
    try:
        return llm_router.ask(prompt, model=MODEL, temperature=0.7, max_tokens=1200).strip()
    except Exception:
        body = {"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1200}}
        r = llm_router.generate_content(NATIVE_MODEL, body, force_native=True)
        return llm_router.text_of(r).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="ja")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    name = LANG_NAME[a.lang]
    rows = []
    for i, change in enumerate(CHANGES):
        for j, style in enumerate(STYLES):
            prompt = style.format(lang=name) + "\n\nChange:\n" + change + "\n\nOutput only the commit message."
            try:
                txt = ask(prompt)
            except Exception as e:
                print("  ERR %d/%d %s" % (i, j, str(e)[:120]))
                time.sleep(2)
                continue
            txt = txt.replace("```", "").strip("` \n")
            if txt:
                rows.append({"msg": txt, "change": i, "style": j})
                print("  %s %d/%d ok" % (a.lang, len(rows), len(CHANGES) * len(STYLES)))
    path = os.path.join(OUT, "llm_%s.json" % a.lang)
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print("%s: %d messages -> %s" % (a.lang, len(rows), path))


if __name__ == "__main__":
    main()
