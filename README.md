# ai-kousei ─ AI校正

![MIT](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/python-3.9%2B-blue) ![Node](https://img.shields.io/badge/node-14%2B-blue) ![deps](https://img.shields.io/badge/dependencies-0-brightgreen) ![no api](https://img.shields.io/badge/API%20calls-none-brightgreen) ![rules](https://img.shields.io/badge/ja%20rules-23%20cited-orange)

**AI に日本語のコミットや報告を書かせると、本文の敬体率が 1.0% から 83.3% に跳ねる。**
ai-kousei は、その差を公的文書の条文を根拠に、ローカルの正規表現だけで止めます。

**日本語** ・ [English](README.en.md) ・ [한국어](README.ko.md)

[デモを開く](https://aidenlee0011.github.io/ai-kousei/) ・ AIが書いた文章の見分け方 / AI 文章 チェック / AI 文章 判定 / 日本語 校正 / コミットメッセージ 日本語

![AS-IS to TO-BE](docs/hero.png)

```bash
npx ai-kousei lint report.md --profile report      # Node
npx ai-kousei hook install --lang ja               # git hook
```

---

## 他の校正ツールと何が違うのか

**1. 指摘に条番号と原文が付く。しかも CI が原文と一字一句照合する。**

規則 23 件はすべて公用文作成の考え方・JTF日本語標準スタイルガイド・textlint-ja のいずれかを引用しています。「なんとなく不自然」ではなく「どの文書の第何項に反するか」が出ます。
CI は毎回、出典 18 件をダウンロードして引用文が原文にあるかを照合し、無ければビルドを落とします。**この検査を最初に走らせたとき、作者が書いた引用 7 件が要約になっていて落ちました。**規則が作文に流れる余地を、仕組みで塞いでいます。

**2. 用途によって規則が反転する。**

同じ「です・ます体」が、記録では誤りで、対顧客では必須です。用途を推測せず `--profile` で明示します。

```
--profile commit    「導入しました」 → ERROR   記録は常体・体言止め（公用文 Ⅲ-1-ア）
--profile customer  「停止する。」   → ERROR   通知は敬体（同 Ⅲ-1-ア）
--profile agent     「適宜リトライ」 → ERROR   機械が実行できない（同 Ⅲ-3-シ）
```

**3. 人が書いた文章は素通りする。実測している。**

| 検査対象（すべて人が書いた文章） | プロファイル | error 発火 |
|---|---|---:|
| コミット 96 件（2022-11 以前 = LLM 普及前） | commit | **2.1%** |
| 公開報告書の本文 400 ブロック（JPCERT/CC） | report | **2.2%** |
| LLM が書いたコミット 30 件 | commit | **86.7%** |

**4. モデル呼び出しなし・ネットワークなし・依存ゼロ。** 規則ロードに 4ms、1 メッセージの判定に 0.24ms。フックが API キーを要求しないので、外されません。

---

## 近いツールとの違い

| ツール | 対象 | ai-kousei との違い |
|---|---|---|
| [textlint-rule-preset-ai-writing](https://github.com/textlint-ja/textlint-rule-preset-ai-writing) 1,095★ | 散文の AI パターン | 出典は自前の判断基準。ai-kousei は条番号を提示し、CI が原文照合する |
| [textlint-rule-preset-JTF-style](https://github.com/textlint-ja/textlint-rule-preset-JTF-style) 218★ | JTF 表記規則 | **JTF 2.1/2.2 版ベース**。ai-kousei は **4.0 版（2026-07-25, CC BY 4.0）** を引用 |
| [patina](https://github.com/devswha/patina) 316★ | KO/EN/ZH/JA の humanize・書き換え | 書き換えまで行う。ai-kousei は**書き換えず**指摘と条文だけ出す。用途別に規則が反転する設計は無い |
| [humanizer-ja](https://github.com/gonta223/humanizer-ja) 123★ | 日本語 AI 文体 20 パターン | Claude Code スキル。ai-kousei は CLI とフック、根拠提示、誤検出の実測値を持つ |

「最初」でも「唯一」でもありません。**根拠が条番号でたどれること、用途で規則が反転すること、誤検出率を測って公開していること**が違いです。

---

## エージェント間の受け渡しで効く例

```
AS-IS  エラー時は適宜リトライし、必要に応じて通知する。
       確認しました。対応済み。

TO-BE  エラー時は最大3回・10秒間隔でリトライする。
       3回失敗したら Slack #ops へ通知する。
```

「適宜」「必要に応じて」「対応済み」は、人間なら補完できますが受け手が機械だと実行できません。
根拠は公用文作成の考え方 Ⅲ-3-シ「言葉の係り方によって複数の意味に取れることがないようにする」と Ⅲ-3-オ「主語と述語の関係が分かるようにする」です。

![profiles](docs/profiles.png)

| プロファイル | 対象 | 主な検査 |
|---|---|---|
| `commit` | コミット・PR（記録） | 常体・体言止め、件名で内容がつかめるか、なぜ/なにを/確認 |
| `report` | 社内報告書 | 見出し階層（第1 → 1 → （1） → ア）、文体の統一、誇張と冗長 |
| `agent` | エージェント間の受け渡し | 曖昧語の禁止、動作主の明示 |
| `customer` | 対顧客の文面 | 敬体の強制、社内用語の言い換え |

---

## 出力

```
$ git commit -m "feat: 各種修正"
next: 対象と結果を書く。「決済リトライの上限を3回に変更」
日本語 / コミット・PR（記録）  score 88/100  errors 1  warnings 0  [blocked]
1. [ERROR] 件名だけでは内容がつかめない
     found: feat: 各種修正
     src:   公用文作成の考え方（文化審議会建議） Ⅲ-2-エ 文書の構成
     rule:  ja-koyo-vague-heading
```

1 行目が次にやること。指摘は重み順に 5 件まで（全件は `--all`）。error があると exit 1、warning は表示のみ。merge・squash・fixup は対象外です。

---

## 出典

| 出典 | 発行 | 使っている箇所 |
|---|---|---|
| [公用文作成の考え方（文化審議会建議）](https://www.bunka.go.jp/seisaku/bunkashingikai/kokugo/hokoku/pdf/93651301_01.pdf) | 文化審議会・2022-01-07 | 文体の選択、一文の長さ、受身、二重否定、同じ助詞の連続、項目の階層、用語の言い換え |
| [JTF日本語標準スタイルガイド（翻訳用）](https://www.jtf.jp/pdf/jtf_style_guide.pdf) | 日本翻訳連盟 | 見出しは常体または体言止め、和文の句読点、半角カタカナ |
| [textlint-rule-preset-ja-technical-writing](https://github.com/textlint-ja/textlint-rule-preset-ja-technical-writing) ・ [preset-ai-writing](https://github.com/textlint-ja/textlint-rule-preset-ai-writing) | textlint-ja | 弱い表現、冗長表現、読点の数、漢字の連続、誇張、太字ラベル |
| 公開報告書コーパス（JPCERT/CC 活動報告 8 件・8,181 文） | 実測 | 報告書テンプレートの文末（体言止め 44.7%・敬体 20.6%・常体 1.6%） |

![architecture](docs/architecture.png)

規則は JSON です。Python CLI・Node CLI・ブラウザデモが同じファイルと同じ判定エンジンを読むため、デモで試した結果とフックの判定はずれません。

```json
{
  "id": "ja-customer-plain-form",
  "severity": "error",
  "profiles": ["customer"],
  "pattern": "(?:である|だ|した|する|ない)。",
  "title": "対顧客の文面が常体",
  "fix": "敬体に直す。「変更した。」→「変更しました。」",
  "example": { "before": "9月1日にサービスを停止する。", "after": "9月1日にサービスを停止します。" },
  "source": { "doc": "koyobun", "loc": "Ⅲ-1-ア 文体の選択",
              "quote": "通知、依頼、照会、回答など、特定の相手を対象とした文書では敬体（です・ます体）を用いる。" }
}
```

`source` のない規則は受け付けません。selftest が出典の解決と、AS-IS 例が実際にその規則を発火させることを検査します。

---

## コマンド

```bash
ai-kousei lint .git/COMMIT_EDITMSG            # ファイル
ai-kousei lint -m "fix: 各種修正"              # 文字列
git log -1 --format=%B | ai-kousei lint       # 標準入力
ai-kousei lint report.md --profile report --json
ai-kousei rules --lang ja                     # 全規則 + 出典 + AS-IS/TO-BE
ai-kousei metrics -m "..."                    # 定量指標をコーパス実測値と並べる
ai-kousei template --lang ja                  # コミット / PR / 報告書テンプレート
python -m ai-kousei selftest                  # 77 規則 / 7 パック
python bench/run.py --lang ja --rules      # 実測の再現
```

## 対応言語と限界

日本語が主対象です。韓国語・中国語・ドイツ語・フランス語・スペイン語は初期版の規則のみで、出典の整備はこれから。英語は対象外です（既存ツールが充実しているため）。
規則は 23 件で textlint 系の網羅性には及びません。形態素解析を使わないため文脈依存の判定は苦手です。

## 貢献

日本語の規則追加には `source`（文書名・条番号・引用）と `example`（AS-IS / TO-BE）が必須です。他言語は `ai_kousei/rules/<code>.json` を追加し、その言語の公的文書・業界標準を出典にしてください。`python -m ai-kousei selftest` が通ること。

MIT License。出典は条番号と短い引用のみを掲載し、原文の再配布は行っていません。
