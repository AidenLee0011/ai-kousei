# nativecommit

![MIT](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/python-3.9%2B-blue) ![deps](https://img.shields.io/badge/dependencies-0-brightgreen) ![rules](https://img.shields.io/badge/ja%20rules-19%20sourced-orange)

**日本語のコミット・PR・報告文を、公的文書の条文を根拠に直すリンター。**
A deterministic linter that holds Japanese commit messages, pull requests and reports to the standards published by Japanese public bodies.

モデル呼び出しなし・ネットワークなし・依存パッケージなし ・ デモ: <http://118.130.18.231:8500/nativecommit/>

![AS-IS to TO-BE](docs/hero.png)

```bash
pip install nativecommit
natc hook install --lang ja     # これだけ。次のコミットから効く
```

---

## なぜ効くのか（実測）

AI が書いた日本語のコミット本文は、ほぼ必ず「です・ます体の説明文」になる。日本語話者が書くコミットは常体か体言止めの記録である。感覚ではなく数えられる差である。

![benchmark](docs/bench.png)

| 指標 | 人手コミット（2022-11 以前・96 件） | LLM 生成（30 件） |
|---|---:|---:|
| 本文が敬体 | 1.0% | **83.3%** |
| 文体（常体・敬体）の混在 | 1.0% | 80.0% |
| 一文 60 字超 | 2.1% | 33.3% |
| 受身形の多用 | 0.0% | 13.3% |
| **コミット拒否（error 発火）** | **2.1%** | **86.7%** |

人手側は LLM が普及する前（2022 年 11 月以前）のコミットだけを集めているため、ここでの発火は誤検出として数える。再現手順は [`bench/`](bench/)。

```bash
python bench/run.py --lang ja --rules
```

---

## 強み: 規則に出典がある

**すべての規則が、日本語の公的文書または実測コーパスに紐づく。** 作者の感覚で作った規則は 1 件も入っていない。出典を示せない信号は規則にせず、指標として出すだけにとどめている。

| 出典 | 発行 | 使っている箇所 |
|---|---|---|
| [公用文作成の考え方（文化審議会建議）](https://www.bunka.go.jp/seisaku/bunkashingikai/kokugo/hokoku/pdf/93651301_01.pdf) | 文化審議会・2022-01-07 | 文体の選択、一文の長さ、受身、二重否定、同じ助詞の連続、項目の階層 |
| [JTF日本語標準スタイルガイド（翻訳用）](https://www.jtf.jp/pdf/jtf_style_guide.pdf) | 日本翻訳連盟 | 見出しは常体または体言止め、和文の句読点、半角カタカナ |
| [textlint-rule-preset-ja-technical-writing](https://github.com/textlint-ja/textlint-rule-preset-ja-technical-writing) | textlint-ja | 弱い表現、冗長表現、読点の数、漢字の連続 |
| [textlint-rule-preset-ai-writing](https://github.com/textlint-ja/textlint-rule-preset-ai-writing) | textlint-ja | 誇張表現、太字ラベルの箇条書き、コロン継続 |
| 公開報告書コーパス（JPCERT/CC 活動報告 8 件・8,181 文） | 実測 | 報告書テンプレートの文末（体言止め 44.7%・敬体 20.6%・常体 1.6%） |

指摘には必ず条番号と原文引用が付く。

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

## しくみ

![architecture](docs/architecture.png)

規則は JSON である。CLI とブラウザデモが同じファイルを読むため、デモで試した結果とフックの判定はずれない。

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

`source` のない規則は受け付けない。selftest が全規則について出典の解決と、AS-IS 例が実際にその規則を発火させることを検査する。

---

## AS-IS → TO-BE

指摘だけでは書き直せない。全規則に書き換え例を同梱している（`natc rules --lang ja`）。

| | AS-IS | TO-BE |
|---|---|---|
| 件名 | `fix: 各種修正` / `feat: …を変更しました` | `fix: 決済リトライの上限を3回に変更` |
| 本文 | Redis キャッシュを導入しました。TTL は 300 秒に設定されています。 | なぜ: 応答が遅い / なにを: Redis を前段に追加。TTL 300 秒 / 確認: p95 820ms → 210ms |
| 箇条書き | `- **重要**: TTL を 300 秒に設定` / `- ✅ キャッシュ追加` | `- TTL: 300 秒` / `- キャッシュ追加` |
| 効果 | 革命的なキャッシュ導入により、すべての課題を解決します。 | p95 応答が 820ms から 210ms に短縮。 |
| 推量 | これで解決したと思います。 | 再現手順 3 件で再現しないことを確認。 |

---

## 使い方

```bash
natc lint .git/COMMIT_EDITMSG      # ファイル
natc lint -m "fix: 各種修正"        # 文字列
git log -1 --format=%B | natc lint # 標準入力
natc lint -m "..." --json          # 機械可読
natc rules --lang ja               # 全規則 + 出典 + AS-IS/TO-BE
natc metrics -m "..."              # 定量指標をコーパス実測値と並べる
natc template --lang ja            # コミット / PR / 報告書テンプレート
python -m natc selftest            # 73 規則 / 7 パック
```

error があると exit 1、warning は表示のみ。merge・squash・fixup は対象外。出力は既定 5 件まで、1 行目が次にやること、全件は `--all`。

## 報告書テンプレート

項目の階層は公用文作成の考え方 Ⅱ-6-ウ の順序（第1 → 1 → （1） → ア → （ア））に従う。文末は公開報告書の実測分布に合わせ体言止めを既定とする。

```
件名: {内容}について（報告）

1 概要      {結論を1文・体言止め}
2 背景      {なぜ着手したか}
3 対応      (1) {実施事項} (2) {実施事項}
4 結果      {実測値。数値を必ず入れる}
5 今後の対応 {次の一手を1件}

以上
```

## 対応言語

日本語（出典付き・実測済み）が主対象。韓国語・中国語・ドイツ語・フランス語・スペイン語は初期版の規則のみで、出典整備はこれから。**英語は対象外**とし、既存ツールに委ねている。

## 貢献

1. 日本語の規則追加には `source`（文書名・条番号・引用）と `example`（AS-IS / TO-BE）が必須。
2. 他言語は `natc/rules/<code>.json` を追加し、その言語の公的文書・業界標準を出典にする。
3. `python -m natc selftest` が通ること。

## ライセンス

MIT。出典は条番号と短い引用のみを掲載し、原文の再配布は行っていない。

<br>

---

<br>

# English

**A deterministic linter for Japanese commit messages, pull requests and reports, where every rule cites a Japanese public standard.**

No model call. No network. No dependencies. English is deliberately out of scope.

```bash
pip install nativecommit
natc hook install --lang ja
```

## Why it works

A Japanese commit body written by an LLM is almost always polite-form prose (です・ます体). A Japanese engineer writes a terse record in 常体 or 体言止め. The gap is measurable.

| signal | human commits, before 2022-11 (n=96) | LLM written (n=30) |
|---|---:|---:|
| polite form in the body | 1.0% | **83.3%** |
| mixed sentence endings | 1.0% | 80.0% |
| sentence over 60 characters | 2.1% | 33.3% |
| passive voice overuse | 0.0% | 13.3% |
| **commit rejected (error level)** | **2.1%** | **86.7%** |

The human half predates widespread chat LLMs, so any finding there counts as a false positive. Reproduce with `python bench/run.py --lang ja --rules`.

## What makes it different

Every rule maps to a Japanese public standard or to a measured corpus: the Council for Cultural Affairs guidance on public documents (2022), the Japan Translation Federation style guide, the textlint-ja presets, and two corpora measured for this repository. A rule without a citation is rejected by the selftest, and each finding prints the clause number and the quoted line.

Findings are actionable by construction: every rule ships a before/after rewrite, the CLI leads with the single next action, and output stops at five items.

## Commands

```bash
natc lint .git/COMMIT_EDITMSG      # file
natc lint -m "fix: 各種修正"        # string
git log -1 --format=%B | natc lint # stdin
natc lint -m "..." --json          # machine readable
natc rules --lang ja               # rules with citations and before/after
natc metrics -m "..."              # deterministic signals vs the corpus values
natc template --lang ja            # commit / PR / report templates
python -m natc selftest            # 73 rules / 7 packs
```

## Contributing

A Japanese rule needs `source` (document, clause, quote) and `example` (before, after). A new language goes in `natc/rules/<code>.json`, sourced from that language's public standards, not from intuition. `python -m natc selftest` must pass.

## License

MIT. Sources are cited by clause with short quotations; no source document is redistributed.
