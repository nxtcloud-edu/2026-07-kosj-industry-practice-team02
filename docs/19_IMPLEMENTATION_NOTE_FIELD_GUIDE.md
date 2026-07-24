# 구현 노트 필드 작성 가이드

## 왜 상세해야 하는가

코드는 현재 상태만 보여주지만 구현 노트는 변경의 이유, 대안, 테스트, 데이터·보안 영향, 롤백을 보여준다. 후임 개발자는 코드만 보고 당시의 제약을 추측하지 않아야 한다.

## 6W1H 작성 예

| 필드 | 나쁜 기록 | 좋은 기록 |
|---|---|---|
| Who | Codex가 함 | 요청자: 팀 PM, 구현: Codex, 검토 필요: BE 담당 |
| When | 오늘 | 2026-07-14 10:10~11:25 KST, 3주차 시작 전 |
| Where | 백엔드 | `apps/api/src/privacy/redaction.py`, `/api/v1/chat`, test DB |
| What | 마스킹 추가 | 전화/주민번호/이메일을 외부 provider 호출 전에 치환하고 원문 persistence 차단 |
| Why | 보안 | SER-001/002, 외부 LLM 전송 최소화, 원문 로그 위험 방지 |
| How | 정규식 | compiled detector chain + typed RedactionResult + payload spy test |
| How much | 몇 파일 | 4 files, 12 unit tests, API contract unchanged, schema version unchanged |

## 버전 기록

- 코드 버전: Git HEAD/branch + application semver
- API 버전: OpenAPI info.version
- DB 버전: migration revision/schema manifest
- 데이터 버전: source registry/data manifest
- 프롬프트 버전: prompt template hash/semver
- 테스트 버전: 평가셋·테스트 코드 버전
- 문서 버전: source-of-truth/guide version

## 테스트 기록

`테스트 완료`라고만 쓰지 않는다.

```text
Command: uv run pytest tests/privacy -q
Result: 18 passed in 0.62s
Evidence: terminal output in note; no raw fixture values
```

실행하지 못했으면:

```text
Not run: Playwright — web app not scaffolded yet.
Alternative evidence: JSON schema validation only.
Risk: UI integration remains unverified.
```

## 데이터 기록

- official/mock/AI generated 분류
- source URL/verified date
- before/after row count
- transform command
- reviewer/approval
- impacted tests

## 인간/AI 구분 예

### 인간이 알아야 함

- API 응답에서 `confidence`를 제거하면 UI와 평가 기준이 달라짐
- 새 LLM 공급자는 요청 보관정책 확인 필요

### AI 내부 세부

- regex 컴파일 캐시
- fixture factory 파일 분리
- helper function 이름
