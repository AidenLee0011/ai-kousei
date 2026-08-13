# buntai 文体

![MIT](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/python-3.9%2B-blue) ![Node](https://img.shields.io/badge/node-14%2B-blue) ![deps](https://img.shields.io/badge/dependencies-0-brightgreen) ![no api](https://img.shields.io/badge/API%20calls-none-brightgreen) ![rules](https://img.shields.io/badge/ja%20rules-23%20cited-orange)

**Ask an LLM for a Japanese commit message and the polite-form rate in the body jumps from 1.0% to 83.3%.**
buntai catches that with local regular expressions, and every rule points at a clause in a Japanese public standard.

[日本語](README.md) ・ **English** ・ [한국어](README.ko.md)

[Open the demo](https://aidenlee0011.github.io/buntai/) ・ japanese writing linter / japanese proofreading / AI writing detection / commit message lint / no Node required

![AS-IS to TO-BE](docs/hero.png)

```bash
pip install buntai-lint && buntai hook install --lang ja     # Python
npx buntai-lint lint report.md --profile report              # Node
```

---

## What is actually different

**1. Findings carry a clause number and the quoted line, and CI checks the quotes verbatim.**

All 23 Japanese rules cite one of: the Council for Cultural Affairs guidance on public documents (公用文作成の考え方, 2022), the Japan Translation Federation style guide (JTF 4.0, CC BY 4.0), or the textlint-ja presets. You do not get "this feels unnatural", you get which clause of which document the text breaks.
On every push, CI downloads the 18 cited documents and fails the build when a quoted line is not in the original. **The first run of that check failed on 7 of the author's own quotes**, which had drifted into paraphrase. Rules cannot quietly become invention.

**2. The rules invert by use.**

Polite form is an error in a commit record and required in a customer notice, so the use is declared rather than guessed.

```
--profile commit    "導入しました" -> ERROR   records use plain form (公用文 Ⅲ-1-ア)
--profile customer  "停止する。"   -> ERROR   notices use polite form (same clause)
--profile agent     "適宜リトライ" -> ERROR   a machine cannot act on "as appropriate" (Ⅲ-3-シ)
```

**3. Human writing passes, and that is measured.**

| corpus, all written by people | profile | error rate |
|---|---|---:|
| 96 commits authored before 2022-11 (pre chat LLM) | commit | **2.1%** |
| 400 blocks from published reports (JPCERT/CC) | report | **2.2%** |
| 30 commits written by an LLM | commit | **86.7%** |

**4. No model call, no network, no dependencies.** Rules load in 4 ms, a message lints in 0.24 ms. A hook that needs an API key gets uninstalled.

---

## How it differs from nearby tools

Not the first and not the only one. Japanese AI-writing tools already exist.

| tool | scope | difference |
|---|---|---|
| [textlint-rule-preset-ai-writing](https://github.com/textlint-ja/textlint-rule-preset-ai-writing) 1,095★ | AI patterns in prose | buntai prints the clause and CI verifies the quote |
| [textlint-rule-preset-JTF-style](https://github.com/textlint-ja/textlint-rule-preset-JTF-style) 218★ | JTF notation rules | that preset tracks JTF 2.1/2.2; buntai cites **4.0 (2026-07-25, CC BY 4.0)** |
| [patina](https://github.com/devswha/patina) 316★ | KO/EN/ZH/JA humanizer, has a commit-message document type | patina rewrites; buntai **never rewrites**, it reports and cites. No profile inversion there |
| [humanizer-ja](https://github.com/gonta223/humanizer-ja) 123★ | 20 Japanese AI-writing patterns | a Claude Code skill; buntai is a CLI and a hook with published false-positive rates |

The three differences are: **traceable clause-level sources**, **rules that invert by use**, and **a measured, published false-positive rate**.

---

## Where it earns its place: agent handoffs

```
AS-IS  エラー時は適宜リトライし、必要に応じて通知する。
       確認しました。対応済み。

TO-BE  エラー時は最大3回・10秒間隔でリトライする。
       3回失敗したら Slack #ops へ通知する。
```

"As appropriate", "as needed" and "handled" are things a human reader fills in and a machine cannot. The basis is 公用文作成の考え方 Ⅲ-3-シ (no sentence should allow two readings) and Ⅲ-3-オ (the subject and predicate relation must be visible).

![profiles](docs/profiles.png)

| profile | target | checks |
|---|---|---|
| `commit` | commits and pull requests | plain form, informative subject, why / what / verified |
| `report` | internal reports | heading hierarchy (第1 → 1 → （1） → ア), one sentence style, no hype |
| `agent` | machine-to-machine handoff | no vague terms, explicit actor, numeric conditions |
| `customer` | customer-facing text | polite form required, internal jargon rewritten |

---

## Output

```
$ git commit -m "feat: 各種修正"
next: 対象と結果を書く。「決済リトライの上限を3回に変更」
日本語 / コミット・PR（記録）  score 88/100  errors 1  warnings 0  [blocked]
1. [ERROR] 件名だけでは内容がつかめない
     found: feat: 各種修正
     src:   公用文作成の考え方（文化審議会建議） Ⅲ-2-エ 文書の構成
     rule:  ja-koyo-vague-heading
```

The first line is the single next action. Findings are ranked and capped at five (`--all` for everything). Error exits 1, warnings print and pass. Merge, squash and fixup messages are skipped.

## Sources

| source | publisher | used for |
|---|---|---|
| [公用文作成の考え方](https://www.bunka.go.jp/seisaku/bunkashingikai/kokugo/hokoku/pdf/93651301_01.pdf) | Council for Cultural Affairs, 2022-01-07 | sentence style, sentence length, passive voice, double negatives, repeated particles, heading hierarchy, term rewriting |
| [JTF Japanese Style Guide 4.0](https://www.jtf.jp/pdf/jtf_style_guide.pdf) | Japan Translation Federation, CC BY 4.0 | headings in plain form or noun ending, Japanese punctuation, half-width kana |
| [textlint-ja presets](https://github.com/textlint-ja/textlint-rule-preset-ja-technical-writing) | textlint-ja, MIT | weak phrasing, redundancy, comma count, ideograph runs, hype, bold labels |
| Public report corpus (8 JPCERT/CC reports, 8,181 sentences) | measured | report template endings: noun ending 44.7%, polite 20.6%, plain 1.6% |

![architecture](docs/architecture.png)

Rules are JSON. The Python CLI, the Node CLI and the browser demo read the same files through the same engine, so the demo cannot drift away from what the hook enforces. A rule without `source` is rejected by the selftest, which also checks that each before-example actually trips its own rule.

## Commands

```bash
buntai lint .git/COMMIT_EDITMSG            # file
buntai lint -m "fix: 各種修正"              # string
git log -1 --format=%B | buntai lint       # stdin
buntai lint report.md --profile report --json
buntai rules --lang ja                     # rules with citations and before/after
buntai metrics -m "..."                    # deterministic signals vs the corpus
buntai template --lang ja                  # commit / PR / report templates
python -m buntai selftest                  # 77 rules / 7 packs
python bench/run.py --lang ja --rules      # reproduce the measurements
```

## Coverage and limits

Japanese is the sourced pack. Korean, Chinese, German, French and Spanish ship starter rules whose citations are not yet in place. English is out of scope on purpose.
There are 23 Japanese rules, far short of the textlint ecosystem's coverage, and no morphological analysis, so context-dependent judgements are weak.

## Contributing

A Japanese rule needs `source` (document, clause, quote) and `example` (before, after). A new language goes in `buntai/rules/<code>.json`, sourced from that language's public standards rather than intuition. `python -m buntai selftest` must pass.

MIT License. Sources are cited by clause with short quotations; no source document is redistributed.
