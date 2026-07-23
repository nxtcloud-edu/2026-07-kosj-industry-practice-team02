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

- [`DATA-SEED-002 / 0.1.0-initial.2`](DATA-SEED-002-0.1.0-initial.2.md) — canonical immutable
  19/3/10 filesystem release and active dispatcher. The supported actual local cycle passed and
  promotes `official_data=0.1.0-initial.2`; it remains distinct from application readiness and the
  later candidate workflow.
- [`MVP-001 KB-WASTE-03 local workflow`](MVP-001-KB-WASTE-03-LOCAL-WORKFLOW.md) — local/private
  19→20 governed runtime evidence only; no official `.2` artifact or source data changed.
- [`DATA-SEED-001 / 0.1.0-initial.1`](DATA-SEED-001-0.1.0-initial.1.md) — filesystem release
  19/3/10 published/verified; actual PostgreSQL import Blocked before seed, `official_data` not
  promoted; retained as the immutable predecessor of DATA-SEED-002
