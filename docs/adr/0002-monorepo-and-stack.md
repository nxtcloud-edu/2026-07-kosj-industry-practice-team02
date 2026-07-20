# ADR-0002: 독립 모노레포·런타임 기준·local-first 배포

- Status: Accepted; source-remote/Cloud collaboration clauses partially superseded by ADR-0019;
  public deployment details remain deferred
- Date: 2026-07-13 (updated 2026-07-14 by Q-REPO-001, Q-DEV-001, Q-DEP-001, Q-CI-001;
  partial successor 2026-07-20 by ADR-0019)

## Decision

- apps/web: Next.js + TypeScript + Tailwind
- apps/api: FastAPI + Python
- DB: Supabase PostgreSQL
- 이 workspace를 원본 원격 없는 새 독립 Git 저장소로 만들고 기본 브랜치를 `main`으로 사용한다.
- Codex 작업 브랜치는 `codex/<task-id>-<slug>` 형식을 사용한다.
- 현재 단계에는 원격 저장소와 CI를 연결하지 않는다. local Git에서 lint·typecheck·test·build·contract·secret 검사를 수동 완료 gate로 사용한다.
- 원격 백업·CI·branch protection은 사용자가 Git 연결을 다시 요청할 때 계정·소유권·쿼터와 함께 결정한다.
- Web runtime/tooling: Node 24.x + pnpm
- API runtime/tooling: Python 3.12 + uv
- 초기 완료 기준: local-first, 외부 인프라 지출 한도 0원
- 향후 관리형 배포 추천: Vercel + Render + Supabase. 계정·리전·로그·CORS·예산 승인 전에는 활성 목표가 아니다.
- local backup required

실제 `git init`, 도구 설치, 앱 스캐폴딩은 인터뷰 블로커를 해소하고 사용자가 최종 실행계획을 승인한 뒤 수행한다. 정확한 pnpm/uv patch 버전은 그때 lock/manifest에 고정한다.

위 원격/CI 유예 문장은 2026-07-14 당시의 권위와 역사다. 사용자는 2026-07-20 ADR-0019에서
개인 계정 private GitHub source remote, Frontend collaborator와 role-scoped PR/CI, Codex Cloud
Draft-PR-only 방향과 COLLAB-001 실행계획을 D-054로 승인했다. 로컬 collaboration gate는 구현 중이고
실제 remote/App 설정은 account 확인과 사용자 browser 인증 뒤에만 수행한다. 이는
Vercel/Render/Supabase application deployment나 remote DB 승인이 아니다.

## Consequences

프론트/백엔드 책임 경계와 로컬 재현성을 얻지만 두 런타임 관리가 필요하다. 관리형 배포는 당장 요구하지 않으므로 CORS·계정·리전·비밀·비용 위험을 공개 배포 승인 시점까지 격리한다. ADR-0019 실행 전까지 원격 tracked-history 복사본과 자동 검증이 없으므로 단일 PC 손실·수동 gate 누락 위험을 인수인계와 체크리스트에 명시한다. 실행 뒤에도 ignored env·Docker state·DB dump는 GitHub가 백업하지 않으며 local-only gate는 유지한다.
