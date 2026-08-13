"""ringi — deterministic linter for non-English commit messages and PR bodies.

No network, no LLM, no dependencies. Rules live in ringi/rules/*.json and are the
single source of truth shared with the browser demo.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata

__version__ = "0.1.0"

RULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules")
COMMON = "_common"

SEVERITY_ORDER = {"error": 0, "warn": 1}


def load_packs(rules_dir: str = RULES_DIR) -> dict:
    packs = {}
    for fn in sorted(os.listdir(rules_dir)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(rules_dir, fn), encoding="utf-8") as f:
            pack = json.load(f)
        packs[pack["lang"]] = pack
    return packs


# JSON carries astral-plane emoji as a JS surrogate-pair class. Python works on
# code points, so the same class is rewritten before compiling. Both runtimes
# then read one rule file.
_JS_SURROGATE_PAIR = r"[\uD83C-\uDBFF][\uDC00-\uDFFF]"
_PY_ASTRAL = r"[\U0001F000-\U0001FAFF]"


def _compile(pattern: str, flags: str = "") -> re.Pattern:
    pattern = pattern.replace(_JS_SURROGATE_PAIR, _PY_ASTRAL)
    f = 0
    if "i" in flags:
        f |= re.IGNORECASE
    if "m" in flags:
        f |= re.MULTILINE
    return re.compile(pattern, f)


def width(s: str) -> int:
    """Display columns. East Asian wide/fullwidth count as 2."""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


def split_message(text: str) -> tuple[str, str]:
    """git commit message -> (subject, body). Comment lines and diff are dropped."""
    lines = []
    for ln in text.replace("\r\n", "\n").split("\n"):
        if ln.startswith("#"):
            continue
        if ln.startswith("diff --git ") or ln.startswith("# ------------------------ >8"):
            break
        lines.append(ln)
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        return "", ""
    subject = lines[0].strip()
    body = "\n".join(lines[1:]).strip("\n")
    return subject, body


def detect_lang(text: str, packs: dict) -> str | None:
    """Script first (ja/ko/zh), then stopwords for latin-script packs."""
    scores: dict[str, float] = {}
    for lang, pack in packs.items():
        if lang == COMMON:
            continue
        det = pack.get("detect") or {}
        sc = 0.0
        if det.get("script"):
            hits = len(re.findall(det["script"], text))
            sc += hits * float(det.get("weight", 1))
        for w in det.get("stopwords", []):
            sc += len(re.findall(r"(?<![\w])" + re.escape(w) + r"(?![\w])", text, re.IGNORECASE)) * float(
                det.get("weight", 1)
            )
        if sc:
            scores[lang] = sc
    if not scores:
        return None
    best = max(scores, key=lambda k: scores[k])
    # Japanese kana beats a bare-hanzi zh match; kana is exclusive to ja.
    if "ja" in scores and re.search(r"[぀-ゟ゠-ヿ]", text):
        best = "ja"
    return best if scores[best] >= 2 else None


def _cite(pack: dict, src) -> str:
    """Render a rule's citation as 'document, section'. Empty when unsourced."""
    if not src:
        return ""
    doc = (pack.get("sources") or {}).get(src.get("doc"), {})
    title = doc.get("title", src.get("doc", ""))
    loc = src.get("loc", "")
    return ("%s %s" % (title, loc)).strip()


def _scope_text(scope: str, subject: str, body: str) -> str:
    if scope == "subject":
        return subject
    if scope == "body":
        return body
    return (subject + "\n" + body).strip()


EN_LABELS = {
    "sentence_long": {
        "title": "sentence of {n} characters > {max}",
        "why": "Long sentences hide the subject-predicate relation.",
        "fix": "Split the sentence.",
    },
    "max_ten": {
        "title": "{n} commas in one sentence > {max}",
        "why": "Too many commas means the sentence carries more than one point.",
        "fix": "Split the sentence or use a list.",
    },
    "kanji_run": {
        "title": "{n} ideographs in a row > {max}",
        "why": "Long ideograph runs are hard to parse.",
        "fix": "Break the compound or rephrase.",
    },
    "heading_order": {
        "title": "mixed enumeration markers",
        "why": "One document should use one hierarchy of markers.",
        "fix": "Use a single official order.",
    },
    "subject_long": {
        "title": "subject {w} > {max} columns",
        "why": "Long subjects get truncated in git log and in review lists.",
        "fix": "Move the detail into the body.",
    },
    "subject_period": {
        "title": "subject ends with a period",
        "why": "A commit subject is a headline, not a sentence.",
        "fix": "Drop the trailing period.",
    },
    "bullets": {
        "title": "{n} bullets in the body",
        "why": "A laundry list of bullets is a generation habit. It also hides the reason for the change.",
        "fix": "Keep the {max} that matter, or split the commit.",
    },
    "sections": {
        "title": "report sections missing: {missing}",
        "why": "The standard report shape is what makes a human-written log scannable.",
        "fix": "Run `ringi template --lang {lang}`.",
    },
}


def _label(st: dict, key: str, **kw) -> dict:
    base = dict(EN_LABELS[key])
    base.update((st.get("labels") or {}).get(key, {}))
    return {k: str(v).format(**kw) for k, v in base.items()}


def _structural(pack: dict, subject: str, body: str) -> list:
    out = []
    st = pack.get("structural") or {}
    lang = pack["lang"]
    max_w = st.get("subject_max_width")
    if max_w and subject and width(subject) > max_w:
        out.append(
            dict(
                id="%s-subject-too-long" % lang,
                severity="warn",
                weight=6,
                scope="subject",
                match=subject[:40],
                line=1,
                **_label(st, "subject_long", w=width(subject), max=max_w)
            )
        )
    per = st.get("subject_no_period")
    if per and subject and re.search(per, subject):
        out.append(
            dict(
                id="%s-subject-period" % lang,
                severity="warn",
                weight=3,
                scope="subject",
                match=subject[-8:],
                line=1,
                **_label(st, "subject_period")
            )
        )
    bmax = st.get("bullet_max")
    if bmax:
        bullets = len(re.findall(r"^\s*(?:[-*]|\d+[.)])\s+", body, re.MULTILINE))
        if bullets > bmax:
            out.append(
                dict(
                    id="%s-bullet-flood" % lang,
                    severity="warn",
                    weight=7,
                    scope="body",
                    match="",
                    line=None,
                    **_label(st, "bullets", n=bullets, max=bmax)
                )
            )
    secs = st.get("body_sections") or []
    if secs and len([l for l in body.split("\n") if l.strip()]) >= 2:
        missing = [s for s in secs if s.lower() not in body.lower()]
        if missing:
            out.append(
                dict(
                    id="%s-missing-sections" % lang,
                    severity="warn",
                    weight=5,
                    scope="body",
                    match="",
                    line=None,
                    **_label(st, "sections", missing=", ".join(missing), lang=lang)
                )
            )
    # Per sentence checks. Sentences are split on the Japanese full stop and on
    # line breaks, which is what the cited rules operate on.
    smax = st.get("sentence_max_chars")
    tmax = st.get("max_ten")
    kmax = st.get("kanji_run_max")
    if smax or tmax or kmax:
        for sent in [s for s in re.split(r"[。\n]", body) if s.strip()]:
            if smax and len(sent) > smax:
                out.append(dict(id="%s-sentence-too-long" % lang, severity="warn", weight=7,
                                scope="body", match=sent[:40], line=None,
                                **_label(st, "sentence_long", n=len(sent), max=smax)))
                break
        for sent in [s for s in re.split(r"[。\n]", body) if s.strip()]:
            n = sent.count("、")
            if tmax and n > tmax:
                out.append(dict(id="%s-max-ten" % lang, severity="warn", weight=6,
                                scope="body", match=sent[:40], line=None,
                                **_label(st, "max_ten", n=n, max=tmax)))
                break
        if kmax:
            m = re.search(r"[一-鿿]{%d,}" % (kmax + 1), body)
            if m:
                out.append(dict(id="%s-kanji-run" % lang, severity="warn", weight=5,
                                scope="body", match=m.group(0)[:20], line=None,
                                **_label(st, "kanji_run", n=len(m.group(0)), max=kmax)))

    if st.get("heading_order"):
        kinds = set()
        for ln in body.split("\n"):
            s = ln.strip()
            if re.match(r"^[-*]\s", s):
                kinds.add("dash")
            elif re.match(r"^[・]\s?", s):
                kinds.add("nakaten")
            elif re.match(r"^\d+[.)．）]\s?", s):
                kinds.add("digit")
            elif re.match(r"^[①-⑳]", s):
                kinds.add("circled")
            elif re.match(r"^[ア-ン][.、)）]\s?", s):
                kinds.add("kana")
        if len(kinds) > 1:
            out.append(dict(id="%s-heading-order" % lang, severity="warn", weight=6,
                            scope="body", match="/".join(sorted(kinds)), line=None,
                            **_label(st, "heading_order")))

    tone = st.get("tone")
    if tone and body:
        a = _compile(tone["a"]).findall(body + "\n")
        b = _compile(tone["b"]).findall(body + "\n")
        if a and b:
            out.append(
                dict(
                    id="%s-tone-mix" % lang,
                    severity="warn",
                    weight=8,
                    scope="body",
                    title=tone.get("title", "sentence ending mixed"),
                    why=tone.get("why", ""),
                    fix=tone.get("fix", ""),
                    source=tone.get("source", ""),
                    match="",
                    line=None,
                )
            )
    return out


def lint(text: str, lang: str | None = None, packs: dict | None = None,
         profile: str = "commit") -> dict:
    """profile picks the rule set: a record, a report, an agent handoff or a
    customer facing message. Some rules invert between them, which is why the
    profile is explicit rather than guessed."""
    packs = packs if packs is not None else load_packs()
    subject, body = split_message(text)
    full = (subject + "\n" + body).strip()
    lang = lang or detect_lang(full, packs)
    findings = []

    active = [packs[COMMON]] if COMMON in packs else []
    if lang and lang in packs:
        active.append(packs[lang])
    prof = ((packs.get(lang) or {}).get("profiles") or {}).get(profile, {})
    off = set(prof.get("off", []))

    for pack in active:
        for rule in pack.get("rules", []):
            only = rule.get("profiles")
            if (only and profile not in only) or rule["id"] in off:
                continue
            scope = rule.get("scope", "any")
            target = _scope_text(scope, subject, body)
            if not target:
                continue
            m = _compile(rule["pattern"], rule.get("flags", "")).search(target)
            if not m:
                continue
            line = full[: full.find(m.group(0))].count("\n") + 1 if m.group(0) in full else None
            loc = (rule.get("i18n") or {}).get(lang or "", {})
            findings.append(
                dict(
                    id=rule["id"],
                    severity=rule.get("severity", "warn"),
                    weight=int(rule.get("weight", 5)),
                    scope=scope,
                    title=loc.get("title", rule.get("title", rule["id"])),
                    why=loc.get("why", rule.get("why", "")),
                    fix=loc.get("fix", rule.get("fix", "")),
                    match=m.group(0)[:60],
                    line=line,
                    source=_cite(pack, rule.get("source")),
                )
            )

    if lang and lang in packs:
        findings += [f for f in _structural(packs[lang], subject, body) if f["id"] not in off]

    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f["severity"], 9), -f["weight"]))
    score = max(0, 100 - sum(f["weight"] for f in findings))
    errors = sum(1 for f in findings if f["severity"] == "error")
    return dict(
        lang=lang,
        profile=profile,
        profile_label=prof.get("label", profile),
        lang_name=(packs.get(lang) or {}).get("name") if lang else None,
        maturity=(packs.get(lang) or {}).get("maturity") if lang else None,
        subject=subject,
        body=body,
        findings=findings,
        score=score,
        errors=errors,
        warns=len(findings) - errors,
        passed=errors == 0,
    )
