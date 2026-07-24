# ADR-0008: Supabase CLI 버전 SQL 마이그레이션

- Status: Accepted for local development; remote execution deferred
- Date: 2026-07-14

## Decision

PostgreSQL 스키마의 실행 권위는 `supabase/migrations/<timestamp>_<name>.sql`의 순서가 있는 SQL 파일이다. `database/schema-v1.draft.sql`은 논리 설계 참고본이며 직접 실행하거나 실행 권위로 취급하지 않는다.

- local stack은 Supabase CLI와 Docker를 사용한다.
- 이미 적용된 migration 파일은 수정하지 않고 새 forward migration을 추가한다.
- 로컬 초기화·검증은 `supabase db reset`으로 빈 DB에 전체 계보를 replay한다.
- Supabase CLI가 일반적인 down migration을 자동 보장한다고 가정하지 않는다. 각 위험 변경에는 명시적 보상/rollback SQL, 데이터 백업, 복구 절차와 인수 기준을 함께 기록한다.
- 원격 `db push`, 파괴적 DDL, 운영 데이터 삭제·이동은 백업과 인간 승인을 받은 뒤에만 수행한다.
- enum/check/trigger/function/RLS/GRANT를 SQL에서 명시하고 backend-only 권한을 테스트한다.

Supabase CLI 설치, Docker 엔진 시작, migration 디렉터리 생성·실행은 Q-DB-001로 도구 선택만 승인된 상태이므로 최종 계획 승인 후 수행한다. 2026-07-14 감사 시 Docker CLI 29.2.1은 설치돼 있었지만 엔진은 실행 중이 아니었고 Supabase CLI는 없었다.

## Consequences

Supabase 대상 기능과 로컬/향후 원격 계보를 같은 SQL로 재현할 수 있다. 대신 Docker/CLI가 개발 전제이며 자동 rollback에 의존할 수 없다. 빈 DB replay, 권한·상태 불변조건, 백업 복구 후 retention 재실행을 완료 gate로 둔다.
