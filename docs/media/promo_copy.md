# ai-kousei 配信用コピー / promo copy

素材: `ai-kousei-demo-shorts-1080x1920.mp4`（縦・Shorts/Reels/TikTok）、`ai-kousei-demo-square.mp4`（X・LinkedIn）、`ai-kousei-demo.gif`（README・Reddit）
リンク: https://github.com/AidenLee0011/ai-kousei ・ https://aidenlee0011.github.io/ai-kousei/

数字はすべて実測。誇張表現と絵文字は使わない。

---

## X / Twitter（日本語・本命）

```
AIに日本語のコミットを書かせると、本文の敬体率が 1.0% から 83.3% に跳ねる。
人が書いた記録は常体か体言止めで、これは公用文作成の考え方 Ⅲ-1-ア に書いてある。

その差を条文を根拠に止めるリンターを作った。依存ゼロ、モデル呼び出しなし。

https://github.com/AidenLee0011/ai-kousei
```

スレッド 2 本目

```
指摘には条番号と原文引用が付く。CIが毎回18件の原典をダウンロードして一字一句照合する。
最初に走らせたとき、自分が書いた引用7件が要約になっていて落ちた。

誤検出は人手コミット2.1%、公開報告書2.2%。数字は bench/ で再現できる。
```

## X / Twitter（English）

```
Ask an LLM for a Japanese commit message and the polite-form rate in the body goes 1.0% -> 83.3%.

ai-kousei flags that with local regex only. Every rule cites a clause of a Japanese public standard, and CI verifies those quotes verbatim against the original documents.

https://github.com/AidenLee0011/ai-kousei
```

## Reddit（r/opensource, r/coolgithubprojects, r/SideProject）

タイトル

```
ai-kousei - a Japanese writing linter where every rule cites a government style clause, and CI verifies the quotes verbatim
```

本文

```
I measured 96 Japanese commits authored before Nov 2022 (pre chat-LLM) against 30 commits written by an LLM for the same diffs.

  polite form in the body: 1.0% (human) vs 83.3% (LLM)
  mixed sentence endings:  1.0% vs 80.0%
  sentence over 60 chars:  2.1% vs 33.3%

Japanese engineering records use plain form or noun endings. That is not taste: it is written in the Council for Cultural Affairs guidance on public documents (2022), clause III-1-a.

So I built the linter around the standards instead of around my intuition:

- 23 Japanese rules, each citing a document, a clause and the quoted line
- CI downloads the 18 cited documents on every push and fails the build if a quote is not in the original. The first run caught 7 of my own quotes that had drifted into paraphrase
- rules invert by use: polite form is an error in a commit record and required in a customer notice, so you pass --profile commit|report|agent|customer
- measured false positives: 2.1% on human commits, 2.2% on 400 blocks of published reports
- zero dependencies, no model call, no network. Python and Node

Not the first Japanese AI-writing tool. textlint-ja presets, patina and humanizer-ja exist. The difference is traceable sources, profile inversion, and published false-positive rates.

Repo: https://github.com/AidenLee0011/ai-kousei
Browser demo: https://aidenlee0011.github.io/ai-kousei/
```

## YouTube Shorts / Reels / TikTok（読み上げ台本・35秒）

```
0:00  AIに日本語のコミットを書かせると、こうなる。
      画面: 敬体の説明文、score 54、差し戻し
0:08  人が書いた記録はこう。なぜ、なにを、確認。
      画面: 体言止めの3項目、score 100、通過
0:16  面白いのは、用途を変えると正解が反転すること。
0:20  対顧客に切り替えると、さっきの常体がエラーになる。
      画面: profile を customer に切り替え、常体がエラー
0:26  根拠は全部、公用文作成の考え方とJTFスタイルガイドの条文。
      CIが原文と一字一句照合している。
0:33  ai-kousei。リンクは概要欄。
```

概要欄

```
AIが書いた日本語は敬体率83%、人が書いた記録は1%。
公用文作成の考え方とJTF日本語標準スタイルガイドの条文を根拠に、コミット・報告書・エージェント間・対顧客の日本語を検査するリンターです。依存ゼロ、モデル呼び出しなし。

GitHub: https://github.com/AidenLee0011/ai-kousei
デモ: https://aidenlee0011.github.io/ai-kousei/
解説記事: https://qiita.com/AidenLee0011/items/40faf0bfb8f230c37430
```

## ハッシュタグ

- X（日本語）: #個人開発 #日本語 #textlint #OSS #AI
- Shorts / Reels: #プログラミング #エンジニア #AI #開発 #日本語
- Reddit: ハッシュタグを使わない。自己宣伝規定のあるサブレは事前確認。

## 投稿順序

1. Qiita 記事（公開済み）
2. X 日本語スレッド（記事とデモを引用）
3. Shorts / Reels（縦動画）
4. Reddit r/opensource、反応を見て r/programming
5. Zenn（GitHub 連携が通り次第）
