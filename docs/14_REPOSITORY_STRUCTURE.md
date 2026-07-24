# 공개 평가 Snapshot 구조

```text
apps/api/                  FastAPI 시민·관리자 API
apps/web/                  Next.js 시민·관리자 UI
packages/shared-contracts/ generated TypeScript 계약
contracts/                 OpenAPI·JSON Schema 권위
supabase/migrations/       실행 가능한 forward migration
supabase/tests/database/   pgTAP
database/rollbacks/        disposable local rollback
data/official/             승인된 immutable release
data/staging/              hash-bound 작성·승인 입력
data/processed/            canonical PM packet·검증 report 2개
data/evaluation/           결정론적 표본
data/mock/                 시연용 샘플
scripts/                   재현·검증 도구
tools/web-e2e/             Playwright
docs/source-of-truth/      정책·범위
docs/adr/                  아키텍처 결정
docs/data-lineage/         공식 데이터 계보
docs/test-reports/         평가 결과
versions/manifest.json     버전 권위
```

`.env`, `.tools`, `.venv`, `node_modules`, `.next`, Docker/Supabase local state, trace, coverage와
실제 로그는 생성 가능하지만 commit하지 않습니다. `legacy`와 내부 협업 자료는 공개 평가
snapshot에 포함하지 않습니다.
