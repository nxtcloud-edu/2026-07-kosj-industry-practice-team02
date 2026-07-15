# Database

`schema-v1.draft.sql`은 최종 정책을 반영한 논리 참고 초안이며 직접 운영 DB에 실행하지 않는다. 실행 권위는 최종 계획 승인 후 생성할 `supabase/migrations/<timestamp>_<name>.sql`의 Supabase CLI 버전 SQL 계보다.

- 이미 적용한 migration은 수정하지 않고 새 forward migration을 추가한다.
- local 검증은 Docker engine이 실행된 상태에서 `supabase db reset`으로 빈 DB replay를 확인한다.
- 자동 down migration을 가정하지 않고 위험 변경마다 명시적 보상/rollback SQL, 백업·복구 절차를 기록한다.
- 원격 `db push`, 파괴적 변경, 데이터 삭제·이동은 인간 승인 전 금지한다.

2026-07-16 확인 결과 Docker daemon이 Linux container mode로 응답한다. Supabase CLI, supabase/ 설정, 실행 migration, DB 통합 테스트는 아직 없다. Q-DB-002 기본값 또는 답변을 반영한 DB 설계 명세 승인 전에는 CLI 설치·image pull·container 시작·migration 생성/실행을 하지 않는다. 상세 간극과 추천 경계는 [DB-001 발견 감사 보고서](../docs/discovery/DB_001_DISCOVERY_REPORT.md)를 따른다.
