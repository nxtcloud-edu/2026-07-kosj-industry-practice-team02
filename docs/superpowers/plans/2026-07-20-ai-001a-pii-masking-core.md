# AI-001A PII Masking Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 승인된 AI-001 명세대로 외부 I/O 없는 결정론적 개인정보 마스킹 코어와 동결된 합성 평가셋을 구현한다.

**Architecture:** `sejong_ai_api.privacy` 안의 순수 typed rule engine 하나가 입력 정규화, span 탐지·우선순위 병합, 고정 token 치환, 잔여 위험 재검사를 수행한다. route·DB·provider는 import하지 않으며, 안전한 결과를 만들 수 없으면 `masked_text=None`인 닫힌 결과만 반환한다. 전체 AI-001 activation은 DATA-SEED-001과 후속 consumer 계약에 계속 Blocked다.

**Tech Stack:** Python 3.12.13, 표준 라이브러리 `dataclasses`/`enum`/`re`/`unicodedata`, pytest 9.1.1, Ruff 0.15.21, mypy 2.3.0, uv 0.11.28

## Global Constraints

- 구현 기준 commit: 이 계획과 승인 기록을 포함하는 최종 documentation commit의 clean HEAD다.
  실행 시작 직전 SHA를 `$ExecutionBase = git rev-parse HEAD`로 고정해 구현 노트에 기록하고,
  모든 누적 diff gate는 그 SHA부터 현재 implementation worktree까지 검사한다.
- 사용자가 정식 명세를 `PII 명세 승인`으로 2026-07-20T10:22:13+09:00 승인했다.
- 이 계획 승인 전 제품 코드·테스트 fixture를 작성하지 않는다.
- 실행은 사용자가 `Q-PII-003=A`와 이 계획 승인을 함께 명시한 경우에만 Task 0부터 시작한다.
  B이면 이 계획을 실행하지 않고 signature·official-data lineage 설계로 되돌아간다.
- Task 0 documentation commit 뒤 `superpowers:using-git-worktrees`로 `codex/ai-001a-pii-core`
  격리 worktree를 만든다.
- 새 production/development dependency, network/provider 호출, DB 연결·migration·seed, route/OpenAPI 변경은 0건이어야 한다.
- 실제 시민 질문은 마스킹 여부와 무관하게 DeepSeek 전송 금지다.
- 원문 값/hash는 result/finding/exception/log에 넣지 않는다.
- 입력은 exact `str`, raw/normalized 길이 1~1000, NFKC와 승인된 Unicode 규칙을 따른다.
- unresolved 결과는 `masked_text=None`, 두 안전 플래그 false이며 metadata-only event 외 소비를 허용하지 않는다.
- `apps/api/tests/privacy/fixtures/pii_masking_cases.v1.json`은 production 구현 전 RED commit에서 동결한다.
- fixture v1 case 삭제·기대값 완화는 금지한다. 추가 시 fixture/test-suite version과 구현 노트를 함께 갱신한다.
- API package version을 `0.2.0`으로 올릴 때 `apps/api/uv.lock`의 local project version만 재생성하고 dependency/version/hash set은 바꾸지 않는다.
- API `2.0.1-draft`, DB `0.3.0-local`, official data `0.0.0-not-populated`, prompt set `0.0.2-deepseek-v4-flash-selected`는 불변이다.
- A-030/Q-SEED-002와 A-021/Q-SEC-003을 해결·우회하거나 D-040을 생성하지 않는다.

---

## 상태

Done — pure core, frozen/security 회귀, 전체 API/repository gate와 독립 재리뷰 완료

## 목표와 비목표

- 목표: typed PII core, frozen synthetic v1 fixture, TDD 단위·privacy·architecture·성능 gate를 구현한다.
- 목표: AI-001A를 독립적으로 GREEN으로 만들고 전체 AI-001은 Blocked 상태로 유지한다.
- 비목표: `/chat`, 분류·검색·응답, DB writer, DeepSeek adapter, 시민-visible privacy fallback, 공식 데이터, readiness.

## 사용자 가치와 인수 기준

- 개인정보가 명확하면 원문 값 없는 고정 token으로 결정론적으로 치환한다.
- 안전한 판정이 불가능하면 원문을 흘리지 않고 no-text 결과로 닫는다.
- 13개 범주마다 합성 positive 3개 이상, Unicode 10개 이상, overlap 5개 이상, negative 20개 이상을 검증한다.
- frozen v1에서 PII miss 0, unsafe 결과의 text 0, raw sentinel 노출 0을 달성한다.
- 실제 provider/DB/route 호출과 제품 데이터 변화는 0이다.
- API focused/full test, Ruff format/lint, mypy, root default/warm-offline gate가 통과한다.

## 권위 근거

- RFP/요구사항: P0-06, SER-001, SER-002; downstream task LOG-001
- source-of-truth: `docs/source-of-truth/PRIVACY_POLICY.md`, `TEAM_DECISIONS.md`, `PROJECT_PLAN.md`
- ADR/결정: ADR-0004, D-017, D-041, D-042
- 명세: `docs/superpowers/specs/2026-07-20-ai-001-pii-masking-design.md`
- 발견 감사: `docs/discovery/AI_001_PII_MASKING_DISCOVERY_REPORT.md`
- 계획 승인 노트: `docs/implementation-notes/IMP-20260720-004-ai-001a-pii-명세-승인과-tdd-실행계획.md`

## 현재 상태와 조사 결과

- API package는 `src/sejong_ai_api/{api,contracts,core,db}`만 있고 runtime privacy package가 없다.
- staging validator는 detection-only이며 API가 `scripts/`를 import하면 안 된다.
- `apps/api/pyproject.toml`의 승인 dependency는 그대로 유지할 수 있다.
- API test는 pytest, strict mypy, Ruff, AST architecture gate를 이미 사용한다.
- DB `record_interaction`의 metadata-only 경계는 후속 consumer가 사용할 수 있지만 이번 계획은 DB를 호출하지 않는다.
- `TASKS.md`의 전체 AI-001은 DATA-SEED-001 때문에 Blocked다. AI-001A만 별도 Review/Ready→In Progress→Done으로 추적한다.

## 파일 구조

### 새 파일

- `apps/api/src/sejong_ai_api/privacy/__init__.py`: 승인된 내부 privacy 타입과 진입점 export
- `apps/api/src/sejong_ai_api/privacy/redaction.py`: 유일한 runtime 정규화·탐지·치환 core
- `apps/api/tests/privacy/__init__.py`: privacy test package marker
- `apps/api/tests/privacy/fixtures/pii_masking_cases.v1.json`: 동결 합성 평가셋
- `apps/api/tests/privacy/test_redaction.py`: fixture contract, 타입, Unicode, pattern, overlap, no-leak, 성능 테스트
- Q-PII-003=A/계획 승인 preflight 시 새
  `docs/implementation-notes/IMP-20260720-005-q-pii-003-a와-ai-001a-계획-승인.md`
- 구현 완료 시 새 `docs/implementation-notes/IMP-20260720-006-ai-001a-pii-마스킹-코어-구현.md`

### 수정 파일

- `apps/api/tests/test_architecture.py`: privacy module import/I/O/dependency 금지 AST gate
- `apps/api/pyproject.toml`: package version `0.1.0→0.2.0`; dependency 배열 불변
- `apps/api/uv.lock`: local virtual project version `0.1.0→0.2.0`만 동기화; registry dependency/hash 불변
- `apps/api/src/sejong_ai_api/__init__.py`: package `__version__=0.2.0`
- `docs/08_TEST_STRATEGY.md`: frozen fixture와 core/consumer spy 경계
- `TASKS.md`: AI-001A 상태·증거, parent AI-001 Blocked 유지
- `CHANGELOG.md`, `versions/manifest.json`: 구현·test/docs version
- 이 계획: 실행 결과와 실제 명령 기록
- 구현 노트 INDEX

## 미지의 영역과 인터뷰

| ID | 영향 | 질문 | 상태 | 결정 |
|---|---|---|---|---|
| AI-001A-PLAN | code/test | 이 계획으로 core를 구현할 것인가 | Approved | Task 0 decision commit 뒤 isolated TDD 실행 |
| A-030/Q-SEED-002 | data/READY | official seed membership 보정 | Open/Blocked | AI-001A unit core만 분리, activation 금지 |
| A-031/Q-PII-002 | public behavior/API | unresolved PII 시민 응답·event reason | Open/Deferred | consumer slice 전 인간 결정; core blocker 아님 |
| A-032/Q-PII-003 | privacy/core | 공식 대표번호라고 주장된 phone-shaped value 처리 | Resolved / D-043 | A 확정: label을 신뢰하지 않고 항상 mask; 공식 연락처는 server-combined metadata/card |
| A-021/Q-SEC-003 | public deployment | privileged function posture | Open/Deferred | local-only; public release 금지 |

## 제안 설계

```text
raw_question (request scope only)
  → strict type/raw length
  → CRLF/CR→LF → NFKC → approved zero-width removal
  → unsafe category/bidi scan
  → immutable rule candidates
  → category total order / longer / earlier overlap selection
  → normalized high-risk span가 selected finding 하나에 완전히 포함되는지 검사
  → reverse fixed-token replacement
  → ambiguous name/address + residual rule re-scan
  ├─ safe: RedactionResult(masked_text, findings, true, true, None)
  └─ unresolved: RedactionResult(None, value-free findings, false, false, reason)
```

- public API/DB 변경: 없음.
- 보안: module import 시 env/time/logger/path/file/network/DB/provider 접근 0.
- 실패: 예외에 원문을 넣지 않고 닫힌 `UnresolvedReason`만 반환한다.
- 후속 경계: consumer가 붙을 때 provider/DB writer spy와 시민-visible response mapping을 별도 구현한다.

---

### Task 0: Materialize Q-PII-003=A and plan approval before code

**Files:**
- Modify: `docs/source-of-truth/TEAM_DECISIONS.md`
- Modify: `docs/source-of-truth/PROJECT_PLAN.md`
- Modify: `docs/source-of-truth/PRIVACY_POLICY.md`
- Modify: `docs/adr/0004-privacy-first-event-logging.md`
- Modify: `docs/superpowers/specs/2026-07-20-ai-001-pii-masking-design.md`
- Modify: `docs/decisions/DECISION_LOG.md`
- Modify: `docs/11_AMBIGUITY_REGISTER.md`
- Modify: `TASKS.md`
- Modify: `CHANGELOG.md`
- Modify: `versions/manifest.json`
- Modify: this plan
- Create: `docs/implementation-notes/IMP-20260720-005-q-pii-003-a와-ai-001a-계획-승인.md`
- Modify: `docs/implementation-notes/INDEX.md`

**Gate:** 사용자가 exact 의미로 `Q-PII-003: A`와 `계획 승인, 구현 시작`을 함께 답한 경우에만
실행한다. B 또는 plan 미승인이면 여기서 중단하며 제품 코드·fixture 0을 유지한다.

- [x] **Step 1: Record the semantic specification amendment and decision**

`D-043`에 시민 입력의 “공식” label을 신뢰하지 않고 모든 phone-shaped value를 마스킹하며,
공식 기관 연락처는 후속 서버 결합 KB metadata/card에서만 제공한다는 결정을 기록한다.
A-032/Q-PII-003을 Resolved로 바꾸고 spec의 “공공기관 대표번호 false-positive 표본”을
“대표전화 문의 문구는 false-positive 표본이지만 질문에 포함된 실제 phone-shaped value는
마스킹”으로 명시한다. plan 상태를 Approved, AI-001A를 Ready로 갱신한다.
같은 의미를 `TEAM_DECISIONS`, `PROJECT_PLAN`, `PRIVACY_POLICY`에 한 문장씩 동기화하고
ADR-0004에 D-043 addendum을 추가한다. 모든 source-of-truth version 표기와 `RFP_MATRIX` 참조를
검사하되 요구사항 상태가 바뀌지 않으면 `RFP_MATRIX` 내용은 변경하지 않는다. frozen fixture
계약에는 `expected_masked_text` exact oracle 필드를 추가해 부분·과잉 마스킹을 금지한다.

- [x] **Step 2: Synchronize lineage without touching product code**

- product spec `2.2.2→2.2.3`
- documentation `2.7.8→2.7.9`
- application/API package/test/DB/data/prompt/web/dependency axes unchanged
- `IMP-20260720-005`에 승인 문구·시각, semantic change, alternatives, rollback과 인간/AI 경계를 기록

- [x] **Step 3: Verify and commit the decision-only preflight**

```powershell
python -m json.tool versions/manifest.json > $null
python -B scripts/validate_codex_package.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
git diff --check
git diff --name-only -- apps/api contracts database supabase data
git status --short
git add docs TASKS.md CHANGELOG.md versions/manifest.json
git diff --cached --check
git commit -m "docs(ai): approve public-number masking plan"
$ExecutionBase = git rev-parse HEAD
```

Expected: 제품/fixture/API/DB/data diff 0, D-043 exactly 1, A-032 Resolved, 네 권위 문서와 spec의
phone/oracle 의미 일치, product spec `2.2.3`, docs `2.7.9`, preflight commit 성공. 이 clean
`$ExecutionBase`를 구현 누적 diff 기준으로 노트에 기록한 뒤에만 isolated worktree를 만든다.

- [x] **Step 4: Create the isolated worktree and persistent execution note**

`superpowers:using-git-worktrees` 절차로 방금 Task 0 commit에서 `codex/ai-001a-pii-core`를 만들고
그 worktree 안에서 다음 명령을 실행한다.

```powershell
python scripts/new_implementation_note.py --title "AI-001A PII 마스킹 코어 구현" --task-id "AI-001A" --type "implementation-security"
```

Expected generated path:
`docs/implementation-notes/IMP-20260720-006-ai-001a-pii-마스킹-코어-구현.md`.
다르면 중단해 INDEX/동시 작업 상태를 재감사한다. `apply_patch`로 note metadata에
`Execution base SHA` label, colon, backtick, `$ExecutionBase`의 exact 40-hex 값, backtick 순서인
한 줄을 추가하고 아래 형식 검사를 통과시킨다. 이 note는 Task 1~5 동안 누적 갱신하고 최종
commit에 포함한다.

```powershell
$ExecutionBase = git rev-parse HEAD
$baseEvidence = @(Select-String -LiteralPath 'docs/implementation-notes/IMP-20260720-006-ai-001a-pii-마스킹-코어-구현.md' -Pattern '^- Execution base SHA: `([0-9a-f]{40})`$')
if ($baseEvidence.Count -ne 1) { throw 'EXECUTION_BASE_EVIDENCE_INVALID' }
if ($baseEvidence[0].Matches[0].Groups[1].Value -ne $ExecutionBase) {
  throw 'EXECUTION_BASE_EVIDENCE_MISMATCH'
}
```

---

### Task 1: Freeze the v1 synthetic contract in a RED commit

**Files:**
- Create: `apps/api/tests/privacy/__init__.py`
- Create: `apps/api/tests/privacy/fixtures/pii_masking_cases.v1.json`
- Create: `apps/api/tests/privacy/test_redaction.py`

**Interfaces:**
- Consumes: approved 13 `PiiCategory`, 5 `UnresolvedReason`, fixed token names from the spec
- Produces: immutable v1 fixture contract and failing import of `redact_question`

- [x] **Step 1: Create the exact fixture schema and exhaustive case matrix**

각 JSON case는 다음 exact shape를 사용한다.

```json
{
  "fixture_version": 1,
  "synthetic_only": true,
  "cases": [
    {
      "id": "name-01",
      "input": "제 이름은 김가상입니다.",
      "outcome": "MASKED",
      "categories": ["NAME"],
      "tokens": ["[이름]"],
      "expected_masked_text": "제 이름은 [이름]입니다.",
      "unresolved_reason": null
    }
  ]
}
```

모든 case의 key set은 위 7개 key로 exact 고정한다. `MASKED`와 `SAFE_UNCHANGED`는
`expected_masked_text`에 정규화 후 완전한 기대 문자열을 직접 기록하고 `UNRESOLVED`는 `null`을
기록한다. `MASKED` 기대값은 표에 표시된 합성 민감 span **전체**만 고정 token으로 바꾼 값이다.
예를 들어 `name-01`은 `김가상입`이 아니라 `김가상`만 바뀐 위 문자열이어야 한다. 이 exact equality가
부분 마스킹과 과잉 마스킹을 모두 RED로 만든다.

아래 39개 category positive를 그대로 넣는다.

| Category | ID / synthetic input 3개 | token |
|---|---|---|
| NAME | `name-01` 제 이름은 김가상입니다. / `name-02` 신청인 성명 박테스트 / `name-03` 저는 이샘플이에요. | `[이름]` |
| RESIDENT_REGISTRATION_NUMBER | `rrn-01` 주민번호 000101-3000000 / `rrn-02` 주민등록번호는 000101 4000000 / `rrn-03` 0001013000000이 제 주민번호예요. | `[주민등록번호]` |
| PASSPORT_OR_LICENSE | `identity-01` 여권번호 M00000000 / `identity-02` 운전면허번호 11-00-000000-00 / `identity-03` 면허번호 서울 00-000000-00 | `[여권·면허번호]` |
| PHONE_NUMBER | `phone-01` 연락처 010-0000-0000 / `phone-02` 휴대폰 010 1111 0000 / `phone-03` 자택전화 044-000-0000 | `[전화번호]` |
| EMAIL | `email-01` 이메일 test.person@example.invalid / `email-02` 메일 qa+pii@example.invalid / `email-03` 연락 메일 MASKING@EXAMPLE.INVALID | `[이메일]` |
| DETAILED_ADDRESS | `address-01` 주소는 세종특별자치시 가상로 12 101동 202호 / `address-02` 사는 곳 세종시 테스트길 34-5 / `address-03` 상세주소: 조치원읍 샘플로 1 2층 | `[상세주소]` |
| FINANCIAL_ACCOUNT | `account-01` 계좌번호 000-0000-0000-00 / `account-02` 입금계좌 111111-00-000000 / `account-03` 통장 22 0000 000000 | `[계좌번호]` |
| PAYMENT_CARD | `card-01` 카드번호 0000-0000-0000-0000 / `card-02` 결제카드 1111 1111 1111 1111 / `card-03` 제 카드는 4242424242424242입니다. | `[카드번호]` |
| AUTH_SECRET | `auth-01` 인증번호 000000 / `auth-02` OTP: ABCD00 / `auth-03` 비밀번호 sample-secret | `[인증정보]` |
| VEHICLE_PLATE | `vehicle-01` 차량번호 00가0000 / `vehicle-02` 자동차 123나0000 / `vehicle-03` 번호판 12다 0000 | `[차량번호]` |
| CASE_REFERENCE | `case-01` 접수번호 SJ-2026-000000 / `case-02` 민원번호 2026-000000 / `case-03` 접수번호 TEST-000000 | `[접수번호]` |
| SENSITIVE_HEALTH_WELFARE | `sensitive-01` 저는 당뇨 진단을 받았습니다. / `sensitive-02` 장애등급 0급입니다. / `sensitive-03` 저는 기초생활수급자입니다. | `[건강·복지정보]` |
| PRECISE_LOCATION | `location-01` 현재 위치 36.500000, 127.250000 / `location-02` GPS: 36.5,127.25 / `location-03` 위도 36.5000 경도 127.2500 | `[정밀위치]` |

아래 10개 Unicode case를 넣는다.

| ID | JSON input | outcome / expected |
|---|---|---|
| unicode-01 | `주민번호 ０００１０１－３００００００` | MASKED / RRN token |
| unicode-02 | `연락처 010\u200b-0000-0000` | MASKED / PHONE token |
| unicode-03 | `메일 qa\u200c@example.invalid` | MASKED / EMAIL token |
| unicode-04 | `주소 \ufeff세종시 테스트길 34-5` | MASKED / ADDRESS token |
| unicode-05 | `질문\u202e000101-3000000` | UNRESOLVED / `UNSAFE_UNICODE` |
| unicode-06 | `질문\u2063000101-3000000` | UNRESOLVED / `UNSAFE_UNICODE` |
| unicode-07 | `질문\u0000000101-3000000` | UNRESOLVED / `UNSAFE_UNICODE` |
| unicode-08 | `질문\ud800` | UNRESOLVED / `UNSAFE_UNICODE` |
| unicode-09 | `제 이름은\r\n김가상입니다.` | MASKED / NAME token |
| unicode-10 | `메일 ＱＡ＠ＥＸＡＭＰＬＥ．ＩＮＶＡＬＩＤ` | MASKED / EMAIL token |

`unicode-05`~`unicode-08`은 `categories=[]`, `tokens=[]`이며 나머지 Unicode MASKED case는
표의 category 하나와 해당 고정 token 하나를 사용한다.

아래 overlap 5개를 넣는다. 기대 category는 total priority 결과만 적는다.

| ID | input | expected category/token |
|---|---|---|
| overlap-01 | `민원번호 000101-3000000` | RRN / `[주민등록번호]` |
| overlap-02 | `계좌번호 0000-0000-0000-0000` | PAYMENT_CARD / `[카드번호]` |
| overlap-03 | `연락처 전화번호 010-0000-0000` | PHONE_NUMBER / `[전화번호]` |
| overlap-04 | `주소 세종시 가상로 12가0000` | VEHICLE_PLATE / `[차량번호]` |
| overlap-05 | `비밀번호 qa-secret@example.invalid` | AUTH_SECRET / `[인증정보]` |

아래 20개 negative를 `SAFE_UNCHANGED`, 빈 category/token, null reason으로 넣는다.

```text
negative-01 수수료는 1,000원입니다.
negative-02 확인일은 2026-07-20입니다.
negative-03 행정복지센터 대표전화는 어디서 확인하나요?
negative-04 아름동을 선택했어요.
negative-05 전입신고는 어떻게 하나요?
negative-06 대형폐기물 수수료가 궁금해요.
negative-07 우편번호는 30100입니다.
negative-08 운영시간은 09:00~18:00입니다.
negative-09 KB-MOVE-01 문서를 확인해 주세요.
negative-10 https://www.gov.kr 안내를 봤어요.
negative-11 정부24에서 발급할 수 있나요?
negative-12 증명서 3통이 필요해요.
negative-13 지방세 일반 안내가 필요해요.
negative-14 보건소 운영시간이 궁금해요.
negative-15 장애인 주차구역 기준을 알려주세요.
negative-16 세율은 10%인가요?
negative-17 비밀번호는 어디에서 변경하나요?
negative-18 차량 등록 절차를 알려주세요.
negative-19 주소 변경 방법을 알려주세요.
negative-20 이름을 어디에 쓰나요?
```

#### Frozen v1 exact oracle

위 input matrix와 아래 oracle row를 ID로 1:1 결합해 JSON을 작성한다. 아래 값은 계산 예시가
아니라 그대로 복사해야 하는 승인 대상 test oracle이다. `expected_masked_text=null`은 결과 text가
없다는 뜻이며, JSON 배열·enum·token·reason도 exact다.

| ID | outcome | categories | tokens | expected_masked_text | unresolved_reason |
|---|---|---|---|---|---|
| name-01 | MASKED | `["NAME"]` | `["[이름]"]` | `제 이름은 [이름]입니다.` | null |
| name-02 | MASKED | `["NAME"]` | `["[이름]"]` | `신청인 성명 [이름]` | null |
| name-03 | MASKED | `["NAME"]` | `["[이름]"]` | `저는 [이름]이에요.` | null |
| rrn-01 | MASKED | `["RESIDENT_REGISTRATION_NUMBER"]` | `["[주민등록번호]"]` | `주민번호 [주민등록번호]` | null |
| rrn-02 | MASKED | `["RESIDENT_REGISTRATION_NUMBER"]` | `["[주민등록번호]"]` | `주민등록번호는 [주민등록번호]` | null |
| rrn-03 | MASKED | `["RESIDENT_REGISTRATION_NUMBER"]` | `["[주민등록번호]"]` | `[주민등록번호]이 제 주민번호예요.` | null |
| identity-01 | MASKED | `["PASSPORT_OR_LICENSE"]` | `["[여권·면허번호]"]` | `여권번호 [여권·면허번호]` | null |
| identity-02 | MASKED | `["PASSPORT_OR_LICENSE"]` | `["[여권·면허번호]"]` | `운전면허번호 [여권·면허번호]` | null |
| identity-03 | MASKED | `["PASSPORT_OR_LICENSE"]` | `["[여권·면허번호]"]` | `면허번호 [여권·면허번호]` | null |
| phone-01 | MASKED | `["PHONE_NUMBER"]` | `["[전화번호]"]` | `연락처 [전화번호]` | null |
| phone-02 | MASKED | `["PHONE_NUMBER"]` | `["[전화번호]"]` | `휴대폰 [전화번호]` | null |
| phone-03 | MASKED | `["PHONE_NUMBER"]` | `["[전화번호]"]` | `자택전화 [전화번호]` | null |
| email-01 | MASKED | `["EMAIL"]` | `["[이메일]"]` | `이메일 [이메일]` | null |
| email-02 | MASKED | `["EMAIL"]` | `["[이메일]"]` | `메일 [이메일]` | null |
| email-03 | MASKED | `["EMAIL"]` | `["[이메일]"]` | `연락 메일 [이메일]` | null |
| address-01 | MASKED | `["DETAILED_ADDRESS"]` | `["[상세주소]"]` | `주소는 [상세주소]` | null |
| address-02 | MASKED | `["DETAILED_ADDRESS"]` | `["[상세주소]"]` | `사는 곳 [상세주소]` | null |
| address-03 | MASKED | `["DETAILED_ADDRESS"]` | `["[상세주소]"]` | `상세주소: [상세주소]` | null |
| account-01 | MASKED | `["FINANCIAL_ACCOUNT"]` | `["[계좌번호]"]` | `계좌번호 [계좌번호]` | null |
| account-02 | MASKED | `["FINANCIAL_ACCOUNT"]` | `["[계좌번호]"]` | `입금계좌 [계좌번호]` | null |
| account-03 | MASKED | `["FINANCIAL_ACCOUNT"]` | `["[계좌번호]"]` | `통장 [계좌번호]` | null |
| card-01 | MASKED | `["PAYMENT_CARD"]` | `["[카드번호]"]` | `카드번호 [카드번호]` | null |
| card-02 | MASKED | `["PAYMENT_CARD"]` | `["[카드번호]"]` | `결제카드 [카드번호]` | null |
| card-03 | MASKED | `["PAYMENT_CARD"]` | `["[카드번호]"]` | `제 카드는 [카드번호]입니다.` | null |
| auth-01 | MASKED | `["AUTH_SECRET"]` | `["[인증정보]"]` | `인증번호 [인증정보]` | null |
| auth-02 | MASKED | `["AUTH_SECRET"]` | `["[인증정보]"]` | `OTP: [인증정보]` | null |
| auth-03 | MASKED | `["AUTH_SECRET"]` | `["[인증정보]"]` | `비밀번호 [인증정보]` | null |
| vehicle-01 | MASKED | `["VEHICLE_PLATE"]` | `["[차량번호]"]` | `차량번호 [차량번호]` | null |
| vehicle-02 | MASKED | `["VEHICLE_PLATE"]` | `["[차량번호]"]` | `자동차 [차량번호]` | null |
| vehicle-03 | MASKED | `["VEHICLE_PLATE"]` | `["[차량번호]"]` | `번호판 [차량번호]` | null |
| case-01 | MASKED | `["CASE_REFERENCE"]` | `["[접수번호]"]` | `접수번호 [접수번호]` | null |
| case-02 | MASKED | `["CASE_REFERENCE"]` | `["[접수번호]"]` | `민원번호 [접수번호]` | null |
| case-03 | MASKED | `["CASE_REFERENCE"]` | `["[접수번호]"]` | `접수번호 [접수번호]` | null |
| sensitive-01 | MASKED | `["SENSITIVE_HEALTH_WELFARE"]` | `["[건강·복지정보]"]` | `저는 [건강·복지정보]을 받았습니다.` | null |
| sensitive-02 | MASKED | `["SENSITIVE_HEALTH_WELFARE"]` | `["[건강·복지정보]"]` | `[건강·복지정보]입니다.` | null |
| sensitive-03 | MASKED | `["SENSITIVE_HEALTH_WELFARE"]` | `["[건강·복지정보]"]` | `저는 [건강·복지정보]입니다.` | null |
| location-01 | MASKED | `["PRECISE_LOCATION"]` | `["[정밀위치]"]` | `현재 위치 [정밀위치]` | null |
| location-02 | MASKED | `["PRECISE_LOCATION"]` | `["[정밀위치]"]` | `GPS: [정밀위치]` | null |
| location-03 | MASKED | `["PRECISE_LOCATION"]` | `["[정밀위치]"]` | `위도 [정밀위치]` | null |
| unicode-01 | MASKED | `["RESIDENT_REGISTRATION_NUMBER"]` | `["[주민등록번호]"]` | `주민번호 [주민등록번호]` | null |
| unicode-02 | MASKED | `["PHONE_NUMBER"]` | `["[전화번호]"]` | `연락처 [전화번호]` | null |
| unicode-03 | MASKED | `["EMAIL"]` | `["[이메일]"]` | `메일 [이메일]` | null |
| unicode-04 | MASKED | `["DETAILED_ADDRESS"]` | `["[상세주소]"]` | `주소 [상세주소]` | null |
| unicode-05 | UNRESOLVED | `[]` | `[]` | null | UNSAFE_UNICODE |
| unicode-06 | UNRESOLVED | `[]` | `[]` | null | UNSAFE_UNICODE |
| unicode-07 | UNRESOLVED | `[]` | `[]` | null | UNSAFE_UNICODE |
| unicode-08 | UNRESOLVED | `[]` | `[]` | null | UNSAFE_UNICODE |
| unicode-09 | MASKED | `["NAME"]` | `["[이름]"]` | `제 이름은\n[이름]입니다.` | null |
| unicode-10 | MASKED | `["EMAIL"]` | `["[이메일]"]` | `메일 [이메일]` | null |
| overlap-01 | MASKED | `["RESIDENT_REGISTRATION_NUMBER"]` | `["[주민등록번호]"]` | `민원번호 [주민등록번호]` | null |
| overlap-02 | MASKED | `["PAYMENT_CARD"]` | `["[카드번호]"]` | `계좌번호 [카드번호]` | null |
| overlap-03 | MASKED | `["PHONE_NUMBER"]` | `["[전화번호]"]` | `연락처 전화번호 [전화번호]` | null |
| overlap-04 | MASKED | `["VEHICLE_PLATE"]` | `["[차량번호]"]` | `주소 세종시 가상로 [차량번호]` | null |
| overlap-05 | MASKED | `["AUTH_SECRET"]` | `["[인증정보]"]` | `비밀번호 [인증정보]` | null |
| negative-01 | SAFE_UNCHANGED | `[]` | `[]` | `수수료는 1,000원입니다.` | null |
| negative-02 | SAFE_UNCHANGED | `[]` | `[]` | `확인일은 2026-07-20입니다.` | null |
| negative-03 | SAFE_UNCHANGED | `[]` | `[]` | `행정복지센터 대표전화는 어디서 확인하나요?` | null |
| negative-04 | SAFE_UNCHANGED | `[]` | `[]` | `아름동을 선택했어요.` | null |
| negative-05 | SAFE_UNCHANGED | `[]` | `[]` | `전입신고는 어떻게 하나요?` | null |
| negative-06 | SAFE_UNCHANGED | `[]` | `[]` | `대형폐기물 수수료가 궁금해요.` | null |
| negative-07 | SAFE_UNCHANGED | `[]` | `[]` | `우편번호는 30100입니다.` | null |
| negative-08 | SAFE_UNCHANGED | `[]` | `[]` | `운영시간은 09:00~18:00입니다.` | null |
| negative-09 | SAFE_UNCHANGED | `[]` | `[]` | `KB-MOVE-01 문서를 확인해 주세요.` | null |
| negative-10 | SAFE_UNCHANGED | `[]` | `[]` | `https://www.gov.kr 안내를 봤어요.` | null |
| negative-11 | SAFE_UNCHANGED | `[]` | `[]` | `정부24에서 발급할 수 있나요?` | null |
| negative-12 | SAFE_UNCHANGED | `[]` | `[]` | `증명서 3통이 필요해요.` | null |
| negative-13 | SAFE_UNCHANGED | `[]` | `[]` | `지방세 일반 안내가 필요해요.` | null |
| negative-14 | SAFE_UNCHANGED | `[]` | `[]` | `보건소 운영시간이 궁금해요.` | null |
| negative-15 | SAFE_UNCHANGED | `[]` | `[]` | `장애인 주차구역 기준을 알려주세요.` | null |
| negative-16 | SAFE_UNCHANGED | `[]` | `[]` | `세율은 10%인가요?` | null |
| negative-17 | SAFE_UNCHANGED | `[]` | `[]` | `비밀번호는 어디에서 변경하나요?` | null |
| negative-18 | SAFE_UNCHANGED | `[]` | `[]` | `차량 등록 절차를 알려주세요.` | null |
| negative-19 | SAFE_UNCHANGED | `[]` | `[]` | `주소 변경 방법을 알려주세요.` | null |
| negative-20 | SAFE_UNCHANGED | `[]` | `[]` | `이름을 어디에 쓰나요?` | null |

Task 1 RED commit 전에 fixture JSON을 이 74-row oracle과 대조하고, case object key order를
`id,input,outcome,categories,tokens,expected_masked_text,unresolved_reason`으로 고정한다. 구현 중
이 표를 바꾸지 않는다.

- [x] **Step 2: Write the fixture loader and failing public-contract tests**

`test_redaction.py`의 첫 구현은 아래 loader와 assertions를 포함한다.

```python
from __future__ import annotations

import json
import logging
import time
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import TypedDict, cast

import pytest

from sejong_ai_api.privacy import (
    PiiCategory,
    RedactionFinding,
    RedactionResult,
    UnresolvedReason,
    redact_question,
)

class FixtureCase(TypedDict):
    id: str
    input: str
    outcome: str
    categories: list[str]
    tokens: list[str]
    expected_masked_text: str | None
    unresolved_reason: str | None


class FixtureDocument(TypedDict):
    fixture_version: int
    synthetic_only: bool
    cases: list[FixtureCase]


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pii_masking_cases.v1.json"
CASES = cast(
    FixtureDocument,
    json.loads(FIXTURE_PATH.read_text(encoding="utf-8")),
)
EXPECTED_TOKENS = {
    "[이름]", "[주민등록번호]", "[여권·면허번호]", "[전화번호]", "[이메일]",
    "[상세주소]", "[계좌번호]", "[카드번호]", "[인증정보]", "[차량번호]",
    "[접수번호]", "[건강·복지정보]", "[정밀위치]",
}


def test_fixture_contract_is_frozen_synthetic_and_complete() -> None:
    assert CASES["fixture_version"] == 1
    assert CASES["synthetic_only"] is True
    cases = CASES["cases"]
    assert len(cases) == 74
    positive_prefixes = (
        "name", "rrn", "identity", "phone", "email", "address", "account",
        "card", "auth", "vehicle", "case", "sensitive", "location",
    )
    expected_ids = {
        *(f"{prefix}-{number:02d}" for prefix in positive_prefixes for number in range(1, 4)),
        *(f"unicode-{number:02d}" for number in range(1, 11)),
        *(f"overlap-{number:02d}" for number in range(1, 6)),
        *(f"negative-{number:02d}" for number in range(1, 21)),
    }
    assert {case["id"] for case in cases} == expected_ids
    assert [case["outcome"] for case in cases].count("MASKED") == 50
    assert [case["outcome"] for case in cases].count("SAFE_UNCHANGED") == 20
    assert [case["outcome"] for case in cases].count("UNRESOLVED") == 4
    exact_keys = {
        "id", "input", "outcome", "categories", "tokens",
        "expected_masked_text", "unresolved_reason",
    }
    for case in cases:
        assert set(case) == exact_keys
        assert case["outcome"] in {"MASKED", "SAFE_UNCHANGED", "UNRESOLVED"}
        assert set(case["categories"]) <= {category.value for category in PiiCategory}
        assert set(case["tokens"]) <= EXPECTED_TOKENS
        reason = case["unresolved_reason"]
        assert reason is None or reason in {item.value for item in UnresolvedReason}
        assert (case["outcome"] == "UNRESOLVED") is (reason is not None)
        assert (case["outcome"] == "UNRESOLVED") is (
            case["expected_masked_text"] is None
        )
    for prefix in positive_prefixes:
        assert sum(case["id"].startswith(f"{prefix}-") for case in cases) == 3


def _case_id(case: FixtureCase) -> str:
    return case["id"]


@pytest.mark.parametrize("case", CASES["cases"], ids=_case_id)
def test_frozen_v1_case(case: FixtureCase) -> None:
    raw = case["input"]
    assert type(raw) is str
    result = redact_question(raw)
    assert isinstance(result, RedactionResult)
    assert [finding.category.value for finding in result.findings] == case["categories"]
    assert result.masked_text == case["expected_masked_text"]
    if case["outcome"] == "SAFE_UNCHANGED":
        assert result.safe_for_failure_storage is True
        assert result.safe_for_synthetic_provider is True
        assert result.unresolved_reason is None
    elif case["outcome"] == "MASKED":
        assert result.masked_text is not None
        assert result.masked_text != raw
        assert all(token in result.masked_text for token in case["tokens"])
        assert result.safe_for_failure_storage is True
        assert result.safe_for_synthetic_provider is True
        assert result.unresolved_reason is None
    else:
        reason = case["unresolved_reason"]
        assert reason is not None
        assert result.masked_text is None
        assert result.safe_for_failure_storage is False
        assert result.safe_for_synthetic_provider is False
        assert result.unresolved_reason is UnresolvedReason(reason)
```

같은 파일에 enum exactness, frozen/slotted dataclass, strict invalid input, offset, deterministic,
raw sentinel, no-log, 1000-char performance tests를 각각 이름 있는 함수로 추가한다. 예외나 repr의
raw sentinel 검사는 다음 exact 형태를 사용한다.

```python
def test_raw_identifier_never_appears_in_value_objects_exception_or_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    sentinel = "unique.secret@example.invalid"
    with caplog.at_level(logging.DEBUG):
        result = redact_question(f"이메일 {sentinel}")
    assert sentinel not in repr(result)
    assert sentinel not in repr(result.findings)
    assert all(sentinel not in record.getMessage() for record in caplog.records)


def test_pathological_1000_character_inputs_finish_within_two_seconds() -> None:
    inputs = (
        ("0-" * 499) + "0x",
        ("가" * 970) + "아파트 999동 999호?",
        ("a." * 490) + "@invalid",
        ("저는 " * 200) + "가가가가라",
        ("면허번호 " * 100) + "00-00-000000-x",
    )
    assert all(len(raw) <= 1000 for raw in inputs)
    started = time.perf_counter()
    for raw in inputs:
        for _ in range(20):
            redact_question(raw)
    assert time.perf_counter() - started < 2.0
```

- [x] **Step 3: Run the focused test and verify RED**

Run:

```powershell
.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q -p no:cacheprovider tests/privacy/test_redaction.py
```

먼저 fixture만 독립 검증한다.

```powershell
.\.tools\uv\uv.exe run --directory apps/api --frozen python -c "import json,pathlib; p=pathlib.Path('tests/privacy/fixtures/pii_masking_cases.v1.json'); d=json.loads(p.read_text(encoding='utf-8')); assert d['fixture_version']==1 and d['synthetic_only'] is True and len(d['cases'])==74"
```

Expected: fixture parse command exit 0. 이어 focused pytest는 collection FAIL with
`ModuleNotFoundError: No module named 'sejong_ai_api.privacy'`.

- [x] **Step 4: Freeze the RED fixture on the isolated branch**

```powershell
git add apps/api/tests/privacy
git diff --cached --check
git commit -m "test(ai): freeze PII masking v1 contract"
```

Expected: one RED test/fixture commit on `codex/ai-001a-pii-core`; do not merge it alone to `main`.

---

### Task 2: Implement immutable types and Unicode normalization

**Files:**
- Create: `apps/api/src/sejong_ai_api/privacy/__init__.py`
- Create: `apps/api/src/sejong_ai_api/privacy/redaction.py`
- Modify: `apps/api/tests/privacy/test_redaction.py`

**Interfaces:**
- Consumes: fixture outcome vocabulary from Task 1
- Produces: `PiiCategory`, `UnresolvedReason`, `RedactionFinding`, `RedactionResult`, `redact_question(str)`

- [x] **Step 1: Add focused failing tests for enum/type/input semantics**

```python
def test_enum_values_are_closed_and_exact() -> None:
    assert [item.value for item in PiiCategory] == [
        "NAME", "RESIDENT_REGISTRATION_NUMBER", "PASSPORT_OR_LICENSE",
        "PHONE_NUMBER", "EMAIL", "DETAILED_ADDRESS", "FINANCIAL_ACCOUNT",
        "PAYMENT_CARD", "AUTH_SECRET", "VEHICLE_PLATE", "CASE_REFERENCE",
        "SENSITIVE_HEALTH_WELFARE", "PRECISE_LOCATION",
    ]


def test_value_objects_are_frozen_slotted_and_value_free() -> None:
    finding = RedactionFinding(PiiCategory.EMAIL, 3, 10, "[이메일]")
    result = RedactionResult("메일 [이메일]", (finding,), True, True, None)
    assert not hasattr(finding, "__dict__")
    assert not hasattr(result, "__dict__")
    assert not hasattr(finding, "matched_value")
    with pytest.raises(FrozenInstanceError):
        finding.start = 0  # type: ignore[misc]
    with pytest.raises(ValueError, match="^REDACTION_FINDING_INVALID$"):
        RedactionFinding(PiiCategory.EMAIL, 3, 10, "raw@example.invalid")
    with pytest.raises(ValueError, match="^REDACTION_RESULT_INVALID$"):
        RedactionResult("raw", (), False, True, None)
    assert [item.value for item in UnresolvedReason] == [
        "INPUT_INVALID", "UNSAFE_UNICODE", "AMBIGUOUS_PERSON_NAME",
        "AMBIGUOUS_DETAILED_ADDRESS", "RESIDUAL_HIGH_RISK_PATTERN",
    ]


@pytest.mark.parametrize("raw", [None, 1, b"question", "", " ", "x" * 1001])
def test_invalid_input_is_closed_without_text(raw: object) -> None:
    result = redact_question(raw)  # type: ignore[arg-type]
    assert result == RedactionResult(None, (), False, False, UnresolvedReason.INPUT_INVALID)


@pytest.mark.parametrize("raw", ["x\x00y", "x\u202ey", "x\u2063y", "x\ud800y"])
def test_unsafe_unicode_is_closed_without_findings(raw: str) -> None:
    result = redact_question(raw)
    assert result == RedactionResult(None, (), False, False, UnresolvedReason.UNSAFE_UNICODE)


@pytest.mark.parametrize("character", ["\u200b", "\u200c", "\u200d", "\u2060", "\ufeff"])
def test_approved_zero_width_characters_are_removed_before_detection(character: str) -> None:
    result = redact_question(f"일반{character}질문")
    assert result == RedactionResult("일반질문", (), True, True, None)


@pytest.mark.parametrize(
    "character",
    ["\u202a", "\u202b", "\u202c", "\u202d", "\u202e", "\u2066", "\u2067", "\u2068", "\u2069"],
)
def test_every_bidi_override_or_isolate_is_rejected(character: str) -> None:
    result = redact_question(f"질문{character}값")
    assert result.unresolved_reason is UnresolvedReason.UNSAFE_UNICODE
    assert result.masked_text is None
```

Run:

```powershell
.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q -p no:cacheprovider tests/privacy/test_redaction.py -k "enum_values or value_objects or invalid_input or unsafe_unicode or zero_width or bidi"
```

Expected: exit 1 during collection because `sejong_ai_api.privacy` symbols do not exist yet.

- [x] **Step 2: Implement the complete immutable type and normalization base**

`redaction.py` starts with the following complete public contract and normalization helper.

```python
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Final


class PiiCategory(str, Enum):  # noqa: UP042 - approved wire-independent value contract
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


class UnresolvedReason(str, Enum):  # noqa: UP042 - approved value contract
    INPUT_INVALID = "INPUT_INVALID"
    UNSAFE_UNICODE = "UNSAFE_UNICODE"
    AMBIGUOUS_PERSON_NAME = "AMBIGUOUS_PERSON_NAME"
    AMBIGUOUS_DETAILED_ADDRESS = "AMBIGUOUS_DETAILED_ADDRESS"
    RESIDUAL_HIGH_RISK_PATTERN = "RESIDUAL_HIGH_RISK_PATTERN"


def _replacement(category: PiiCategory) -> str:
    return {
        PiiCategory.RESIDENT_REGISTRATION_NUMBER: "[주민등록번호]",
        PiiCategory.PAYMENT_CARD: "[카드번호]",
        PiiCategory.FINANCIAL_ACCOUNT: "[계좌번호]",
        PiiCategory.AUTH_SECRET: "[인증정보]",
        PiiCategory.PASSPORT_OR_LICENSE: "[여권·면허번호]",
        PiiCategory.PHONE_NUMBER: "[전화번호]",
        PiiCategory.EMAIL: "[이메일]",
        PiiCategory.PRECISE_LOCATION: "[정밀위치]",
        PiiCategory.VEHICLE_PLATE: "[차량번호]",
        PiiCategory.CASE_REFERENCE: "[접수번호]",
        PiiCategory.DETAILED_ADDRESS: "[상세주소]",
        PiiCategory.NAME: "[이름]",
        PiiCategory.SENSITIVE_HEALTH_WELFARE: "[건강·복지정보]",
    }[category]


@dataclass(frozen=True, slots=True)
class RedactionFinding:
    category: PiiCategory
    start: int
    end: int
    replacement: str

    def __post_init__(self) -> None:
        if (
            type(self.category) is not PiiCategory
            or type(self.start) is not int
            or type(self.end) is not int
            or self.start < 0
            or self.end <= self.start
            or self.replacement != _replacement(self.category)
        ):
            raise ValueError("REDACTION_FINDING_INVALID")


@dataclass(frozen=True, slots=True)
class RedactionResult:
    masked_text: str | None
    findings: tuple[RedactionFinding, ...]
    safe_for_failure_storage: bool
    safe_for_synthetic_provider: bool
    unresolved_reason: UnresolvedReason | None

    def __post_init__(self) -> None:
        findings_are_valid = type(self.findings) is tuple and all(
            type(item) is RedactionFinding for item in self.findings
        )
        if not findings_are_valid:
            raise ValueError("REDACTION_RESULT_INVALID")
        if self.masked_text is None:
            if (
                self.safe_for_failure_storage is not False
                or self.safe_for_synthetic_provider is not False
                or type(self.unresolved_reason) is not UnresolvedReason
            ):
                raise ValueError("REDACTION_RESULT_INVALID")
            return
        if (
            type(self.masked_text) is not str
            or not self.masked_text
            or self.safe_for_failure_storage is not True
            or self.safe_for_synthetic_provider is not True
            or self.unresolved_reason is not None
        ):
            raise ValueError("REDACTION_RESULT_INVALID")


_MAX_QUESTION_LENGTH: Final = 1000
_REMOVED_FORMAT_CHARACTERS: Final = (
    "\u200b",
    "\u200c",
    "\u200d",
    "\u2060",
    "\ufeff",
)
_UNSAFE_BIDI_CLASSES: Final = frozenset(
    {"LRE", "RLE", "LRO", "RLO", "PDF", "LRI", "RLI", "FSI", "PDI"}
)


def _closed(
    reason: UnresolvedReason,
    findings: tuple[RedactionFinding, ...] = (),
) -> RedactionResult:
    return RedactionResult(None, findings, False, False, reason)


def _normalize(raw_question: object) -> tuple[str | None, UnresolvedReason | None]:
    if type(raw_question) is not str:
        return None, UnresolvedReason.INPUT_INVALID
    if not raw_question or len(raw_question) > _MAX_QUESTION_LENGTH or not raw_question.strip():
        return None, UnresolvedReason.INPUT_INVALID
    normalized = unicodedata.normalize(
        "NFKC",
        raw_question.replace("\r\n", "\n").replace("\r", "\n"),
    )
    for character in _REMOVED_FORMAT_CHARACTERS:
        normalized = normalized.replace(character, "")
    if not normalized or len(normalized) > _MAX_QUESTION_LENGTH or not normalized.strip():
        return None, UnresolvedReason.INPUT_INVALID
    for character in normalized:
        category = unicodedata.category(character)
        if category == "Cs":
            return None, UnresolvedReason.UNSAFE_UNICODE
        if category == "Cc" and character not in {"\t", "\n"}:
            return None, UnresolvedReason.UNSAFE_UNICODE
        if category == "Cf" or unicodedata.bidirectional(character) in _UNSAFE_BIDI_CLASSES:
            return None, UnresolvedReason.UNSAFE_UNICODE
    return normalized, None


def redact_question(raw_question: str) -> RedactionResult:
    normalized, reason = _normalize(raw_question)
    if reason is not None:
        return _closed(reason)
    assert normalized is not None
    return RedactionResult(normalized, (), True, True, None)
```

`privacy/__init__.py`는 다섯 symbol만 명시적으로 export한다.

```python
"""Pure fail-closed privacy boundary."""

from sejong_ai_api.privacy.redaction import (
    PiiCategory,
    RedactionFinding,
    RedactionResult,
    UnresolvedReason,
    redact_question,
)

__all__ = [
    "PiiCategory",
    "RedactionFinding",
    "RedactionResult",
    "UnresolvedReason",
    "redact_question",
]
```

- [x] **Step 3: Run normalization tests GREEN and full fixture still RED**

```powershell
.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q -p no:cacheprovider tests/privacy/test_redaction.py -k "enum_values or value_objects or invalid_input or unsafe_unicode or zero_width or bidi"
.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q -p no:cacheprovider tests/privacy/test_redaction.py
```

Expected: 첫 명령은 exit 0이고 선택된 enum/input/Unicode base test가 모두 PASS한다. 둘째 명령은
collection error 없이 exit 1이며 아직 구현하지 않은 `MASKED` identifier/context fixture가 exact
`expected_masked_text` 불일치로 FAIL한다. fixture 기대값을 완화하지 않는다.

- [x] **Step 4: Commit the independently reviewed normalization base**

```powershell
git add apps/api/src/sejong_ai_api/privacy apps/api/tests/privacy/test_redaction.py
git diff --cached --check
git commit -m "feat(ai): add fail-closed PII value contract"
```

---

### Task 3: Implement high-signal identifier rules and deterministic span selection

**Files:**
- Modify: `apps/api/src/sejong_ai_api/privacy/redaction.py`
- Modify: `apps/api/tests/privacy/test_redaction.py`

**Interfaces:**
- Consumes: normalized string and immutable result types from Task 2
- Produces: value-free findings for RRN, ID/license, phone, email, account, card, auth, vehicle, case reference

- [x] **Step 1: Add focused exact-replacement and offset tests**

```python
def test_exact_replacement_and_normalized_offsets() -> None:
    result = redact_question("연락처 010\u200b-0000-0000")
    assert result.masked_text == "연락처 [전화번호]"
    assert result.findings == (
        RedactionFinding(PiiCategory.PHONE_NUMBER, 4, 17, "[전화번호]"),
    )


def test_multiple_findings_are_returned_in_text_order() -> None:
    result = redact_question("메일 qa@example.invalid 전화 010-0000-0000")
    assert [item.category for item in result.findings] == [
        PiiCategory.EMAIL, PiiCategory.PHONE_NUMBER,
    ]
    assert result.masked_text == "메일 [이메일] 전화 [전화번호]"


EXPECTED_CATEGORY_PRIORITY = (
    PiiCategory.RESIDENT_REGISTRATION_NUMBER,
    PiiCategory.PAYMENT_CARD,
    PiiCategory.FINANCIAL_ACCOUNT,
    PiiCategory.AUTH_SECRET,
    PiiCategory.PASSPORT_OR_LICENSE,
    PiiCategory.PHONE_NUMBER,
    PiiCategory.EMAIL,
    PiiCategory.PRECISE_LOCATION,
    PiiCategory.VEHICLE_PLATE,
    PiiCategory.CASE_REFERENCE,
    PiiCategory.DETAILED_ADDRESS,
    PiiCategory.NAME,
    PiiCategory.SENSITIVE_HEALTH_WELFARE,
)
TOKEN_BY_CATEGORY = dict(zip(EXPECTED_CATEGORY_PRIORITY, (
    "[주민등록번호]", "[카드번호]", "[계좌번호]", "[인증정보]",
    "[여권·면허번호]", "[전화번호]", "[이메일]", "[정밀위치]", "[차량번호]",
    "[접수번호]", "[상세주소]", "[이름]", "[건강·복지정보]",
), strict=True))


@pytest.mark.parametrize(
    ("higher", "lower"),
    zip(
        EXPECTED_CATEGORY_PRIORITY[:-1],
        EXPECTED_CATEGORY_PRIORITY[1:],
        strict=True,
    ),
)
def test_every_adjacent_total_priority_pair_selects_higher(
    higher: PiiCategory,
    lower: PiiCategory,
) -> None:
    from sejong_ai_api.privacy.redaction import _select_findings

    candidates = (
        RedactionFinding(lower, 2, 10, TOKEN_BY_CATEGORY[lower]),
        RedactionFinding(higher, 2, 10, TOKEN_BY_CATEGORY[higher]),
    )
    assert _select_findings(candidates) == (candidates[1],)


def test_same_category_prefers_longer_then_earlier_overlap() -> None:
    from sejong_ai_api.privacy.redaction import _select_findings

    category = PiiCategory.EMAIL
    token = TOKEN_BY_CATEGORY[category]
    short = RedactionFinding(category, 2, 8, token)
    long = RedactionFinding(category, 2, 10, token)
    later_tie = RedactionFinding(category, 3, 11, token)
    assert _select_findings((short, long)) == (long,)
    assert _select_findings((later_tie, long)) == (long,)


@pytest.mark.parametrize(
    ("raw", "expected_text", "expected_category"),
    [
        ("연락처 070-1234-5678", "연락처 [전화번호]", PiiCategory.PHONE_NUMBER),
        ("연락처 010.1234.5678", "연락처 [전화번호]", PiiCategory.PHONE_NUMBER),
        (
            "면허번호 부산 12-34-567890-12",
            "면허번호 [여권·면허번호]",
            PiiCategory.PASSPORT_OR_LICENSE,
        ),
        ("비밀번호 !secret!", "비밀번호 [인증정보]", PiiCategory.AUTH_SECRET),
        (
            "비밀번호 sample-secret입니다.",
            "비밀번호 [인증정보]입니다.",
            PiiCategory.AUTH_SECRET,
        ),
        ("카드 3782-822463-10005", "카드 [카드번호]", PiiCategory.PAYMENT_CARD),
    ],
)
def test_identifier_separator_bypasses_are_not_fail_open(
    raw: str,
    expected_text: str,
    expected_category: PiiCategory,
) -> None:
    result = redact_question(raw)
    assert result.masked_text == expected_text
    assert [finding.category for finding in result.findings] == [expected_category]


def test_q_pii_003_a_masks_phone_even_when_input_calls_it_official() -> None:
    result = redact_question("세종시청 대표전화 044-000-0000")
    assert result.masked_text == "세종시청 대표전화 [전화번호]"
    assert [finding.category for finding in result.findings] == [
        PiiCategory.PHONE_NUMBER
    ]
```

Run:

```powershell
.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q -p no:cacheprovider tests/privacy/test_redaction.py -k "exact_replacement or multiple_findings or total_priority or same_category or identifier_separator or q_pii_003_a"
```

Expected: exit 1; exact replacement/multiple findings, selector contract, 6 identifier
separator/suffix bypass와 Q-PII-003=A policy가 아직 구현되지 않아 FAIL한다.

- [x] **Step 2: Add immutable rule definitions and total-order selection**

`redaction.py`에 `_Rule`, `_RULES`, `_replacement`, `_collect_findings`,
`_select_findings`, `_apply_findings`를 추가한다. rule regex는 모두 named `value` group을 사용한다.

```python
@dataclass(frozen=True, slots=True)
class _Rule:
    category: PiiCategory
    pattern: re.Pattern[str]


_CATEGORY_PRIORITY: Final = (
    PiiCategory.RESIDENT_REGISTRATION_NUMBER,
    PiiCategory.PAYMENT_CARD,
    PiiCategory.FINANCIAL_ACCOUNT,
    PiiCategory.AUTH_SECRET,
    PiiCategory.PASSPORT_OR_LICENSE,
    PiiCategory.PHONE_NUMBER,
    PiiCategory.EMAIL,
    PiiCategory.PRECISE_LOCATION,
    PiiCategory.VEHICLE_PLATE,
    PiiCategory.CASE_REFERENCE,
    PiiCategory.DETAILED_ADDRESS,
    PiiCategory.NAME,
    PiiCategory.SENSITIVE_HEALTH_WELFARE,
)
_RULES: Final = (
    _Rule(
        PiiCategory.RESIDENT_REGISTRATION_NUMBER,
        re.compile(r"(?<!\d)(?P<value>\d{6}\s*[- ]?\s*[1-8]\d{6})(?!\d)"),
    ),
    _Rule(
        PiiCategory.PAYMENT_CARD,
        re.compile(
            r"(?<!\d)(?P<value>(?:\d{4}(?:[- .]?\d{4}){3}|"
            r"\d{4}[- .]?\d{6}[- .]?\d{5}))(?!\d)"
        ),
    ),
    _Rule(
        PiiCategory.FINANCIAL_ACCOUNT,
        re.compile(
            r"(?:계좌(?:번호)?|입금계좌|통장)\s*[:：]?\s*"
            r"(?P<value>\d{2,6}(?:[- ]\d{2,6}){1,4})"
        ),
    ),
    _Rule(
        PiiCategory.AUTH_SECRET,
        re.compile(
            r"(?:비밀번호|인증번호|OTP|PIN)\s*[:：]?\s*(?!\[)"
            r"(?P<value>[A-Z0-9!#$%&()*+,\-./:;<=>?@\^_`{|}~]{3,63}"
            r"[A-Z0-9!#$%&()*+\-/:;<=>?@\^_`{|}~])"
            r"(?=$|[\s,.!?]|입니다|이에요|예요|이고|라고)",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        PiiCategory.PASSPORT_OR_LICENSE,
        re.compile(
            r"(?:여권번호|운전면허번호|면허번호)\s*[:：]?\s*"
            r"(?P<value>(?:[A-Z]\d{8}|(?:[가-힣]{2,4}\s*)?"
            r"\d{2}(?:-\d{2})?-\d{6}-\d{2}))",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        PiiCategory.PHONE_NUMBER,
        re.compile(
            r"(?<!\d)(?P<value>(?:01[016789]|070)(?:[- .]?\d{3,4})"
            r"[- .]?\d{4})(?!\d)"
        ),
    ),
    _Rule(
        PiiCategory.PHONE_NUMBER,
        re.compile(
            r"(?<!\d)(?P<value>0(?:2|[3-6][1-5])[- .]?\d{3,4}"
            r"[- .]?\d{4})(?!\d)"
        ),
    ),
    _Rule(
        PiiCategory.EMAIL,
        re.compile(
            r"(?<![\w.+-])(?P<value>[A-Z0-9._%+\-]+@[A-Z0-9.\-]+"
            r"\.[A-Z]{2,})(?![\w.-])",
            re.IGNORECASE,
        ),
    ),
    _Rule(
        PiiCategory.VEHICLE_PLATE,
        re.compile(r"(?<!\d)(?P<value>\d{2,3}[가-힣]\s?\d{4})(?!\d)"),
    ),
    _Rule(
        PiiCategory.CASE_REFERENCE,
        re.compile(
            r"(?:접수번호|민원번호)\s*[:：]?\s*"
            r"(?P<value>(?:[A-Z]+-)?\d{4}-\d{6}|[A-Z]+-\d{6}|\d{6}-\d{7})",
            re.IGNORECASE,
        ),
    ),
)


def _match_bounds(match: re.Match[str]) -> tuple[int, int]:
    if match.groupdict().get("value") is not None:
        return match.span("value")
    return match.start("value_lat"), match.end("value_lng")


def _collect_findings(text: str) -> tuple[RedactionFinding, ...]:
    findings: list[RedactionFinding] = []
    for rule in _RULES:
        for match in rule.pattern.finditer(text):
            start, end = _match_bounds(match)
            findings.append(
                RedactionFinding(rule.category, start, end, _replacement(rule.category))
            )
    return tuple(findings)


def _overlaps(left: RedactionFinding, right: RedactionFinding) -> bool:
    return left.start < right.end and right.start < left.end


def _select_findings(
    candidates: tuple[RedactionFinding, ...],
) -> tuple[RedactionFinding, ...]:
    ranked = sorted(
        candidates,
        key=lambda item: (
            _CATEGORY_PRIORITY.index(item.category),
            -(item.end - item.start),
            item.start,
        ),
    )
    selected: list[RedactionFinding] = []
    for candidate in ranked:
        if not any(_overlaps(candidate, existing) for existing in selected):
            selected.append(candidate)
    return tuple(
        sorted(
            selected,
            key=lambda item: (
                item.start,
                item.end,
                _CATEGORY_PRIORITY.index(item.category),
            ),
        )
    )


def _apply_findings(text: str, findings: tuple[RedactionFinding, ...]) -> str:
    masked = text
    for finding in reversed(findings):
        masked = masked[:finding.start] + finding.replacement + masked[finding.end:]
    return masked
```

Task 2의 `_replacement` dict를 module global로 올리지 않는다. 함수-local literal은 호출 후
공유되지 않으므로 global mutable state가 아니다. span 선택은 category priority index, negative
length, start 순으로 후보를 정렬하고 기존 선택 span과 겹치지 않는 것만 고른다. 반환 findings는
`(start, end, category priority)` 순으로 재정렬한다. 치환은 findings 역순으로 수행한다.

Q-PII-003=A가 plan 승인과 함께 확정될 때만 공식 연락처라는 사용자 입력 label을 신뢰하지
않고 phone-shaped value를 항상 마스킹한다. negative fixture는 실제 번호가 아닌 공식 연락처
안내 문구를 사용한다. B가 선택되면 이 계획을 구현하지 않고 함수 signature·공식 데이터
주입 경계를 다시 설계한다.

- [x] **Step 3: Wire identifier findings into `redact_question` and run identifier/overlap tests**

```python
def redact_question(raw_question: str) -> RedactionResult:
    normalized, reason = _normalize(raw_question)
    if reason is not None:
        return _closed(reason)
    assert normalized is not None
    findings = _select_findings(_collect_findings(normalized))
    masked = _apply_findings(normalized, findings)
    return RedactionResult(masked, findings, True, True, None)
```

Run the exact Task 3 subset:

```powershell
$caseIds = @(
  'rrn-01','rrn-02','rrn-03','identity-01','identity-02','identity-03',
  'phone-01','phone-02','phone-03','email-01','email-02','email-03',
  'account-01','account-02','account-03','card-01','card-02','card-03',
  'auth-01','auth-02','auth-03','vehicle-01','vehicle-02','vehicle-03',
  'case-01','case-02','case-03','overlap-01','overlap-02','overlap-03','overlap-05'
)
$nodes = $caseIds | ForEach-Object { "tests/privacy/test_redaction.py::test_frozen_v1_case[$_]" }
.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q -p no:cacheprovider @nodes
```

Expected: exit 0 and all 31 selected cases PASS. Then run the complete privacy file; Expected: exit 1,
with contextual name/address/health/location fixture cases still RED and no collection error.

```powershell
.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q -p no:cacheprovider tests/privacy/test_redaction.py
```

위 complete run 전에 Task 3 direct selector gate도 다시 실행한다.

```powershell
.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q -p no:cacheprovider tests/privacy/test_redaction.py -k "exact_replacement or multiple_findings or total_priority or same_category or identifier_separator or q_pii_003_a"
```

Expected: exit 0이고 12 adjacent priority pair, same-category longer/earlier tie와 6 identifier
separator/suffix bypass, Q-PII-003=A policy test가 모두 PASS한다.

- [x] **Step 4: Commit the high-signal rules**

```powershell
git add apps/api/src/sejong_ai_api/privacy/redaction.py apps/api/tests/privacy/test_redaction.py
git diff --cached --check
git commit -m "feat(ai): redact high-signal identifiers"
```

---

### Task 4: Add contextual rules, ambiguity and residual fail-closed checks

**Files:**
- Modify: `apps/api/src/sejong_ai_api/privacy/redaction.py`
- Modify: `apps/api/tests/privacy/test_redaction.py`

**Interfaces:**
- Consumes: deterministic identifier engine from Task 3
- Produces: all 13 categories, ambiguity reasons, residual re-scan, full frozen v1 GREEN

- [x] **Step 1: Add RED ambiguity/residual tests**

```python
@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        ("민원인은 가상씨라고 합니다.", UnresolvedReason.AMBIGUOUS_PERSON_NAME),
        ("샘플아파트 101동 202호", UnresolvedReason.AMBIGUOUS_DETAILED_ADDRESS),
    ],
)
def test_ambiguous_context_returns_no_text(raw: str, reason: UnresolvedReason) -> None:
    result = redact_question(raw)
    assert result.masked_text is None
    assert result.safe_for_failure_storage is False
    assert result.safe_for_synthetic_provider is False
    assert result.unresolved_reason is reason


def test_input_is_not_mutated_and_repeated_results_are_identical() -> None:
    raw = "제 이름은 김가상이고 주소는 세종시 테스트길 34-5입니다."
    first = redact_question(raw)
    second = redact_question(raw)
    assert raw == "제 이름은 김가상이고 주소는 세종시 테스트길 34-5입니다."
    assert first == second


def test_residual_unclassified_numeric_identifier_is_closed() -> None:
    for raw in (
        "식별번호 123456789012",
        "식별번호 12345678901234567890",
        "식별번호 1234-5678-9012-3456-7890",
    ):
        result = redact_question(raw)
        assert result.masked_text is None
        assert result.safe_for_failure_storage is False
        assert result.safe_for_synthetic_provider is False
        assert result.unresolved_reason is UnresolvedReason.RESIDUAL_HIGH_RISK_PATTERN


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        ("메일 홍길동@예시.한국", UnresolvedReason.RESIDUAL_HIGH_RISK_PATTERN),
        ("민원인은 김철수입니다.", UnresolvedReason.AMBIGUOUS_PERSON_NAME),
        ("주소 아름동 123번지 101호", UnresolvedReason.AMBIGUOUS_DETAILED_ADDRESS),
    ],
)
def test_explicit_but_unclassified_pii_context_is_closed(
    raw: str,
    reason: UnresolvedReason,
) -> None:
    result = redact_question(raw)
    assert result.masked_text is None
    assert result.safe_for_failure_storage is False
    assert result.safe_for_synthetic_provider is False
    assert result.unresolved_reason is reason


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        ("김철수입니다.", UnresolvedReason.AMBIGUOUS_PERSON_NAME),
        ("엄정화입니다.", UnresolvedReason.AMBIGUOUS_PERSON_NAME),
        ("류현진입니다.", UnresolvedReason.AMBIGUOUS_PERSON_NAME),
        ("제갈량입니다.", UnresolvedReason.AMBIGUOUS_PERSON_NAME),
        ("아름동 123번지", UnresolvedReason.AMBIGUOUS_DETAILED_ADDRESS),
        ("홍길동@예시.한국", UnresolvedReason.RESIDUAL_HIGH_RISK_PATTERN),
        ("메일 홍길동@예시.한국 [이메일]", UnresolvedReason.RESIDUAL_HIGH_RISK_PATTERN),
        (
            "메일 홍길동@예시.한국 test@example.invalid",
            UnresolvedReason.RESIDUAL_HIGH_RISK_PATTERN,
        ),
        ("메일 문의 홍길동@예시.한국", UnresolvedReason.RESIDUAL_HIGH_RISK_PATTERN),
        ("메일은 홍길동@예시.한국", UnresolvedReason.RESIDUAL_HIGH_RISK_PATTERN),
    ],
)
def test_independent_and_token_or_inquiry_suffix_pii_is_closed(
    raw: str,
    reason: UnresolvedReason,
) -> None:
    result = redact_question(raw)
    assert result.masked_text is None
    assert result.safe_for_failure_storage is False
    assert result.safe_for_synthetic_provider is False
    assert result.unresolved_reason is reason


@pytest.mark.parametrize(
    "raw",
    [
        "아름동입니다.",
        "전입신고입니다.",
        "이메일입니다.",
        "신청서입니다.",
        "민원인입니다.",
    ],
)
def test_standalone_admin_terms_are_not_person_names(raw: str) -> None:
    assert redact_question(raw) == RedactionResult(raw, (), True, True, None)


def test_masked_email_followed_by_ascii_public_term_stays_safe() -> None:
    result = redact_question("메일 test@example.invalid FAQ 확인")
    assert result.masked_text == "메일 [이메일] FAQ 확인"
    assert [finding.category for finding in result.findings] == [PiiCategory.EMAIL]


@pytest.mark.parametrize(
    ("raw", "expected_text", "expected_category"),
    [
        ("위치는 36.5,127.25", "위치는 [정밀위치]", PiiCategory.PRECISE_LOCATION),
        ("한누리대로 123 101동 202호", "[상세주소]", PiiCategory.DETAILED_ADDRESS),
        ("진단명 희귀가상증후군", "진단명 [건강·복지정보]", PiiCategory.SENSITIVE_HEALTH_WELFARE),
        ("복지대상 가상지원등급", "복지대상 [건강·복지정보]", PiiCategory.SENSITIVE_HEALTH_WELFARE),
    ],
)
def test_contextual_labeled_pii_bypasses_are_not_fail_open(
    raw: str,
    expected_text: str,
    expected_category: PiiCategory,
) -> None:
    result = redact_question(raw)
    assert result.masked_text == expected_text
    assert [finding.category for finding in result.findings] == [expected_category]


def test_fixed_tokens_are_not_reclassified_as_raw_pii() -> None:
    raw = "비밀번호 [인증정보] 진단명 [건강·복지정보]"
    result = redact_question(raw)
    assert result == RedactionResult(raw, (), True, True, None)
```

Run:

```powershell
.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q -p no:cacheprovider tests/privacy/test_redaction.py -k "ambiguous_context or residual_unclassified or explicit_but_unclassified or independent_and_token or contextual_labeled or fixed_tokens or standalone_admin or masked_email_followed"
```

Expected: exit 1; ambiguity/residual, 명시적 미분류 3개, 독립·token/inquiry suffix 10개와
4개 contextual 우회 test가 아직 구현되지 않아 FAIL한다. 다섯 standalone admin negative와
masked-email+FAQ regression은 PASS 상태를 유지한다.

- [x] **Step 2: Add the four contextual categories and ambiguity patterns**

`_RULES`에 total order에 맞춰 다음 exact rules를 넣는다.

```python
_Rule(PiiCategory.PRECISE_LOCATION, re.compile(
    r"(?:(?<![\d.])(?P<value>-?\d{1,2}\.\d+\s*,\s*-?\d{1,3}\.\d+)"
    r"(?![\d.])|(?:위도\s*(?P<value_lat>-?\d{1,2}(?:\.\d+)?)\s*"
    r"경도\s*(?P<value_lng>-?\d{1,3}(?:\.\d+)?)))",
    re.IGNORECASE,
)),
_Rule(PiiCategory.DETAILED_ADDRESS, re.compile(
    r"(?:(?:주소(?:는)?|사는\s*곳|거주지|상세주소)\s*[:：]?\s*)?"
    r"(?P<value>(?:(?:세종특별자치시|세종시)\s*)?(?:[가-힣]+(?:읍|면|동)\s+)?"
    r"[가-힣0-9]+(?:대로|로|길)\s+\d+(?:-\d+)?"
    r"(?:\s+\d+동\s+\d+호|\s+\d+층)?)"
)),
_Rule(PiiCategory.NAME, re.compile(
    r"(?:이름(?:은|이)?|성명|신청인\s*성명|신청인(?!\s*성명))"
    r"\s*[:：]?\s*"
    r"(?P<value>[가-힣]{2,4})(?=입니다|이에요|예요|이고|라고|[\s,.!?]|$)"
)),
_Rule(PiiCategory.NAME, re.compile(
    r"저는\s*(?P<value>[가-힣]{2,4})(?=입니다|이에요|예요|이고|라고)"
)),
_Rule(PiiCategory.SENSITIVE_HEALTH_WELFARE, re.compile(
    r"(?P<value>(?:당뇨|암|고혈압|우울증)\s*(?:진단|치료|환자)|"
    r"장애등급\s*\d+급|기초생활수급자)"
)),
_Rule(PiiCategory.SENSITIVE_HEALTH_WELFARE, re.compile(
    r"(?:진단명|복지대상)\s*[:：]?\s*(?!\[)(?P<value>[^\s,.!?]{2,40})"
)),
```

PRECISE_LOCATION의 두 대안은 named group이 달라 `_collect_findings`가 `value`, 또는
`value_lat` 시작부터 `value_lng` 끝까지 하나의 span으로 계산하도록 구현한다.

```python
_AMBIGUOUS_NAME = re.compile(
    r"(?:(?<![가-힣])(?P<value>[가-힣]{2,4})(?:씨|님)"
    r"(?=이라고|라고|입니다|이에요|예요|[\s,.!?]|$)|"
    r"(?:민원인|신청인)(?:은|는)\s*(?P<labeled_value>[가-힣]{2,4})"
    r"(?=입니다|이에요|예요|[\s,.!?]|$)|"
    r"(?<![가-힣])(?P<standalone_value>[가-힣]{3})"
    r"(?=입니다(?:[\s,.!?]|$)|이에요(?:[\s,.!?]|$)|예요(?:[\s,.!?]|$)))"
)
_SAFE_STANDALONE_NAME_TERMS = frozenset({"이메일", "신청서", "민원인"})
_AMBIGUOUS_ADDRESS = re.compile(
    r"(?P<value>(?:[가-힣0-9]+(?:아파트|빌라)\s*\d+동\s*\d+호|"
    r"(?:[가-힣]+(?:읍|면|동)\s*)?\d+(?:-\d+)?번지(?:\s*\d+(?:동|호))*))"
)
_AMBIGUOUS_EXPLICIT_PII = re.compile(
    r"(?:주민(?:등록)?번호|여권번호|면허번호|연락처|전화번호|휴대폰|이메일|메일|"
    r"주소|거주지|계좌번호|카드번호|비밀번호|인증번호|OTP|PIN|차량번호|번호판|"
    r"접수번호|민원번호|진단명|복지대상|GPS|위치)"
    r"(?:은|는|이|가|을|를)?(?:\s*[:：]\s*|\s+)"
    r"(?!\[(?:이름|주민등록번호|여권·면허번호|전화번호|이메일|상세주소|계좌번호|"
    r"카드번호|인증정보|차량번호|접수번호|건강·복지정보|정밀위치)\]"
    r"(?=$|[\s,.!?]))"
    r"(?P<unclassified_value>(?=[^\n]*(?:@|\d|[A-Z]))[^\n]{2,})",
    re.IGNORECASE,
)
_HIGH_RISK_SPAN_PATTERNS = (
    re.compile(r"(?<!\d)(?:\d[- ./]?){9,}\d(?!\d)"),
    re.compile(r"(?<!\S)[^\s@]+@[^\s@,.!?]+(?=$|[\s,.!?])"),
    re.compile(
        r"(?<![\w.+-])[A-Z0-9._%+\-]+@[A-Z0-9.\-]+"
        r"\.[A-Z]{2,}(?![\w.-])",
        re.IGNORECASE,
    ),
)


def _has_uncovered_high_risk_span(
    text: str,
    findings: tuple[RedactionFinding, ...],
) -> bool:
    for pattern in _HIGH_RISK_SPAN_PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span()
            if not any(
                finding.start <= start and finding.end >= end for finding in findings
            ):
                return True
    return False


def _has_ambiguous_name(text: str) -> bool:
    for match in _AMBIGUOUS_NAME.finditer(text):
        standalone = match.groupdict().get("standalone_value")
        if standalone is not None and (
            standalone in _SAFE_STANDALONE_NAME_TERMS
            or standalone.endswith(("읍", "면", "동"))
        ):
            continue
        return True
    return False
```

- [x] **Step 3: Implement ambiguity after masking and residual re-scan**

```python
if _has_uncovered_high_risk_span(normalized, findings):
    return _closed(UnresolvedReason.RESIDUAL_HIGH_RISK_PATTERN, findings)
masked = _apply_findings(normalized, findings)
if _has_ambiguous_name(masked):
    return _closed(UnresolvedReason.AMBIGUOUS_PERSON_NAME, findings)
if _AMBIGUOUS_ADDRESS.search(masked):
    return _closed(UnresolvedReason.AMBIGUOUS_DETAILED_ADDRESS, findings)
if _AMBIGUOUS_EXPLICIT_PII.search(masked) or _select_findings(
    _collect_findings(masked)
) or _has_uncovered_high_risk_span(masked, ()):
    return _closed(UnresolvedReason.RESIDUAL_HIGH_RISK_PATTERN, findings)
return RedactionResult(masked, findings, True, True, None)
```

unresolved result의 repr에는 확정 finding의 category/offset/token만 있고 원문이 없어야 한다.
Context 없는 정확히 3음절+서술격 입력은 Q-PRIV-002=A의 재현율 우선 정책으로 ambiguity에 닫는다.
단, exact 안전 어휘 `이메일/신청서/민원인`과 `읍/면/동` suffix는 행정 용어·지역 false positive로
제외한다. 이 allowlist의 확대나 3음절 규칙 완화는 성공률 80% 미달 증거와 인간 재승인 없이는
금지한다.

- [x] **Step 4: Run the entire frozen v1 suite GREEN**

Run:

```powershell
.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q -p no:cacheprovider tests/privacy/test_redaction.py
```

Expected: all 74 exact-output parameterized fixture cases, 10 bypass regressions,
Q-PII-003=A public-number policy와 direct boundary tests PASS; PII miss 0; raw sentinel 0.
`MASKED` output는 fixture의 complete string과 같아야 하며
부분/과잉 마스킹은 PASS로 세지 않는다.
If a frozen expectation is wrong, stop and obtain privacy-contract approval instead of deleting or weakening it.

- [x] **Step 5: Commit all contextual/fail-closed behavior**

```powershell
git add apps/api/src/sejong_ai_api/privacy/redaction.py apps/api/tests/privacy/test_redaction.py
git diff --cached --check
git commit -m "feat(ai): close ambiguous PII inputs"
```

---

### Task 5: Enforce architecture, versions and full verification

**Files:**
- Modify: `apps/api/tests/test_architecture.py`
- Modify: `apps/api/pyproject.toml`
- Modify: `apps/api/uv.lock`
- Modify: `apps/api/src/sejong_ai_api/__init__.py`
- Modify: `docs/08_TEST_STRATEGY.md`
- Modify: `TASKS.md`
- Modify: `CHANGELOG.md`
- Modify: `versions/manifest.json`
- Modify: this plan
- Create: implementation note and update `docs/implementation-notes/INDEX.md`

**Interfaces:**
- Consumes: complete pure core from Task 4
- Produces: permanent no-I/O architecture gate, version lineage, reproducible completion evidence

- [x] **Step 1: Add RED architecture assertions**

`test_architecture.py`에 privacy source를 기존 boundary 목록에 추가하고 다음 exact test를 쓴다.

```python
PRIVACY_SOURCE = API_ROOT / "src" / "sejong_ai_api" / "privacy" / "redaction.py"
PRIVACY_ALLOWED_IMPORT_ROOTS = {
    "__future__", "dataclasses", "enum", "re", "typing", "unicodedata",
}


def test_privacy_module_is_stdlib_only_and_import_safe() -> None:
    tree = ast.parse(PRIVACY_SOURCE.read_text(encoding="utf-8"), filename=str(PRIVACY_SOURCE))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    assert roots <= PRIVACY_ALLOWED_IMPORT_ROOTS
    source = PRIVACY_SOURCE.read_text(encoding="utf-8")
    for forbidden in ("getenv", "environ", "logging", "open(", "httpx", "psycopg", "requests"):
        assert forbidden not in source
```

RED mutation을 exact하게 증명한다. `apply_patch`로 `redaction.py`의 `import re` 다음 줄에 임시
`import logging` 한 줄을 삽입하고 아래 명령을 실행한다.

```powershell
.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q -p no:cacheprovider tests/test_architecture.py -k privacy_module_is_stdlib_only_and_import_safe
```

Expected: exit 1이고 import-root 또는 forbidden-source assertion이 `logging` 때문에 FAIL한다.
즉시 `apply_patch`로 임시 `import logging` 한 줄만 제거하고 같은 명령을 다시 실행한다.
Expected: exit 0. `git diff -- apps/api/src/sejong_ai_api/privacy/redaction.py`로 임시 marker가 남지
않았음을 확인하며 marker는 commit하지 않는다.

- [x] **Step 2: Run focused architecture, format, lint and mypy**

```powershell
.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q -p no:cacheprovider tests/test_architecture.py tests/privacy/test_redaction.py
.\.tools\uv\uv.exe run --directory apps/api --frozen ruff format --check src tests
.\.tools\uv\uv.exe run --directory apps/api --frozen ruff check src tests
.\.tools\uv\uv.exe run --directory apps/api --frozen mypy src tests
```

Expected: all commands exit 0. If format check fails, run `ruff format` only on changed Python files, inspect the diff, then rerun all four.

- [x] **Step 3: Update package and repository versions without dependency drift**

- `apps/api/pyproject.toml project.version`: `0.1.0→0.2.0`
- `sejong_ai_api.__version__`: `0.1.0→0.2.0`
- `apps/api/uv.lock` local package `sejong-ai-api` version: `0.1.0→0.2.0`
- `versions/manifest.json application`: `0.2.0→0.3.0-pii-core`
- `test_suite`: `0.8.2-data-seed-filesystem-gate→0.9.0-pii-core`
- `documentation`: approved preflight value `2.7.9→2.7.10`
- web/API/shared contract/DB/official/mock/prompt/repo guidance: unchanged
- product spec: approved preflight value `2.2.3` unchanged during implementation

`pyproject.toml`과 `__version__`을 먼저 고친 뒤 아래 offline 명령으로 lock을 재생성한다.

```powershell
.\.tools\uv\uv.exe lock --directory apps/api --offline
```

Expected: exit 0이고 `apps/api/uv.lock`에서는 local virtual package version 한 줄만
`0.1.0→0.2.0`으로 바뀐다. registry dependency/version/hash set은 불변이다. 기존 architecture
dependency exact-set test가 그대로 PASS해야 하며 같은 test에 아래 package-version assertions를
추가한다.

```python
from sejong_ai_api import __version__

assert pyproject["project"]["version"] == "0.2.0"
assert __version__ == "0.2.0"
```

- [x] **Step 4: Run full API and repository gates**

```powershell
.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q -p no:cacheprovider
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1 -Offline
python -B scripts/validate_codex_package.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
git diff --check
```

Expected: full API and every declared default/warm-offline root gate PASS, package/secret/diff exit 0. DB gate와
Docker는 실행하지 않는다. 오래 걸리는 root `TEST-ROOT`를 조기 종료하지 않는다.

- [x] **Step 5: Perform privacy-specific evidence scans**

```powershell
$baseEvidence = @(Select-String -LiteralPath 'docs/implementation-notes/IMP-20260720-006-ai-001a-pii-마스킹-코어-구현.md' -Pattern '^- Execution base SHA: `([0-9a-f]{40})`$')
if ($baseEvidence.Count -ne 1) { throw 'EXECUTION_BASE_EVIDENCE_INVALID' }
$ExecutionBase = $baseEvidence[0].Matches[0].Groups[1].Value
$actualMergeBase = git merge-base HEAD main
if ($actualMergeBase -ne $ExecutionBase) { throw 'EXECUTION_BASE_DIVERGED' }
$protected = @(git diff --name-only $ExecutionBase -- contracts database supabase data)
if ($protected.Count -ne 0) { $protected; throw 'PROTECTED_PATH_DRIFT' }
$lockDiff = @(git diff --unified=0 $ExecutionBase -- apps/api/uv.lock)
$lockChanges = @($lockDiff | Where-Object {
  $_ -match '^[+-]' -and $_ -notmatch '^(---|\+\+\+)'
})
$expectedLockChanges = @('-version = "0.1.0"', '+version = "0.2.0"')
if (($lockChanges -join "`n") -ne ($expectedLockChanges -join "`n")) {
  $lockDiff
  throw 'UV_LOCK_DRIFT'
}
git diff $ExecutionBase -- apps/api/pyproject.toml apps/api/uv.lock
$forbidden = @(rg -n "DEEPSEEK|httpx|psycopg|requests|logging|getenv|environ" apps/api/src/sejong_ai_api/privacy)
if ($LASTEXITCODE -eq 0) { $forbidden; throw 'PRIVACY_FORBIDDEN_SOURCE_USE' }
if ($LASTEXITCODE -gt 1) { throw 'PRIVACY_SCAN_FAILED' }
```

Expected: branch 전체에서 protected contract/DB/data path 0, uv.lock local version line 외 diff 0,
architecture test의 dependency exact set unchanged, privacy source forbidden import/use 0. `pyproject.toml` diff는
project version 한 줄만 변경한다. String mentions in tests/docs do not count as runtime use.

- [x] **Step 6: Complete implementation note, self-review and independent code review**

Task 0에서 만든
`docs/implementation-notes/IMP-20260720-006-ai-001a-pii-마스킹-코어-구현.md`에
execution base SHA, RED/GREEN commit, fixture
74+direct test count, timings, version axes, no raw/network/DB/data, rollback,
Q-PII-002/Q-PII-003/A-030/A-021을 기록한다. `superpowers:requesting-code-review`로 spec compliance와
code quality 두 단계 독립 리뷰를 요청한다. Critical/Important를 모두 고치고 관련 gate를 재실행한다.

- [x] **Step 7: Final verification and commit**

`superpowers:verification-before-completion`을 읽고 최종 code HEAD에서 focused privacy, full API,
Ruff/mypy, root offline gate, secret/package/diff/status를 fresh rerun한다.

```powershell
git add apps/api docs TASKS.md CHANGELOG.md versions/manifest.json
git diff --cached --check
git commit -m "feat(ai): add fail-closed PII masking core"
git status --short
```

Expected: final commit succeeds and worktree is clean. 그 뒤에만 AI-001A Done을 보고한다.

---

## 테스트 계획

- 단위: 13 category, 5 unresolved reason, strict type/length, Unicode, offsets, overlap, determinism.
- 계약: internal dataclass/enum exactness; public OpenAPI/JSON Schema는 diff 0.
- 통합: 없음. consumer/provider/DB spy는 후속 slice.
- E2E: 없음. `/chat` 입력은 계속 비활성.
- 보안/PII: frozen 74 cases+direct tests, miss 0, unsafe text 0, raw repr/log 0, AST I/O/import 0.
- 접근성: UI 없음.
- 성능: worst-shaped 1000-char input 5종을 각 20회, 총 100회 local gate에서 2초 미만.

## 버전 변경 계획

- current plan stage: documentation `2.7.7→2.7.8`; 나머지 불변.
- Q-PII-003=A/plan-approval preflight: product spec `2.2.2→2.2.3`, docs `2.7.8→2.7.9`; 나머지 불변.
- implementation: application `0.2.0→0.3.0-pii-core`, API package `0.1.0→0.2.0`, tests `0.8.2→0.9.0-pii-core`, docs `2.7.9→2.7.10`.
- api wire/schema/data/prompts/web/dependencies: unchanged.

## 위험과 롤백

- 위험: 이름·주소 false positive. 조기 신호는 negative fixture failure와 답변 성공률 저하다.
- 위험: regex backtracking. 1000-char performance test와 bounded pattern review로 차단한다.
- 위험: frozen fixture를 구현에 맞춰 약화. RED commit SHA와 case count/ID 검사로 차단한다.
- 위험: consumer가 safe flag를 자동 승인으로 오해. core만 export하고 후속 Q-PII-002 gate를 유지한다.
- 롤백: consumer 연결 전이므로 privacy package/tests와 package version commit을 revert한다. DB/data/API rollback은 없다.

## 인간이 승인해야 하는 사항

- 지금 필요한 결정: Q-PII-003. 추천 A는 입력 label을 신뢰하지 않고 모든 phone-shaped value를
  마스킹하며, B는 승인된 공식번호 주입 경계를 다시 설계한다.
- 지금 필요한 승인: Q-PII-003=A일 때 이 실행계획으로 AI-001A를 구현할지 여부. B이면 이 계획을
  승인하지 않고 architecture/signature/data-lineage plan을 다시 쓴다.
- 나중에 필요한 결정: Q-PII-002 unresolved PII의 시민 응답·event reason.
- 별도 blocker: Q-SEED-002, Q-SEC-003. 이번 계획 승인으로 해결되지 않는다.

## AI 내부 구현 세부

- helper 함수명, regex compile 배치, test parameterization, 파일 formatting.
- 같은 fixture/계약 안에서 false-positive test를 추가하는 것.
- reviewer 지적에 따른 비공개 리팩터링.

## 진행 기록

- 2026-07-20T10:08:44+09:00: PII core 설계 승인.
- 2026-07-20T10:22:13+09:00: written specification 승인.
- 2026-07-20: Task 0+5 TDD 계획과 74-row exact oracle 작성. 독립 전체/regex review
  Critical 0 / Important 0. Q-PII-003 결정과 구현 승인 대기.
- 2026-07-20T11:32:00+09:00: Q-PII-003=A와 계획 승인·구현 시작 확정. D-043/A-032,
  exact oracle, product spec 2.2.3/docs 2.7.9 preflight 동기화 시작.
- 2026-07-20: isolated Task 1 RED `e9f9fbf`, Task 2 type/normalization `556e55e`, Task 3
  high-signal `7b13878`+verification cleanup `a4b7446`, Task 4 contextual/fail-closed `8f02955`.
  Task 1~4 independent reviews Critical/Important/Minor 0/0/0 after one clean-output fix.
- 2026-07-20T13:01:58+09:00: privacy 153, full API 310+8 DB skips, root default/offline,
  package/secret/diff/privacy evidence PASS. 첫 root run의 worktree-local ignored `.tools` 부재 4건은
  검증된 main `.tools` junction 후 focused 4/4와 두 full gate PASS로 환경 원인을 확정했다.
- 2026-07-20: whole-branch review가 fixed-token tail, Hangul explicit context, 1588 대표번호,
  반복/탭/줄바꿈 separator fail-open과 safe 문자열 객체 identity를 발견했다. 동결 74건은 바꾸지
  않고 13개 직접 회귀를 RED→GREEN으로 보정해 privacy 166건을 통과했다. 문서 closeout과
  후속 consumer spy gate 누락도 함께 보정했다.
- 2026-07-20T14:04:13+09:00: 여러 차례 독립 fuzz에서 추가로 확인한 공백 이메일, 임의 숫자
  grouping, 공백 차량번호, 건강정보 수식어, 전화 내선, generated-token 사이 raw tail, 주소/차량
  overlap 이름 leak, 값 없는 문의 false positive를 RED→GREEN으로 보정했다. frozen 74 oracle는
  `e9f9fbf`와 diff 0이고 privacy 282, architecture+privacy 286+5 subtests, full API 439+8
  local-DB skips+5 subtests, Ruff/mypy가 PASS했다.
- 2026-07-20T16:46:00+09:00: label-only 탐지를 positive value evidence로 재구성하고 독립
  category-gap 회귀를 254건까지 확장했다. frozen 74는 계속 불변이며 privacy 1,161,
  architecture+privacy 1,165+5 subtests, full API 1,318+8 local-DB skips+5 subtests가 PASS했다.
  최종 동결 SHA-256 `824F509A8AD7D01A7F0C5166D4687A52436DC941D5AC53F2DB84CC29B4C4942E`에서
  실제형 77건 raw fail-open 0(75 mask·2 fail-closed), safe 219 오탐 0, insertion 6,272·Unicode
  1,940·separator 252 fail-open 0, 두 독립 리뷰 Critical/Important 0/0을 확인했다.
- 2026-07-20T19:40:50+09:00: 최종 문서 동기화 뒤 fresh `verify.ps1 -Offline`이 root·data·
  seed·Web·API·contract regeneration·secret·package·diff 전 단계를 PASS했다. 같은 최종
  source에서 privacy 1,161, architecture+privacy 1,165, full API 1,318 결과도 재확인했다.
- 2026-07-20 IMP-007 safety addendum: 위 historical main `.tools` junction은 통합 cleanup에서
  Windows Git이 target까지 삭제하는 실제 위험을 만들었으므로 재사용을 금지한다. 후속 worktree는
  exact ignored binary를 byte-copy/hash/`-VerifyOnly`로 검증하고 worktree-local 사본만 정리한다.

## 결과와 회고

- 실제 결과: Task 1~4 구현과 Task 5 architecture/version/root 검증을 완료했고, 독립 리뷰에서
  확인한 separator·Unicode·provenance·context 조합 우회를 추가 TDD로 보정했다.
- 계획과 달라진 점: 최초 계획의 단일 separator regex만으로는 반복 공백·탭·줄바꿈 숫자
  skeleton을 닫지 못해 bounded regex와 선형 residual scan을 함께 사용했다. frozen v1은 불변이다.
- 다음 단계: Q-PII-002와 Q-SEED-002 결정 후 provider/DB-writer spy를 먼저 고정하는 parent AI-001
  consumer 계획을 작성한다. `/chat`·DB·DeepSeek 활성화는 이 완료 범위 밖이다.
