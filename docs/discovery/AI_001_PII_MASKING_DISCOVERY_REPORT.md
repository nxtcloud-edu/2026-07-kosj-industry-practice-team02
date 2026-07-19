# AI-001 PII 마스킹 독립 슬라이스 발견 감사

- Audit ID: `AI-001-PII-DESIGN`
- 감사 시각: 2026-07-20T04:29:49+09:00
- 기준 commit: `c08ee27`
- 상태: Discovery complete / Design approval pending / Product code unchanged

## 1. 목적과 범위

DATA-SEED-001 actual DB가 A-030/Q-SEED-002에서 Blocked인 동안에도 개인정보 마스킹
코어를 독립적으로 설계할 수 있는지 확인했다. 이번 감사는 구현·route 활성화·DB write·provider
호출을 포함하지 않는다.

검토 범위는 다음으로 제한했다.

- 시민 질문과 KB 후보 입력의 PII 탐지·마스킹 도메인 경계
- 원문이 DB·로그·provider로 흐르지 않는 실패 처리
- 기존 staging PII validator와 runtime API 코드의 재사용 가능성
- 새 production dependency 없이 구현 가능한지
- DATA-SEED blocker와 분리 가능한 설계·테스트 범위

## 2. 읽은 권위와 실제 파일

- `AGENTS.md`, `apps/api/AGENTS.md`
- `docs/00_SOURCE_OF_TRUTH.md`
- `TEAM_DECISIONS.md`, `PROJECT_PLAN.md`, `RFP_MATRIX.md`
- `PRIVACY_POLICY.md`, `APPROVAL_POLICY.md`, `KB_GUIDE.md`
- ADR-0004, ADR-0005, ADR-0006, ADR-0011
- `DECISION_LOG.md`, `TASKS.md`, `versions/manifest.json`
- `contracts/openapi-v1.yaml`
- `apps/api/src/sejong_ai_api/`, `apps/api/tests/`
- `scripts/data_staging_validation.py`와 관련 DATA-001 테스트
- `supabase/migrations/` 및 `supabase/tests/`의 `masked_question` lifecycle

`legacy/`는 사용하지 않았다.

## 3. 현재 구현과 권위 기준 차이

| 영역 | 권위 기준 | 실제 상태 | 판정 |
|---|---|---|---|
| raw HTTP logging | body/query/header/cookie/IP 미기록 | metadata-only middleware와 Uvicorn 필터 구현·검증됨 | 충족 |
| runtime PII masker | 외부 호출 전 보수적 마스킹 | API domain module 없음 | 미구현 |
| staging PII 검사 | 공식 데이터에 PII 0 | value-free detection-only regex와 테스트 존재 | 다른 목적의 구현 |
| 실패 질문 안전 저장 | 안전한 `masked_question`만 30일 | DB capability는 masked text가 없으면 event만 만들고 failure row는 만들지 않음 | fail-closed 기반 존재 |
| DeepSeek 전송 | 합성 allowlist+마스킹만 | provider adapter·route 없음, 기본 disabled | 안전하게 미구현 |
| KB 후보 PII 재검사 | 저장 전 재검사 | 공개 계약 설명만 있고 application service 없음 | 미구현 |
| 개인정보 평가셋 | 누락 0과 성공률 동시 측정 | DATA-001 안전 fixture는 있으나 runtime mask 결과 fixture 없음 | 미구현 |
| NLP dependency | 신규 dependency는 승인 필요 | FastAPI/Pydantic/httpx/psycopg만 존재 | 추가 없이 가능 |

## 4. 핵심 발견

### 4.1 staging validator를 runtime masker로 직접 재사용하면 안 된다

기존 `_PII_PATTERNS`는 공식 데이터 artifact에서 PII 가능성을 value-free issue로 거부하기 위한
검사다. replacement, 중첩 span, Unicode canonicalization, unresolved ambiguity, storage/provider
적격성을 표현하지 않는다. 또한 `scripts/`를 API domain이 import하면 실행 도구와 제품 계층이
결합된다.

패턴의 위험 사례와 합성 fixture 아이디어는 참고할 수 있지만 runtime API에는 별도의 typed
privacy module이 필요하다.

### 4.2 안전하게 마스킹할 수 없는 질문은 계약 변경 없이 text-free 처리할 수 있다

DB의 `record_interaction`은 supported fallback이라도 `masked_question`이 없으면 interaction
metadata만 저장하고 `failed_questions` row를 만들지 않는다. 따라서 불확실한 PII를 억지로
보존하거나 DB migration을 만들 필요가 없다.

권고 기본값은 다음과 같다.

```text
명확한 PII 전부 마스킹 성공
→ masked text 사용 가능

개인정보 가능성이 남거나 입력 canonicalization을 안전하게 완료할 수 없음
→ masked text 없음
→ provider 전송 금지
→ failure text/row 생성 금지, metadata event만 허용
```

### 4.3 실제 시민 DeepSeek 호출과 무관하게 masker는 필요하다

D-017 때문에 실제 시민 자유 입력은 마스킹 여부와 무관하게 DeepSeek로 보내지 않는다. 그러나
masker는 실패 질문 30일 보관, KB 후보 입력 재검사, 합성 provider fixture, privacy 평가에 필요하다.

### 4.4 DATA-SEED blocker와 설계·unit test는 분리 가능하다

PII module은 DB connection, ACTIVE KB, provider, route를 import하지 않는 pure domain component로
설계할 수 있다. 다만 현재 `TASKS.md`의 AI-001 전체는 DATA-SEED-001에 Blocked다. 구현을
시작하려면 승인된 설계와 계획에서 `AI-001A` 같은 준비 subtask를 명시하고, route/search/provider
activation은 계속 차단해야 한다.

## 5. 모호성 분류

### A / Blocker

- 새 항목 0건.
- 기존 A-030/Q-SEED-002는 전체 AI/READY activation을 계속 차단하지만 PII core의 설계 자체를
  막지는 않는다.

### B / High

- 새 항목 0건. Q-PRIV-002/D-019가 보수적 재현율 우선과 완화 재승인 경계를 이미 확정했다.

### C / Defaultable

- Python 표준 라이브러리 기반 deterministic rule engine을 사용한다.
- Unicode NFKC normalization과 zero-width/control 제거 뒤 검사하며, 안전하게 canonicalize할 수
  없는 입력은 unresolved로 처리한다.
- 확실한 식별자는 고정 한국어 placeholder로 치환하고, 불확실한 PII가 남으면 text를 저장·전송하지
  않는다.
- synthetic evaluation fixture는 실제 사람·연락처가 아닌 명시적 테스트 값만 사용한다.

### D / Internal

- span overlap은 위험도가 높은/긴 구간 우선으로 한 번만 치환한다.
- finding에는 category와 위치만 두고 원문 match value는 `repr`, exception, log에 넣지 않는다.
- API route, DB repository, provider를 import하지 않는 pure module과 unit test로 시작한다.
- 기존 staging validator와 패턴 implementation을 공유하지 않고 policy fixture coverage만 맞춘다.

`docs/11_AMBIGUITY_REGISTER.md`와 `DECISION_LOG.md`에는 새 인간 질문·확정 결정이 없어 행을
추가하지 않았다.

## 6. 비교한 접근

### 접근 A — 전용 deterministic rule engine (추천)

- 장점: dependency 0, 결과·우선순위·오류가 재현 가능하고 value-free test가 쉽다.
- 단점: 한국어 이름·상세주소의 보수적 heuristic과 fixture 유지가 필요하며 과잉 차단이 생길 수 있다.

### 접근 B — 한국어 NER/형태소 production dependency

- 장점: 이름·주소 문맥 분류를 확장할 가능성이 있다.
- 단점: 신규 production dependency 승인, 모델/사전 버전·성능·라이선스·다운로드·결정성 문제가
  생긴다. 0원 local-first와 현재 20개 KB 규모에 과하다.

### 접근 C — staging validator 패턴 직접 import

- 장점: 코드량이 적다.
- 단점: 제품/API가 `scripts/`에 결합되고 detection-only 동작을 masking으로 오인하게 된다.
  공공 연락처 allowlist 같은 staging 전용 예외가 시민 입력 경계로 새어 나갈 수 있다.

## 7. 추천 설계 초안 — 아직 승인 전

### public internal API

```text
redact_question(raw_question: str) -> RedactionResult

RedactionResult
- masked_text: str | None
- findings: immutable category/normalized-span metadata
- safe_for_failure_storage: bool
- safe_for_synthetic_provider: bool
- unresolved_reason: closed enum | None
```

원문과 match value는 result, exception, log에 포함하지 않는다. provider/storage용 text는 완전히
검증된 `masked_text` 하나뿐이다.

### 탐지 순서

1. strict type/length와 Unicode canonicalization
2. 주민번호, 전화, 이메일, 여권/면허, 계좌/카드, 인증·비밀번호, 차량, 민원 접수번호, GPS,
   건강·복지 민감정보 같은 high-signal identifier
3. context-bound 한국어 이름·상세주소
4. span merge와 고정 placeholder 치환
5. placeholder 결과를 다시 scan해 residual high-risk pattern이 있으면 fail closed

### 오류 처리

- 잘못된 타입·길이·control abuse·unresolved PII: value-free closed reason만 반환한다.
- provider와 DB adapter는 raw question을 받지 않고 `RedactionResult`의 safe flag와 masked text만
  소비한다.
- unresolved input은 정책 응답 경로에서 안전 폴백하고 text-free event만 허용한다.

### 테스트 경계

- 개인정보 정책의 모든 저장 금지 category별 positive/variant fixture
- 정상 민원 키워드·공식 기관 연락처·수수료 숫자 false-positive fixture
- 붙여쓰기, 공백/하이픈, Unicode full-width/zero-width, 중첩 identifier
- raw sentinel이 exception/log/result/provider spy/DB writer spy에 0건
- 동일 입력 동일 결과, 입력 object 불변, shared mutable state 0
- 개인정보 누락 0과 분류 성공률을 같은 synthetic evaluation set에서 별도 집계

## 8. 범위 밖

- chat route, classifier, retriever, grounding, context token
- DB write와 30일 purge 실행
- DeepSeek/network 호출
- 실제 시민/실제 개인정보 fixture
- 새 production dependency
- Q-SEED-002, Q-SEC-003 해결 또는 public deployment

## 9. 다음 gate

사용자가 접근 A와 위 fail-closed 결과 계약을 승인하면 정식 design spec을 작성·자체 검토·commit한
뒤, 별도 implementation plan을 작성해 다시 승인받는다. 그전에는 제품 코드를 작성하지 않는다.
