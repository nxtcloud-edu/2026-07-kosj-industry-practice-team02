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
| `docs/plans/PLAN-20260714-001-foundation-and-governed-chat.md` | A/Blocker 0, 사용자 승인 대기 Draft 실행계획 |

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
| `database/` | 개인정보·승인 불변조건을 반영한 DB 논리 초안 |
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
