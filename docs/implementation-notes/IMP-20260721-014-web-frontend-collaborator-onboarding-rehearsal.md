# IMP-20260721-014 — web frontend collaborator onboarding rehearsal

- Date/Time (KST): 2026-07-21T16:33:16+09:00
- Task ID: COLLAB-ONBOARDING
- Type: web-onboarding
- Status: AI/local scope Done — hosted PR/CI/self-merge pending human (GitHub UI)
- Author/Agent: Claude Code (local, frontend teammate rehearsal 대행), 인간 결정자 사용자
- Branch: feat/web-COLLAB-ONBOARDING-doc-check
- Base commit: d54fd6f (= clone/pull 시점 최신 origin/main, PR #3 병합 반영)
- Related plan/ADR/RFP: `docs/handoffs/HANDOFF-20260720-FRONTEND-COLLABORATOR.md` §0 onboarding PR, Lane F0 step 4 / Task 5 PR-only, `AGENTS.md` §6, ADR-0019

## 1. 사용자 요청과 완료 기준

### 요청

Handoff §0 팀원 onboarding 절차를 이어서 수행한다: 문서만 바꾸는 첫 test PR로 branch/CI/self-merge
리허설. 신규 web 구현 노트 1개와 `docs/implementation-notes/INDEX.md` 마지막 1행 append,
정확히 2파일. `FRONTEND_SELF_MERGE_ELIGIBLE`이며 Frontend CI 포함 모든 check가 green일 때만 GitHub
화면에서 "Create a merge commit". 완료를 정해진 형식으로 보고하고, 확인 전 실제 화면 코딩 금지.

### Acceptance Criteria

- diff 정확히 2파일: 신규 `IMP-*-web-*.md` 1개(add-only)와 INDEX 마지막 1행 append.
- 금지 파일(`pnpm-workspace.yaml`, `package.json`, `pnpm-lock.yaml`, `.github/**`, `apps/api/**`,
  `contracts/**`, `packages/shared-contracts/**`, 생성물, manifest/lockfile 등) 변경 0.
- user-visible behavior·dependency/lockfile·secret·official/mock 데이터 변경 0.
- base = clone/pull 시점 최신 `origin/main`(특정 SHA 고정 금지). 현재 feat = `d54fd6f` = origin/main.
- 로컬 scope classifier가 `FRONTEND_SELF_MERGE_ELIGIBLE` 반환.
- frontend gate와 contract drift gate가 로컬 통과.
- 실제 PR open·hosted CI·self-merge는 GitHub/인간 단계로 정직히 구분 보고.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 인간 결정자(사용자, scope owner), 실행 에이전트(local Claude Code, teammate 대행), 검토자(owner) |
| When — 언제 | 2026-07-21 KST. 로컬 산출물·검증 완료; hosted PR/CI/merge 미실행 |
| Where — 어디서 | `feat/web-COLLAB-ONBOARDING-doc-check`, `docs/implementation-notes/` 2개 파일 |
| What — 무엇을 | 문서 전용 2파일 준비 + 로컬 gate/scope/secret/docs 검증 |
| Why — 왜 | branch/CI/self-merge 절차와 허용 경계를 코드 변경 없이 리허설 |
| How — 어떻게 | handoff §0 파라미터로 `new_implementation_note.py` 실행, PS 5.1 로컬 gate, python scope classifier |
| How much — 어느 정도 | 파일 2개, 코드 0줄, web unit test 6/6, 버전 축 불변 |

## 3. 시작 전 상태

- 관련 파일: `docs/implementation-notes/INDEX.md`, 신규 노트, `apps/web/**`(읽기만), 협업 정책 스크립트.
- 기존 동작: `/`와 입력·저장 없는 정적 `/chat`만, `/admin` 없음, `/ready=503` 정상.
- 발견한 충돌/부채와 교정:
  1. 작업 트리에 `pnpm-workspace.yaml`의 미커밋 placeholder 추가분이 있어, 승인(규칙 2 예외)받아
     `git restore`로 main과 동일 커밋 상태로 복원.
  2. 최초 시도는 stale `origin/main`(`ce8a608`) 기준이라 seq 003 충돌·실제 main(`b61f676`) 기준
     `OWNER_REVIEW_REQUIRED`. ff-sync 후 011로 재작성.
  3. 그 사이 PR #3이 병합되어 `IMP-20260721-011-cloud-docs-rehearsal.md`가 main에 추가돼 011이 다시
     충돌. `origin/main`을 `d54fd6f`로 ff-sync하고 feat를 재작성해 노트를 **012**로 재부여했다.
  - 교훈: self-merge 자격은 feat가 최신 main 위에 있을 때만 성립하며, 동시 PR로 main이 전진하면
    seq/삭제 충돌로 자격을 잃는다(moving target).
- Git 상태: feat head == local main == origin/main == `d54fd6f`.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| A-1 | 지시 | 노트 title/type이 handoff §0에 명시 | title `web frontend collaborator onboarding rehearsal`, type `web-onboarding` | 문서/분류 |
| A-2 | 블로커 | 로컬에 `gh` CLI 미설치 | `gh pr create`/`gh pr checks`/merge 불가 → 인간 GitHub 단계로 핸드오프 | 협업 절차 |
| A-3 | 정책 | self-merge는 hosted CI green + configured login(`koregy`) 기준 | 로컬 PASS는 hosted 증거 대체 불가; merge는 인간 UI 동작 | 협업 권위 |
| A-4 | 원격 | 동시 PR 병합으로 main이 반복 전진(seq 011 충돌) | 매번 ff-sync + renumber + force-with-lease로 수렴 | 원격 이력/타이밍 |

## 5. 설계 결정과 대안

### 선택

handoff §0 절차를 그대로 따라 지정 파라미터로 노트+INDEX를 생성해 add-only 2파일로 한정하고,
PR open/merge는 수행하지 않고 인간/hosted 단계로 넘긴다. base는 특정 SHA 고정 없이 최신 origin/main.

### 이유

`AGENTS.md` §6·handoff §11: local 에이전트는 스스로 merge하지 않으며 GitHub Free의 merge 버튼·green
CI는 인간 승인이 아니다. self-merge 자격은 hosted 워크플로가 `vars.FRONTEND_COLLABORATOR_LOGIN`과
base/head SHA로 판정한다. 로컬은 자격 "형태"만 증명 가능.

### 고려했지만 선택하지 않은 대안

- `gh` 설치 후 로컬 PR/merge: 새 도구·인증 도입 + 정책상 인간 단계 침범이라 배제.
- 낡은 base/충돌 seq 유지: 실제 base 기준 `OWNER_REVIEW_REQUIRED`라 배제, 재작성·renumber 선택.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `docs/implementation-notes/IMP-20260721-014-web-frontend-collaborator-onboarding-rehearsal.md` | 신규 노트 추가(add-only) | onboarding 리허설 기록 |
| `docs/implementation-notes/INDEX.md` | 마지막 행 1줄 append | 노트 인덱싱, self-merge 허용 형태 유지 |

### 데이터 흐름/상태 변화

없음. 런타임·API·DB·데이터·프롬프트 무변경. 문서 전용.

### 오류·빈 상태·롤백

롤백: 노트 삭제 + INDEX 마지막 행 제거, 또는 브랜치 폐기.

## 7. 버전 전후

### 생성 시 매니페스트
- product_spec: 2.2.5
- repo_guidance: 1.7.6
- application: 0.3.0-pii-core
- web: 0.2.0-static-chat-shell
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.3.0-local
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 1.0.0-collaboration
- documentation: 2.10.1

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.3.0-pii-core | 0.3.0-pii-core | 무변경 |
| Web | 0.2.0-static-chat-shell | 0.2.0-static-chat-shell | 무변경 |
| API | 2.0.1-draft | 2.0.1-draft | 무변경 |
| DB schema | 0.3.0-local | 0.3.0-local | 무변경 |
| Official data | 0.0.0-not-populated | 0.0.0-not-populated | 무변경 |
| Mock data | 0.0.0-not-populated | 0.0.0-not-populated | 무변경 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 0.0.2-deepseek-v4-flash-selected | 무변경 |
| Test suite | 1.0.0-collaboration | 1.0.0-collaboration | 무변경 |
| Docs | 2.10.1 | 2.10.1 | 매니페스트는 2파일 범위 밖이라 미변경 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `pnpm install --frozen-lockfile --ignore-scripts` | PASS exit 0 | 이미 최신 | 세션 로그 |
| `pnpm contracts:check` | PASS exit 0 | drift 0 | 세션 로그 |
| `pnpm --filter @sejong-ai/web lint` | PASS exit 0 | - | 세션 로그 |
| `pnpm --filter @sejong-ai/web typecheck` | PASS exit 0 | - | 세션 로그 |
| `pnpm --filter @sejong-ai/web test` | PASS exit 0 | 6/6 | 세션 로그 |
| `pnpm --filter @sejong-ai/web build` (synthetic sentinel env) | PASS exit 0 | `/`,`/chat` static | 세션 로그 |
| `check_collaboration_scope.py` (base=origin/main, head=feat, koregy) | FRONTEND_SELF_MERGE_ELIGIBLE | §14 | 세션 로그 |
| `check_repository_docs.py --repository-root .` | passed | - | 세션 로그 |
| `check_secret_patterns.ps1 -RepositoryRoot .` | exit 0 | - | 세션 로그 |

### 미실행 검증과 이유

- hosted Frontend CI / Collaboration policy: PR이 GitHub에 열려야 실행되며 `gh` 미설치·인간 단계라 미실행.
- `tools/web-e2e` Playwright E2E, bundle secret scan, prod dependency boundary: 문서 전용 범위(코드 변경 0)라 생략. 필요 시 별도 실행.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 시민 질문/답변/PII 없음. 문서 전용.
- Security: secret/token/DSN/키 미포함. 로컬 secret 패턴 스캔으로 확인.
- Accessibility: UI 변경 없음.
- Performance/cost: 영향 없음.

## 10. 데이터와 출처 영향

- 공식 데이터: 무변경.
- mock/AI 생성: 없음.
- schema/lineage: 무변경.
- verified date: 해당 없음.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- **local Claude는 PR open·merge를 수행하지 않았다**: (1) `gh` CLI 미설치, (2) `AGENTS.md`
  §6/handoff §11 — merge는 인간 GitHub UI 단계이며 merge 버튼·green CI는 인간 승인이 아님, (3)
  hosted CI 통과 증거는 로컬 PASS로 대체 불가.
- **moving-target 주의**: 동시 PR로 `origin/main`이 전진하면 feat가 뒤처져 seq 충돌/삭제 diff로
  `OWNER_REVIEW_REQUIRED`가 된다. force-with-lease 재반영 직후 main이 정지한 짧은 창에서 인간이 PR
  open→CI green→merge를 신속히 진행해야 한다.
- **self-merge 자격**: PR author == configured `koregy`이고 2파일 add-only일 때만
  `FRONTEND_SELF_MERGE_ELIGIBLE`. 로컬 git author는 `Jungha Kim`이므로 실제 push 계정이 `koregy`인지
  인간이 확인. 병합 방식은 "Create a merge commit"만.
- 첫 실제 제품 작업(Lane F1 `/chat` fixture)은 owner가 shared-contracts 소비 경계를 준비·검토하고
  별도 `WEB-CHAT-FIXTURE-*` TASK를 내리기 전까지 시작하지 않는다(handoff §0.3).

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- 노트 파일명 slug는 classifier 정규식 `IMP-YYYYMMDD-NNN-web-[a-z0-9]+(-[a-z0-9]+)*\.md`를 만족.
- INDEX append는 full-context diff 기준 마지막 단일 `+` 라인이어야 하며 생성 도구가 이 형태를 보장.
- 최신 main엔 003~011이 있어 next sequence가 012로 자동 부여됨(011은 병합된 cloud-docs 노트가 점유).

## 13. 인수인계·재현·롤백

### 재현

1. `git switch main` → `git pull --ff-only origin main` → `git switch -c feat/web-COLLAB-ONBOARDING-doc-check`.
2. `python scripts/new_implementation_note.py --title "web frontend collaborator onboarding rehearsal" --task-id COLLAB-ONBOARDING --type web-onboarding`.
3. 노트 작성 후 `git add`로 노트 + INDEX만 → commit `docs(web): record frontend collaborator onboarding`.
4. `python scripts/check_collaboration_scope.py --base-sha $(git rev-parse origin/main) --head-sha $(git rev-parse HEAD) --pr-author koregy --frontend-login koregy`.

### 롤백

노트 삭제 + INDEX 마지막 행 제거, 또는 브랜치 폐기. history rewrite/force push는 인간 승인 하에서만; 잘못 병합 시 revert PR.

### 다음 개발자 시작점

인간이 최신 remote main 기준 PR을 열고 hosted Frontend CI + Collaboration policy green +
`FRONTEND_SELF_MERGE_ELIGIBLE`을 확인한 뒤 GitHub UI "Create a merge commit"으로 self-merge 리허설을 마감한다.

## 14. 남은 위험·미해결 질문·다음 단계

- 다음 단계(인간): feat 원격 반영(완료 시점) → PR open(문서 전용) → `gh pr checks --watch`/Actions에서
  hosted CI green + scope 분류 확인 → "Create a merge commit" → 결과 사용자 확인.
- 위험: 실제 push 계정이 `koregy`가 아니면 강등; main이 또 전진하면 재-sync/renumber 필요.
- 실제 화면 코딩(Lane F1+)은 사용자 확인 전까지 시작하지 않음.

## 15. 자체 리뷰

- [x] 요청 충족 (handoff §0 지정 파라미터로 2파일 산출물·검증; hosted/merge는 인간 단계로 구분)
- [x] 테스트/검증 (frontend gate + contract drift PASS, scope/docs/secret 로컬 재검증)
- [x] source-of-truth/계약/버전 동기화 (버전 축 불변, 매니페스트 미변경)
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
