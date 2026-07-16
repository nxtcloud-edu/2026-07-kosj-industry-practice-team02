# 저장소 구조 기준

```text
.
├─ AGENTS.md
├─ CODEX_START_PROMPT.md
├─ PLANS.md
├─ TASKS.md
├─ apps/
│  ├─ web/
│  └─ api/
├─ packages/
│  └─ shared-contracts/
├─ contracts/
├─ database/
│  ├─ rollbacks/
│  ├─ schema-v1.draft.sql
│  └─ verify_db001_absent.sql
├─ supabase/
│  ├─ migrations/
│  ├─ tests/database/
│  ├─ config.toml
│  └─ seed.sql
├─ data/
│  ├─ official/
│  ├─ evaluation/
│  ├─ mock/
│  └─ processed/
├─ docs/
│  ├─ source-of-truth/
│  ├─ adr/
│  ├─ decisions/
│  ├─ plans/
│  ├─ superpowers/
│  │  ├─ specs/
│  │  └─ plans/
│  ├─ implementation-notes/
│  ├─ test-reports/
│  ├─ data-lineage/
│  └─ handoffs/
├─ scripts/
├─ versions/
└─ legacy/
```

## 규칙

- 활성 애플리케이션은 `apps/` 밖에 만들지 않는다.
- OpenAPI/JSON Schema 원본은 `contracts/`에 둔다.
- 생성된 타입은 `packages/shared-contracts/` 또는 앱별 generated에 둔다.
- raw official과 mock을 절대 같은 파일/테이블로 취급하지 않는다.
- 일회성 분석 결과는 `artifacts/`(gitignore) 또는 명확한 reports에 둔다.
- 임시 이름(`final2`, `new_new`, `copy`)을 사용하지 않는다.
- legacy는 읽기 전용에 가깝게 유지한다.
- DB 실행 권위는 `supabase/migrations/`; `database/`의 논리 projection은 직접 실행하지 않는다.
- `.tools/`, `.env`, `supabase/.temp/`, `supabase/.branches/`, Docker state와 backup dump는
  transient/ignored이며 commit하지 않는다.
