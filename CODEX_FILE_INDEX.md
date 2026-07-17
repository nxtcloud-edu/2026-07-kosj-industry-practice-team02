# Codex 파일 인덱스

## 반드시 Codex가 자동/초기에 읽는 파일

| 파일 | 목적 |
|---|---|
| `AGENTS.md` | 매 작업 공통 규칙, 범위, 안전, 구현 노트 의무 |
| `apps/web/AGENTS.md` | 프론트 로컬 규칙 |
| `apps/api/AGENTS.md` | 백엔드 로컬 규칙 |
| `data/AGENTS.md` | 공식/mock/평가 데이터 규칙 |
| `contracts/AGENTS.md` | 공개 계약 변경 규칙 |

## 사용자가 첫 세션에 입력할 파일

| 파일 | 목적 |
|---|---|
| `CODEX_START_PROMPT.md` | 발견 감사, 모호성 탐색, 우선순위 인터뷰, 계획 승인 요구 |
| `FIRST_RUN_CHECKLIST.md` | 첫 실행 누락 방지 |

## Codex가 계획과 작업을 관리하는 파일

| 파일 | 목적 |
|---|---|
| `PLANS.md` | 긴 작업 실행계획 규약 |
| `TASKS.md` | 현재 P0/P1 백로그와 의존성 |
| `docs/11_AMBIGUITY_REGISTER.md` | 미지의 영역·질문 상태 |
| `docs/decisions/DECISION_LOG.md` | 사용자 결정 로그 |
| `docs/adr/` | 장기 아키텍처 결정 |
| `docs/discovery/INTERVIEW_ANSWERS.md` | 인터뷰 답변 원문·해석·해결 상태 |
| `docs/superpowers/specs/` | 구현계획 전에 사용자가 검토하는 기능·아키텍처 서면 설계 |
| `docs/superpowers/plans/` | 승인된 명세를 TDD 실행 단위·명령·검증·commit으로 분해한 구현계획 |
| `docs/plans/PLAN-20260714-001-foundation-and-governed-chat.md` | 승인된 전체 실행계획과 단계별 gate |
| `docs/superpowers/plans/2026-07-16-db-001-layered-enforcement.md` | 승인된 DB-001 상세 실행계획; Tasks 0~9 완료, Q-SEC-004=A 보정은 불충분했고 Task 10은 Q-SEC-005/A-023으로 차단 |

## 모든 작업 후 갱신할 파일

| 파일 | 목적 |
|---|---|
| `docs/implementation-notes/` | 6W1H 구현·결정 기록 |
| `versions/manifest.json` | 코드/API/DB/데이터/프롬프트/테스트/문서 버전 |
| `CHANGELOG.md` | 외부에 설명할 변경 요약 |
| 관련 계약/계보/테스트 리포트 | 실제 동작과 문서 정합 |

## 구현 계약과 설계

| 위치 | 목적 |
|---|---|
| `contracts/` | OpenAPI 2.0.1-draft와 동기화 JSON Schema |
| `supabase/migrations/`, `supabase/tests/database/` | DB-001 timestamp 실행 권위와 pgTAP |
| `database/` | `0.3.0-local` 후보 논리 projection, 역순 disposable-local 보상, absence proof; manifest는 blocker로 `0.2.0-draft` 유지 |
| `docs/test-reports/DB-001-LOCAL-BASELINE.md` | DB-001 후보의 과거 DB 증거와 현재 Q-SEC-005/A-023 IPv6 port 차단 상태 |
| `docs/handoffs/HANDOFF-20260717-DB-001-LOCAL-BASELINE.md` | 차단된 local DB 후보의 재개 조건·rollback/recovery·public-release blocker 인수인계 |
| `docs/03_ARCHITECTURE.md` | 시스템 경계와 장애 전략 |
| `docs/04_DOMAIN_AND_STATE_MODEL.md` | enum·상태·불변조건 |
| `docs/05_API_AND_CONTRACTS.md` | API 관리 규칙 |
| `docs/07_SECURITY_PRIVACY.md` | 구현 보안 기준 |
| `docs/08_TEST_STRATEGY.md` | 검증 전략 |

## source-of-truth와 legacy

| 위치 | 목적 |
|---|---|
| `docs/source-of-truth/` | 최종 확정 제품·RFP·정책 |
| `legacy/uploaded-project/` | 사용자가 올린 초기 프로젝트 원본(full package에만 포함) |
| `docs/02_CURRENT_REPO_AUDIT.md` | 초기 프로젝트와 최종 기준 충돌표 |

## 자동화 도구

| 파일 | 목적 |
|---|---|
| `scripts/new_implementation_note.py` | 노트와 INDEX 생성 |
| `scripts/capture_repo_state.py` | Git/버전 상태 캡처 |
| `scripts/check_scope_drift.py` | 오래된 범위의 활성 복귀 탐지 |
| `scripts/validate_codex_package.py` | 필수 파일과 지침 검증 |
