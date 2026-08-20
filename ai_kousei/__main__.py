"""ai-kousei CLI — lint / template / hook / langs / selftest."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

from . import COMMON, __version__, detect_lang, lint, load_packs

HOOK = """#!/bin/sh
# ai-kousei commit-msg hook
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
    # repository can pin its language: git config ai-kousei.lang ja
    r = lint(text, a.lang or _git_config("ai-kousei.lang"),
             profile=a.profile or _git_config("ai-kousei.profile") or "commit")
    if a.json:
        _out(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["passed"] else 1
    if r["lang"] is None:
        _out("ai-kousei: language not detected. English is out of scope on purpose "
             "(use blader/humanizer). Force with --lang ja|ko|zh|de|fr|es.")
        return 0
    # Output shape: the first line is the one thing to do next, then at most five
    # findings ranked by weight. A wall of twenty findings gets closed unread.
    fs = r["findings"]
    if fs:
        _out("next: %s" % (fs[0].get("fix") or fs[0]["title"]))
    _out("%s / %s  score %d/100  errors %d  warnings %d  %s"
         % (r["lang_name"], r["profile_label"], r["score"], r["errors"], r["warns"],
            "[blocked]" if not r["passed"] else "[passes]"))
    if r["maturity"] == "starter":
        _out("  pack maturity: starter — rules are a first pass, contributions welcome")
    cap = len(fs) if (a.all or a.json) else 5
    for i, f in enumerate(fs[:cap], 1):
        tag = "ERROR" if f["severity"] == "error" else "warn "
        loc = ("L%d " % f["line"]) if f.get("line") else ""
        head = "%d. [%s] %s%s" % (i, tag, loc, f["title"])
        if f.get("fix"):
            head += "  → %s" % f["fix"]
        _out(head)
        if f.get("match"):
            _out("     found: %s" % f["match"])
        if not a.quiet and f.get("why"):
            _out("     why:   %s" % f["why"])
        if not a.quiet and f.get("source"):
            _out("     src:   %s" % f["source"])
        _out("     rule:  %s" % f["id"])
    if len(fs) > cap:
        _out("%d more, run with --all" % (len(fs) - cap))
    if not fs:
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


def cmd_rules(a) -> int:
    """Every rule with its citation and its before/after example."""
    packs = load_packs()
    lang = a.lang or "ja"
    if lang not in packs:
        _out("unknown lang: %s" % lang)
        return 2
    p = packs[lang]
    srcs = p.get("sources") or {}
    if srcs:
        _out("sources")
        for k, s in srcs.items():
            _out("  %-16s %s  %s" % (k, s.get("title", ""), s.get("url", "")))
        _out("")
    for r in p.get("rules", []):
        if a.rule and a.rule not in r["id"]:
            continue
        src = r.get("source") or {}
        doc = srcs.get(src.get("doc"), {})
        _out("%s  [%s]" % (r["id"], r.get("severity", "warn")))
        _out("  %s" % r.get("title", ""))
        if src:
            _out("  src:    %s %s" % (doc.get("title", src.get("doc", "")), src.get("loc", "")))
            if src.get("quote"):
                _out("  quote:  %s" % src["quote"])
        exm = r.get("example") or {}
        if exm:
            for tag, key in (("AS-IS", "before"), ("TO-BE", "after")):
                for i, ln in enumerate((exm.get(key) or "").split("\n")):
                    _out("  %-7s %s" % (tag if i == 0 else "", ln))
        _out("")
    return 0


def cmd_metrics(a) -> int:
    """Deterministic signals, next to the two measured corpora."""
    from .metrics import compute
    if a.message is not None:
        text = a.message
    elif a.file and a.file != "-":
        with open(a.file, encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    m = compute(text)
    packs = load_packs()
    base = ((packs.get("ja") or {}).get("sources") or {})
    hum = (base.get("human_commits") or {}).get("measured", {})
    _out("%-24s %8s   %s" % ("signal", "this text", "human commit corpus"))
    pairs = (("polite_rate", "敬体率"), ("passive_rate", "受身率"),
             ("demonstrative_rate", "指示語率"), ("suffix_abstract_rate", "抽象名詞化率"),
             ("nominal_particle_rate", "助詞重ね率"), ("progressive_rate", "進行相率"),
             ("mean_len", "一文平均字数"))
    ref = {"polite_rate": hum.get("敬体率", 1.0) / 100.0, "demonstrative_rate": hum.get("指示語率", 0.021),
           "passive_rate": hum.get("受身率", 0.0), "mean_len": 24.7}
    for k, label in pairs:
        r = ref.get(k)
        _out("%-24s %8s   %s" % (label, m.get(k), ("%s" % r) if r is not None else "-"))
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
        if os.path.exists(path) and any(k in open(path, encoding="utf-8").read() for k in ("ai_kousei", "ai-kousei")):
            os.remove(path)
            _out("removed %s" % path)
        return 0
    cmd = a.cmd or ("%s -m ai_kousei" % os.path.basename(sys.executable).replace(".exe", ""))
    if a.lang:
        subprocess.run(["git", "config", "ai-kousei.lang", a.lang], capture_output=True, timeout=10)
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

    # Japanese: a generated-looking message is caught, with citations attached
    ng_ja = "\n".join([
        "feat: 各種修正しました",
        "",
        "本変更は革命的な改善ではないでしょうか。",
        "- **重要**: ログを整理しました",
    ])
    r = lint(ng_ja, "ja")
    got = {f["id"] for f in r["findings"]}
    assert {"ja-koyo-vague-heading", "ja-ai-hype", "ja-tech-weak-phrase", "ja-ai-bold-list-label"} <= got, got
    assert not r["passed"] and r["score"] < 70, r["score"]
    for f in r["findings"]:
        if f["id"].startswith("ja-") and not f["id"].endswith(("-tone-mix", "-heading-order")):
            assert f.get("source"), "ja rule without citation: %s" % f["id"]

    # Japanese: a report-shaped human message passes
    ok_ja = "\n".join([
        "fix: 決済リトライの上限を3回に変更",
        "",
        "なぜ: リトライが無限に繰り返され、キューが滞留した",
        "なにを: retry_max を3で固定し、超過分は dead-letter へ送る",
        "確認: 負荷試験1時間、キュー滞留 0",
    ])
    r = lint(ok_ja)
    assert r["lang"] == "ja" and r["passed"], (r["lang"], [f["id"] for f in r["findings"]])
    assert r["score"] >= 85, (r["score"], [f["id"] for f in r["findings"]])

    # Japanese: every rule carries a resolvable source and a before/after example
    ja = packs["ja"]
    for rule in ja["rules"]:
        src = rule.get("source")
        assert src and src.get("doc") in ja["sources"], rule["id"]
        assert src.get("loc") and src.get("quote"), rule["id"]
        exm = rule.get("example") or {}
        assert exm.get("before") and exm.get("after"), "no example: %s" % rule["id"]
        # the AS-IS example must actually trip its own rule, under its own profile
        prof = (rule.get("profiles") or ["commit"])[0]
        sub_before = "x: y\n\n" + exm["before"] if rule.get("scope") == "body" else exm["before"]
        hit = {f["id"] for f in lint(sub_before, "ja", profile=prof)["findings"]}
        assert rule["id"] in hit, "example does not trip %s (profile %s)" % (rule["id"], prof)

    # deterministic metrics separate the two measured corpora in the right direction
    from .metrics import compute
    llm_like = compute("feat: キャッシュ追加\n\n商品APIの応答速度向上のため、キャッシュを導入しました。TTL は 300 秒に設定されています。")
    human_like = compute("fix: キャッシュ追加\n\nなぜ: 応答が遅い\nなにを: Redis を前段に追加。TTL 300 秒\n確認: p95 820ms → 210ms")
    assert llm_like["polite_rate"] > human_like["polite_rate"], (llm_like, human_like)

    # profiles: the same sentence is right in one and wrong in another
    notice = "\n".join(["お知らせ: メンテナンス実施", "", "9月1日にサービスを停止する。"])
    assert "ja-customer-plain-form" in {f["id"] for f in lint(notice, "ja", profile="customer")["findings"]}
    assert "ja-customer-plain-form" not in {f["id"] for f in lint(notice, "ja", profile="commit")["findings"]}
    polite = "\n".join(["fix: キャッシュ追加", "", "TTL を 300 秒に設定しました。"])
    assert "ja-koyo-body-polite" in {f["id"] for f in lint(polite, "ja", profile="commit")["findings"]}
    assert "ja-koyo-body-polite" not in {f["id"] for f in lint(polite, "ja", profile="customer")["findings"]}
    vague = "\n".join(["task: 再試行方針", "", "エラー時は適宜リトライする。"])
    assert "ja-agent-vague-term" in {f["id"] for f in lint(vague, "ja", profile="agent")["findings"]}
    assert "ja-agent-vague-term" not in {f["id"] for f in lint(vague, "ja", profile="commit")["findings"]}

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
    p = argparse.ArgumentParser(prog="ai-kousei", description="commit messages that read like a human wrote them, in your language")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("lint", help="lint a commit message file, -m string, or stdin")
    q.add_argument("file", nargs="?", default="-")
    q.add_argument("-m", "--message")
    q.add_argument("--lang")
    q.add_argument("--profile", choices=["commit", "report", "agent", "customer"],
                   help="which rule set applies (default: commit, or git config ai-kousei.profile)")
    q.add_argument("--json", action="store_true")
    q.add_argument("--quiet", action="store_true", help="findings only, no why/source")
    q.add_argument("--all", action="store_true", help="show every finding (default caps at 5)")
    q.set_defaults(fn=cmd_lint)

    q = sub.add_parser("template", help="print the report template")
    q.add_argument("--lang")
    q.add_argument("--pr", action="store_true")
    q.set_defaults(fn=cmd_template)

    q = sub.add_parser("hook", help="install or remove the commit-msg hook")
    q.add_argument("action", choices=["install", "uninstall"])
    q.add_argument("--lang")
    q.add_argument("--cmd", help="command used inside the hook (default: python -m ai_kousei)")
    q.set_defaults(fn=cmd_hook)

    q = sub.add_parser("rules", help="print every rule with its citation and before/after example")
    q.add_argument("--lang")
    q.add_argument("--rule", help="filter by rule id substring")
    q.set_defaults(fn=cmd_rules)

    q = sub.add_parser("metrics", help="deterministic signals for one message")
    q.add_argument("file", nargs="?", default="-")
    q.add_argument("-m", "--message")
    q.set_defaults(fn=cmd_metrics)

    q = sub.add_parser("langs", help="list rule packs")
    q.set_defaults(fn=cmd_langs)

    q = sub.add_parser("selftest", help="run the built-in checks")
    q.set_defaults(fn=cmd_selftest)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
