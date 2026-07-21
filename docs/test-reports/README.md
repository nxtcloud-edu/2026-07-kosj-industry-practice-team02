# Test reports

표본 평가, 회귀, 접근성, 성능 보고서를 버전과 실행환경과 함께 보관한다.

## 현재 보고서

- [DB-001 local baseline — local verified / public blocked](DB-001-LOCAL-BASELINE.md) — Supabase/PostgreSQL 환경,
  6+6 lineage hash, 과거 pgTAP 282·integration 8/8·rollback/replay와 현재 D-031 구현 local/
  D-046 deferred `00700` public-release block
- [DATA-SEED-002 actual disposable DB — blocked](DATA-SEED-002-LOCAL-VERIFICATION.md) — `.2`
  canonical release/dispatcher는 published/byte-verified지만 reviewed diagnostic이 concurrency B의
  `CAPABILITY_WRITE_DID_NOT_BLOCK`를 확인; cleanup PASS,
  `official_data=0.0.0-not-populated`, PostgreSQL ACTIVE 19는 미검증
- [DATA-SEED-001 actual disposable DB — blocked](DATA-SEED-001-LOCAL-VERIFICATION.md) — `.1`
  filesystem release/dispatcher는 verified, actual PostgreSQL은 seed write 전 grantor-option union 대
  immutable single-row guard 충돌로 Blocked; DATA-SEED-002의 불변 predecessor로 보존
