# 회귀 테스트 실행 기록 — 2026-07-30

측정 대상: 로컬 스택(API `:8000` + Web `:3000` + local DB, ACTIVE KB 19/기관 3/매핑 10)
실행기: `scripts/run_regression_metrics.py`
표본: `data/evaluation/sample_questions_20.csv` (T-01~T-20) + 제안서 §7.5 데모 5문항

## 1. 전체 실행 결과

| 실행 | commit | intent | status | source | fallbk | answer | pii | lat(ms) | err | demo | 상태 실패 문항 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 기준선 provider-disabled | 028053d | 0.80 | 0.85 | 1.00 | 1.00 | 0.70 | 1.00 | 171 | 0.00 | — | T-02,07,08 |
| 기준선 grounded | 028053d | 0.80 | 0.85 | 1.00 | 1.00 | 0.70 | 1.00 | 625 | 0.00 | — | T-02,07,08 |
| A 원본 프롬프트 ON | b867ca7 | 0.75 | 0.80 | 1.00 | 0.85 | 1.00 | 1.00 | 1246 | 0.00 | — | T-11,12,19,20 |
| A′ 재실행 | b867ca7 | 0.75 | 0.80 | 1.00 | 0.85 | 1.00 | 1.00 | 1511 | 0.00 | — | 동일 |
| B 분류기 OFF | b867ca7 | 0.80 | 0.85 | 1.00 | 1.00 | 0.70 | 1.00 | 700 | 0.00 | — | T-02,07,08 |
| C 예시 교체 | b867ca7 | 0.90 | 0.95 | 1.00 | 1.00 | 1.00 | 1.00 | 1222 | 0.00 | — | T-12 |
| C′ 재확인 | b867ca7 | 0.90 | 0.95 | 1.00 | 1.00 | 1.00 | 1.00 | 1180 | 0.00 | — | 동일 |
| D 예산확대+규칙2 | b867ca7 | 0.85 | 0.90 | 1.00 | 0.95 | 1.00 | 1.00 | 1324 | 0.00 | — | T-19,20 |
| D′ 재확인 | b867ca7 | 0.85 | 0.90 | 1.00 | 0.95 | 1.00 | 1.00 | 1307 | 0.00 | — | 동일 |
| ~~E 라벨갱신(철회)~~ | b867ca7 | 0.85 | 0.95 | 1.00 | 0.95 | 1.00 | 1.00 | 1242 | 0.00 | — | T-19 |
| F 규칙4 흡수금지 | b867ca7 | 0.80 | 0.85 | 1.00 | 0.90 | 1.00 | 1.00 | 1278 | 0.00 | — | T-12,19,20 |
| G 순서절차 4단계 | b867ca7 | 0.85 | 0.90 | 1.00 | 0.90 | 1.00 | 1.00 | 1168 | 0.00 | — | T-19,20 |
| H 최종 5단계 | b867ca7 | 0.85 | 0.90 | 1.00 | 0.90 | 1.00 | 1.00 | 1175 | 0.00 | — | T-19,20 |
| I 판정기준 v2 | b867ca7 | 0.85 | 0.90 | 1.00 | 0.90 | 1.00 | 1.00 | 1262 | 0.00 | 0.60 | T-19,20 |
| **J 개인조회 수정 + 승인 완주** | b867ca7 | **0.85** | **0.90** | **1.00** | **0.90** | **1.00** | **1.00** | 1291 | **0.00** | **1.00** | T-19,20 |
| 목표치 | | 0.85 | 0.80 | 1.00 | 0.90 | 0.80 | 1.00 | 3000 | 0.00 | 1.00 | |

> **`demo_completion_rate`의 `—`는 미측정이 아니라 "비교 대상 아님"이다.** 해당 실행은 판정 기준 v1로
> 측정했고 v2와 자를 달리하므로 같은 축에 놓지 않는다. v1 원값은 §6.3에 별도로 보존한다.
>
> **I는 코드 변경이 아니라 판정 기준 교정 결과**이고(0.60), **J는 그 위에 개인 조회 결함 수정과
> 승인 흐름 완주를 더한 결과**다(1.00). **0.60 → 1.00은 같은 기준 안에서의 실제 개선**이다.

모든 실행은 `classifier=true,grounded=true`(B 제외: `classifier=false,grounded=true`).
`′` 표시는 동일 설정 재실행이며 기능 지표가 완전히 일치했다(지연시간만 변동).

**측정 회차는 총 15회다.** 위 표의 마지막 행 `목표치`는 실행이 아니라 판정 기준이므로
회차에 포함하지 않는다. §6.3.1의 "기준선~H 13회"에 I·J를 더한 값과 일치한다.

## 2. 문항별 실제 동작 변화

```
id     기준선            A 원본            B OFF           C 교체            D 규칙2           F 규칙4           H 최종
T-02   FOLLOWUP  X    SUCCESS   O    FOLLOWUP  X    SUCCESS   O    SUCCESS   O    SUCCESS   O    SUCCESS   O
T-07   FOLLOWUP  X    SUCCESS   O    FOLLOWUP  X    SUCCESS   O    SUCCESS   O    SUCCESS   O    SUCCESS   O
T-08   FOLLOWUP  X    SUCCESS   O    FOLLOWUP  X    SUCCESS   O    SUCCESS   O    SUCCESS   O    SUCCESS   O
T-11   FOLLOWUP  O    SCOPE_GAP X    FOLLOWUP  O    FOLLOWUP  O    FOLLOWUP  O    FOLLOWUP  O    FOLLOWUP  O
T-12   FOLLOWUP  O    SUCCESS   X    FOLLOWUP  O    SUCCESS   X    FOLLOWUP  O    SUCCESS   X    FOLLOWUP  O
T-19   FOLLOWUP  O    SCOPE_GAP X    FOLLOWUP  O    FOLLOWUP  O    SUCCESS   X    SCOPE_GAP X    SCOPE_GAP X
T-20   FOLLOWUP  O    SCOPE_GAP X    FOLLOWUP  O    FOLLOWUP  O    SCOPE_GAP X    SCOPE_GAP X    SCOPE_GAP X
```

O/X는 CSV 라벨(= provider-disabled 기대값) 대비 판정이다.

## 3. 핵심 발견

### 3.1 이전 빌드의 분류기는 이 표본에서 아무 결과도 바꾸지 못했다

기준선 provider-disabled와 grounded의 기능 지표가 완전히 동일하다
(0.80 / 0.85 / 1.00 / 1.00 / 0.70 / 1.00). 차이는 지연시간 171 → 625뿐이다.

### 3.2 현재 빌드의 분류기는 7개 문항을 실제로 움직인다

A(ON)와 B(OFF) 대조에서 T-02·07·08은 개선, T-11·12·19·20은 악화.
`answerable_success_rate` 0.70 → 1.00, `fallback_appropriateness` 1.00 → 0.85.
작동은 하되 방향이 절반 틀린 상태였고 이것이 개선 작업의 출발점이 되었다.

### 3.3 원인은 분류 프롬프트 단일 지점이었다

3단 대조로 확정했다.

| 조건 | T-11 | T-12 | T-19 | T-20 |
|---|---|---|---|---|
| 분류기 OFF (현재 빌드) | O | O | O | O |
| 분류기 ON (현재 빌드, 원본 프롬프트) | X | X | X | X |
| 분류기 ON (이전 빌드) | O | O | O | O |

결정론적 코드는 네 문항 모두 정답을 낸다. 분류기를 켤 때만 깨졌고,
두 빌드의 `classifier_prompt.py`가 전면 재작성되어 있었다.

### 3.4 지표가 놓친 회귀가 있었다

G 버전에서 19→20 승인 데모의 핵심 문항(“침대 2인용 프레임 수수료”)이
`INSUFFICIENT_GROUNDING` → `FOLLOWUP`으로 깨졌으나 **9개 지표가 G와 H에서 완전히 동일**하다.
하니스의 D-5 판정은 큐 행 수만 세고 답변 상태를 보지 않으며, 이 질문은 표본 20문항에도 없다.
별도 probe(13문항 × 3회)로 검출했다. 회귀 하니스의 커버리지 공백이다.

## 4. 수정 내역

### 4.1 분류 프롬프트 — 순서 있는 5단계 판정 절차

```
1 순수 범주어(서류/증명서/신고/민원/발급)만        → NEEDS_FOLLOWUP
2 지목한 서비스·품목이 cat 행에 있음               → SUPPORTED
3 지원 분야지만 해당 행 없음                      → NO_TOPIC_MATCH
4 행정 민원이지만 지원 분야 밖                    → CIVIC_SCOPE_GAP
5 행정 민원 아님                                → NON_CIVIC
+ 행이 명시하지 않은 서비스로 확장 금지
```

few-shot 예시를 `SUPPORTED` / `NEEDS_FOLLOWUP` / `CIVIC_SCOPE_GAP` 3종으로 균형화했다.
원본에는 `SUPPORTED`와 `CIVIC_SCOPE_GAP` 2종뿐이어서 모호한 질문이 범위 밖으로 쏠렸다.

3단계(`NO_TOPIC_MATCH`) 누락이 3.4의 회귀 원인이었다. 경로를 하나 빠뜨리면
그 트래픽이 다른 경로로 샌다.

### 4.2 프롬프트 입력 예산 확대

| 항목 | 이전 | 이후 |
|---|---:|---:|
| `UPSTAGE_MAX_INPUT_TOKENS` | 4096 | 8192 |
| `LLM_MAX_INPUT_TOKENS` | 4096 | 8192 |
| `LOCAL_INTERACTIVE_COST_CAP_USD` | 0.20 | 0.30 |
| `LLM_SESSION_COST_CAP_USD` | 0.20 | 0.30 |

입력 상한은 1회 호출 최악 비용의 입력값이므로 비용 상한을 함께 올려야 했다.
입력 8192에서 generator 100회(시도 상한)의 최악 비용이 $0.2028로 기존 상한 0.20을 넘어,
시도 상한에 닿기 전에 비용이 먼저 소진되었다. 0.30은 원래 설계 관계
(레인별은 시도 수가, 합산 160회 $0.324는 비용이 제한)를 보존하는 최소값이다.

### 4.3 시도했다가 되돌린 것

- **결정론적 경로 수정**: `_UNSUPPORTED_ADMIN_TERMS`로 직접 `CIVIC_SCOPE_GAP` 라우팅.
  테스트 9건 실패, 그중 4건이 `..._are_deferred_to_the_closed_provider`로 설계 의도를 명시.
  미지원 행정 민원은 provider가 판단하도록 한 설계였으므로 전면 원복.
- **CSV 라벨 갱신**: T-19·T-20을 `FALLBACK`/`CIVIC_SCOPE_GAP`으로 변경.
  `test_sample_questions_20.py`가 LLM 없이 결정론적 파이프라인만 돌려 CSV와 대조하므로
  이 라벨은 계약상 provider-disabled 기대값이다. 원복하고 `비고` 열에 모드별 동작만 기록.

## 5. 최종 상태

| 지표 | 기준선(028053d) | 최종 H(b867ca7) | 목표 |
|---|---:|---:|---:|
| `intent_accuracy` | 0.80 미달 | **0.85 달성** | 0.85 |
| `answer_status_accuracy` | 0.85 | **0.90** | 0.80 |
| `source_labeling_rate` | 1.00 | 1.00 | 1.00 |
| `fallback_appropriateness` | 1.00 | 0.90 | 0.90 |
| `answerable_success_rate` | 0.70 미달 | **1.00** | 0.80 |
| `pii_masking_rate` | 1.00 | 1.00 | 1.00 |
| `latency_mean_ms` | 625 | 1175 | 3000 |
| `error_rate` | 0.00 | 0.00 | 0.00 |
| `demo_completion_rate` | 비교 대상 아님 | **1.00 달성** | 1.00 |
| **목표 달성** | **6/9** (v1 기준) | **9/9** | |

핵심 13문항 × 3회 probe: **39/39 전부 기대값 일치**.
품질 게이트: ruff format/check 통과, strict mypy 통과, pytest 2,617 passed / 8 skipped.

## 6. 남은 것과 해석 주의

### 6.1 T-19·T-20은 결함이 아니라 모드 차이다

| | 결정론적(분류기 OFF) | 분류기 ON |
|---|---|---|
| “여권 발급 방법 알려줘” | FOLLOWUP | `CIVIC_SCOPE_GAP` |
| “반려동물 등록 어디서 해요?” | FOLLOWUP | `CIVIC_SCOPE_GAP` |

두 동작 모두 각 모드에서 타당하다. CSV의 `기대 상태` 열은 하나뿐이고
결정론적 값으로 고정되어 있어, 분류기 ON 실행을 채점하면 구조적으로 어긋난다.
T-19의 **실제 결함**(여권 → 증명서 KB로 `SUCCESS`)은 H에서 해소되었다.

### 6.2 표본 점수만으로 고르면 안 된다

C가 표본 점수 최고(0.90/0.95)지만 여권 결함이 남아 있고
`CIVIC_SCOPE_GAP` 경로가 사실상 죽은 상태였다(큐 증가 0).

### 6.3 데모 완주율 0.00은 대부분 측정 아티팩트였다

판정 기준 v1은 D-1의 딥링크와 D-3의 관련 민원 제안을 **API 응답 필드**로 검사했다.
그러나 딥링크는 `apps/web/src/lib/labels.ts`의 `DEEP_LINK_BY_INTENT` 상수로 답변 카드에
렌더링되며(`AnswerCard.tsx:243`), API 응답 필드가 아니다. **구현되어 있으나 하니스가 볼 수 없는
계층에 있었다.** 관련 민원 제안은 팀이 화면 복잡도를 이유로 범위에서 제외한 항목이다.
D-2는 실제 화면과 달리 하니스가 지역을 선택하지 않고 질문만 보내 실패했다.

기준을 교정하자(v2) 완주율이 v1의 0.00에서 **0.60**이 되었다. 남은 두 건은 성격이 달랐다.

| 데모 | v2 최초(I) | 성격 | 조치 후(J) |
|---|---|---|---|
| D-1, D-2, D-3 | 통과 | v1에서는 측정 방식 때문에 실패로 집계 | 통과 |
| D-4 자동차세 | 실패 | **유일한 실제 결함** — 개인 조회 판정에 세목명 부재 | **수정 후 통과** |
| D-5 선순환 | 실패 | `kb-candidates ≥ 1` 미충족. 상태 전제 | **승인 완주 후 통과** |

D-4는 `_PERSONAL_LOOKUP_TERMS`에 세목명을 추가하면서 `_SUBJECT_BOUND_LOOKUP_TERMS`
제외 집합을 함께 도입해 해결했다. 단순 추가는 "자동차세 납부 방법 알려주세요" 같은 일반 안내
질문까지 개인 조회로 오분류시키므로, 세목명은 **1인칭 주어가 함께 있을 때만** 개인 조회로 본다.

D-5는 결함이 아니라 측정 시점의 DB 상태였다. 승인 흐름을 완주하자 충족되었다.

**결과적으로 판정 기준 v2 안에서 0.60 → 1.00으로 올랐고, 이 구간은 자를 바꾸지 않은
동일 기준 비교이므로 실제 개선이다.**

### 6.3.1 v1 원값 보존

아래는 판정 기준 v1로 측정한 `demo_completion_rate` 원값이다. v2 값과 같은 축에 놓지 않는다.

| 실행 | v1 원값 | 당시 실패 데모 |
|---|---:|---|
| 기준선 grounded ~ H (13회 전부) | 0.00 | D-1 ~ D-5 |

v1은 딥링크·관련 민원을 API 응답 필드로 검사했고 지역을 선택하지 않고 호출했다.
따라서 이 0.00은 **구현 상태의 측정이 아니라 판정 기준의 산물**이다.

### 6.4 v1과 v2의 비교 규칙

- **표본 20문항 기반 8개 지표**(`intent_accuracy`, `answer_status_accuracy`,
  `source_labeling_rate`, `fallback_appropriateness`, `answerable_success_rate`,
  `pii_masking_rate`, `latency_mean_ms`, `error_rate`)는 판정 로직이 변하지 않았으므로
  **전 구간 직접 비교 가능**하다.
- **`demo_completion_rate`는 v1과 v2를 비교하지 않는다.** 판정 항목이 다르므로 서로 다른 계열이다.
  이는 `REGRESSION-METRICS.md` §3이 프로바이더 모드 불일치에 적용한 원칙
  (`BASELINE_MODE_MISMATCH` — 조건이 다르면 게이트 미적용)과 같은 규칙이다.
- **v1 원값은 삭제하지 않고 §6.3.1에 보존**하되, 본 표의 추이 축에는 올리지 않고 `—`로 둔다.
  "미측정"이 아니라 "다른 자로 측정하여 비교 대상 아님"이라는 뜻이다.
- **개선 주장은 v2 구간(I → J, 0.60 → 1.00) 안에서만 한다.** 이 구간은 판정 기준이 동일하고
  변화 요인이 코드 수정과 흐름 완주뿐이므로 공정한 비교다.
- 표본 20문항 기반 8개 지표는 전 구간 동일 로직이므로 v1·v2 구분 없이 비교한다.
  **오늘의 품질 개선 주장은 이 8개를 근거로 한다.**

### 6.5 선순환 재질의는 예약 바인딩 정확 일치가 전제다

`apps/api/src/sejong_ai_api/admin/candidate_binding.py`는 `KB-WASTE-03` 활성화를
**서버가 예약한 공식 값과의 정확 일치**로 제한한다.

- `claims_reserved_binding()` — `title`·`source_title`·`source_url` 세 필드로 예약 건임을 주장
- `is_exact_reserved_candidate()` — `representative_question`, `answer_summary`,
  `procedure_steps`, `required_documents`, `processing_time`, `fee`, `department`,
  `last_verified_at`, `caution` **전부 일치** 요구

2026-07-30 검증에서 확인한 실패·성공 양상은 다음과 같다.

| 후보 내용 | 생성 | 승인 | 재질의 |
|---|---|---|---|
| 임의 작성 | 201 | 200 | **폴백 유지** — 예약 바인딩 미주장으로 KB 미활성 |
| staging 파일 문구 | 422 | — | — |
| staging 문구에서 `procedure_steps` 제외 | 201 | 422 | — |
| **바인딩 상수 그대로** | **201** | **200** | **`SUCCESS` + 출처 `KB-WASTE-03` (3/3)** |

**`data/staging/data-001/0.1.0-draft.1/kb_records.json`의 문구는 바인딩 상수와 다르다.**
예: 절차 첫 항목이 staging은 "침대 프레임의 공식 표기인…", 바인딩은 "공식 품목표에서 침대 프레임의…".
staging을 참조해 후보를 작성하면 실패한다.

또한 바인딩의 `_REPRESENTATIVE_QUESTION`이 제안서 §7.5 #5 원문
"침대 2인용 프레임 수수료가 얼마예요?"와 동일하다. 따라서
`docs/data-lineage/MVP-001-KB-WASTE-03-LOCAL-WORKFLOW.md`의 2026-07-24 기록
"same-query SUCCESS"가 현재 동작과 일치하며, 2026-07-22의 K1/K2 구분은 해당 시점 조건으로 본다.

### 6.6 기준선과 현재는 갈라진 두 계보다

`028053d`(2026-07-28)는 `b867ca7`(2026-07-30) 히스토리에 존재하지 않는다.
“before/after”가 아니라 “두 구현의 대조”로 표현해야 한다.

## 7. 후속 과제

1. **T-19·T-20 모드 차이 해소** — 아래 세 방안 중 택일(§6.1)
   - 결정론적 경로를 `CIVIC_SCOPE_GAP`으로 통일 (계약 테스트 4건 갱신 필요)
   - CSV에 모드별 기대값 열 추가 (테스트·하니스 양쪽 수정 필요)
   - 정본 게이트를 provider-disabled로 유지하고 grounded는 별도 기준선 파일로 보관
     (`REGRESSION-METRICS.md` §3이 이미 규정한 방식)
2. **D-4 개인조회 미분기** — `_PERSONAL_LOOKUP_TERMS`에 세목명 추가 시
   `intrinsically_personal` 제외 집합에도 함께 넣어야 일반 안내 질문이 오분류되지 않는다
3. **마스킹 오탐** — “주민세 …”가 `AMBIGUOUS_PERSON_NAME`으로 거절된다
   (`_SAFE_STANDALONE_NAME_TERMS`에 `주민세` 누락)
4. **하니스 커버리지** — 데모 문항의 답변 상태를 판정 항목에 포함 (§3.4)
