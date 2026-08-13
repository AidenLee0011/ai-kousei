# buntai 文体

![MIT](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/python-3.9%2B-blue) ![Node](https://img.shields.io/badge/node-14%2B-blue) ![deps](https://img.shields.io/badge/dependencies-0-brightgreen) ![no api](https://img.shields.io/badge/API%20calls-none-brightgreen) ![rules](https://img.shields.io/badge/ja%20rules-23%20cited-orange)

**LLM 에게 일본어 커밋·보고를 시키면 본문 경체(です・ます) 비율이 1.0% 에서 83.3% 로 튑니다.**
buntai 는 그 차이를 일본 공적문서의 조문을 근거로, 로컬 정규식만으로 잡습니다.

[日本語](README.md) ・ [English](README.en.md) ・ **한국어**

[데모 열기](https://aidenlee0011.github.io/buntai/) ・ 일본어 교정 / 일본어 린터 / AI 문체 판별 / 커밋 메시지 검사 / Node 불필요

![AS-IS to TO-BE](docs/hero.png)

```bash
pip install buntai-lint && buntai hook install --lang ja     # Python
npx buntai-lint lint report.md --profile report              # Node
```

---

## 무엇이 다른가

**1. 지적에 조번호와 원문 인용이 붙고, CI 가 원문과 축자 대조합니다.**

일본어 규칙 23건 전부가 「公用文作成の考え方」(문화심의회 건의, 2022) · JTF 일본어표준스타일가이드 4.0(CC BY 4.0) · textlint-ja 프리셋 중 하나를 인용합니다. "어쩐지 부자연스럽다"가 아니라 **어느 문서 몇 항 위반인지**가 나옵니다.
CI 는 매 푸시마다 인용 원문 18건을 내려받아 대조하고, 불일치면 빌드를 떨어뜨립니다. **이 검사를 처음 돌렸을 때 작성자 본인의 인용 7건이 요약이라 걸렸습니다.** 규칙이 창작으로 흐를 여지를 구조로 막았습니다.

**2. 용도에 따라 규칙이 반전합니다.**

같은 경체가 기록에서는 오류, 대고객에서는 필수입니다. 그래서 추측하지 않고 `--profile` 로 선언합니다.

```
--profile commit    "導入しました" -> ERROR   기록은 상체·체언止め (公用文 Ⅲ-1-ア)
--profile customer  "停止する。"   -> ERROR   통지는 경체 (같은 조)
--profile agent     "適宜リトライ" -> ERROR   기계는 "적절히"를 실행할 수 없음 (Ⅲ-3-シ)
```

**3. 사람이 쓴 글은 통과합니다. 측정했습니다.**

| 대상 (전부 사람이 쓴 글) | 프로파일 | error 발화 |
|---|---|---:|
| 커밋 96건 (2022-11 이전 = LLM 보급 전) | commit | **2.1%** |
| 공개 보고서 본문 400블록 (JPCERT/CC) | report | **2.2%** |
| LLM 이 쓴 커밋 30건 | commit | **86.7%** |

**4. 모델 호출·네트워크·의존성 0.** 규칙 로드 4ms, 메시지 1건 판정 0.24ms. API 키를 요구하는 훅은 결국 제거됩니다.

---

## 근접 도구와의 차이

"최초"도 "유일"도 아닙니다. 일본어 AI 문체 도구는 이미 존재합니다.

| 도구 | 대상 | 차이 |
|---|---|---|
| [textlint-rule-preset-ai-writing](https://github.com/textlint-ja/textlint-rule-preset-ai-writing) 1,095★ | 산문의 AI 패턴 | buntai 는 조번호를 제시하고 CI 가 원문 대조 |
| [textlint-rule-preset-JTF-style](https://github.com/textlint-ja/textlint-rule-preset-JTF-style) 218★ | JTF 표기 규칙 | 해당 프리셋은 JTF 2.1/2.2 기반, buntai 는 **4.0(2026-07-25)** 인용 |
| [patina](https://github.com/devswha/patina) 316★ | KO/EN/ZH/JA humanizer, commit-message 문서유형 보유 | patina 는 재작성까지 수행. buntai 는 **재작성하지 않고** 지적과 조문만 제시. 용도 반전 설계 없음 |
| [humanizer-ja](https://github.com/gonta223/humanizer-ja) 123★ | 일본어 AI 문체 20패턴 | Claude Code 스킬. buntai 는 CLI·훅 + 오탐률 공개 |

차이는 3가지입니다. **조문 단위로 추적되는 근거**, **용도에 따른 규칙 반전**, **측정해 공개한 오탐률**.

---

## 에이전트 간 인계에서 효과

```
AS-IS  エラー時は適宜リトライし、必要に応じて通知する。
       確認しました。対応済み。

TO-BE  エラー時は最大3回・10秒間隔でリトライする。
       3回失敗したら Slack #ops へ通知する。
```

「適宜」「必要に応じて」「対応済み」은 사람은 보완해 읽지만 받는 쪽이 기계면 실행이 불가능합니다. 근거는 公用文作成の考え方 Ⅲ-3-シ(두 가지로 읽히지 않게)와 Ⅲ-3-オ(주어·술어 관계가 드러나게)입니다.

![profiles](docs/profiles.png)

| 프로파일 | 대상 | 주요 검사 |
|---|---|---|
| `commit` | 커밋·PR (기록) | 상체·체언止め, 제목만으로 내용 파악, 왜/무엇/확인 |
| `report` | 사내 보고서 | 견출 계층(第1 → 1 → (1) → ア), 문체 통일, 과장·용장 |
| `agent` | 에이전트 간 인계 | 모호어 금지, 동작주 명시 |
| `customer` | 대고객 문면 | 경체 강제, 사내용어 언어화 |

---

## 출력

```
$ git commit -m "feat: 各種修正"
next: 対象と結果を書く。「決済リトライの上限を3回に変更」
日本語 / コミット・PR（記録）  score 88/100  errors 1  warnings 0  [blocked]
1. [ERROR] 件名だけでは内容がつかめない
     found: feat: 各種修正
     src:   公用文作成の考え方（文化審議会建議） Ⅲ-2-エ 文書の構成
     rule:  ja-koyo-vague-heading
```

1행이 다음에 할 일. 지적은 가중치 순 5건까지(전체는 `--all`). error 면 exit 1, warning 은 표시만. merge·squash·fixup 은 대상 외.

## 출처

| 출처 | 발행 | 사용처 |
|---|---|---|
| [公用文作成の考え方](https://www.bunka.go.jp/seisaku/bunkashingikai/kokugo/hokoku/pdf/93651301_01.pdf) | 문화심의회 건의 2022-01-07 | 문체 선택, 일문 길이, 수동, 이중부정, 조사 연속, 항목 계층, 용어 언어화 |
| [JTF日本語標準スタイルガイド 4.0](https://www.jtf.jp/pdf/jtf_style_guide.pdf) | 일본번역연맹, CC BY 4.0 | 견출은 상체·체언止め, 일문 구두점, 반각 가나 |
| [textlint-ja 프리셋](https://github.com/textlint-ja/textlint-rule-preset-ja-technical-writing) | textlint-ja, MIT | 약한 표현, 용장 표현, 독점 수, 한자 연속, 과장, 굵은 라벨 |
| 공개 보고서 코퍼스 (JPCERT/CC 8건·8,181문) | 실측 | 보고서 템플릿 문말(체언止め 44.7%·경체 20.6%·상체 1.6%) |

![architecture](docs/architecture.png)

규칙은 JSON 입니다. Python CLI·Node CLI·브라우저 데모가 같은 파일과 같은 엔진을 읽어 데모와 훅의 판정이 어긋나지 않습니다. `source` 없는 규칙은 selftest 가 거부하고, AS-IS 예시가 실제로 그 규칙을 발화시키는지도 검사합니다.

## 명령

```bash
buntai lint .git/COMMIT_EDITMSG            # 파일
buntai lint -m "fix: 各種修正"              # 문자열
git log -1 --format=%B | buntai lint       # 표준입력
buntai lint report.md --profile report --json
buntai rules --lang ja                     # 전 규칙 + 출처 + AS-IS/TO-BE
buntai metrics -m "..."                    # 정량 지표를 코퍼스 실측치와 병렬 표시
buntai template --lang ja                  # 커밋 / PR / 보고서 템플릿
python -m buntai selftest                  # 77 규칙 / 7 팩
python bench/run.py --lang ja --rules      # 측정 재현
```

## 범위와 한계

일본어가 주 대상입니다. 한국어·중국어·독일어·프랑스어·스페인어는 초기 규칙만 있고 출처 정비는 이제부터입니다. 영어는 의도적으로 제외했습니다.
일본어 규칙은 23건으로 textlint 생태계의 망라성에는 못 미치고, 형태소 분석을 쓰지 않아 문맥 의존 판정에는 약합니다.

## 기여

일본어 규칙 추가에는 `source`(문서명·조번호·인용)와 `example`(AS-IS / TO-BE)이 필수입니다. 다른 언어는 `buntai/rules/<code>.json` 을 추가하고, 그 언어의 공적문서·업계표준을 출처로 삼아 주세요. `python -m buntai selftest` 통과 필수.

MIT License. 출처는 조번호와 짧은 인용만 게재하며 원문은 재배포하지 않습니다.
