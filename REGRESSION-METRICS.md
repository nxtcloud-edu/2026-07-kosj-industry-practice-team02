# 회귀지표 — 제안서 7.3 품질 지표의 실행 가능한 정의

- 실행기: `scripts/run_regression_metrics.py`
- 기준선: `docs/test-reports/regression-metrics-baseline.json`
- 최초 기준선 커밋: `028053d` (`feat(chat): add bounded hybrid RAG conversation (#20)`), 2026-07-28
- 표본: `data/evaluation/sample_questions_20.csv` (T-01~T-20 정답 라벨) + 제안서 §7.5 데모 5문항
- Scope: local/private. 표본 기준이며 전체 민원 정확도로 일반화하지 않는다

제안서 §7.3은 7개 지표와 목표치를 선언했지만 측정 방법은 "수동 평가", "확인" 수준으로만
적혀 있다. 이 문서는 그 선언을 **매 빌드 실행 가능한 숫자**로 고정하고, 기준선 대비 하락을
종료코드로 잡는 게이트를 정의한다.

## 1. 지표 정의

| 지표 | 목표 | 방향 | 산식 | 제안서 근거 |
|---|---:|---|---|---|
| `intent_accuracy` | 0.85 | 높을수록 | 라벨 intent == 응답 `intent` 비율 (T-01~T-20) | §7.3 의도 분류 정확도 |
| `answer_status_accuracy` | 0.80 | 높을수록 | 라벨 상태 == 응답 `answer_status` 비율 | §7.3 답변 정확도 |
| `source_labeling_rate` | 1.00 | 높을수록 | `SUCCESS` 응답 중 `sources≥1` 이고 전 항목에 `source_id`·`last_verified_at`이 있는 비율 | §7.3 출처 표기율 100%, SER-003 |
| `fallback_appropriateness` | 0.90 | 높을수록 | 1 − (과소 폴백 + 과잉 폴백 + 사유 오분류) / 채점 대상 | §7.3 폴백 적절성, 양방향 채점 |
| `answerable_success_rate` | 0.80 | 높을수록 | `SUCCESS` 라벨 문항 중 실제 `SUCCESS` 비율 | §7.3 "답할 수 있는 질문을 회피한 과잉 폴백"의 FOLLOWUP 경로 |
| `pii_masking_rate` | 1.00 | 높을수록 | PII 라벨 문항의 원문 식별자가 응답 본문에 남지 않은 비율 | §7.3 개인정보 마스킹 100%, SER-002 |
| `latency_mean_ms` | 3000 | **낮을수록** | 성공 요청의 평균 왕복 시간 | §7.3 / PER-001 평균 3초 |
| `error_rate` | 0.00 | **낮을수록** | HTTP 비200 또는 본문 파싱 실패 비율 | §7.3 "오류율 병행 실측" |
| `demo_completion_rate` | 1.00 | 높을수록 | 제안서 §7.5 데모 5문항 중 전 판정 항목 통과 비율 | §7.5 무중단 완주 |

`latency_p95_ms`도 함께 기록한다. 제안서 §7.3이 "평균과 함께 p95, 오류율을 병행 실측"을
약속했기 때문이며, 목표치는 선언되지 않아 게이트 대상에서는 제외한다.

### `answerable_success_rate`를 따로 둔 이유

`fallback_appropriateness`는 `FALLBACK` 방향만 본다. 답할 수 있는 질문이 `FOLLOWUP`으로
빠지면 이 지표는 깨끗한 채로 남는다. 제안서 §7.3은 "답할 수 있는 질문을 회피한 과잉 폴백"도
실패로 집계한다고 못박았으므로, 회피가 지표에서 새지 않도록 별도 지표로 분리했다.
실제로 최초 측정에서 이 지표만 T-02·T-07·T-08의 회피를 잡아냈다.

### 데모 판정 항목

각 데모 문항은 제안서 §7.5 "증명하는 것"을 판정 항목으로 분해한다. 하나라도 실패하면 그
문항은 미통과다.

**판정 기준 버전: v2 (2026-07-30)**

| 데모 | 판정 항목 |
|---|---|
| D-1 전입신고 기한 | `answer_status=SUCCESS`, 본문에 `14일`, 출처+확인일 |
| D-2 아름동 대형폐기물 | `SUCCESS`, 본문에 `시설관리공단`, 출처+확인일, **지역 반영**(요청에 `selected_region=아름동`을 실어 호출) |
| D-3 이사 관련 | `FOLLOWUP` |
| D-4 자동차세 | `FALLBACK` + `fallback.reason=PERSONAL_LOOKUP` |
| D-5 선순환 | `failed-questions.total ≥ 1` **그리고** `kb-candidates.total ≥ 1` |

### v1 → v2 변경 사유

| 항목 | v1 | v2 | 사유 |
|---|---|---|---|
| D-1 `deep_link` 존재 | 요구 | **제거** | 딥링크는 intent 기반 UI 상수(`apps/web/src/lib/labels.ts` `DEEP_LINK_BY_INTENT`)로 답변 카드에 렌더링된다. API 응답 필드가 아니므로 HTTP 클라이언트인 이 하니스가 볼 수 없다. **구현되어 있으나 계층이 다르다.** 검증 책임은 Web E2E로 이관한다 |
| D-2 지역 반영 | 질문만 전송 후 응답에서 지역 확인 | **`selected_region`을 실어 호출** | 실제 화면은 지역 드롭다운 선택 후 질문한다. 질문만 보내면 기관 카드가 붙지 않아 **구현이 아니라 호출 방식** 때문에 실패했다 |
| D-3 `related_question` 존재 | 요구 | **제거** | 관련 민원 한 줄 제안은 팀 논의 결과 **화면 복잡도를 이유로 범위에서 제외**했다. 없는 기능을 계속 감점하지 않는다 |

**v1과 v2의 `demo_completion_rate`는 비교하지 않는다.** 판정 항목이 다르므로 서로 다른 계열이다.
표본 20문항 기반 8개 지표는 변경되지 않았으므로 v1 실행과 직접 비교할 수 있다.

## 2. 실행

```powershell
$env:SEJONG_BASELINE_COMMIT = (git rev-parse --short HEAD)
$env:SEJONG_PROVIDER_MODES  = "classifier=false,grounded=false"

apps/api/.venv/Scripts/python.exe -B scripts/run_regression_metrics.py `
  --baseline docs/test-reports/regression-metrics-baseline.json `
  --fail-on-regression
```

전제: 로컬 DB + API(`:8000`) + 웹(`:3000`)이 떠 있고 `/ready=200`. 질문은 브라우저와 동일하게
웹 오리진의 `POST /api/v1/chat`으로 나간다. 관리자 큐는 `X-Demo-Actor-Id`/`X-Demo-Role`
헤더로 조회한다.

주요 인자:

| 인자 | 용도 |
|---|---|
| `--origin` | 기본 `http://127.0.0.1:3000`. API 직접 측정 시 `:8000` |
| `--baseline` | 비교 대상 기준선 JSON |
| `--write-baseline` | 현재 측정을 새 기준선으로 저장 |
| `--json-out` | 실행 결과 전체를 JSON으로 보관 |
| `--fail-on-regression` | 기준선 대비 하락이 있으면 종료코드 1 |

종료코드: `0` 정상 · `1` 회귀 감지 · `2` 스택 미기동 등 측정 불가.

**질문·답변 본문은 출력하지 않는다.** 라벨, 계약 enum, 카운트, 소요시간만 남는다.

## 3. 게이트 규칙

- **회귀 판정은 목표 달성 여부와 별개다.** 목표에 미달한 지표라도 기준선보다 더 떨어지면
  회귀로 잡는다. 반대로 목표를 넘겼어도 기준선보다 낮아지면 회귀다. 개선을 반영하려면
  `--write-baseline`으로 기준선을 갱신한다.
- **프로바이더 모드가 다르면 게이트를 적용하지 않는다.** 기준선의 `provider_modes`와 현재
  실행이 다르면 `BASELINE_MODE_MISMATCH`를 출력하고 드리프트를 참고값으로만 표시한다.
  grounded 모드는 프로바이더 왕복이 붙어 지연시간이 구조적으로 커지므로, 이를 코드 회귀로
  오판하지 않기 위한 장치다.
- **정본 기준선은 provider-disabled로 뜬다.** 결정적이고, 네트워크·비용이 들지 않으며,
  제안서 §6.4가 기술한 기본 상태이기 때문이다. grounded 실행 결과는 별도 파일로 보관한다.

## 4. 최초 기준선 (2026-07-28, `028053d`)

provider-disabled (`classifier=false,grounded=false`) 기준.

| 지표 | 측정 | 목표 | 판정 |
|---|---:|---:|---|
| `intent_accuracy` | 0.80 | 0.85 | **미달** |
| `answer_status_accuracy` | 0.85 | 0.80 | 달성 |
| `source_labeling_rate` | 1.00 | 1.00 | 달성 |
| `fallback_appropriateness` | 1.00 | 0.90 | 달성 |
| `answerable_success_rate` | 0.70 | 0.80 | **미달** |
| `pii_masking_rate` | 1.00 | 1.00 | 달성 |
| `latency_mean_ms` | 171.2 | 3000 | 달성 |
| `error_rate` | 0.00 | 0.00 | 달성 |
| `demo_completion_rate` | 0.00 | 1.00 | **미달** |

미통과 항목:

```
evaded_answerable  = [(T-02, FOLLOWUP), (T-07, FOLLOWUP), (T-08, FOLLOWUP)]
demo_failures      = [D-1, D-2, D-3, D-4, D-5]
```

데모 미통과 사유는 각각 `deep_link` 부재(D-1), 지역 미반영(D-2), `related_question` 부재(D-3),
`PERSONAL_LOOKUP` 미분기(D-4), 큐 0행(D-5)이다. 상세 근거는
[입찰제안서 §7.5 데모 시나리오 시뮬레이션](PROPOSAL-DEMO-SIMULATION-20260728.md) 참조.

grounded 모드(`classifier=true,grounded=true`) 실행은
`regression-metrics-20260728-grounded.json`에 보관했다. 기능 지표는 provider-disabled와
동일하고 `latency_mean_ms`만 171.2 → 670.2로 증가한다. 즉 **현재 결함은 프로바이더와
무관하다.**

## 5. 이 지표가 잡지 못하는 것

- **답변 사실 정확도.** 상태·출처·폴백 분류는 채점하지만 본문 내용의 사실성은 채점하지
  않는다. 제안서 §7.3의 "답변 정확도 80% — 수동 평가"는 사람이 계속 수행해야 한다.
  현재 `answer_status_accuracy`는 그 대리 지표일 뿐이다.
- **접근성과 반응형.** QUR-001(KWCAG 2.2), 390px·430px 확인은 범위 밖이다.
- **동시 처리.** PER-002는 이 하니스의 대상이 아니다.
- **마스킹 오탐.** `pii_masking_rate`는 "PII가 새지 않았는가"만 본다. 개인정보가 아닌
  행정 용어가 사람 이름으로 오탐되어 `PRIVACY_UNRESOLVED`로 빠지는 문제는 이 지표에
  잡히지 않고 `answerable_success_rate`와 `demo_completion_rate`에 간접적으로만 나타난다.
  전용 오탐 지표는 후속 과제다.
- **`answer_mode` 안정성.** grounded 모드에서 같은 질문의 `TEMPLATE`/`GENERATED`가 실행마다
  달라지는 문제는 결과 JSON에 기록되지만 게이트 대상이 아니다.
