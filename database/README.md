# Database

`schema-v1.draft.sql`은 최종 정책을 반영한 논리 참고 초안이며 직접 운영 DB에 실행하지 않는다. 실행 권위는 최종 계획 승인 후 생성할 `supabase/migrations/<timestamp>_<name>.sql`의 Supabase CLI 버전 SQL 계보다.

- 이미 적용한 migration은 수정하지 않고 새 forward migration을 추가한다.
- local 검증은 Docker engine이 실행된 상태에서 `supabase db reset`으로 빈 DB replay를 확인한다.
- 자동 down migration을 가정하지 않고 위험 변경마다 명시적 보상/rollback SQL, 백업·복구 절차를 기록한다.
- 원격 `db push`, 파괴적 변경, 데이터 삭제·이동은 인간 승인 전 금지한다.

2026-07-14 현재 Docker CLI 29.2.1은 있으나 engine은 꺼져 있고 Supabase CLI는 설치되지 않았다. 설치·engine 시작·migration 생성/실행은 제품 구현과 함께 최종 계획 승인 후 수행한다.
