# -*- coding: utf-8 -*-
"""Generate the README figures. Plain SVG, no dependencies.

    python docs/gen_docs.py        # writes docs/*.svg

Rasterise to PNG with any headless browser; GitHub renders the SVG directly.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BG = "#ffffff"
INK = "#1f2328"
DIM = "#6e7781"
LINE = "#d0d7de"
BAD = "#e5534b"
GOOD = "#3fb950"
BLUE = "#4c8dff"
JP = "-apple-system,Segoe UI,Hiragino Sans,Noto Sans JP,sans-serif"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def hero():
    """AS-IS vs TO-BE, the three second version."""
    W, H = 1200, 430
    o = io.StringIO()
    o.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="%s">' % (W, H, W, H, JP))
    o.write('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))
    o.write('<text x="30" y="38" font-size="19" font-weight="700" fill="%s">AI が書いた日本語コミットは、日本語話者が書くコミットと形が違う</text>' % INK)
    o.write('<text x="30" y="62" font-size="13" fill="%s">ai-kousei はその差を、公的文書の条文を根拠に指摘して直す。</text>' % DIM)

    def card(x, y, w, h, tag, color, lines, foot):
        o.write('<rect x="%d" y="%d" width="%d" height="%d" rx="9" fill="%s" fill-opacity="0.05" stroke="%s" stroke-opacity="0.5"/>' % (x, y, w, h, color, color))
        o.write('<rect x="%d" y="%d" width="86" height="24" rx="5" fill="%s" fill-opacity="0.14"/>' % (x + 16, y + 16, color))
        o.write('<text x="%d" y="%d" font-size="12.5" font-weight="700" fill="%s">%s</text>' % (x + 30, y + 33, color, tag))
        for i, ln in enumerate(lines):
            o.write('<text x="%d" y="%d" font-size="13.5" fill="%s" font-family="Consolas,Noto Sans Mono CJK JP,monospace">%s</text>'
                    % (x + 18, y + 66 + i * 24, INK, esc(ln)))
        o.write('<text x="%d" y="%d" font-size="12" fill="%s">%s</text>' % (x + 18, y + h - 18, DIM, esc(foot)))

    card(30, 86, 540, 300, "AS-IS", BAD, [
        "feat: 商品詳細APIにRedisキャッシュを追加",
        "",
        "商品詳細APIの応答速度向上とデータベース負荷軽減の",
        "ため、Redisキャッシュを導入しました。",
        "キャッシュの有効期限（TTL）は300秒に設定されて",
        "います。",
        "- **重要**: 監視対象に追加しました",
    ], "敬体の説明文・太字ラベル・数値なし  →  score 54 / commit blocked")

    o.write('<path d="M596 236 L634 236" stroke="%s" stroke-width="2"/>' % DIM)
    o.write('<path d="M628 230 L636 236 L628 242 z" fill="%s"/>' % DIM)

    card(650, 86, 520, 300, "TO-BE", GOOD, [
        "fix: 商品詳細APIにRedisキャッシュを追加",
        "",
        "なぜ: 商品詳細APIの応答が遅く、DB負荷も高い",
        "なにを: Redis を前段に追加。TTL 300秒",
        "確認: p95 820ms → 210ms",
    ], "体言止め・報告3項目・実測値  →  score 100 / passes")
    o.write('</svg>')
    return o.getvalue()


def architecture():
    W, H = 1200, 460
    o = io.StringIO()
    o.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="%s">' % (W, H, W, H, JP))
    o.write('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))
    o.write('<defs><marker id="a" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 z" fill="%s"/></marker></defs>' % DIM)
    o.write('<text x="30" y="36" font-size="18" font-weight="700" fill="%s">出典 → 規則 → フック。規則の根拠と閾値の出どころが全部たどれる</text>' % INK)

    def box(x, y, w, h, title, sub, color=LINE, strong=False):
        o.write('<rect x="%d" y="%d" width="%d" height="%d" rx="8" fill="%s" fill-opacity="%s" stroke="%s"/>'
                % (x, y, w, h, color if strong else "#f6f8fa", "0.08" if strong else "1", color))
        o.write('<text x="%d" y="%d" font-size="13" font-weight="700" fill="%s">%s</text>' % (x + 12, y + 23, INK, esc(title)))
        for i, ln in enumerate(sub):
            o.write('<text x="%d" y="%d" font-size="11.5" fill="%s">%s</text>' % (x + 12, y + 43 + i * 16, DIM, esc(ln)))

    def arrow(x1, y1, x2, y2):
        o.write('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.4" marker-end="url(#a)"/>' % (x1, y1, x2, y2, DIM))

    o.write('<text x="30" y="72" font-size="11.5" font-weight="700" fill="%s">1. 根拠</text>' % DIM)
    box(30, 82, 250, 92, "公用文作成の考え方", ["文化審議会建議 2022-01-07", "文体・一文長・受身・階層"], BLUE, True)
    box(30, 182, 250, 78, "JTF日本語標準スタイルガイド", ["日本翻訳連盟", "見出し・句読点・カタカナ"], BLUE, True)
    box(30, 268, 250, 78, "textlint-ja プリセット", ["技術文書 / AI ライティング", "読点数・漢字連続・誇張"], BLUE, True)
    box(30, 354, 250, 78, "実測コーパス", ["人手コミット 96 / LLM 30", "公開報告書 8 件 8,181 文"], GOOD, True)

    o.write('<text x="330" y="72" font-size="11.5" font-weight="700" fill="%s">2. 規則ファイル</text>' % DIM)
    box(330, 82, 300, 350, "ai_kousei/rules/ja.json", [
        "1 規則 = pattern + severity + weight",
        "        + source{doc, loc, quote}",
        "        + example{before, after}",
        "",
        "出典のない規則は入れない。",
        "selftest が出典解決と、",
        "AS-IS 例が実際に発火することを検査。",
        "",
        "閾値は実測から決める:",
        "  一文 60 字（公用文 Ⅲ-3-ア）",
        "  読点 3 個（textlint max-ten）",
        "  敬体（人手 1.0% / LLM 83.3%）",
    ])
    arrow(284, 128, 326, 200)
    arrow(284, 220, 326, 220)
    arrow(284, 306, 326, 250)
    arrow(284, 392, 326, 280)

    o.write('<text x="680" y="72" font-size="11.5" font-weight="700" fill="%s">3. 実行</text>' % DIM)
    box(680, 82, 230, 84, "commit-msg フック", ["merge/squash/fixup は除外", "error があれば exit 1"])
    box(680, 178, 230, 84, "ai-kousei lint / rules", ["次にやること 1 行 → 5 件", "各指摘に条番号と引用"])
    box(680, 274, 230, 84, "ブラウザデモ", ["同じ JSON を読む", "判定がずれない"])
    box(680, 370, 230, 62, "bench/", ["閾値の再測定"])
    arrow(634, 200, 676, 124)
    arrow(634, 220, 676, 220)
    arrow(634, 240, 676, 316)
    arrow(634, 300, 676, 400)

    box(950, 82, 220, 84, "git commit", ["生成文らしければ止まる"], BAD, True)
    box(950, 178, 220, 84, "書き手", ["AS-IS → TO-BE を見て直す"])
    box(950, 274, 220, 84, "指摘 0 でコミット", ["公的基準に沿った記録"], GOOD, True)
    arrow(914, 124, 946, 124)
    arrow(914, 220, 946, 220)
    arrow(1060, 166, 1060, 176)
    arrow(1060, 262, 1060, 272)
    o.write('</svg>')
    return o.getvalue()


def bench():
    W, H = 1200, 300
    rows = [
        ("LLM が書いたコミット (n=30)", 86.7, BAD),
        ("人手・手書き 2022-11 以前 (n=96)", 2.1, GOOD),
        ("人手・squash マージ (n=50)", 6.0, DIM),
    ]
    o = io.StringIO()
    o.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="%s">' % (W, H, W, H, JP))
    o.write('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))
    o.write('<text x="30" y="36" font-size="18" font-weight="700" fill="%s">コミットが止まる割合（error 発火率）</text>' % INK)
    o.write('<text x="30" y="58" font-size="12.5" fill="%s">人手側は LLM 普及前のコミットのみ。ここでの発火は誤検出として数える。python bench/run.py --lang ja</text>' % DIM)
    for i, (label, v, col) in enumerate(rows):
        y = 92 + i * 58
        o.write('<text x="30" y="%d" font-size="13" fill="%s">%s</text>' % (y + 16, INK, esc(label)))
        o.write('<rect x="380" y="%d" width="700" height="22" rx="4" fill="#f0f3f6"/>' % y)
        o.write('<rect x="380" y="%d" width="%d" height="22" rx="4" fill="%s"/>' % (y, int(700 * v / 100.0), col))
        o.write('<text x="%d" y="%d" font-size="13" font-weight="700" fill="%s">%.1f%%</text>' % (390 + int(700 * v / 100.0), y + 16, col, v))
    o.write('<text x="30" y="276" font-size="12" fill="%s">判別に効いた規則（人手 → LLM）: 本文敬体 1.0%% → 83.3%% ・ 文体混在 1.0%% → 80.0%% ・ 一文60字超 2.1%% → 33.3%% ・ 受身多用 0.0%% → 13.3%%</text>' % DIM)
    o.write('</svg>')
    return o.getvalue()


def profiles():
    """One tool, four rule sets. The same sentence flips between them."""
    W, H = 1200, 560
    o = io.StringIO()
    o.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="%s">' % (W, H, W, H, JP))
    o.write('<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG))
    o.write('<text x="30" y="36" font-size="18" font-weight="700" fill="%s">用途ごとに規則が変わる。対顧客では敬体が正解、記録では敬体が誤り。</text>' % INK)
    o.write('<text x="30" y="58" font-size="12.5" fill="%s">ai-kousei lint --profile commit | report | agent | customer</text>' % DIM)
    rows = [
        ("報告書  --profile report",
         ["本日、キャッシュ機構の全面刷新を行いました。これにより、", "応答速度が大幅に改善されたと考えております。"],
         ["1 概要  商品詳細APIの応答改善", "2 対応  Redis を前段に追加。TTL 300秒", "3 結果  p95 820ms → 210ms", "以上"],
         "誇張・冗長・数値なし", "見出し階層 第1→1→(1)→ア、結果は実測値"),
        ("エージェント間  --profile agent",
         ["エラー時は適宜リトライし、必要に応じて通知する。", "確認しました。対応済み。"],
         ["エラー時は最大3回・10秒間隔でリトライする。", "3回失敗したら Slack #ops へ通知する。"],
         "曖昧語・動作主なし = 機械が実行できない", "数値・条件・対象を明示"),
        ("対顧客  --profile customer",
         ["本日デプロイを実施し、キャッシュ削除を行った。", "ご利用は可能である。"],
         ["本日、新機能を公開しました。", "表示が古い場合は再読み込みをお願いします。"],
         "常体・社内用語", "敬体・日常語（公用文 Ⅲ-1-ア / Ⅱ 用語）"),
    ]
    y = 84
    for title, before, after, bad, good in rows:
        o.write('<text x="30" y="%d" font-size="13.5" font-weight="700" fill="%s">%s</text>' % (y + 16, INK, esc(title)))
        for x, txt, tag, note, col in ((30, before, "AS-IS", bad, BAD), (620, after, "TO-BE", good, GOOD)):
            o.write('<rect x="%d" y="%d" width="550" height="112" rx="8" fill="%s" fill-opacity="0.05" stroke="%s" stroke-opacity="0.45"/>' % (x, y + 26, col, col))
            o.write('<text x="%d" y="%d" font-size="11" font-weight="700" fill="%s">%s</text>' % (x + 14, y + 46, col, tag))
            for i, ln in enumerate(txt):
                o.write('<text x="%d" y="%d" font-size="12.5" fill="%s" font-family="Consolas,Noto Sans Mono CJK JP,monospace">%s</text>' % (x + 14, y + 68 + i * 20, INK, esc(ln)))
            o.write('<text x="%d" y="%d" font-size="11.5" fill="%s">%s</text>' % (x + 14, y + 128, DIM, esc(note)))
        y += 162
    o.write('</svg>')
    return o.getvalue()


if __name__ == "__main__":
    for name, fn in (("hero.svg", hero), ("profiles.svg", profiles), ("architecture.svg", architecture), ("bench.svg", bench)):
        path = os.path.join(HERE, name)
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(fn())
        print("wrote", path)
