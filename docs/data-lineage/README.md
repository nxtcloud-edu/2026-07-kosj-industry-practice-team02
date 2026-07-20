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

- [`DATA-SEED-001 / 0.1.0-initial.1`](DATA-SEED-001-0.1.0-initial.1.md) — filesystem release
  19/3/10 published/verified; actual PostgreSQL import Blocked before seed, `official_data` not
  promoted; D-044/ADR-0017의 `.2` successor spec·plan Review
