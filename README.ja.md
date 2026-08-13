# nativecommit

日本語のコミットメッセージ・PR・報告文を、**公的文書の基準**に沿った書き方へ直すための決定論リンターです。

モデル呼び出しなし。ネットワークなし。依存パッケージなし。

[English](README.md) ・ デモ: <http://118.130.18.231:8500/nativecommit/>

---

## 何を解く道具か

AI が生成した日本語のコミット本文は、ほぼ必ず「です・ます体の説明文」になります。日本語話者が実際に書くコミットは、常体か体言止めの記録です。この差は感覚ではなく実測できます。

| 指標 | 人手コミット（2022-11 以前・96 件） | LLM 生成（30 件） |
|---|---:|---:|
| 本文が敬体 | 1.0% | 83.3% |
| 文体（常体・敬体）の混在 | 1.0% | 80.0% |
| 一文 60 字超 | 2.1% | 33.3% |
| 受身形の多用 | 0.0% | 13.3% |
| コミット拒否（error 発火） | **2.1%** | **86.7%** |

計測手順は [`bench/`](bench/) にあります。人手側は LLM が一般化する前（2022 年 11 月以前）のコミットだけを GitHub から収集しているため、発火は誤検出として数えられます。

---

## 強み: 規則に出典がある

**すべての規則が、日本語の公的文書または実測コーパスに紐づいています。** 作者の感覚で作った規則は 1 件も入っていません。出典を提示できない規則は、規則にせず指標に留めています。

| 出典 | 発行 | 使っている箇所 |
|---|---|---|
| [公用文作成の考え方（文化審議会建議）](https://www.bunka.go.jp/seisaku/bunkashingikai/kokugo/hokoku/pdf/93651301_01.pdf) | 文化審議会・2022-01-07 | 文体の選択、一文の長さ、受身、二重否定、同じ助詞の連続、項目の階層 |
| [JTF日本語標準スタイルガイド（翻訳用）](https://www.jtf.jp/pdf/jtf_style_guide.pdf) | 日本翻訳連盟 | 見出しは常体または体言止め、和文の句読点、半角カタカナ |
| [textlint-rule-preset-ja-technical-writing](https://github.com/textlint-ja/textlint-rule-preset-ja-technical-writing) | textlint-ja | 弱い表現、冗長表現、読点の数、漢字の連続 |
| [textlint-rule-preset-ai-writing](https://github.com/textlint-ja/textlint-rule-preset-ai-writing) | textlint-ja | 誇張表現、太字ラベルの箇条書き、コロン継続 |
| 公開報告書コーパス（JPCERT/CC 活動報告 8 件・8,181 文） | 実測 | 報告書テンプレートの文末（体言止め 44.7%・敬体 20.6%・常体 1.6%） |

指摘には必ず条番号と原文引用が付きます。

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

## AS-IS → TO-BE

指摘だけでは書き直せません。全規則に対応する書き換え例を同梱しています（`natc rules --lang ja`）。

**コミット本文**

| | |
|---|---|
| AS-IS | 商品詳細 API の応答速度向上とデータベース負荷軽減のため、Redis キャッシュを導入しました。キャッシュの有効期限（TTL）は 300 秒に設定されています。 |
| TO-BE | なぜ: 商品詳細 API の応答が遅い<br>なにを: Redis キャッシュを前段に追加。TTL 300 秒<br>確認: p95 820ms → 210ms |

**件名**

| | |
|---|---|
| AS-IS | `fix: 各種修正` / `feat: 決済リトライの上限を3回に変更しました` |
| TO-BE | `fix: 決済リトライの上限を3回に変更` |

**箇条書き**

| | |
|---|---|
| AS-IS | `- **重要**: TTL を 300 秒に設定` / `- ✅ キャッシュ追加` |
| TO-BE | `- TTL: 300 秒` / `- キャッシュ追加` |

**効果の書き方**

| | |
|---|---|
| AS-IS | 革命的なキャッシュ導入により、すべての課題を解決します。 |
| TO-BE | キャッシュ導入により p95 応答が 820ms から 210ms に短縮。 |

---

## 導入

```bash
pip install nativecommit
natc hook install --lang ja      # .git/hooks/commit-msg を書き、git config natc.lang ja を設定
```

以後、生成文らしいコミットはコミット前に止まります。error があると exit 1、warning は表示のみです。merge・squash・fixup は対象外です。

```bash
natc lint .git/COMMIT_EDITMSG      # ファイル
natc lint -m "fix: 各種修正"        # 文字列
git log -1 --format=%B | natc lint # 標準入力
natc lint -m "..." --json          # 機械可読
natc rules --lang ja               # 全規則 + 出典 + AS-IS/TO-BE
natc metrics -m "..."              # 定量指標をコーパス実測値と並べる
natc template --lang ja            # コミット / PR / 報告書テンプレート
```

出力は既定で 5 件までです。最初の 1 行が次にやること、以降は重み順に並びます。全件は `--all`。

---

## 報告書テンプレート

項目の階層は公用文作成の考え方 Ⅱ-6-ウ の順序（第1 → 1 → （1） → ア → （ア））に従います。文末は公開報告書の実測分布（体言止め 44.7%）に合わせ、体言止めを既定にしています。

```
件名: {内容}について（報告）

1 概要
 {結論を1文・体言止め}

2 背景
 {なぜ着手したか}

3 対応
 (1) {実施事項}
 (2) {実施事項}

4 結果
 {実測値。数値を必ず入れる}

5 今後の対応
 {次の一手を1件}

以上
```

---

## 規則の形

規則は JSON です。CLI とブラウザデモが同じファイルを読むため、デモで試した結果とフックの判定はずれません。

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

`source` のない規則は受け付けません。selftest が全規則について出典の解決と、AS-IS 例が実際にその規則を発火させることを検査します。

```bash
python -m natc selftest      # 73 規則 / 7 パック
python bench/run.py --lang ja --rules
```

---

## 対応言語

日本語（出典付き・実測済み）が主対象です。韓国語・中国語・ドイツ語・フランス語・スペイン語は初期版の規則のみで、出典整備はこれからです。**英語は対象外**とし、既存ツールに委ねています。

## 貢献

1. `natc/rules/ja.json` に規則を追加する場合、`source`（文書名・条番号・引用）と `example`（AS-IS / TO-BE）が必須です。
2. 他言語は `natc/rules/<code>.json` を追加し、その言語の公的文書・業界標準を出典にしてください。
3. `python -m natc selftest` が通ることを確認してください。

## ライセンス

MIT。引用は各出典の条番号と短い引用に限っており、原文の再配布は行っていません。
