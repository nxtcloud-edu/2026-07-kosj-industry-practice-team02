# Database

`schema-v1.draft.sql`은 최종 정책을 반영한 논리 참고 초안이며 직접 운영 DB에 실행하지 않는다. 실행 권위는 최종 계획 승인 후 생성할 `supabase/migrations/<timestamp>_<name>.sql`의 Supabase CLI 버전 SQL 계보다.

- 이미 적용한 migration은 수정하지 않고 새 forward migration을 추가한다.
- local 검증은 Docker engine이 실행된 상태에서 `supabase db reset`으로 빈 DB replay를 확인한다.
- 자동 down migration을 가정하지 않고 위험 변경마다 명시적 보상/rollback SQL, 백업·복구 절차를 기록한다.
- 원격 `db push`, 파괴적 변경, 데이터 삭제·이동은 인간 승인 전 금지한다.

2026-07-16 현재 pinned Supabase CLI와 local PostgreSQL 환경이 준비됐고, 실행 migration `00100`~`00300`과 matching compensation, pgTAP 검증이 구현됐다. 적용·commit된 migration은 불변이다. Q-SEC-002=A에 따라 non-superuser runner가 위험 role을 발견하면 privileged 자동 교정 없이 fail closed한다. Q-WF-001=A에 따른 candidate workflow는 새 `00400`, 시민 read/index는 `00500`에서 구현하며 rollback은 `00500 → 00400 → 00300 → 00200 → 00100` 순서다. 공식/mock seed는 여전히 없으므로 `/ready=503`을 유지한다. 현재 기준은 [ADR-0011](../docs/adr/0011-layered-database-and-backend-enforcement.md), [승인된 설계](../docs/superpowers/specs/2026-07-16-db-001-layered-enforcement-design.md), [승인된 실행계획](../docs/superpowers/plans/2026-07-16-db-001-layered-enforcement.md)이다.
