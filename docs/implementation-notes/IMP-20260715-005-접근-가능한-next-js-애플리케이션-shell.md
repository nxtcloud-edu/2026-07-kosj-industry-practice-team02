# IMP-20260715-005 — 접근 가능한 Next.js 애플리케이션 shell

- Date/Time (KST): 2026-07-15T04:16:09+09:00 (문서 마감 시각; 구현 시작 시각은 별도 계측하지 않음)
- Task ID: DEV-001C
- Type: implementation
- Status: Done
- Author/Agent: `dev001c_implementer`(TDD·초기 코드), Codex `/root`(의존성·호환성 수정·빌드·브라우저 QA), `dev001c_code_reviewer`(독립 검토), `dev001c_docs_implementer`(구현 노트 작성)
- Branch: `codex/DEV-001-repo-scaffold`
- Base commit: `59d9b27`
- Related plan/ADR/RFP: PLAN-20260715-002 Task 3, TEAM_DECISIONS 제품·기술 범위, RFP `COR-002`·`QUR-001`, 후속 `WEB-HOME-001`

## 1. 사용자 요청과 완료 기준

### 요청

- 승인된 Phase 1을 계속 진행하되, 코딩은 구현 에이전트에게 위임하고 중요한 의존성·명령·코드·검토는 `/root`가 통제한다.
- 이번 단위에서는 제품 기능을 넓히지 않고 최소 Next.js Web shell을 만든다.

### Acceptance Criteria

- 활성 Web 앱은 `/` 하나만 제공하고 `/chat`·`/admin` 제품 동작이나 죽은 링크를 만들지 않는다.
- 서비스명, 핵심 원칙, 승인된 네 지원 분야와 “채팅·민원 신청·개인 조회·공식 KB 미제공” 개발 한계를 사실대로 표시한다.
- 의미론적 `header`·`main`·`section`·`footer`, 정확히 한 개의 `h1`, 본문 바로가기와 지원 분야 내부 링크를 제공한다.
- 기본 본문은 18px 이상, 주요 색상 대비는 4.5:1 이상이며 390/430px에서 가로 넘침이 없다.
- client component, API fetch, 환경변수, browser storage, cookie, analytics, 외부 폰트·이미지는 0건이다.
- 승인된 exact dependency만 사용하고 frozen install, lint, typecheck, unit test, production build, 브라우저 QA를 통과한다.
- 공개 API·DB·데이터·프롬프트·LLM 호출은 변경하거나 실행하지 않는다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 구현을 승인했고, 구현 에이전트가 RED→GREEN 코드를 작성했으며 `/root`가 dependency·lock·도구 호환성·브라우저 결과를 통제했다. 이 노트는 문서 전담 에이전트가 동기화했고 최종 완료 판정은 `/root` 리뷰 후 남아 있다. |
| When — 언제 | 2026-07-15 KST, Phase 1 Task 3; 문서 마감 04:16:09 |
| Where — 어디서 | 격리 worktree의 `apps/web`, root pnpm lock, TASKS/plan/version/changelog/implementation note |
| What — 무엇을 | Next.js App Router 정적 홈 shell, 반응형·접근성 CSS, 렌더 단위 테스트, exact Web manifest와 lock을 추가했다. |
| Why — 왜 | `/chat` 기능 전에도 제품 정체성·지원 범위·현재 한계를 과장 없이 보여 주고, 후속 시민 UI가 올라갈 재현 가능한 기반을 마련하기 위해서다. |
| How — 어떻게 | missing-Vitest RED, server component와 semantic markup, Tailwind CSS v4+로컬 CSS, Vitest Oxc JSX transform, ESLint 9 호환 조정, frozen install·품질 gate·실제 production browser QA로 구현했다. |
| How much — 어느 정도 | Web runtime dependency 3개, dev dependency 13개, test file 1개/4 tests, 정적 route 1개, 지원 분야 4개, 외부 asset/API/DB/data/LLM 호출 0건, 인프라 비용 0원 |

## 3. 시작 전 상태

- 관련 파일: `apps/web/README.md` placeholder, root runtime/workspace 계약, wireframe와 source-of-truth, PLAN-20260715-002 Task 3.
- 기존 동작: 활성 Web manifest·source·test·lock과 실행 가능한 route가 0개였고 README는 “스캐폴딩 전”이라고 표시했다.
- 발견한 충돌/부채:
  - 후속 전체 범위에는 `/chat` 진입이 필요하지만, DEV-001C에는 채팅 동작이 없으므로 dead `/chat` CTA를 만들 수 없었다.
  - ESLint 10.7.0 후보는 `eslint-config-next@16.2.10`에 포함된 `eslint-plugin-react@7.37.5`의 peer 범위를 벗어나 lint가 실행 중 예외로 종료됐다.
  - Vite 8/Vitest 4는 `esbuild` JSX 설정을 무시하고 Oxc를 사용하므로 초기 JSX transform 설정이 테스트와 typecheck를 동시에 깨뜨렸다.
  - 브라우저 플러그인은 키보드 Enter 입력 전달을 수락하지 않아 자동 키보드 활성화 증거를 만들 수 없었다.
- Git 상태: branch `codex/DEV-001-repo-scaffold`, base `59d9b27`, remote 0. 시작 시 Task 2 commit 이후 clean이었고, Task 3 변경은 최종 commit 전이다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| WEB-CTA-PRECHAT | Resolved | 채팅 미구현 상태의 진입 링크 | `/chat` 링크를 만들지 않고 `#supported-services` 내부 링크와 명시적 개발 한계를 제공 | 사용자 신뢰·후속 WEB-HOME-001 |
| WEB-ESLINT-COMPAT | Resolved internal | ESLint 10.7 후보와 bundled plugin 비호환 | 같은 승인된 dev package의 exact `eslint@9.39.5`로 조정; 새 package 0 | lock·local quality gate |
| WEB-JSX-TOOLING | Resolved internal | Next build/TS와 Vitest의 JSX transform 차이 | TS `jsx=react-jsx`, Vitest `oxc.jsx.runtime=automatic` | test/typecheck/build |
| WEB-KEYBOARD-ACTIVATION | Deferred verification | 자동 Enter 활성화 미검증 | native semantic anchor, visible focus ring, click activation·focus 이동을 확인; 완전한 keyboard E2E는 후속 접근성 gate | QUR-001·A11Y-001 |
| WEB-200-ZOOM | Deferred verification | 200% 확대 검증 | 이번 task의 390/430 overflow 검증까지만 기록; A11Y-001에서 확대·전체 제품 UI 검증 | 접근성 완료 범위 |

## 5. 설계 결정과 대안

### 선택

- `page.tsx`를 client directive가 없는 순수 server component로 두고 정적 `/`만 생성한다.
- 사용자에게 보이는 CTA는 구현된 내부 section으로만 연결한다.
- 공식 데이터가 없음을 개발 공지에서 직접 밝히고, 네 분야를 “지원 완료”가 아닌 “먼저 준비하는 범위”로 표현한다.
- 시스템 한글 font stack과 로컬 CSS만 사용하며 외부 asset 요청을 만들지 않는다.
- base font 18px, 명확한 focus ring, mobile-first grid와 `minmax(0, 1fr)`를 적용한다.
- Vitest 4/Vite 8의 내장 Oxc automatic JSX runtime을 사용한다.

### 이유

- 구현되지 않은 채팅·공식 KB를 제공하는 것처럼 보이지 않으면서도 제품 정체성과 범위를 검증할 수 있다.
- server-only 정적 shell은 개인정보·세션·네트워크 경계를 넓히지 않고 후속 UI의 접근성 기반을 만든다.
- Oxc 설정은 새 plugin dependency 없이 현재 exact toolchain에서 test와 Next build를 함께 만족한다.

### 고려했지만 선택하지 않은 대안

- `/chat` placeholder 또는 dead CTA: 사용자가 실제 기능으로 오인할 수 있어 제외했다.
- client state·fetch·analytics·cookie: DEV-001C 범위 밖이며 개인정보/오류 경계를 불필요하게 넓혀 제외했다.
- `@vitejs/plugin-react` 추가: Oxc로 해결 가능하고 새 dev dependency가 불필요해 제외했다.
- ESLint 10.7 유지: bundled plugin runtime 예외가 재현되어 제외했다.
- 외부 웹폰트·이미지: 네트워크·privacy·빌드 변수를 늘리므로 제외했다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `apps/web/package.json` | package 0.1.0, exact Next/React runtime와 exact dev tooling, dev/build/start/lint/typecheck/test scripts | 재현 가능한 Web 경계 |
| `pnpm-lock.yaml` | workspace root frozen lock | dependency graph 고정 |
| `apps/web/next.config.ts`, `postcss.config.mjs` | 최소 Next·Tailwind v4 build 설정 | 승인된 stack 활성화 |
| `apps/web/tsconfig.json`, `next-env.d.ts` | strict TS, Next generated types, `react-jsx` | build/typecheck 정합 |
| `apps/web/eslint.config.mjs` | Next core-web-vitals/TypeScript flat config와 build artifact ignore | framework lint gate |
| `apps/web/vitest.config.ts`, `src/test/setup.ts` | jsdom·jest-dom과 Oxc automatic JSX | React render unit test |
| `apps/web/src/app/layout.tsx` | 한국어 문서, 서비스 metadata, global CSS | App Router root layout |
| `apps/web/src/app/page.tsx` | 서비스 소개, 원칙, 네 분야, 개발 한계, semantic landmarks·내부 links | 사실 기반 최소 홈 shell |
| `apps/web/src/app/globals.css` | system fonts, 18px base, contrast/focus, mobile-first responsive cards | 접근성·반응형 기반 |
| `apps/web/src/app/page.test.tsx` | identity/h1, internal link, four services, limitations/landmarks 4 tests | scope·semantic 회귀 |
| `apps/web/README.md` | 현재 정적 범위와 local 명령 | 신규 개발자 재현 |
| `.gitignore` | `*.tsbuildinfo` build cache 제외 | 임시 산출물 커밋 방지 |

### 데이터 흐름/상태 변화

- build-time: source/CSS → Next static route `/`와 정적 asset.
- run-time: 브라우저 GET `/` → 정적 markup/CSS. API fetch·environment·storage·cookie·analytics·외부 asset 요청 0.
- 사용자가 내부 링크를 활성화하면 같은 문서의 `#main-content` 또는 `#supported-services`로만 이동한다. 서버 상태와 데이터는 바뀌지 않는다.

### 오류·빈 상태·롤백

- 제품 데이터가 없는 상태를 숨기지 않고 채팅·신청·개인 조회·공식 KB가 아직 제공되지 않는다고 표시한다.
- `/chat`·`/admin` route를 만들지 않아 미완성 제품 경로의 오류 처리를 가장 좁은 범위로 제한한다.
- DB migration·외부 상태·사용자 데이터가 없어 rollback은 task 파일/commit 단위다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.0.1-api-scaffold | 0.0.2-web-api-scaffold | API에 이어 실행 가능한 Web 정적 shell 추가 |
| Web | 0.0.0-not-scaffolded | 0.1.0 | 첫 Next.js App Router package·route·test·build |
| API public contract | 2.0.0-draft | 동일 | API·contract 변경 0 |
| DB schema | 0.2.0-draft | 동일 | migration/연결 0 |
| Official data | 0.0.0-not-populated | 동일 | 공식 KB/기관 데이터 0 |
| Mock data | 0.0.0-not-populated | 동일 | 행정 mock data 0 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | prompt/LLM 코드·호출 0 |
| Test suite | 0.3.2-api-health | 0.3.3-web-shell | Web render/semantic tests 4개와 browser smoke 추가 |
| Repo guidance | 1.3.0 | 동일 | 공통 지침 변경 0 |
| Docs | 2.3.4 | 2.3.5 | Web README·plan·backlog·changelog·note 동기화 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `PNPM_CONFIG_VERIFY_DEPS_BEFORE_RUN=false PNPM_CONFIG_OFFLINE=true corepack pnpm --filter @sejong-ai/web run test` (source/install 전) | expected RED, exit 1: `vitest` not recognized | test runner 0 | implementer report |
| `corepack pnpm install --lockfile-only --ignore-scripts` | PASS, root lock 생성/갱신 | install script 0 | `pnpm-lock.yaml` |
| `corepack pnpm install --frozen-lockfile --ignore-scripts` | PASS | 422 packages | controller terminal |
| 최초 `pnpm --filter @sejong-ai/web test` | expected FAIL: JSX를 Oxc가 transform하지 못함 | test collection 전 실패 | controller terminal |
| 최초 `pnpm --filter @sejong-ai/web lint` | expected FAIL: ESLint 10과 bundled `eslint-plugin-react` runtime 비호환 | lint 실행 중 exception | controller terminal |
| 임시 `esbuild.jsx=automatic` 뒤 typecheck/test | expected FAIL: Vite 8이 esbuild를 무시하고 설정 type도 거부 | compatibility diagnosis | controller terminal |
| `corepack pnpm --filter @sejong-ai/web test` (Oxc 수정 후) | PASS | 1 file, 4 tests | controller terminal |
| `corepack pnpm --filter @sejong-ai/web typecheck` | PASS | TypeScript 오류 0 | controller terminal |
| `corepack pnpm --filter @sejong-ai/web lint` | PASS | ESLint finding 0 | controller terminal |
| `corepack pnpm --filter @sejong-ai/web build` | PASS | Next 16.2.10, static `/` 1 route | controller terminal; `.next` |
| production browser QA, 390px viewport | PASS | browser `clientWidth=375`; horizontal overflow·overflower 0 | in-app browser session |
| production browser QA, 430px viewport | PASS | browser `clientWidth=415`; horizontal overflow·overflower 0 | in-app browser session |
| browser semantic/asset/console 검사 | PASS | h1 1; href는 `#main-content`, `#supported-services`만; external asset 0; console warn/error 0 | in-app browser session |
| browser focus/click 검사 | PASS | focus ring visible; click 후 hash와 focus가 main으로 이동; key text ≥18px; link 높이 57.7px | in-app browser session |
| 색상 대비 계산 | PASS | `#3f4d66/#f4f7fb` 7.93:1; `#084fb7/white` 7.47:1; `#063b88/white` 10.56:1; `#14213d/white` 15.97:1 | controller calculation |

### 미실행 검증과 이유

- 자동 키보드 Enter 활성화: 브라우저 플러그인이 key delivery를 수락하지 않아 실행하지 못했다. native anchor semantic·focus-visible과 click activation은 확인했지만 Enter 자동화 통과로 과장하지 않는다.
- 200% 확대, screen reader, 전체 `/chat`·`/admin` 접근성: 해당 제품 route가 없으며 A11Y-001/후속 Web vertical slice 범위다.
- API·contract·DB·data·prompt·LLM·provider 검증: 이 task에서 해당 항목을 변경하거나 호출하지 않았다. 기존 API gate의 전체 재실행은 Phase 1 통합 gate에서 수행한다.
- 성능 부하·100명 smoke: 정적 build sanity만 이번 범위이며 PERF-001에서 측정한다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문·PII·token 입력/저장/로그/전송 경로가 없고 browser storage·cookie·analytics·외부 asset 요청이 0건이다.
- Security: client component·API 호출·environment access·secret 이름이 없다. 이번 task는 env/log/bundle secret 자동 검사 자체를 구현하지 않으며 DEV-002A에 남긴다.
- Accessibility: `lang=ko`, semantic landmarks, h1 1개, skip link, 내부 CTA, 18px base, visible focus, reduced-motion 처리, 390/430 no overflow와 WCAG AA 이상 대비를 확인했다. 자동 Enter와 200% 확대는 미검증이다.
- Performance/cost: static `/`이고 외부 network/LLM/DB가 없어 운영 API 비용 0원이다. production build만 확인했으며 p95/부하 보증은 하지 않는다.

## 10. 데이터와 출처 영향

- 공식 데이터: 작성·승인·표시·ACTIVE 전환 0건. 네 분야 명칭은 source-of-truth의 승인된 제품 범위이며 행정 절차·수수료·기관 값은 표시하지 않는다.
- mock/AI 생성: 행정 mock record 0건. 화면 문구와 test expectation은 제품 scaffold이며 공식 데이터/KPI가 아니다.
- schema/lineage: OpenAPI·JSON Schema·DB schema·data version/lineage 변경 0.
- verified date: Web dependency/build/UI 동작은 2026-07-15 KST 검증. 공식 행정 데이터의 verified date는 해당 없음.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 현재 Web은 개발용 정적 소개 `/`만 동작한다. 채팅 답변, 신청, 개인 조회, 공식 KB와 `/chat`·`/admin`은 아직 제공하지 않는다.
- runtime dependency는 승인된 exact `next@16.2.10`, `react@19.2.7`, `react-dom@19.2.7`뿐이며 새 production dependency는 없다.
- 초기 ESLint 10.7.0 후보는 bundled plugin과 호환되지 않아 같은 승인된 dev package의 `9.39.5`로 exact 조정했다. 사용자 동작·공개 계약·운영 비용은 바뀌지 않는다.
- 공개 API 2.0.0-draft, DB, 공식/mock 데이터, DeepSeek, 배포/CORS/비밀 정책은 변경하지 않았다.
- 자동 키보드 Enter와 200% 확대는 아직 검증되지 않았으며 완료했다고 간주하지 않는다.
- fresh 독립 리뷰는 코드·task·lock 기준 P0/P1/P2 0으로 승인했고, `/root`가 완료 상태와 문서·버전을 동기화했다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- Next build가 `next-env.d.ts`를 생성했고 strict TS의 JSX mode는 `react-jsx`로 고정됐다.
- Vitest/Vite 8은 deprecated esbuild 설정 대신 `oxc.jsx.runtime=automatic`을 사용한다.
- ESLint flat config는 Next core-web-vitals·TypeScript preset과 build/generated artifact ignore만 포함한다.
- 390/430 browser outer viewport에서 vertical scrollbar 때문에 실제 client width가 각각 375/415였고, 두 client width 모두 overflow element 0이었다.

## 13. 인수인계·재현·롤백

### 재현

1. 저장소 root에서 `.node-version=24.12.0`, `packageManager=pnpm@11.13.0`을 확인한다.
2. `corepack pnpm install --frozen-lockfile --ignore-scripts`를 실행한다.
3. `corepack pnpm --filter @sejong-ai/web test`, `typecheck`, `lint`, `build`를 순서대로 실행한다.
4. `corepack pnpm --filter @sejong-ai/web start`로 production build를 띄워 `/`를 390/430px에서 확인한다.
5. h1 1개, 내부 link 2개, 네 지원 분야, 개발 한계, console error/warn 0과 external asset 0을 확인한다.

### 롤백

- task commit 이후에는 history를 지우지 않고 `git revert <DEV-001C-commit-sha>`를 사용한다.
- commit 전 긴급 복구가 필요하면 `git status`로 Task 3 소유 경로를 먼저 식별한 뒤 tracked Task 3 파일만 `git restore -- <scoped-paths>`하고, Task 3가 만든 untracked 경로만 별도로 제거한다. 이 노트 작성 중 해당 명령을 실행하지 않았다.
- `node_modules`, `.next`, `*.tsbuildinfo`는 ignored 재생성 cache다. DB/data migration·외부 상태가 없어 데이터 backup/복구나 보상 rollback은 필요 없다.

### 다음 개발자 시작점

- DEV-001C 완료 delta는 독립 리뷰를 통과했다. task commit은 이 노트를 포함해 바로 생성하고, 이후 작업은 해당 commit을 기준으로 시작한다.
- 다음 수직 흐름은 PLAN-20260715-002 Task 4 `DEV-002A`: 서비스별 env, metadata-only logging, secret/browser bundle scan이다.
- Task 4와 독립적으로 준비 가능한 다음 계약 흐름은 `CONTRACT-001A`이며, 상위 `DEV-002`·`CONTRACT-001`은 각 하위 전체가 끝날 때까지 Blocked다.

## 14. 남은 위험·미해결 질문·다음 단계

- task commit 생성은 다음 housekeeping 단계이며, 제품 인수 기준과 독립 검토는 완료됐다.
- 자동 키보드 Enter, 200% 확대, screen reader는 미검증이다.
- env allowlist, raw-body logging 방지, browser bundle secret scan은 DEV-002A 전까지 자동화되지 않았다.
- `/chat`·`/admin`, 실제 공식 KB, 오류·빈 상태의 전체 제품 흐름은 후속 단계다.
- 원격 Git/CI가 없어 local 수동 gate와 단일 PC 위험이 유지된다.

## 15. 자체 리뷰

- [x] 요청과 DEV-001C 인수 기준을 실제 증거 범위 안에서 기록
- [x] RED→GREEN·frozen install·build·browser 검증 기록
- [x] 공개 계약/DB/data/prompt/provider 무변경과 version 동기화
- [x] 개인정보 원문·secret·공식/mock 데이터 노출 없음
- [x] 구현 노트 INDEX와 DEV-001C를 `Done` 상태로 갱신
- [x] `/root` complete-delta 검토와 fresh 독립 리뷰(P0/P1/P2 0)
