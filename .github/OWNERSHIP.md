# 협업 소유권과 병합 경계

이 문서는 GitHub Free private repository에서 지키는 사람 운영 규칙이다. branch protection이나
CODEOWNERS가 기술적으로 완전 강제된다고 주장하지 않는다. 모든 작업자는 direct `main` push를 하지
않고 한 TASK ID당 작은 PR 하나를 사용한다.

## Frontend 팀원 소유 범위

Frontend 팀원은 `/`, `/chat`, `/admin`, typed client, loading/empty/error/offline, 반응형·접근성,
frontend unit/E2E의 전체 수직 흐름을 구현한다. 다만 자가 병합 가능한 변경은 다음으로 더 좁다.

- `apps/web/src/**`
- `tools/web-e2e/e2e/**`
- 정확히 하나의 신규 `docs/implementation-notes/IMP-YYYYMMDD-NNN-web-*.md`
- 그 신규 노트 한 행만 append한 `docs/implementation-notes/INDEX.md`

rename은 이전·새 경로 모두 허용 범위일 때만 가능하다. 삭제, 기존 구현 노트나 INDEX 행 수정,
`apps/web/AGENTS.md`, env/example, README/config/package metadata는 자가 병합 대상이 아니다.

## OWNER_REVIEW_REQUIRED

다음 중 하나라도 포함되면 Frontend 팀원이 자가 병합하지 않고 사용자가 검토한다.

- package manifest·lockfile·workspace/runtime pin·새 dependency
- `.github/**`, root policy/guidance, ADR, 개인정보·보안·승인 정책
- 공개 contract·generated type, backend/API, DB/migration
- official/staging/mock data 또는 data lineage
- 허용 경로 밖의 파일, mixed scope, delete/path escape/unknown Git status

계약이 부족하면 임의 type이나 production workaround를 만들지 않고 `[CONTRACT]` Issue를 연다.

## Codex와 증거

Codex Cloud는 `codex/**` branch와 Draft PR까지만 만들고 사용자가 병합한다. Cloud에는 DeepSeek key,
DB DSN, context secret이나 실제 시민 fixture를 넣지 않는다. Docker/Supabase와 DeepSeek actual 증거는
local-only이며 GitHub Actions 성공으로 대체하지 않는다.
