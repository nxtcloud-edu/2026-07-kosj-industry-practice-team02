# Handoff — Frontend Collaborator

- Date: 2026-07-20 KST
- Status: Prepared; Q-GIT-004=A resolved; private GitHub remote·collaborator invitation·CI creation
  pending plan approval
- Canonical branch/HEAD at preparation: `main` / `177dac810468f3cd5aaa4929a971cbde21b4deba`
- Product: 세종 민원 AI 길잡이
- Scope owner: Frontend 팀원
- Architecture/contract/data/security owner: 사용자

## 1. 먼저 읽을 문서

1. `AGENTS.md`
2. `apps/web/AGENTS.md`
3. `docs/00_SOURCE_OF_TRUTH.md`
4. `docs/source-of-truth/TEAM_DECISIONS.md`
5. `docs/24_UI_STATE_MATRIX.md`
6. `docs/05_API_AND_CONTRACTS.md`
7. `TASKS.md`
8. 이 handoff와 최신 frontend 구현 노트

`legacy/`는 참고 자료이며 현재 화면·API·범위의 정답이 아니다.

## 2. 담당 범위

담당자는 `/`, `/chat`, `/admin`의 frontend 전체 흐름을 소유한다.

- typed API client와 승인된 공개 계약 연결
- loading·empty·error·offline·retry·disabled 상태
- mobile 390/430px, desktop, 200% zoom, horizontal overflow 0
- semantic HTML, keyboard, visible focus, modal focus trap/return
- 본문 대비 4.5:1 이상, 상태를 색상만으로 표현하지 않음
- frontend unit/component test와 Playwright E2E
- 시민에게 보이는 mock/official/event/evaluation badge 구분
- 자신의 작업마다 구현 노트와 INDEX 갱신

팀원은 공식 행정 문구나 출처 URL·확인일을 생성하지 않는다. API가 반환한 승인 metadata를 그대로
표시한다.

## 3. 쓰기 가능·금지 경계

### 직접 작업 가능

- `apps/web/**`
- `tools/web-e2e/**`
- frontend 전용 test/doc
- 자신의 `docs/implementation-notes/IMP-*-web-*.md`
- 해당 구현 노트를 추가하는 `docs/implementation-notes/INDEX.md`

위 범위는 작성 책임이다. **자가 병합 가능 범위는 더 좁다:** `apps/web/src/**`,
`tools/web-e2e/e2e/**`, 정확히 하나의 신규 `IMP-*-web-*.md`와 그 한 행만 append한 INDEX다.
기존 note/INDEX 행 수정·삭제와 allowlist 밖으로 드나드는 rename은 owner review다.

### 읽기 전용

- `packages/shared-contracts/src/generated/api.ts`
- `contracts/fixtures/**`
- `docs/source-of-truth/**`, 관련 ADR·정책·계약 문서

### 직접 수정·자가 병합 금지

- `contracts/**`, `packages/shared-contracts/**`
- `apps/api/**`
- `database/**`, `supabase/**`
- `data/official/**`, `data/staging/**`
- privacy/security/approval source-of-truth와 ADR
- `.github/**`, root toolchain/runtime 설정
- `package.json`, `pnpm-lock.yaml`, `tools/web-e2e/package.json`, `tools/web-e2e/pnpm-lock.yaml`
- `.env*` 실제 값, secret, token, 시민 질문·응답 원문

필요한 변경은 Issue로 요청하고 owner의 별도 PR을 기다린다. 새 production dependency는 사용자의
명시적 승인이 없으면 추가하지 않는다.

## 4. 현재 구현 상태와 작업 순서

현재 `/`와 입력·저장·fetch가 없는 정적 `/chat` 준비 화면만 구현돼 있다. `/admin`은 없다.
공식 seed는 아직 실제 DB에서 통과하지 않았고 `/ready=503`이 정상이다. chat/admin backend도
Blocked이므로 가짜 성공 API나 가짜 공식 데이터를 만들어 연결하지 않는다.

### Lane F0 — onboarding과 baseline

1. private repository clone과 runtime version 확인
2. frozen install과 현재 frontend gate 재현
3. `/`와 정적 `/chat`을 390/430/desktop·keyboard로 확인
4. 문서만 바꾸는 첫 test PR로 branch/CI/self-merge 절차 리허설

### Lane F1 — fixture 기반 chat 표현 계층

Backend API를 기다리는 동안 승인된 `contracts/fixtures/chat-response/**`와 generated type을 사용해
SUCCESS, FOLLOWUP, FALLBACK, office 없음, 503·retry UI를 순수 component/state fixture로 구현할 수
있다. 실제 입력 전송과 network client 활성화는 API-CHAT-001/READY 의존성이 풀릴 때까지 분리한다.

### Lane F2 — `/chat` 실제 API 연결

API-CHAT-001이 Ready/Done이 되면 typed client, current-tab transcript, 15분 client-carried context,
중복 전송 차단, timeout/503/retry, 새로고침 시 메모리 소멸을 연결한다. browser storage·raw request
log·URL query에 질문이나 token을 넣지 않는다.

### Lane F3 — `/admin`

ADMIN 계약과 LOG-001 endpoint가 준비되면 실패 질문 목록/필터/상세/만료 빈 상태, 후보 작성,
승인·반려, 역할 구분과 감사 metadata를 순서대로 연결한다. 계약 전에는 layout 탐색 Issue와
component 계획까지만 수행하고 임의 endpoint나 persistence를 만들지 않는다.

### Lane F4 — 회귀와 품질

REG-001 개선 전후 E2E, 쉬운 말·큰 글씨, 접근성 회귀, event/evaluation/mock badge, production build와
offline/error smoke를 닫는다.

## 5. 로컬 설정

요구 버전:

```text
Node 24.12.0
pnpm 11.13.0
Python 3.12.13 — frontend 전용 작업에서는 주로 검증 스크립트용
```

Windows PowerShell에서 저장소 루트 기준:

```powershell
corepack.cmd enable
corepack.cmd prepare pnpm@11.13.0 --activate
if ((node --version) -ne 'v24.12.0') { throw 'NODE_VERSION_MISMATCH' }
if ((corepack.cmd pnpm --version) -ne '11.13.0') { throw 'PNPM_VERSION_MISMATCH' }
corepack.cmd pnpm install --frozen-lockfile --ignore-scripts
corepack.cmd pnpm --filter @sejong-ai/web lint
corepack.cmd pnpm --filter @sejong-ai/web typecheck
corepack.cmd pnpm --filter @sejong-ai/web test
corepack.cmd pnpm --filter @sejong-ai/web build
node scripts/check_web_bundle_secrets.mjs apps/web/.next
corepack.cmd pnpm --dir tools/web-e2e install --frozen-lockfile --ignore-scripts
corepack.cmd pnpm --dir tools/web-e2e test
node scripts/check_web_prod_dependency_boundary.mjs
corepack.cmd pnpm --filter @sejong-ai/shared-contracts generate:check
corepack.cmd pnpm --filter @sejong-ai/shared-contracts test
git diff --check
```

전체 Windows baseline의 synthetic secret build/scan과 환경 복원까지 재현할 때는 Docker를 시작하지
않는 root gate도 실행한다. actual DB/data 검증은 이 명령이 아니라 owner의 별도 gate다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
```

브라우저가 처음인 Windows PC에서는 아래 명령으로 pinned Playwright의 Chromium을 설치한다. 새
dependency를 임의로 추가하지 말고 기존 `tools/web-e2e` lock을 사용한다.

```powershell
corepack.cmd pnpm --dir tools/web-e2e exec playwright install chromium
```

## 6. Git 작업 절차

```powershell
git switch main
git pull --ff-only origin main
git switch -c feat/web-<task-id>-<slug>
```

작업 중:

```powershell
git status --short
git diff --check
git diff --stat
```

작은 논리 단위로 commit하고 push한다.

```powershell
git add <검토한-파일만>
git commit -m "feat(web): <사용자에게 보이는 결과>"
git push -u origin feat/web-<task-id>-<slug>
```

PR에는 TASK ID, 사용자 흐름, 변경 파일, 테스트 실제 결과, 스크린샷, 접근성 확인, contract/API/data
변경 0 여부, 구현 노트를 적는다. 허용 범위를 벗어나거나 dependency/lockfile 변경이 있으면 자가
병합하지 않는다.

## 7. API/계약이 부족할 때

임시 필드를 public type처럼 추가하지 말고 다음 Issue를 만든다.

```text
[CONTRACT] <화면/상태>에 필요한 <필드 또는 endpoint>

- 관련 TASK:
- 막힌 사용자 흐름:
- 현재 계약/fixture 경로:
- 필요한 최소 request/response shape:
- 지금 가능한 안전한 fallback:
- mock이면 시연용 샘플 표시:
- 원하는 준비 시점:
```

Backend owner가 계약·fixture·generated type을 함께 갱신하면 해당 commit을 반영해 integration을
진행한다.

## 8. 절대 금지

- 시민 질문, 답변, PII, API key, DSN, token을 Git·Issue·PR·screenshot·CI log에 넣기
- 출처명·URL·확인일을 frontend에서 생성하거나 보정하기
- `ACTIVE`가 아닌 KB를 시민 답변에 표시하기
- OUT_OF_SCOPE 원문 저장, FOLLOWUP을 실패 질문처럼 표시하기
- mock을 official처럼 표시하기
- 실제 GPS·지도·신청/상태조회·다국어·음성 등 P2를 추가하기
- contract가 없다는 이유로 backend/DB를 frontend PR에서 수정하기

## 9. 장애와 롤백

- CI 실패: 병합하지 않고 원인을 수정한 동일 PR에서 재검증한다.
- API 미준비: fixture component까지만 유지하고 실제 fetch를 feature flag처럼 가장하지 않는다.
- 잘못 병합: history rewrite/force push 대신 revert PR을 만든다.
- secret 의심: 출력·복사하지 말고 즉시 사용자에게 경로와 유형만 알린다.
- `main` 실패: 추가 병합을 멈추고 마지막 green commit과 실패 PR을 사용자에게 알린다.

## 10. 첫 PR 인수 기준

- branch 이름과 TASK ID가 규칙에 맞는다.
- user-visible behavior가 없는 onboarding/test PR이다.
- frontend gate와 scope CI가 모두 통과한다.
- 금지 파일, dependency, secret, official/mock 데이터 변경이 0이다.
- 구현 노트가 있고 사용자가 첫 self-merge 리허설 결과를 확인한다.

## 11. 인간이 반드시 알아야 하는 내용

- GitHub Free에서는 자가 병합 경계를 GitHub가 완전히 강제하지 못한다.
- 팀원은 frontend 구현자이지 API·DB·공식 데이터·PM 승인자가 아니다.
- `/ready=503`, DeepSeek local 합성 전용, public/admin 차단은 현재 정상 상태다.
- 새 production dependency, public contract, DB migration, 데이터 삭제, 배포는 사용자 승인 사항이다.

## 12. AI 내부 구현 세부

component 파일 분리, private helper, fixture adapter, test factory, 명명·formatting은 공개 계약과
인수 기준을 바꾸지 않는 한 팀원이 자율 처리할 수 있다.
