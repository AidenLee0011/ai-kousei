# -*- coding: utf-8 -*-
"""Deterministic Japanese text metrics. Standard library only.

The rules in rules/ja.json answer "does this break a documented standard".
These metrics answer a different question: "how far does this text sit from
how a Japanese engineer writes". They are numbers, not verdicts, and every
threshold used by the CLI is calibrated on the corpora in bench/, never guessed.

Signals are grouped the way the machine-translation literature groups them:
interference (English structure showing through), normalisation (uniform,
flattened rhythm), and simplification (thin vocabulary).

    python -m ringi metrics -m "<text>"
"""
from __future__ import annotations

import re
from collections import Counter
from statistics import mean, pstdev

SENT_SPLIT = re.compile(r"[。．\n]+")
KANJI = r"一-鿿"
KANA = r"぀-ヿ"


def sentences(text: str) -> list:
    return [s.strip() for s in SENT_SPLIT.split(text) if s.strip()]


def _rate(n: int, d: int) -> float:
    return (float(n) / d) if d else 0.0


# --- interference: English structure showing through -------------------------

def passive_rate(sents: list) -> float:
    """公用文作成の考え方 Ⅲ-3-ケ「受身形をむやみに使わない」の量的版."""
    n = sum(1 for s in sents if re.search(r"され(?:る|た|て|ます|ました|ている)", s))
    return _rate(n, len(sents))


def inanimate_subject_rate(sents: list) -> float:
    """「本変更は…を可能にする」型。英語の無生物主語構文の直訳。"""
    pat = re.compile(r"(?:本|この|当)?[%s%s]{2,12}(?:は|が)[^。]{0,40}?を(?:可能に|実現|提供|保証|意味)" % (KANJI, KANA))
    return _rate(sum(1 for s in sents if pat.search(s)), len(sents))


def nominal_particle_rate(sents: list) -> float:
    """「における」「に対しての」「からの」型の助詞重ね。公用文 Ⅲ-3-キ の隣接現象."""
    pat = re.compile(r"における|においての|に対しての|に関しての|からの|への|としての|でのの?")
    return _rate(sum(len(pat.findall(s)) for s in sents), len(sents))


def progressive_rate(sents: list) -> float:
    """「〜している」進行相の多用。英語 -ing の直訳で増える。"""
    return _rate(sum(1 for s in sents if re.search(r"して(?:い|お)ります|している|していま", s)), len(sents))


def demonstrative_rate(sents: list) -> float:
    """「これ」「それ」「その」など指示語の密度。英語代名詞の逐語訳で増える。"""
    return _rate(sum(len(re.findall(r"これ|それ|この|その|そのため|これにより", s)) for s in sents), len(sents))


def suffix_abstract_rate(sents: list) -> float:
    """「〜的」「〜性」「〜化」の抽象名詞化密度."""
    return _rate(sum(len(re.findall(r"[%s]的|[%s]性|[%s]化" % (KANJI, KANJI, KANJI), s)) for s in sents), len(sents))


def antithesis_count(text: str) -> int:
    """「単なる〜ではなく〜」型の否定対句。"""
    return len(re.findall(r"(?:だけ|のみ|単なる|単に)[^。]{0,24}(?:ではなく|でなく)", text))


# --- normalisation: flattened, uniform output --------------------------------

def ending_diversity(sents: list) -> float:
    """文末形の種類 / 文数。1.0 に近いほど多様、低いほど機械的."""
    if not sents:
        return 0.0
    ends = Counter(s[-3:] for s in sents)
    return _rate(len(ends), len(sents))


def length_uniformity(sents: list) -> float:
    """文長の標準偏差 / 平均。低いほど同じ長さの文が並ぶ = 機械的リズム."""
    if len(sents) < 2:
        return 0.0
    lens = [len(s) for s in sents]
    m = mean(lens)
    return (pstdev(lens) / m) if m else 0.0


def polite_rate(sents: list) -> float:
    """敬体(です・ます)率。記録文書では常体・体言止めが標準(JTF 1.1.2)."""
    return _rate(sum(1 for s in sents if re.search(r"(?:です|ます|ました|ません)$", s)), len(sents))


# --- simplification ----------------------------------------------------------

def kanji_ratio(text: str) -> float:
    body = re.sub(r"\s", "", text)
    return _rate(len(re.findall(r"[%s]" % KANJI, body)), len(body))


def compute(text: str) -> dict:
    """All signals for one message. Body only: the subject line is a heading."""
    lines = text.replace("\r\n", "\n").split("\n")
    body = "\n".join(lines[1:]).strip() or text
    sents = sentences(body)
    return {
        "sentences": len(sents),
        "mean_len": round(mean([len(s) for s in sents]), 1) if sents else 0.0,
        "passive_rate": round(passive_rate(sents), 3),
        "inanimate_subject_rate": round(inanimate_subject_rate(sents), 3),
        "nominal_particle_rate": round(nominal_particle_rate(sents), 3),
        "progressive_rate": round(progressive_rate(sents), 3),
        "demonstrative_rate": round(demonstrative_rate(sents), 3),
        "suffix_abstract_rate": round(suffix_abstract_rate(sents), 3),
        "antithesis": antithesis_count(body),
        "ending_diversity": round(ending_diversity(sents), 3),
        "length_uniformity": round(length_uniformity(sents), 3),
        "polite_rate": round(polite_rate(sents), 3),
        "kanji_ratio": round(kanji_ratio(body), 3),
    }
