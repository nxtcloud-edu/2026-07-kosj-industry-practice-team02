# Handoff — 로컬·Codex Cloud·Frontend 현재 실행 레인

- Date: 2026-07-22 KST
- Branch/commit: `codex/COLLAB-001-pr2-merge-evidence` / `b5d6780` at evidence capture
- Versions: documentation `2.10.7` before this handoff; application/API/DB/data unchanged

## Repository/collaboration state

- Source remote owner/name/visibility: private `tskwak111/Sejong_AI`
- Branch/upstream/verified SHA: owner worktree branch is clean and `origin/main`보다 7 commits ahead; captured `origin/main=d54fd6f`. Live remote state must be fetched/rechecked before push.
- Collaborator/App scope and acceptance state (no secrets/contact details): Frontend collaborator write access와 selected-repository Codex App scope는 확인됨. MFA/recovery yes/no는 Pending이며 인증·복구 값은 수집하지 않음.
- Open PRs and merge owner: owner Draft PR #5 `codex/COLLAB-001-pr2-merge-evidence → main`이 생성됐고 사용자 review/merge와 최종 hosted checks를 기다린다. PR #4 `feat/web-COLLAB-ONBOARDING-doc-check → main`은 OPEN/non-draft이나 duplicate note ID 때문에 계속 HOLD다. Corrected eligible Frontend-only PR may be self-merged by the Frontend collaborator; owner/Codex PR은 사용자가 검토·병합.
- Local-only pending gates: Windows Docker/Supabase actual, DeepSeek actual, future approved seed/runtime gates. Cloud PASS로 대체하지 않음.
- Revoke/revert path: unexpected remote mutation은 추가 merge를 중단하고 small revert PR 사용. collaborator/App access는 GitHub 설정에서 revoke. force-push/history rewrite 금지.

## 완료

- Private GitHub bootstrap과 PR #1~#3 human merge/post-merge CI 완료.
- Codex Cloud exact runtime/clean-tree/zero-use evidence 완료.
- Frontend onboarding PR #4 생성과 CI mergeability 확인 완료.
- PR #4의 teammate `IMP-20260721-012`와 owner local `IMP-20260721-012`의 논리 ID 충돌 확인, teammate용 `014` 예약.
- owner lane의 012/013/015/016과 20260722-001 가이드가 로컬 커밋으로 준비됨.

## 현재 실행 순서

### 1. Local owner lane — 가장 먼저

1. 완료: owner branch 전체 diff와 비밀·문서·history·scope·Git 검사를 실행했다.
2. 완료: `codex/COLLAB-001-pr2-merge-evidence`를 원격 작업 브랜치로 normal push했다. `main` 직접 push는 0이다.
3. 완료: Draft owner-review PR #5를 생성했다.
4. Pending: 사용자가 파일·CI를 검토하고 `Create a merge commit`으로 병합한다.
5. Pending: post-merge main CI가 green인지 확인한다.

이 단계가 끝날 때까지 PR #4를 병합하거나 새 Cloud write branch를 시작하지 않는다.

### 2. Frontend lane — owner PR 병합 뒤

PR #4를 새로 clone할 필요는 없다. 기존 브랜치에서 다음을 수행한다.

```powershell
git status --short --branch
git fetch origin
git switch feat/web-COLLAB-ONBOARDING-doc-check
git merge origin/main
```

merge 과정에서 `docs/implementation-notes/INDEX.md` 충돌이 나면 다음 결과를 보존한다.

- owner의 012/013/015/016 및 20260722-001 이후 행을 삭제하지 않는다.
- teammate note 파일명을 `IMP-20260721-012-web-...md`에서 예약된 `IMP-20260721-014-web-...md`로 변경한다.
- note 제목 내부 ID와 INDEX 링크/행도 012→014로 함께 변경한다.
- 기존 INDEX 행을 덮어쓰지 않고 teammate 014 행 하나만 유지한다.

그 뒤 문서·secret·diff 검사를 실행하고 일반 push로 PR #4를 갱신한다. force-push하지 않는다. GitHub PR diff가 최신 main 기준으로 teammate 014 note 1개와 INDEX append 1행뿐이고 필수 checks가 green이면 Frontend collaborator가 self-merge할 수 있다.

### 3. Codex Cloud lane — 지금은 write 대기

- owner PR이 열리면 Cloud는 secret 0/read-only PR 검토를 수행할 수 있다. 파일·commit·PR을 새로 만들지 않는다.
- owner PR과 corrected PR #4가 main에 병합된 뒤에만 최신 `main`에서 새 write task를 시작한다.
- Cloud는 Docker/Supabase actual, DeepSeek actual, local secret-bearing 실행을 맡지 않는다.
- 다음 제품 vertical slice의 Cloud 역할은 platform-neutral diff review·unit/docs/contract 검사다. actual DB/DeepSeek gate는 local lane에서 수행한다.

### 4. 협업 기준선 정리 뒤 제품 개발

- Local 우선 후보: `DATA-SEED-002` 승인 상태 재확인 후 Docker local actual을 포함한 immutable `.2` successor 작업.
- Cloud 병렬 후보: 같은 변경의 secret-free code review와 platform-neutral 검사.
- Frontend: onboarding PR 완료 뒤 exact task를 새 브랜치로 받는다. 현재 `WEB-CHAT-001`은 `API-CHAT-001`에 Blocked이므로 임의 API 연동이나 전체 프론트 구현을 시작하지 않는다.

## 왜 전체 pull만으로 충돌이 없어지지 않는가

일반 clone/pull은 **그 시점에 원격에 push된 tracked 파일과 commit**만 가져온다. 다음은 가져오지 못한다.

- 다른 사람 로컬의 uncommitted 변경
- 다른 사람 로컬의 committed-but-not-pushed 변경
- pull 이후 새로 생긴 변경
- `.gitignore` 대상 secret/runtime 파일

현재 teammate는 당시 최신 remote main을 정상적으로 받았지만 owner의 012 note는 로컬 commit에만 있어 볼 수 없었다. 그래서 양쪽 생성기가 모두 remote main의 마지막 번호 011을 보고 서로 다른 012를 만들었다. 이는 initial pull 실패가 아니라 concurrent unpublished work의 경합이다.

실제 Frontend 제품 작업을 `apps/web/src/**`에, owner 작업을 API/DB/data에 분리하면 텍스트 충돌 가능성은 크게 줄어든다. 그러나 `INDEX.md`, contracts, generated types, package manifests/lockfiles, 공통 config처럼 양쪽이 공유하는 파일은 여전히 사전 조율과 최신 main 반영이 필요하다.

## 실행/테스트 명령

Local owner PR 준비 시 최소 검증:

```powershell
git status --short --branch
git diff --name-status origin/main...HEAD
python -B scripts/check_repository_docs.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1 -RepositoryRoot .
git diff --check origin/main...HEAD
```

Frontend PR #4 correction 뒤:

```powershell
python -B scripts/check_repository_docs.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1 -RepositoryRoot .
git diff --check origin/main...HEAD
git status --short --branch
```

GitHub의 Collaboration policy와 Frontend CI summary도 모두 green이어야 한다.

## 환경변수 이름(값 제외)

- Current docs/onboarding correction에 필요한 secret 환경변수: 없음.
- Repository policy identifier: `FRONTEND_COLLABORATOR_LOGIN` (GitHub repository variable, secret 아님).
- Cloud 금지/미설정 유지: `DEEPSEEK_API_KEY`, `LLM_API_KEY`, `DATABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `CONTEXT_TOKEN_SECRET`.
- 실제 값은 이 handoff·채팅·commit·PR·CI 로그에 기록하지 않는다.

## DB migrate/seed/rollback

- 이 협업 정리 단계의 DB migration/seed/deletion: 0.
- `/ready=503` 유지.
- `DATA-SEED-002`는 별도 승인된 계획과 local Docker gate에서만 수행하며 Cloud 완료 증거로 대체하지 않는다.
- 잘못 병합한 문서 변경은 history rewrite가 아니라 small revert PR로 복구한다.

## 알려진 문제와 위험

- PR #4는 기계적으로 CLEAN이나 의미상 duplicate note ID가 있어 현재 병합 금지다.
- current branch의 7 owner commits가 remote main에 없으므로 새 write branch를 지금 만들면 같은 stale-base 경합이 반복될 수 있다.
- local 기본 worktree의 `main`도 최신 remote와 다를 수 있으므로 branch 생성 전 항상 fetch와 `pull --ff-only`가 필요하다.
- GitHub green check는 다른 unpublished branch의 논리 충돌을 검사하지 않는다.
- Frontend와 owner가 shared contracts/lockfiles/INDEX를 동시에 수정하면 pull을 했더라도 충돌 가능하다.

## 인간이 알아야 하는 결정

- 지금 사용자가 직접 수행할 필수 코딩은 없다. 다음 external action은 owner branch push/PR 생성과 사용자 merge review다.
- PR #4는 owner PR merge 뒤 corrected 014 diff와 green checks를 확인하고 self-merge한다.
- Cloud는 당장 새 write task가 아니라 owner PR read-only review 또는 main 정렬 이후 task만 수행한다.
- Product code, public deployment, remote DB, migration, official seed, new dependency 권한은 이 handoff로 확대되지 않는다.

## 다음 작업과 Acceptance Criteria

1. Owner PR: exact owner branch push, expected diff only, hosted policy/CI green, human merge, post-merge main green.
2. PR #4 correction: latest main merged without losing owner rows, teammate note exactly 014, expected two-file diff, policy/CI green, permitted self-merge.
3. Baseline sync: local main and any new Cloud/Frontend branch start from verified current `origin/main`.
4. Product continuation: DATA-SEED-002 approval/state recheck; local actual lane and Cloud review lane separated.

## 최근 구현 노트/ADR/계획 링크

- `docs/implementation-notes/IMP-20260721-016-구현-노트-번호-충돌-원인-설명.md`
- `docs/implementation-notes/IMP-20260722-001-git-협업-용어와-현재-저장소-상황-설명.md`
- `docs/adr/0019-private-github-role-scoped-collaboration.md`
- `docs/superpowers/plans/2026-07-20-github-codex-cloud-collaboration-transition.md`
- `docs/handoffs/HANDOFF-20260721-OWNER-GITHUB-CLOUD-CHECKLIST.md`
- `docs/handoffs/HANDOFF-20260720-FRONTEND-COLLABORATOR.md`
