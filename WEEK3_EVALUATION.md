# 3주차 MVP 평가 Snapshot

## 1. Provenance

- Source repository: private `tskwak111/Sejong_AI`
- Source branch: `main`
- Source commit: `4cc2f4e5e478668e1d7216fddc08874c9285274b`
- Source commit time: `2026-07-24T14:19:04+09:00`
- Evaluation repository: `nxtcloud-edu/2026-07-kosj-industry-practice-team02`
- Evaluation branch: `submission/week3-mvp`
- Packaging rule: source의 tracked 파일을 별도 staging archive로 export했으며 private `.git`은 복사하지 않음

평가 commit SHA는 commit 생성 뒤 Draft PR과 최종 작업 보고서에 기록합니다. commit이 자기 SHA를 본문에 포함할 수 없으므로 이 문서에는 source SHA만 고정합니다.

## 2. 포함 범위

- `apps/api`, `apps/web`
- `contracts`, `packages/shared-contracts`
- `database`, `supabase/migrations`, `supabase/tests`
- `data/official`, `data/staging`, `data/schemas`, `data/evaluation`, 표시된 mock 문서
- `scripts`, `tools/web-e2e`
- 활성 source-of-truth, ADR, data lineage, 운영·보안 문서
- 잠금 파일과 빈 값의 `.env.example`

## 3. 제외 범위

- `.git`, private Git history, `.worktrees`, `.tools`, `.venv`, `node_modules`, `.next`, coverage
- 실제 `.env`, key, token, DSN, Docker/Supabase local data
- Playwright trace·screenshot·video, test runtime artifact, 실제 로그
- 실제 개인정보와 로컬 사용자 경로가 있는 discovery 기록
- 비권위 `legacy/`
- private 협업용 `.github`, agent/Cloud 설정과 내부 구현 노트·실행계획·감사 trace
- 재생성 가능한 `data/processed`

평가 저장소에 이미 있던 `[2026-세종-0001] 입찰제안서_세종 민원이음_2팀.pdf`와 `notice.md`는 수정하지 않았습니다.

## 4. 실제 구현 구조

### Backend

`apps/api`는 FastAPI 기반입니다.

1. 외부 모델 호출 전에 결정론적 개인정보 마스킹
2. 지원 범위·개인 조회·법적 판단·모호 질문 분류
3. ACTIVE+OFFICIAL KB만 검색
4. 근거 gate를 통과한 경우 구조화 SUCCESS
5. 근거가 부족하면 `INSUFFICIENT_GROUNDING`
6. 출처명·URL·확인일은 서버가 KB 메타데이터에서 결합

### Frontend

`apps/web`은 Next.js/TypeScript 기반이며 `/`, `/chat`, local/private `/admin`을 제공합니다. 기본 transport는 actual API이고 fixture는 명시적 opt-in 개발 모드에서만 `시연용 샘플 — 공식 데이터 아님` 표시와 함께 사용합니다.

## 5. DB와 정식 seed

`supabase/migrations`가 DB 실행 권위입니다. `supabase/config.toml`의 `[db.seed].enabled=false`를 바꾸지 않습니다.

1. patched local Supabase에서 migration reset
2. immutable `0.1.0-initial.2`를 별도 `seed-cycle`
3. `verify-final`로 ACTIVE 19 / office 3 / mapping 10 확인
4. local login provision
5. API 시작 후 `/ready=200` 확인

`db reset`만 실행한 빈 DB를 seeded DB로 간주하지 않습니다.

## 6. 19→20 ACTIVE 개선 루프

1. clean `.2` seed: ACTIVE 19
2. 별도 `INSUFFICIENT_GROUNDING` 질문: masked text만 실패 질문으로 저장
3. 운영자가 실패 사유를 확정하고 `KB-WASTE-03` 후보 작성
4. 동일 작성자의 승인은 차단
5. 다른 승인자가 승인
6. ACTIVE 20, 분야별 5개 확인
7. 같은 질문 재질의: SUCCESS와 공식 출처 확인

`KB-WASTE-03`은 local runtime 승인 흐름에서 생성되며 immutable `.2` release 파일을 수정하지 않습니다.

## 7. PERSONAL_LOOKUP 무저장 정책

개인 자동차세·체납액처럼 본인 인증이 필요한 질문은 다음 계약으로 처리합니다.

- public response: `intent=UNKNOWN`
- reason: `PERSONAL_LOOKUP`
- `candidate_eligible=false`
- 질문 text 저장 0
- interaction event 저장 0
- failed question row 저장 0
- 외부 provider 호출 0

개인 조회를 근거 부족 개선 후보로 위장하지 않습니다.

## 8. 평가 해석 경계

- `/ready=200`, ACTIVE 19→20, 재질의 SUCCESS는 disposable local/private DB 증거입니다.
- import-safe 기본 API는 설정·DB가 없으면 `/ready=503`으로 fail closed합니다.
- Upstage `solar-pro3` 코드는 승인된 합성 평가 전용이며 시민 자유 입력·public provider 연결 증거가 아닙니다.
- public admin, remote DB, public deploy, 자동 merge는 이 snapshot의 승인 범위가 아닙니다.

## 9. Snapshot 검증

아래 결과는 이 공개 export 폴더에서 새로 실행해 Draft PR 설명과 최종 보고서에 기록합니다.

| Gate | 결과 |
|---|---|
| secret scan | PASS — tracked/export tree에서 secret pattern 0 |
| API lint/typecheck/test | PASS — Ruff, strict Mypy 87 files, pytest 1,782 passed / DB-only 8 skipped |
| Web lint/typecheck/test/build | PASS — ESLint, TypeScript, Vitest 48/48, Next production build |
| shared contracts | PASS — 89/89 |
| preserved PDF/notice | PASS |
