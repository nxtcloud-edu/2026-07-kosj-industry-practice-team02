# Data lineage

각 공식 데이터 버전마다 다음을 기록한다.

- dataset/version
- source/provider/URL
- fetched/verified date
- raw location
- transform script and command
- record counts before/after
- validator/reviewer
- affected KB/tests
- rollback artifact

## 현재 lineage

- [`DATA-SEED-002 / 0.1.0-initial.2`](DATA-SEED-002-0.1.0-initial.2.md) — canonical successor
  19/3/10 filesystem release and active dispatcher are published/byte-verified; reviewed diagnostic
  isolated concurrency B as `CAPABILITY_WRITE_DID_NOT_BLOCK`; cleanup PASS,
  `official_data=0.0.0-not-populated`, PostgreSQL ACTIVE 19 not claimed
- [`DATA-SEED-001 / 0.1.0-initial.1`](DATA-SEED-001-0.1.0-initial.1.md) — filesystem release
  19/3/10 published/verified; actual PostgreSQL import Blocked before seed, `official_data` not
  promoted; retained as the immutable predecessor of DATA-SEED-002
