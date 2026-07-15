# Implementation Notes Index

| Note ID | Date | Task | Type | Summary | Versions | Status |
|---|---|---|---|---|---|---|
| [IMP-20260714-001](IMP-20260714-001-초기-저장소-발견-감사.md) | 2026-07-14 | DISC-001 | discovery | 초기 저장소 발견 감사와 첫 인터뷰 7문항 | docs 2.0.0→2.0.1 | Done |
| [IMP-20260714-002](IMP-20260714-002-1차-인터뷰-결정-반영.md) | 2026-07-14 | DISC-002 | decision | 1차 인터뷰 7개 결정·ADR·privacy contract/DB draft·Interviewing plan 반영 | spec 2.0.0→2.0.1; repo 1.0.0→1.1.0; api/db 0.1→0.2 draft; docs 2.0.1→2.1.0 | Decision-only Done |
| [IMP-20260714-003](IMP-20260714-003-2차-인터뷰-결정-반영.md) | 2026-07-14 | DISC-002 | decision | DeepSeek 합성 경계·Supabase SQL·보수 마스킹·503·local gate 반영 | spec 2.0.1→2.1.0; repo 1.1→1.2; api 0.2→1.0 draft; prompt/tests/docs 갱신 | Decision-only Done |
| [IMP-20260714-004](IMP-20260714-004-최종-인터뷰-결정과-실행계획-확정.md) | 2026-07-14 | DISC-002 | decision | DeepSeek Flash guard·서버 무세션 context·API 2.0·최종 plan 반영 | spec 2.1→2.2; api 1.0→2.0 draft; prompt/tests/docs 갱신 | Decision-only Done |
| [IMP-20260715-001](IMP-20260715-001-구현-승인과-phase-1-시작.md) | 2026-07-15 | PLAN-001 | decision | 구현 승인·local Git 기준선 준비와 에이전트 주도 Phase 1 시작 | docs 2.3.0→2.3.1 | Decision-only Done |
| [IMP-20260715-002](IMP-20260715-002-phase-1-상세-실행계획.md) | 2026-07-15 | DEV-001-PLAN | decision | exact 후보·pre-DB readiness·계약/env gate를 포함한 Phase 1 세분화 | docs 2.3.1→2.3.2 | Decision-only Done |
| [IMP-20260715-003](IMP-20260715-003-root-runtime-workspace-contract.md) | 2026-07-15 | DEV-001A | implementation | exact runtime과 dependency-free root workspace 계약 | repo 1.2.0→1.3.0; tests 0.3.0→0.3.1; docs 2.3.2→2.3.3 | Done |
| [IMP-20260715-004](IMP-20260715-004-fastapi-health와-pre-db-readiness.md) | 2026-07-15 | DEV-001B | implementation | exact health·pre-DB readiness와 frozen API lock | app 0.0.0→0.0.1; tests 0.3.1→0.3.2; docs 2.3.3→2.3.4 | Done |
| [IMP-20260715-005](IMP-20260715-005-접근-가능한-next-js-애플리케이션-shell.md) | 2026-07-15 | DEV-001C | implementation | 정직한 개발 한계와 모바일·접근성 기반을 갖춘 정적 Next.js 홈 shell | app 0.0.1→0.0.2; web 0.0.0→0.1.0; tests 0.3.2→0.3.3; docs 2.3.4→2.3.5 | Done |
| [IMP-20260715-006](IMP-20260715-006-서비스별-환경변수와-안전-로그-경계.md) | 2026-07-15 | DEV-002A | security | 서비스별 env 분리·네 필드 요청 로그·저장소/브라우저 scanner 경계 | app 0.0.2→0.0.3; tests 0.3.3→0.3.4; docs 2.3.5→2.3.6 | Done |
| [IMP-20260715-007](IMP-20260715-007-승인-계약-불변조건과-공통-fixture.md) | 2026-07-15 | CONTRACT-001A | implementation | SUCCESS 출처·context·office·503 공통 fixture gate | tests 0.3.4→0.3.5; docs 2.3.6→2.3.7; API 2.0.0-draft 유지 | Done |
| [IMP-20260715-008](IMP-20260715-008-생성-typescript와-pydantic-계약-drift-gate.md) | 2026-07-15 | CONTRACT-001B | implementation | 결정적 TypeScript 생성·strict Pydantic·FastAPI metadata drift gate | shared 0.1→0.2; app 0.0.3→0.0.4; tests 0.3.5→0.4.0; docs 2.3.7→2.3.8; API 2.0.0-draft 유지 | Done |
| [IMP-20260715-009](IMP-20260715-009-clean-local-verification과-phase-1-마감.md) | 2026-07-15 | DEV-001D, DEV-002B | implementation/security | PS 5.1 exact local gate·warm offline·비노출/환경 복원과 최종 계약 drift 보정 | repo 1.3→1.4; app 0.0.4→0.1.0; API 2.0.0-draft→2.0.1-draft; shared 0.2.0→0.2.1; tests 0.4.0→0.4.2; docs 2.3.8→2.3.10; DB/data/prompt 유지 | Done |
