# ADR-0011: DB와 백엔드의 계층형 안전 규칙 강제

- Status: Accepted for DB-001 design; implementation pending written-spec review
- Date: 2026-07-16
- Deciders: 사용자, Codex
- Related: Q-DB-002, D-025, ADR-0003/0004/0007/0008, DB-001

## Context

현재 `database/schema-v1.draft.sql`은 6개 enum, 8개 table, 5개 index의 논리 참고본이다. 실행 migration, 권한, 원자적 승인 함수, 30일 파기 실행 함수, DB 통합 테스트가 없다. 백엔드만 정책을 강제하면 직접 SQL, 다른 writer, 동시 요청이 자기 승인 금지·ACTIVE 전용 검색·텍스트 파기·감사 일관성을 우회할 수 있다.

## Decision

Q-DB-002의 선택지 A를 채택한다. 핵심 정책은 PostgreSQL과 FastAPI 양쪽에서 강제한다.

- 업무 table과 enum은 PostgREST 기본 노출 schema가 아닌 `app_private`에 둔다.
- 시민·관리자 서버가 사용하는 제한 interface는 `app_api`의 view/function으로만 제공한다.
- `PUBLIC`, `anon`, `authenticated`에는 업무 schema/table/function 직접 권한을 주지 않는다.
- `sejong_backend` NOLOGIN capability role은 base table DML 권한 없이 승인된 view/function만 사용한다. 실제 local login credential은 migration 밖에서 생성해 ignored env에만 둔다.
- base table은 RLS를 활성화하고 직접 접근을 거부한다. `SECURITY DEFINER` function은 NOLOGIN owner, 고정 `search_path`, 명시적 schema qualification, `PUBLIC EXECUTE` revoke를 사용한다.
- 백엔드는 client 입력을 그대로 actor 권한으로 신뢰하지 않고 local/private actor boundary를 검사한 뒤 구조화된 값을 DB function에 전달한다. DB는 role, 상태, 작성자와 승인자 불일치, 교차 record 무결성을 다시 검사한다.
- 후보 승인 function은 row lock 안에서 후보 검증, ACTIVE KB와 최소 질문 예시 생성, 후보 연결, 감사 로그 추가를 한 transaction으로 처리한다.
- 시민 읽기 interface는 `ACTIVE`이면서 `OFFICIAL` provenance인 KB와 기관만 반환한다.
- 이벤트·실패 질문 write function은 원문을 받지 않으며, OUT_OF_SCOPE 텍스트와 FOLLOWUP 실패 행을 거부한다. 저장하기로 선택한 masked text만 30일 후 멱등 NULL 파기한다.
- 감사 로그는 질문·답변 snapshot 없이 상태·행위·변경 필드명만 append-only로 남긴다.
- 백엔드는 동일 규칙을 선검증하고 DB constraint/function 오류를 안정된 domain error로 변환한다.

## Alternatives considered

### Backend 중심, DB는 최소 FK/check

초기 Python 구현은 작지만 직접 SQL과 동시성 우회에 약하고 복구한 DB의 정책 준수를 독립적으로 증명하기 어렵다. Q-DB-002에서 선택하지 않았다.

### 전체 정규화 재설계

event source, actor, 상태별 table을 전면 분리하면 무결성은 강해지지만 현재 MVP 공개 계약과 8-table 논리 모델의 변경 폭이 커진다. DB-001에서는 provenance와 subset check 등 필요한 최소 보강만 하고 실제 증거가 생길 때 재검토한다.

## Consequences

### Positive

- API 결함·직접 write·승인 race에 대한 이중 방어가 생긴다.
- ACTIVE·공식 데이터 경계와 30일 파기를 DB test로 재현할 수 있다.
- 승인과 감사 기록이 부분 commit 없이 일치한다.

### Negative / tradeoffs

- SQL function, role, RLS, pgTAP test와 rollback 검증량이 증가한다.
- credential bootstrap은 schema migration과 분리해 별도 local tooling으로 관리해야 한다.
- 공개 운영의 실제 SSO/RBAC와 remote Supabase 연결은 해결하지 않으며 별도 승인이 필요하다.

## Security, data, cost impact

- 원문 질문·답변, context token, IP·기기 ID, 비밀은 새 schema에 추가하지 않는다.
- official/mock provenance는 명시하며 시민 read interface에서 mock을 제외한다.
- 새 production dependency와 외부 인프라 비용은 없다. Supabase CLI는 구현 시 exact 공식 release와 SHA-256을 고정하는 local dev tool이다.

## Migration and rollback

- 실행 권위는 ADR-0008의 timestamp SQL migration 계보다.
- schema/table → invariant/trigger → capability/function/RLS → index/view 순으로 forward migration을 분리한다.
- 위험 단계마다 `database/rollbacks/`에 역순 보상 SQL을 둔다. 자동 down migration을 가정하지 않는다.
- remote push, 실제 데이터 파괴, public deployment는 이번 결정으로 승인되지 않는다.

## Verification

- empty reset/replay와 보상 rollback/replay
- anon/authenticated/PUBLIC/base-role 직접 CRUD 거부
- ACTIVE+OFFICIAL만 시민 interface에서 조회
- 자기 승인, 잘못된 role/status, 중복·동시 승인 거부와 단일 ACTIVE/audit 생성
- OUT_OF_SCOPE text 0, FOLLOWUP failure 0, raw 질문 column/log 0
- 30일 직전·정각·직후와 반복 purge의 멱등성·FK 보존
- official/mock 교차 활성화 거부와 no-seed `/ready=503` 유지
