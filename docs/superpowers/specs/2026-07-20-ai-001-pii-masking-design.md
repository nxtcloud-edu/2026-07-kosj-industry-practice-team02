# AI-001 개인정보 마스킹 코어 정식 명세

- 작성일: 2026-07-20
- 설계 결정 상태: **Approved** — 사용자 `PII 설계 승인` (2026-07-20T10:08:44+09:00)
- 정식 명세 상태: **Review pending**
- 구현 상태: **Not started**
- 관련 결정: D-017, D-041, ADR-0004
- 관련 작업: AI-001

## 1. 목적

시민 질문이 분류·검색·실패 질문 저장·합성 fixture용 외부 LLM 경계로 넘어가기 전에,
개인정보를 재현 가능하게 탐지하고 고정 토큰으로 치환한다. 안전한 마스킹 결과를 만들 수
없으면 텍스트를 반환하지 않는 fail-closed 코어를 제공한다.

이 명세의 구현은 원문을 DB·로그·예외·provider payload에 남기지 않는다는 기존 계약을
강화한다. 실제 시민 질문은 마스킹 성공 여부와 무관하게 DeepSeek에 전송하지 않는다.

## 2. 범위

### 포함

- Python 표준 라이브러리만 사용하는 순수 마스킹 함수
- 닫힌 개인정보 범주·미해결 사유·불변 결과 타입
- Unicode 정규화와 위험 제어문자 처리
- 결정론적 span 병합·고정 토큰 치환·결과 재검사
- 성공/미해결 결과의 명시적 저장·provider 안전 플래그
- 단위·속성·경계 테스트와 로그/예외 원문 비노출 검증

### 제외

- `/chat` 또는 다른 HTTP route 연결
- 분류기·검색기·구조화 답변·대화 문맥 token
- DB 쓰기 또는 migration
- DeepSeek adapter·실제 network 호출
- 시민 입력의 외부 전송 허용
- 공식·mock 데이터 또는 prompt 변경
- 새 프로덕션 의존성

## 3. 모듈 경계

초기 구현 위치는 다음으로 고정한다.

```text
apps/api/src/sejong_ai_api/privacy/redaction.py
apps/api/tests/privacy/test_redaction.py
```

`redaction.py`는 import 시 환경변수, 시간, DB, network, provider, logger를 읽지 않는다.
프로세스 전역의 가변 상태를 만들지 않으며 같은 입력은 언제나 같은 결과를 만든다. 구현
계획에서 단일 파일이 지나치게 커진다는 근거가 확인될 때만 비공개 helper를 같은
`privacy` 패키지 안에서 분리한다.

## 4. 공개할 내부 타입

이 타입은 API wire contract가 아니라 애플리케이션 내부 계약이다.

```python
class PiiCategory(str, Enum):
    NAME = "NAME"
    RESIDENT_REGISTRATION_NUMBER = "RESIDENT_REGISTRATION_NUMBER"
    PASSPORT_OR_LICENSE = "PASSPORT_OR_LICENSE"
    PHONE_NUMBER = "PHONE_NUMBER"
    EMAIL = "EMAIL"
    DETAILED_ADDRESS = "DETAILED_ADDRESS"
    FINANCIAL_ACCOUNT = "FINANCIAL_ACCOUNT"
    PAYMENT_CARD = "PAYMENT_CARD"
    AUTH_SECRET = "AUTH_SECRET"
    VEHICLE_PLATE = "VEHICLE_PLATE"
    CASE_REFERENCE = "CASE_REFERENCE"
    SENSITIVE_HEALTH_WELFARE = "SENSITIVE_HEALTH_WELFARE"
    PRECISE_LOCATION = "PRECISE_LOCATION"

class UnresolvedReason(str, Enum):
    INPUT_INVALID = "INPUT_INVALID"
    UNSAFE_UNICODE = "UNSAFE_UNICODE"
    AMBIGUOUS_PERSON_NAME = "AMBIGUOUS_PERSON_NAME"
    AMBIGUOUS_DETAILED_ADDRESS = "AMBIGUOUS_DETAILED_ADDRESS"
    RESIDUAL_HIGH_RISK_PATTERN = "RESIDUAL_HIGH_RISK_PATTERN"
```

- `RedactionFinding(category, start, end, replacement)`은 불변 값 객체다.
- finding에는 탐지한 원문 또는 hash를 넣지 않는다.
- `RedactionResult`는 `masked_text: str | None`, 불변 findings, 아래 두 안전 플래그와
  optional `unresolved_reason`을 가진다.
- 진입점은 `redact_question(raw_question: str) -> RedactionResult` 하나다.

안전 플래그는 다음 의미로 고정한다.

| 필드 | 의미 |
|---|---|
| `safe_for_failure_storage` | 이 텍스트가 기존 실패 질문 저장 정책을 통과할 수 있는 필요조건 |
| `safe_for_synthetic_provider` | 서버가 별도로 확인한 local/private 합성 fixture가 provider 경계로 갈 수 있는 필요조건 |

두 플래그는 그 자체로 저장 또는 외부 호출을 승인하지 않는다. 저장 대상 사유, OUT_OF_SCOPE,
FOLLOWUP, fixture allowlist, `DEEPSEEK_ENABLED`, 호출 한도 등 기존 상위 정책을 모두 추가로
통과해야 한다.

## 5. 입력과 정규화

1. 입력은 정확히 `str`이어야 한다.
2. 원문 길이는 1~1000자이며 공백만 있는 입력을 거부한다.
3. `CRLF`와 `CR`을 `LF`로 통일한 뒤 Unicode NFKC 정규화를 적용한다.
4. `U+200B`(ZERO WIDTH SPACE), `U+200C`(ZWNJ), `U+200D`(ZWJ),
   `U+2060`(WORD JOINER), `U+FEFF`(BOM/ZWNBSP)는 제거한 뒤 전체 탐지를 다시 수행한다.
5. `TAB`과 `LF`를 제외한 Unicode category `Cc`, 모든 `Cs`, 제거 allowlist 밖의 `Cf`,
   bidi class `LRE/RLE/LRO/RLO/PDF/LRI/RLI/FSI/PDI`가 있으면
   `UNSAFE_UNICODE`로 닫는다.
6. 정규화·제거 후 빈 문자열이거나 1000자를 넘으면 `INPUT_INVALID`로 닫는다.

성공 시 반환하는 `masked_text`는 정규화된 문자열이며 원문 객체를 그대로 반환하지 않는다.
유효하지 않은 입력도 원문을 포함한 예외를 던지지 않고 닫힌 결과를 반환한다.

## 6. 탐지·치환 규칙

### 탐지 순서

1. 주민등록번호·연락처·이메일·계정/카드·인증 비밀 등 high-signal identifier
2. 여권/면허·차량번호·민원 접수번호·정밀 위치
3. 문맥을 동반한 한국어 이름·상세주소·건강/복지 민감정보
4. 마스킹 결과의 잔여 high-risk pattern 재검사

정규식은 표준 라이브러리의 미리 컴파일된 bounded pattern만 사용하고 무제한 중첩·재귀적
패턴을 쓰지 않는다. 독립된 한국어 이름 추정이나 상세주소 가능성을 안전하게 치환할 수
없으면 추측하지 않고 각각 `AMBIGUOUS_PERSON_NAME`,
`AMBIGUOUS_DETAILED_ADDRESS`로 닫는다. 읍·면·동 수준의 지역 선택은 단독으로 개인정보로
간주하지 않는다.

### span 선택

- 모든 후보 span을 먼저 모은다.
- `start`와 `end`는 정규화·zero-width 제거가 끝난 치환 전 문자열의 Python code-point
  half-open offset이다.
- 범주 우선순위는 다음 total order로 고정하고, 같은 범주에서는 더 긴 span, 더 이른 위치
  순으로 선택한다:
  `RESIDENT_REGISTRATION_NUMBER` → `PAYMENT_CARD` → `FINANCIAL_ACCOUNT` →
  `AUTH_SECRET` → `PASSPORT_OR_LICENSE` → `PHONE_NUMBER` → `EMAIL` →
  `PRECISE_LOCATION` → `VEHICLE_PLATE` → `CASE_REFERENCE` → `DETAILED_ADDRESS` →
  `NAME` → `SENSITIVE_HEALTH_WELFARE`.
- 중복 또는 겹치는 span은 한 번만 선택한다.
- 뒤쪽 span부터 치환해 offset 변형을 피한다.
- 원문 값이 없는 고정 토큰만 사용한다.

초기 토큰은 `[이름]`, `[주민등록번호]`, `[여권·면허번호]`, `[전화번호]`, `[이메일]`,
`[상세주소]`, `[계좌번호]`, `[카드번호]`, `[인증정보]`, `[차량번호]`, `[접수번호]`,
`[건강·복지정보]`, `[정밀위치]`로 고정한다.

치환이 끝난 문자열을 다시 검사해 high-risk pattern이 남으면
`RESIDUAL_HIGH_RISK_PATTERN`으로 닫고 텍스트를 반환하지 않는다.

## 7. 결과와 fail-closed 동작

### 안전하게 마스킹된 경우

- `masked_text`: 정규화·치환된 문자열
- `safe_for_failure_storage`: `True`
- `safe_for_synthetic_provider`: `True`
- `unresolved_reason`: `None`

### 안전한 값을 만들지 못한 경우

- `masked_text`: `None`
- `safe_for_failure_storage`: `False`
- `safe_for_synthetic_provider`: `False`
- `unresolved_reason`: 닫힌 enum 값
- 허용: 질문 없는 interaction metadata event
- 금지: `failed_questions.masked_question` 및 질문 텍스트 row 생성, provider 호출

미해결 결과의 finding은 범주·위치·고정 토큰만 포함할 수 있고 원문 값은 포함하지 않는다.
예외·`repr`·로그에도 원문이 나타나지 않아야 한다.
`INPUT_INVALID`와 `UNSAFE_UNICODE` 결과의 findings는 빈 tuple이다. 모호성 또는 잔여 패턴
결과는 이미 확정된 value-free finding을 진단용으로 유지할 수 있지만 `masked_text`는 항상
`None`이다.

## 8. 후속 소비자 계약

향후 request-scoped application service만 원문을 이 함수에 전달한다. 함수 호출 뒤 분류기,
검색기, 실패 질문 writer, 합성 fixture provider adapter에는 `RedactionResult`에서 허용된
값만 전달한다.

- 미해결 결과: 개인정보 안전 폴백으로 전환하고 metadata-only event만 허용한다.
- 안전 결과: 상위 정책을 통과한 소비자만 `masked_text`를 사용한다.
- 실제 시민 질문: D-017에 따라 항상 DeepSeek 전송 금지다.
- local/private 합성 fixture: 마스킹 성공 외에도 서버 allowlist가 필요하다.

## 9. 테스트 전략과 인수 기준

구현은 TDD로 진행한다. core 슬라이스의 최소 검증 범위는 다음과 같다.

- 13개 개인정보 범주의 형식·띄어쓰기·구분자 변형
- 공공기관 대표번호, 수수료, 날짜, 읍·면·동, 공식 용어 등 false-positive 표본
- full-width, zero-width, bidi/control 문자 우회
- 겹침·중첩·동일 시작 위치 span의 결정론
- 결과·finding·예외·모듈 logger capture에서 raw sentinel 0건
- 같은 입력의 반복 결과 동일성과 입력 불변성
- 전역 가변 상태, I/O, 환경변수 접근, 새 의존성 0건
- 아래 frozen v1 합성 평가셋에서 PII 누락 0건
- 답변 성공률 80% 미달은 별도 측정하며 자동 규칙 완화 0건

### 고정 합성 평가셋

- 경로: `apps/api/tests/privacy/fixtures/pii_masking_cases.v1.json`
- 실제 개인정보·공식 데이터가 아닌 명백한 합성 값만 사용하고 file-level
  `fixture_version=1`, `synthetic_only=true`를 둔다.
- 13개 범주마다 positive 변형 3개 이상, Unicode 우회 10개 이상, overlap 5개 이상,
  공공 대표번호·날짜·수수료·읍면동 등 negative 20개 이상을 둔다.
- 각 case는 안정된 ID, synthetic input, expected outcome(`MASKED`, `SAFE_UNCHANGED`,
  `UNRESOLVED` 중 하나), expected category/token만 가진다. 실제 사람·계정과 연결되는
  metadata를 넣지 않는다.
- test fixture 작성은 인간-AI 책임 경계상 내부 테스트 세부다. 이 명세와 후속 실행계획의
  승인 범위 안에서 AI가 작성한다. production implementation 전에 RED tests와 함께 먼저
  commit하고 그 RED commit에서 v1을 동결한다.
- 동결 뒤 case 삭제·기대값 완화는 금지한다. 추가는 가능하되 fixture version과 test-suite
  version, 구현 노트를 함께 갱신한다. 누락 허용이나 범주 축소는 개인정보 계약 변경이므로
  인간 재승인이 필요하다.

provider/DB writer spy로 raw sentinel 미전달을 검증하는 것은 이 core를 소비하는 후속
application-service 슬라이스의 activation gate다. 이번 core 슬라이스는 provider/DB를 import하거나
호출하지 않으며, 그 spy 검증을 완료했다고 주장하지 않는다.

완료 조건은 다음 모두다.

1. 모든 닫힌 범주와 미해결 사유가 테스트된다.
2. 안전하지 않은 결과에는 반환 가능한 텍스트가 없다.
3. 원문이 결과·finding·예외·모듈 logger capture에 나타나지 않는다.
4. 실제 provider·DB·route·공식 데이터는 변경하거나 호출하지 않는다.
5. 관련 test/lint/typecheck/build 및 repository security gate가 통과한다.
6. API·DB·공식 데이터 버전은 변하지 않는다.

후속 consumer 연결의 별도 완료 조건에는 provider spy와 DB writer spy에서 raw sentinel 0건,
미해결 결과의 호출 0건이 반드시 포함된다.

## 10. 보안·운영 고려

- 마스커 결과나 finding에 원문/hash를 보관하지 않는다.
- 오류 코드는 닫힌 상수만 사용한다.
- 성능은 1000자 제한과 bounded pattern으로 제한한다.
- 향후 규칙 완화·범주 삭제·원문 저장·실제 시민 provider 허용은 개인정보 계약 변경이므로
  사람의 재승인과 별도 ADR이 필요하다.
- 마스킹 성공은 공식 근거 충족, 후보 적격, 저장 가능 사유를 대신하지 않는다.

## 11. 롤백과 호환성

이번 단계는 문서만 추가한다. 롤백은 D-041과 이 명세 및 동기화 문서를 함께 되돌리는 것이다.
후속 구현은 route·DB·provider 소비자에 연결하기 전까지 새 모듈과 테스트를 제거하는 것으로
롤백할 수 있다. 공개 API, DB schema, 데이터 version에는 호환성 영향이 없다.

## 12. 구현 전 gate

1. 사용자가 이 정식 명세를 검토·승인한다.
2. `superpowers:writing-plans`로 TDD 실행계획을 작성한다.
3. 사용자가 실행계획을 승인한다.
4. 그 뒤에만 제품 코드와 테스트를 작성한다.

A-030/Q-SEED-002와 A-021/Q-SEC-003은 별도 인간 결정으로 유지되며 이 명세 승인으로
해결되지 않는다.
