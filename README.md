# nativecommit

A deterministic linter that holds Japanese commit messages, pull requests and reports
to the **standards published by Japanese public bodies**.

No model call. No network. No dependencies.

[日本語版 README](README.ja.md) ・ Demo: <http://118.130.18.231:8500/nativecommit/>

---

## The problem, measured

A Japanese commit body written by an LLM is almost always polite-form prose
(です・ます体). A Japanese engineer writes a terse record in 常体 or 体言止め.
That gap is measurable, and it is what this tool acts on.

| signal | human commits, before 2022-11 (n=96) | LLM written (n=30) |
|---|---:|---:|
| polite form in the body | 1.0% | 83.3% |
| mixed sentence endings | 1.0% | 80.0% |
| sentence over 60 characters | 2.1% | 33.3% |
| passive voice overuse | 0.0% | 13.3% |
| **commit rejected (error level)** | **2.1%** | **86.7%** |

The human half is collected from commits authored before chat LLMs were widespread, so
any finding there counts as a false positive. Reproduce with [`bench/`](bench/).

---

## What makes it different: every rule cites a source

**Each rule maps to a Japanese public standard or to a measured corpus.** None of them
come from the author's taste. When a signal has no citable source, it stays a metric and
never becomes a blocking rule.

| source | publisher | used for |
|---|---|---|
| [公用文作成の考え方 (Cabinet-level guidance on public documents)](https://www.bunka.go.jp/seisaku/bunkashingikai/kokugo/hokoku/pdf/93651301_01.pdf) | Council for Cultural Affairs, 2022-01-07 | sentence style, sentence length, passive voice, double negatives, repeated particles, heading hierarchy |
| [JTF Japanese Style Guide for translation](https://www.jtf.jp/pdf/jtf_style_guide.pdf) | Japan Translation Federation | headings in 常体 or 体言止め, Japanese punctuation, half-width kana |
| [textlint-rule-preset-ja-technical-writing](https://github.com/textlint-ja/textlint-rule-preset-ja-technical-writing) | textlint-ja | weak phrasing, redundancy, comma count, ideograph runs |
| [textlint-rule-preset-ai-writing](https://github.com/textlint-ja/textlint-rule-preset-ai-writing) | textlint-ja | hype wording, bold list labels, colon continuation |
| Public report corpus (8 JPCERT/CC activity reports, 8,181 sentences) | measured | report template endings: 体言止め 44.7%, polite 20.6%, plain 1.6% |

Every finding prints the clause number and the quoted line it comes from.

```
$ natc lint --lang ja
next: 常体か体言止めに直す。「導入しました」→「導入した」または「導入」
日本語  score 75/100  errors 1  warnings 2  [commit blocked]
1. [ERROR] L2 本文が敬体（です・ます体）  → 常体か体言止めに直す
     found: しました。
     src:   公用文作成の考え方（文化審議会建議） Ⅲ-1-ア 文体の選択
     rule:  ja-koyo-body-polite
```

---

## Before and after

A finding you cannot act on is noise, so every rule ships a rewrite example
(`natc rules --lang ja`).

**Commit body**

| | |
|---|---|
| before | 商品詳細 API の応答速度向上とデータベース負荷軽減のため、Redis キャッシュを導入しました。キャッシュの有効期限（TTL）は 300 秒に設定されています。 |
| after | なぜ: 商品詳細 API の応答が遅い<br>なにを: Redis キャッシュを前段に追加。TTL 300 秒<br>確認: p95 820ms → 210ms |

**Subject**

| | |
|---|---|
| before | `fix: 各種修正` / `feat: 決済リトライの上限を3回に変更しました` |
| after | `fix: 決済リトライの上限を3回に変更` |

**Lists**

| | |
|---|---|
| before | `- **重要**: TTL を 300 秒に設定` / `- ✅ キャッシュ追加` |
| after | `- TTL: 300 秒` / `- キャッシュ追加` |

**Claims about impact**

| | |
|---|---|
| before | 革命的なキャッシュ導入により、すべての課題を解決します。 |
| after | キャッシュ導入により p95 応答が 820ms から 210ms に短縮。 |

---

## Install

```bash
pip install nativecommit
natc hook install --lang ja      # writes .git/hooks/commit-msg, sets git config natc.lang
```

The next generated-looking commit stops before it lands. Error level exits 1, warnings
print and pass. Merge, squash and fixup messages are skipped.

```bash
natc lint .git/COMMIT_EDITMSG      # file
natc lint -m "fix: 各種修正"        # string
git log -1 --format=%B | natc lint # stdin
natc lint -m "..." --json          # machine readable
natc rules --lang ja               # all rules with citations and before/after
natc metrics -m "..."              # deterministic signals next to the corpus values
natc template --lang ja            # commit / PR / report templates
```

Output stops at five findings. The first line is the next action, the rest are ranked by
weight. `--all` prints everything.

---

## Report template

The hierarchy follows 公用文作成の考え方 Ⅱ-6-ウ (第1 → 1 → （1） → ア → （ア）), and the
default sentence ending follows the measured distribution of published reports.

```
件名: {内容}について（報告）

1 概要 / 2 背景 / 3 対応 / 4 結果 / 5 今後の対応

以上
```

---

## Rule format

Rules are JSON. The CLI and the browser demo read the same files, so the demo cannot
drift away from what the hook enforces.

```json
{
  "id": "ja-jtf-heading-desumasu",
  "severity": "error",
  "scope": "subject",
  "pattern": "(?:です|ます|ました|ません|でした)[。\\s]*$",
  "title": "件名が敬体で終わっている",
  "fix": "体言止めにする",
  "example": { "before": "feat: …を変更しました", "after": "feat: …を変更" },
  "source": { "doc": "jtf", "loc": "1.1.2 見出し（p.10）", "quote": "常体または体言止め。" }
}
```

A rule without `source` is rejected. The selftest checks that every citation resolves and
that each before-example actually trips its own rule.

```bash
python -m natc selftest            # 73 rules / 7 packs
python bench/run.py --lang ja --rules
```

---

## Language coverage

Japanese is the sourced, measured pack. Korean, Chinese, German, French and Spanish ship
starter rules and still need their own citations. **English is out of scope**; that side is
already well served, and covering it would blur the point.

## Contributing

1. A new Japanese rule needs `source` (document, clause, quote) and `example` (before, after).
2. A new language goes in `natc/rules/<code>.json`, sourced from that language's public
   standards, not from intuition.
3. `python -m natc selftest` must pass.

## License

MIT. Sources are cited by clause with short quotations; no source document is redistributed.
