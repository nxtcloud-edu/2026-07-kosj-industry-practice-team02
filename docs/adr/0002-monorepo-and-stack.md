# ADR-0002: 독립 모노레포·런타임 기준·local-first 배포

- Status: Accepted; public deployment details remain deferred
- Date: 2026-07-13 (updated 2026-07-14 by Q-REPO-001, Q-DEV-001, Q-DEP-001, Q-CI-001;
  partial successor 2026-07-20 by ADR-0019)

## Decision

- apps/web: Next.js + TypeScript + Tailwind
- apps/api: FastAPI + Python
- DB: Supabase PostgreSQL
- 이 workspace를 원본 원격 없는 새 독립 Git 저장소로 만들고 기본 브랜치를 `main`으로 사용한다.
- task branch와 PR을 사용하고 lint·typecheck·test·build·contract·secret 검사를 완료 gate로 둔다.
- Web runtime/tooling: Node 24.x + pnpm
- API runtime/tooling: Python 3.12 + uv
- 초기 완료 기준: local-first, 외부 인프라 지출 한도 0원
- 향후 관리형 배포 추천: Vercel + Render + Supabase. 계정·리전·로그·CORS·예산 승인 전에는 활성 목표가 아니다.
- local backup required

실제 `git init`, 도구 설치, 앱 스캐폴딩은 인터뷰 블로커를 해소하고 사용자가 최종 실행계획을 승인한 뒤 수행한다. 정확한 pnpm/uv patch 버전은 그때 lock/manifest에 고정한다.

## Consequences

프론트/백엔드 책임 경계와 로컬 재현성을 얻지만 두 런타임 관리가 필요하다. 관리형 배포는 당장
요구하지 않으므로 CORS·계정·리전·비밀·비용 위험을 공개 배포 승인 시점까지 격리한다. Git은
ignored env·Docker state·DB dump를 백업하지 않으므로 local-only 복구 경계는 별도로 유지한다.
