"""natc CLI — lint / template / hook / langs / selftest."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

from . import COMMON, __version__, detect_lang, lint, load_packs

HOOK = """#!/bin/sh
# nativecommit commit-msg hook
case "$2" in merge|squash|fixup) exit 0;; esac
%s lint "$1" %s || exit 1
"""


def _out(s: str = "") -> None:
    try:
        sys.stdout.write(s + "\n")
    except UnicodeEncodeError:  # cp949 consoles
        sys.stdout.write(s.encode("utf-8", "replace").decode("ascii", "replace") + "\n")


def _git_config(key: str) -> str | None:
    try:
        p = subprocess.run(["git", "config", "--get", key], capture_output=True, text=True, timeout=10)
        return p.stdout.strip() or None if p.returncode == 0 else None
    except Exception:
        return None


def cmd_lint(a) -> int:
    if a.message is not None:
        text = a.message
    elif a.file and a.file != "-":
        with open(a.file, encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    # A kanji-only subject cannot be told apart from Chinese by script alone, so a
    # repository can pin its language: git config natc.lang ja
    r = lint(text, a.lang or _git_config("natc.lang"))
    if a.json:
        _out(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["passed"] else 1
    if r["lang"] is None:
        _out("natc: language not detected. English is out of scope on purpose "
             "(use blader/humanizer). Force with --lang ja|ko|zh|de|fr|es.")
        return 0
    _out("%s  score %d/100  errors %d  warnings %d" % (r["lang_name"], r["score"], r["errors"], r["warns"]))
    if r["maturity"] == "starter":
        _out("  pack maturity: starter — rules are a first pass, contributions welcome")
    for f in r["findings"]:
        tag = "ERROR" if f["severity"] == "error" else "warn "
        loc = ("L%d " % f["line"]) if f.get("line") else ""
        _out("  [%s] %s%s  (%s)" % (tag, loc, f["title"], f["id"]))
        if f.get("match"):
            _out("         found: %s" % f["match"])
        if f.get("why") and not a.quiet:
            _out("         why:   %s" % f["why"])
        if f.get("fix") and not a.quiet:
            _out("         fix:   %s" % f["fix"])
    if not r["findings"]:
        _out("  no findings")
    return 0 if r["passed"] else 1


def cmd_template(a) -> int:
    packs = load_packs()
    lang = a.lang or "ko"
    if lang not in packs:
        _out("unknown lang: %s" % lang)
        return 2
    tpl = (packs[lang].get("template") or {}).get("pr" if a.pr else "commit", "")
    _out(tpl)
    return 0


def cmd_langs(a) -> int:
    packs = load_packs()
    _out("%-6s %-10s %-9s %s" % ("code", "name", "maturity", "rules"))
    for lang, p in sorted(packs.items()):
        if lang == COMMON:
            continue
        _out("%-6s %-10s %-9s %d" % (lang, p["name"], p.get("maturity", "-"), len(p.get("rules", []))))
    _out("%-6s %-10s %-9s %d" % (COMMON, "-", "curated", len(packs[COMMON]["rules"])))
    _out("en     -          n/a       out of scope by design")
    return 0


def _git_dir() -> str | None:
    try:
        p = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True, timeout=10)
        return p.stdout.strip() if p.returncode == 0 else None
    except Exception:
        return None


def cmd_hook(a) -> int:
    gd = _git_dir()
    if not gd:
        _out("not a git repository")
        return 2
    path = os.path.join(gd, "hooks", "commit-msg")
    if a.action == "uninstall":
        if os.path.exists(path) and "nativecommit" in open(path, encoding="utf-8").read():
            os.remove(path)
            _out("removed %s" % path)
        return 0
    cmd = a.cmd or ("%s -m natc" % os.path.basename(sys.executable).replace(".exe", ""))
    if a.lang:
        subprocess.run(["git", "config", "natc.lang", a.lang], capture_output=True, timeout=10)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(HOOK % (cmd, ("--lang " + a.lang) if a.lang else ""))
    os.chmod(path, 0o755)
    _out("installed %s" % path)
    _out("  runs: %s lint <msg> %s" % (cmd, ("--lang " + a.lang) if a.lang else ""))
    return 0


def cmd_selftest(a) -> int:
    packs = load_packs()
    ids = set()
    for lang, p in packs.items():
        assert p.get("rules"), "pack %s has no rules" % lang
        for r in p["rules"]:
            assert r["id"] not in ids, "duplicate rule id %s" % r["id"]
            ids.add(r["id"])
            for k in ("severity", "weight", "title", "why", "fix"):
                assert k in r, "%s missing %s" % (r["id"], k)
            assert r["severity"] in ("error", "warn"), r["id"]
            re.compile(r["pattern"])
        if lang != COMMON:
            assert p.get("template", {}).get("commit"), "%s has no commit template" % lang
            assert p.get("structural", {}).get("body_sections"), "%s has no sections" % lang

    # language detection
    samples = {
        "ja": "決済のリトライ上限を3回に変更した",
        "ko": "결제 재시도 상한을 3회로 변경",
        "zh": "支付重试上限改为三次",
        "de": "Wiederholungen der Zahlung auf drei begrenzt, weil die Warteschlange überlief",
        "fr": "la limite des tentatives de paiement est fixée à trois pour cette file",
        "es": "el limite de reintentos de pago se fija en tres para esta cola",
    }
    for want, s in samples.items():
        got = detect_lang(s, packs)
        assert got == want, "detect %s -> %s" % (want, got)

    # Japanese: generated-looking message is caught
    r = lint("feat: 各種修正\n\nまさに重要な変更ではないでしょうか。\nいかがでしょうか。\n", "ja")
    got = {f["id"] for f in r["findings"]}
    assert "ja-hedge-dewanai" in got and "ja-vague-verb" in got and "ja-ikaga" in got, got
    assert not r["passed"] and r["score"] < 70, r["score"]

    # Korean: blog tone + guess ending + vague subject
    r = lint("fix: 개선\n\n다음과 같습니다. 문제가 해결된 것 같습니다.\n함께 살펴보겠습니다.\n", "ko")
    got = {f["id"] for f in r["findings"]}
    assert {"ko-vague-subject", "ko-geot-gatda", "ko-blog-tone", "ko-daeum-gwa-gatseumnida"} <= got, got

    # Korean: template-shaped human report passes
    ok = ("fix: 결제 재시도 상한 3회로 변경\n\n"
          "왜: 재시도가 무한 반복되어 큐가 밀림\n"
          "무엇: retry_max 를 3 으로 고정, 초과 시 dead-letter 로 이동\n"
          "확인: 부하 테스트 1시간, 큐 적체 0\n")
    r = lint(ok)
    assert r["lang"] == "ko" and r["passed"], (r["lang"], [f["id"] for f in r["findings"]])
    assert r["score"] >= 90, r["score"]

    # astral emoji must be caught on both runtimes
    r = lint("feat: \U0001F680 캐시 계층 추가", "ko")
    assert "common-emoji-subject" in {f["id"] for f in r["findings"]}, [f["id"] for f in r["findings"]]

    # common pack: attribution footer and emoji subject
    r = lint("feat: 캐시 계층 추가\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n", "ko")
    assert "common-ai-attribution" in {f["id"] for f in r["findings"]}
    r = lint("feat: 캐시 추가", "ko")
    assert r["passed"], [f["id"] for f in r["findings"]]

    # scope: body rule must not fire on subject only
    r = lint("다음과 같습니다", "ko")
    assert "ko-daeum-gwa-gatseumnida" not in {f["id"] for f in r["findings"]}

    # tone mixing
    r = lint("chore: 로그 정리\n\n왜: 잡음 제거\n무엇: 디버그 로그를 삭제했습니다\n확인: 테스트 통과함\n", "ko")
    assert "ko-tone-mix" in {f["id"] for f in r["findings"]}

    _out("selftest ok — %d rules, %d packs" % (len(ids), len(packs)))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="natc", description="commit messages that read like a human wrote them, in your language")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("lint", help="lint a commit message file, -m string, or stdin")
    q.add_argument("file", nargs="?", default="-")
    q.add_argument("-m", "--message")
    q.add_argument("--lang")
    q.add_argument("--json", action="store_true")
    q.add_argument("--quiet", action="store_true", help="findings only, no why/fix")
    q.set_defaults(fn=cmd_lint)

    q = sub.add_parser("template", help="print the report template")
    q.add_argument("--lang")
    q.add_argument("--pr", action="store_true")
    q.set_defaults(fn=cmd_template)

    q = sub.add_parser("hook", help="install or remove the commit-msg hook")
    q.add_argument("action", choices=["install", "uninstall"])
    q.add_argument("--lang")
    q.add_argument("--cmd", help="command used inside the hook (default: python -m natc)")
    q.set_defaults(fn=cmd_hook)

    q = sub.add_parser("langs", help="list rule packs")
    q.set_defaults(fn=cmd_langs)

    q = sub.add_parser("selftest", help="run the built-in checks")
    q.set_defaults(fn=cmd_selftest)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
