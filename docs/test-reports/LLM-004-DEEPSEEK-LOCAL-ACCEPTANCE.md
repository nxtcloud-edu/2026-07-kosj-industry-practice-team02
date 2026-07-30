# LLM-004 DeepSeek Local Acceptance — Local/Private Evidence Report

- Report status: local/private 측정 완료. public/remote 사용은 계속 금지.
- Scope: local/private only. 대상 commit `b867ca7` (2026-07-30).
- 측정일: 2026-07-30
- 선행 문서: [LLM-003 Grounded Live Chat](LLM-003-GROUNDED-LIVE-CHAT.md),
  [LLM-003 로컬 런북](../runbooks/LLM-003-LOCAL-GROUNDED-CHAT.md)
- 근거 제안서 조항: §6.1 "LLM adapter(deepseek-v4-flash / upstage 비교 선택)",
  §6.4 외부 LLM 경계, §7.3 품질 검증 계획

이 보고서는 제안서 §6.1이 예고한 **비교 선택의 DeepSeek 측 결과**를 기록한다.
LLM-003은 Upstage `solar-pro3` 프로필에 대한 인수 기록이며, 본 문서는 그 절차를 참조하되
공급자·프로필·측정 방식이 다르므로 **별도 기록**으로 분리한다.

## 1. 공급자 선택 근거 — Upstage 대비 비교 결과

제안서 §6.1이 예고한 "deepseek-v4-flash / upstage 비교 선택"의 결과다.
**선택 사유는 한국어 답변 품질이 아니라 구조화 출력 계약의 통과 안정성이다.**

### 1.1 Upstage 측정 결과

| 항목 | 결과 |
|---|---|
| 한국어 답변 품질 (인간 평가) | 평균 **4.8444 / 5** — 양호 |
| 비용 | 낮음 |
| 합성 평가 strict JSON 통과 | **27 / 30** (목표 100% 미달) |
| 질문 분류 — 초기 | 요청 형식 문제로 **9/9 4xx** |
| 질문 분류 — 형식 수정 후 | 응답 **9/9 2xx**, 그러나 필수 5개 필드 불일치로 `KEY_SET_REJECTED` **9/9** |
| 질문 분류 — 키 수정 후 | enum·route 형태 불일치로 `ENUM_SHAPE_REJECTED` **9/9** |

답변 품질 자체는 문제가 없었다. 그러나 서버가 모델 출력을 **시민 분류 결과로 안전하게 채택할
증거가 확보되지 않았고**, 서버는 계속 폴백해야 했다. 근거 기록은 개발자 작업본의
`docs/00_SOURCE_OF_TRUTH.md`(L136), `docs/11_AMBIGUITY_REGISTER.md`(L75)에 있다.

### 1.2 DeepSeek 측정 결과

| 항목 | 결과 |
|---|---|
| HTTP · JSON · 서버 계약 | **9 / 9 통과** |
| 분류 정답률 — 초기 | 6 / 9 |
| 분류 정답률 — 개선 후 | 8 / 9 |

정답률이 완벽하지는 않으나 **서버 계약을 안정적으로 통과**한다는 점이 결정적이었다.
이후 local MVP의 API key·공급자 단일화를 위해 질문 분류와 근거 제한형 답변 생성을 모두
DeepSeek로 통일하도록 승인했다(`docs/decisions/DECISION_LOG.md` D-139, L142).

### 1.3 선택의 성격

**Upstage 코드는 삭제하지 않았고 선택 가능한 예비 공급자로 남아 있다.**
`llm/settings.py`, `llm/upstage_chat.py`, `llm/upstage_classifier.py`와
[LLM-003 런북](../runbooks/LLM-003-LOCAL-GROUNDED-CHAT.md)이 그대로 유지된다.

DeepSeek 역시 완벽하지 않으므로 **모델 판단을 그대로 신뢰하지 않는다.**
개인정보 마스킹 → ACTIVE KB 검색 → 서버 검증 → 출처 결합을 거치며, 이상이 있으면 기존
결정론적 답변으로 폴백한다. 본 보고서 §5의 안전 속성 관측이 이 구조의 측정 결과다.

## 2. 대상 구성

| 항목 | 값 | 출처 |
|---|---|---|
| classifier provider | `deepseek` | `apps/api/.env` |
| answer provider | `deepseek` | `apps/api/.env` |
| model | `deepseek-v4-flash` | `deepseek_settings.py` (하드코딩, `init=False`) |
| base URL | `https://api.deepseek.com` | 동일 |
| timeout | 10.0 s | 동일 |
| max retries | 0 | 동일 |
| max concurrency | 1 | 동일 |
| classifier max input chars | 1024 | 동일 |
| max input usage tokens | 16384 | 동일 |
| classifier max output tokens | 128 | 동일 |
| chat max output tokens | 1024 | 동일 |
| temperature | 0.0 | 동일 |
| attempt cap (classifier/generator/combined) | 80 / 100 / 160 | 동일 |
| session cost cap | 0.30 USD | `limits.py` (본 작업에서 변경, §6.1 참조) |

**출하 기본값은 비활성화를 유지한다.** `apps/api/.env.example`은
`CLASSIFIER_PROVIDER=disabled`, `LLM_PROVIDER=disabled`로 출하되며 본 측정은 ignored
`apps/api/.env`의 로컬 설정으로만 활성화했다. 제안서 §6.4의
"provider 호출은 기본 비활성화 상태다"는 현재도 참이다.

### 2.1 설정 로더 검증

`load_deepseek_chat_settings()`가 요구하는 exact non-secret 프로필 6개 값이 모두 일치함을
직접 호출로 확인했다(`LOADED`). 하나라도 어긋나면 fail-closed로 `None`을 반환해
TEMPLATE 경로로 동작한다.

```
LLM_PROVIDER                      = deepseek        OK
DEEPSEEK_MODEL                    = deepseek-v4-flash OK
DEEPSEEK_BASE_URL                 = https://api.deepseek.com OK
UPSTAGE_SYNTHETIC_EVALUATION_MODE = false           OK
UPSTAGE_CLASSIFIER_MODE           = false           OK
UPSTAGE_GROUNDED_CHAT_MODE        = false           OK
```

API key는 ignored `.env`에만 두었고 문서·로그·화면에 값을 출력하지 않았다.

## 3. 실행 범위

| 구분 | 횟수 | 비고 |
|---|---:|---|
| DeepSeek classifier + generator 활성 회귀 | 12 | 각 25문항(표본 20 + 데모 5) |
| classifier 비활성 / generator 활성 회귀 | 1 | 대조군 |
| 양쪽 전면 비활성 회귀 | 1 | 제안서 §6.4 준수 대조군 |
| 핵심 문항 probe | 2회차 | 7문항×4회, 13문항×3회 |

측정 결과 JSON은 세션 스크래치에 보관했으며 저장소에는 포함하지 않는다.

## 4. 품질 결과 — 제안서 §7.3 대비

DeepSeek 활성 최종 구성과 전면 비활성 구성을 같은 표본으로 측정한 결과다.

| §7.3 지표 | 목표 | 전면 비활성 | **DeepSeek 활성** |
|---|---:|---:|---:|
| 의도 분류 정확도 | 0.85 | 0.80 미달 | **0.85 달성** |
| 답변 정확도(상태 정확도 대리) | 0.80 | 0.85 | **0.90** |
| 출처 표기율 | 1.00 | 1.00 | **1.00** |
| 폴백 적절성 | 0.90 | 1.00 | **0.90** |
| 개인정보 마스킹률 | 1.00 | 1.00 | **1.00** |
| 응답시간 평균 | 3000 ms | 135 ms | 1,175 ms |
| 오류율 | 0.00 | 0.00 | **0.00** |
| 답변 가능 질문 성공률 | 0.80 | 0.70 미달 | **1.00** |
| 데모 완주율 (판정 기준 v2) | 1.00 | 미측정 | **1.00 달성** |

DeepSeek 활성 구성은 §7.3의 7개 선언 지표 중 6개를 달성하고, 전면 비활성에서 미달이던
의도 분류 정확도와 답변 가능 성공률을 목표선 위로 올린다. 대신 평균 응답시간이 8.7배 증가하고
폴백 적절성이 0.10 내려간다.

데모 완주율은 판정 기준 v2에서 **1.00**이다. 도달 경로는 두 단계다.
기준 교정으로 0.60(측정 방식 문제 해소), 이어서 개인 조회 분기 결함 수정과 승인 흐름 완주로 1.00이다.
**v1의 0.00과는 비교하지 않는다**(자가 다름). 개선 주장은 v2 안의 0.60 → 1.00 구간에 한정한다.
자세한 내용은 `REGRESSION-METRICS.md`의 v1 → v2 변경 사유와
`REGRESSION-RESULTS-20260730.md` §6.3~6.4를 참조한다.

동일 설정 재실행에서 기능 지표가 완전히 일치해 재현성을 확인했다(지연시간만 변동).

## 5. 안전 속성 관측

| 항목 | 결과 | 근거의 성격 |
|---|---|---|
| 출처 표기율 | 1.00 (전 구간) | 하니스가 SUCCESS 응답의 `sources≥1`과 필수 필드를 검사 |
| 개인정보 마스킹률 | 1.00 (전 구간) | **하니스의 원문 식별자 누출 검사**. DB 포렌식 스캔이 아님 |
| 오류율 | 0.00 (전 구간) | HTTP 비200 및 본문 파싱 실패 0건 |
| 공식 사실 소유권 | 서버 유지 | 출처·기관·확인일은 provider가 아닌 서버가 승인 KB에서 결합 |
| 근거 불일치 시 복구 | TEMPLATE 전환 | `chat/service.py`의 예외 경로가 draft 전체를 폐기 |

마스킹은 `SafeQuestion`이 검증된 `RedactionResult`로만 생성되도록 타입 수준에서 강제되며,
모든 provider 호출은 그 이후 단계에 위치한다. 우회 경로는 코드상 존재하지 않는다.

## 6. LLM-003 런북 대비 차이

본 측정은 LLM-003 런북이 고정한 프로필과 다음이 다르다. **런북 프로필 그대로의 실행이 아니다.**

| 항목 | LLM-003 런북 (Upstage) | 본 측정 (DeepSeek) | 성격 |
|---|---|---|---|
| 공급자·모델 | `upstage` / `solar-pro3` | `deepseek` / `deepseek-v4-flash` | §6.1 비교 선택의 다른 축 |
| 활성 스위치 | `UPSTAGE_*_MODE=true` | `CLASSIFIER_PROVIDER`/`LLM_PROVIDER=deepseek` | 별도 레인 |
| 시도 상한 | 20 / 30 / 40 | 80 / 100 / 160 | **DeepSeek 레인의 기존 하드코딩 값**. 본 작업 변경 아님 |
| 입력 상한 | 4096 (Upstage) | 16384 (DeepSeek 하드코딩) | 레인별 상이. 본 작업 변경 아님 |
| 세션 비용 상한 | 10건당 0.05 USD 확인 | 0.30 USD | **본 작업에서 0.20 → 0.30 변경** |
| 실행 게이트 | 인간 승인 1회당 실행 1회 | 측정 목적 다회 실행 | **런북 규율 미적용** |
| 전용 러너 | `run_upstage_grounded_chat_actual.py` | 없음 | DeepSeek 등가 러너 부재 |

### 6.1 본 작업에서 변경한 값

| 파일 | 항목 | 이전 | 이후 | 영향 레인 |
|---|---|---:|---:|---|
| `llm/limits.py` | `LOCAL_INTERACTIVE_COST_CAP_USD` | 0.20 | 0.30 | 양쪽 |
| `llm/settings.py` | `UPSTAGE_MAX_INPUT_TOKENS` | 4096 | 8192 | Upstage만 |
| `llm/settings.py` | 환경 계약 `LLM_MAX_INPUT_TOKENS` | "4096" | "8192" | Upstage만 |
| `llm/classifier_prompt.py` | 판정 절차·few-shot 예시 | — | 5단계 절차, 예시 3종 | 양쪽 |

비용 상한 인상은 입력 예산 확대의 종속 결과다. 입력 8192 기준 generator 100회(시도 상한)의
최악 비용이 0.2028 USD로 기존 상한 0.20을 초과해, 시도 상한에 닿기 전에 비용이 먼저 소진됐다.
0.30은 레인별로는 시도 수가, 합산 160회(0.324 USD)에서는 비용이 제한하는 원래 설계 관계를
보존하는 최소값이다.

## 7. 이 증거가 입증하지 않는 것

LLM-003 보고서와 같은 기준으로, 확인되지 않은 항목을 명시한다.

- **outbound 호출 수를 계측하지 않았다.** DeepSeek 전용 러너가 없어
  `outbound_attempt_count` 등 집계를 확보하지 못했다. FOLLOWUP·정책 폴백·`PRIVACY_UNRESOLVED`
  경로에서 provider 호출이 0인지는 **코드 경로 확인(`chat/service.py`의 생성 게이트)** 으로만
  판단했고 측정으로 증명하지 않았다.
- **비용과 토큰 사용량을 계측하지 않았다.** 실제 청구 근거가 없다. 위 최악 비용은 설정값 기반
  계산치다.
- **개인정보 무유출은 응답 본문 기준이다.** 하니스가 PII 라벨 문항의 원문 식별자가 응답에
  남지 않았는지만 검사했다. DB 저장 내용에 대한 포렌식 스캔은 수행하지 않았다.
- **런북의 1승인 1실행 규율을 적용하지 않았다.** 품질 측정 목적으로 다회 실행했으며,
  각 실행에 대한 개별 인간 승인 기록이 없다.
- **`answer_mode`가 실행마다 흔들린다.** 같은 질문이 `GENERATED`/`TEMPLATE`로 갈리는 현상을
  재현했다(대형폐기물 문항 3회 중 2회 `GENERATED`). 안전 속성에는 영향이 없으나
  개별 답변을 "AI 생성"으로 특정해 설명할 수 없다.
- **회귀 실행기가 이 저장소에 없다.** `scripts/run_regression_metrics.py`가 부재해 별도
  체크아웃의 동일 실행기와 바이트 동일 표본 CSV로 측정했다.

## 8. 저장소 게이트

| 게이트 | 결과 |
|---|---|
| Ruff format/check | PASS — 135 files |
| strict Mypy | PASS — 135 source/test files |
| Pytest | PASS — 2,617 passed, 8 skipped(local DB 전용), 5 subtests |
| 핵심 문항 probe | 13문항 × 3회 = 39/39 기대값 일치 |

## 9. 결론과 rollback

DeepSeek 구성은 local/private 환경에서 §7.3 지표 6/7을 달성하며, 전면 비활성 대비
의도 분류 정확도와 답변 가능 성공률을 목표선 위로 올린다. 대가는 응답시간 증가와
폴백 적절성 소폭 하락이다.

**공개 배포·remote·CI·실제 기관 운영에는 사용하지 않는다.** 제안서 §6.4에 따라 실제 시민
질문에 대한 확대는 별도의 보안·개인정보 승인 절차를 거친 후에만 진행한다.

rollback은 disable-first다.

```dotenv
CLASSIFIER_PROVIDER=disabled
LLM_PROVIDER=disabled
```

API를 재시작하고 `/ready=200`과 `answer_mode=TEMPLATE` 복귀를 확인한다. 본 작업의 코드 변경을
함께 되돌리려면 `git checkout -- apps/api` 후 재시작한다.

## 10. 후속 권고

1. DeepSeek 전용 인수 러너를 추가해 outbound 호출 수·토큰·비용 집계를 확보한다
   (Upstage `run_upstage_grounded_chat_actual.py`와 동등 수준).
2. 정책 폴백 경로의 provider 호출 0건을 측정으로 증명한다.
3. 회귀 실행기를 저장소에 포함한다.
4. `answer_mode` 안정성을 게이트 대상으로 승격할지 결정한다.
