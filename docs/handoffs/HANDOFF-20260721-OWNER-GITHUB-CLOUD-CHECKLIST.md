# 저장소 소유자 GitHub·Codex Cloud 실행 체크리스트

- 대상: 저장소 소유자 `tskwak111`, Frontend 협업자 `koregy`
- 적용 저장소 식별자: `tskwak111/Sejong_AI` (private)
- 상태: Task 4 완료, Task 5 일부 완료, Tasks 6~7 대기
- 원칙: `main` 직접 push 금지, Codex Cloud는 Draft PR까지만, 비밀·시민 원문은 GitHub/Cloud에 입력하지 않음

이 문서는 사람이 실제 화면에서 해야 하는 COLLAB-001 후속 작업을 실행 순서대로 설명한다. 공개 배포,
remote DB, DeepSeek 실호출, Docker/Supabase actual gate를 승인하거나 수행하는 문서가 아니다.

## 0. 가장 빠른 실행 순서

```text
지금: GitHub App 설정 확인 ─┐
                           ├─> PR #1 검토·병합
지금: koregy MFA 확인 ──────┘

PR #1 병합 뒤: Codex Cloud 문서-only 리허설 ─┐
                                             ├─> 두 PR 증거 확인 → COLLAB-001 마감 판단
PR #1 병합 뒤: koregy 온보딩·정책 리허설 ────┘
```

- GitHub App 확인과 `koregy` MFA 확인은 서로 독립이므로 동시에 해도 된다.
- PR #1은 App 설정이 `Only select repositories / Sejong_AI`임을 확인한 뒤 병합한다.
- Cloud와 팀원 리허설은 PR #1의 협업 정책 파일이 `main`에 들어간 뒤 서로 병렬로 진행한다.
- 체크리스트를 읽었다는 사실만으로 Tasks 5~7을 완료 처리하지 않는다. 실제 PR·CI·사람 확인이 필요하다.

## 1. 저장소 소유자 — GitHub App 범위 확인

공식 절차: [GitHub Apps 설치 검토·수정](https://docs.github.com/en/apps/using-github-apps/reviewing-and-modifying-installed-github-apps)

### 화면에서 할 일

1. GitHub에 `tskwak111` 계정으로 로그인한다.
2. 우측 상단 프로필 사진 → **Settings**를 누른다.
3. 왼쪽 **Integrations → Applications → Installed GitHub Apps**로 이동한다.
   바로 가기는 `https://github.com/settings/installations`이다.
4. `Sejong_AI`에 연결한 Codex/ChatGPT GitHub App을 찾아 **Configure**를 누른다.
5. **Repository access**를 확인한다.
   - 이미 **Only select repositories**이고 목록에 `Sejong_AI`만 있으면 올바르다. 변경하지 않는다.
   - **All repositories**이면 **Only select repositories**로 바꾸고 `Sejong_AI`만 선택한 뒤 **Save**를 누른다.
6. 화면의 **Permissions**도 읽어 보고, 예상하지 못한 관리자·비밀 권한이 보이면 저장하지 말고 작업을 중단해
   소유자 Codex 작업에 알려 준다.

### 헷갈리기 쉬운 점

GitHub 공식 문서에 따르면 GitHub App은 선택 설치와 별개로 공개 GitHub 저장소에 최소 read-only로 접근할
수 있다. 따라서 Codex 쪽 목록에 본인 공개 저장소가 같이 보이는 것은 `All repositories`의 증거가 아니다.
판정 기준은 위 설정 화면의 **Repository access** 값과 선택된 private 저장소 목록이다.

### 완료 보고 형식

다음 값만 알려 준다. 앱 권한 화면 전체 캡처, 다른 private 저장소 이름, 토큰은 보내지 않는다.

```text
GitHub App 확인 완료
- Repository access: Only select repositories
- Selected private repository: Sejong_AI
- Result: already configured / changed and saved
```

## 2. Frontend 팀원 `koregy` — MFA와 복구 수단 확인

이 작업은 계정 소유자인 `koregy`가 직접 한다. 저장소 소유자에게 QR 코드, OTP, recovery code, 전화번호,
비밀번호 또는 인증 화면 캡처를 공유하지 않는다.

공식 절차:

- [GitHub 2FA 설정](https://docs.github.com/en/authentication/securing-your-account-with-two-factor-authentication-2fa/configuring-two-factor-authentication)
- [GitHub 2FA 복구 수단](https://docs.github.com/en/authentication/securing-your-account-with-two-factor-authentication-2fa/configuring-two-factor-authentication-recovery-methods?apiVersion=2022-11-28)

### 팀원이 할 일

1. GitHub 로그인 → 프로필 사진 → **Settings**로 이동한다.
2. 왼쪽 **Access → Password and authentication**을 연다.
3. **Two-factor authentication** 상태를 확인한다.
   - 꺼져 있으면 **Enable two-factor authentication**을 누르고 passkey 또는 TOTP 인증 앱을 우선 설정한다.
   - 이미 켜져 있으면 현재 수단이 실제로 사용 가능한지만 확인한다.
4. **Two-factor methods**에서 두 번째 방법을 하나 더 구성한다. 예: passkey + TOTP, 또는 TOTP + 보안 키.
5. **Recovery codes → View**를 누른다.
6. **Download**, **Print**, 또는 **Copy** 중 하나로 복구 코드를 안전한 비밀번호 관리자나 오프라인 보관소에
   저장한다. 일반 메신저·Git 저장소·프로젝트 `.env`·스크린샷 폴더에 두지 않는다.
7. 팀원은 코드 값 없이 아래 완료 문장만 저장소 소유자에게 보낸다.

```text
koregy GitHub 보안 확인 완료
- 2FA: enabled
- second method: configured
- recovery codes: stored securely
```

개인 계정 소유 private 저장소이므로 현재 자동 조직 정책으로 이 상태를 강제·조회하지 않는다. 위 사람 확인이
Task 5 증거다.

## 3. 저장소 소유자 — Draft PR #1 검토와 병합

현재 PR은 협업 기반 문서·정책 증거만 담은 Draft PR이다. 제품 코드, 공개 API, DB, 공식 데이터, dependency,
배포 변경이 없어야 한다.

공식 절차:

- [Draft PR을 Ready로 변경](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/changing-the-stage-of-a-pull-request?apiVersion=2022-11-28)
- [Pull request 병합](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/merging-a-pull-request?tool=webui)

### 병합 전 확인

1. `tskwak111/Sejong_AI` → **Pull requests** → **#1**을 연다.
2. 상단에서 다음을 확인한다.
   - base: `main`
   - compare/head: `codex/COLLAB-001-bootstrap-evidence`
   - 상태: Draft
3. **Checks**에서 collaboration policy와 Frontend CI가 모두 초록색인지 확인한다.
4. **Files changed**를 열어 제품/API/DB/data/package/lockfile 변경이 없는지 확인한다.
5. 예상하지 못한 파일이나 빨간 검사가 하나라도 있으면 병합하지 말고 소유자 Codex 작업에 PR 번호와 실패한
   검사 이름만 알려 준다. 로그에 비밀처럼 보이는 값이 있으면 그 값은 복사하지 않는다.

### 병합

1. PR 하단 merge box에서 **Ready for review**를 누른다.
2. 검사가 여전히 초록색이고 merge conflict가 없음을 다시 확인한다.
3. 병합 방식 드롭다운에서 **Create a merge commit**을 선택한다. PR 페이지에 표시된 검토 완료 branch
   commit 계보를 보존하기 위한 기본값이다.
4. **Merge pull request → Confirm merge**를 누른다.
5. 병합 성공 뒤 **Delete branch**가 보이면 remote feature branch를 삭제해도 된다. `main`은 삭제하지 않는다.
6. 소유자 Codex 작업에 `PR #1 병합 완료`라고 알려 준다. Codex가 remote `main`과 병합 뒤 CI를 다시 검증한다.

`Squash and merge`와 `Rebase and merge`는 검토한 branch commit SHA를 새 SHA로 바꾸므로 기본값으로
사용하지 않는다. `main`에 직접 push하거나 force-push하지 않는다.

## 4. 저장소 소유자 — Codex Cloud 환경 만들기

PR #1 병합 확인 뒤 진행한다. 공식 개요는
[OpenAI Codex GitHub 환경 설정](https://help.openai.com/en/articles/11390924)과
[Codex Cloud 환경](https://learn.chatgpt.com/docs/environments/cloud-environment)을 따른다.

### 4.1 환경 생성

1. `https://chatgpt.com/codex`를 연다.
2. GitHub가 연결되지 않았으면 **Connect to GitHub**를 누르고 방금 확인한 App으로 연결한다.
3. `https://chatgpt.com/codex/settings/environments`로 이동해 **Create Environment**를 누른다.
4. repository로 `tskwak111/Sejong_AI`를 선택한다.
5. 환경 이름은 `sejong-ai-cloud-docs`로 한다.
6. Runtime/package 설정에서 선택할 수 있으면 Node `24.12.0`, Python `3.12.13`을 지정한다. exact patch를
   선택할 수 없는 UI라면 임의로 계속하지 말고 setup 검증 결과를 확인한다. pnpm과 uv도 아래 setup에서
   exact 버전을 확인한다.

### 4.2 Setup script

환경의 setup script에 아래 내용을 그대로 넣는다.

```bash
set -euo pipefail
corepack enable
corepack prepare pnpm@11.13.0 --activate
test "$(node --version)" = "v24.12.0"
test "$(corepack pnpm --version)" = "11.13.0"
test "$(python --version)" = "Python 3.12.13"
corepack pnpm install --frozen-lockfile --ignore-scripts
python -m pip install --disable-pip-version-check --user uv==0.11.28
UV_BIN="$(python -c 'import site; print(site.USER_BASE)')/bin/uv"
test "$("$UV_BIN" --version)" = "uv 0.11.28"
"$UV_BIN" sync --project apps/api --frozen
```

Setup은 별도 shell에서 실행되므로 `export`한 임시 값에 의존하지 않는다. dependency 설치를 위한 setup 인터넷은
사용할 수 있지만, agent 작업 중 인터넷 접근은 **Off**로 둔다. 나중에 인터넷이 꼭 필요한 별도 작업이 생기면
목적지 allowlist와 이유를 먼저 검토한다.

### 4.3 환경변수·비밀

이 리허설에는 환경변수와 secret을 **한 개도 추가하지 않는다**. 특히 다음은 금지한다.

- DeepSeek API key
- DB DSN, Supabase key 또는 local `.env` 값
- context-token secret
- 실제 시민 질문·연락처·주소가 포함된 fixture

설정을 저장한다. setup script나 runtime 설정을 나중에 바꿨다면 캐시를 reset한 뒤 다시 실행한다.

## 5. 저장소 소유자 — 첫 Codex Cloud Draft PR 리허설

새 Cloud 작업을 만들고 아래 프롬프트를 그대로 붙여 넣는다.

```text
TASK COLLAB-CLOUD-REHEARSAL-001 — docs-only Cloud rehearsal

먼저 AGENTS.md와 docs/superpowers/plans/2026-07-20-github-codex-cloud-collaboration-transition.md를 읽어라.

허용 변경은 정확히 두 가지다.
1) 새 docs/implementation-notes/IMP-*-cloud-*.md 파일 하나
2) docs/implementation-notes/INDEX.md 끝에 그 노트 행 하나 append

contracts, apps/api, apps/web, database, supabase, official/staging data, security/privacy source-of-truth,
.github, package manifest, lockfile는 수정하지 마라. 비밀, DeepSeek, Docker, DB, 배포를 사용하지 마라.

scripts/new_implementation_note.py로 노트를 생성하고, Cloud 환경에서 AGENTS를 읽고 문서 검사와 diff 검토를
수행했다는 사실만 기록하라. Windows/Docker/Supabase/DeepSeek/local-only gate는 Pending으로 명시하라.

branch는 codex/COLLAB-CLOUD-REHEARSAL-001-doc-check를 사용하고 Draft PR만 만들어라. 병합하지 마라.
실행할 검증:
python -B scripts/check_repository_docs.py
python -B scripts/check_current_tree_secrets.py --root .
git diff --check
git status --short
```

### 결과 확인

1. Cloud 작업 결과의 diff에서 새 `IMP-*-cloud-*.md` 1개와 INDEX append 1개만 있는지 확인한다.
2. Cloud UI의 **Create/Open pull request**를 눌러 PR을 만든다.
3. 반드시 **Draft** 상태인지 확인한다. Ready로 열렸다면 즉시 **Convert to draft**한다.
4. 병합하지 말고 PR 번호만 소유자 Codex 작업에 알려 준다.

이것이 실제 Task 6 리허설이다. 현재 PR #1은 local에서 작성한 bootstrap evidence PR이므로 Cloud 리허설을
대체하지 않는다.

## 6. Frontend 팀원 — clone과 기준선 검증

PR #1 병합 뒤 저장소 소유자가 private repository 페이지 링크를 개인 채널로 한 번만 전달한다. 토큰은 보내지
않는다. 팀원 Windows 환경 기준 명령이다.

### 6.1 GitHub CLI와 clone

GitHub CLI가 없으면 팀원이 PowerShell에서 다음을 실행한다.

```powershell
winget install --id GitHub.cli
```

새 PowerShell을 열고:

```powershell
gh auth login
gh repo clone tskwak111/Sejong_AI
Set-Location Sejong_AI
git switch main
git pull --ff-only origin main
```

`gh auth login`에서는 `GitHub.com → HTTPS → Login with a web browser`를 선택한다. PAT나 비밀번호를 저장소,
메신저 또는 구현 노트에 쓰지 않는다. clone이 404면 초대 수락 계정이 `koregy`인지와 `gh auth status`만
확인한다.

### 6.2 exact runtime 확인

```powershell
node --version
python --version
corepack.cmd pnpm --version
```

기대값은 Node `v24.12.0`, Python `3.12.13`, pnpm `11.13.0`이다. 다르면 frontend 작업을 시작하지 말고
버전을 맞춘다.

### 6.3 dependency와 frontend 기준선

```powershell
corepack.cmd enable
corepack.cmd prepare pnpm@11.13.0 --activate
corepack.cmd pnpm install --frozen-lockfile --ignore-scripts
corepack.cmd pnpm --filter @sejong-ai/shared-contracts generate:check
corepack.cmd pnpm --filter @sejong-ai/shared-contracts test
corepack.cmd pnpm --filter @sejong-ai/web lint
corepack.cmd pnpm --filter @sejong-ai/web typecheck
corepack.cmd pnpm --filter @sejong-ai/web test
corepack.cmd pnpm --filter @sejong-ai/web build
node scripts/check_web_bundle_secrets.mjs apps/web/.next
corepack.cmd pnpm --dir tools/web-e2e install --frozen-lockfile --ignore-scripts
corepack.cmd pnpm --dir tools/web-e2e exec playwright install chromium
corepack.cmd pnpm --dir tools/web-e2e test
node scripts/check_web_prod_dependency_boundary.mjs
```

명령 하나라도 실패하면 제품 코드를 고치지 말고 실패 명령과 마지막 오류 20줄만 소유자에게 전달한다. `.env`
값이나 전체 로그는 전달하지 않는다.

## 7. Frontend 팀원 — 허용 범위 self-merge 리허설

### 7.1 문서-only onboarding PR 만들기

```powershell
git switch main
git pull --ff-only origin main
git switch -c feat/web-COLLAB-ONBOARDING-doc-check
$NotePath = python scripts/new_implementation_note.py --title "web frontend collaborator onboarding rehearsal" --task-id COLLAB-ONBOARDING --type web-onboarding
$NotePath
```

생성된 `IMP-*-web-*.md`를 채운다. `INDEX.md`에는 생성기가 추가한 마지막 행만 유지한다. 변경 파일은 정확히
새 web 구현 노트 1개와 INDEX append 1개여야 한다.

```powershell
git status --short
git diff --check
python -B scripts/check_repository_docs.py
python -B scripts/check_current_tree_secrets.py --root .
git add -- $NotePath docs/implementation-notes/INDEX.md
git commit -m "docs(web): record frontend collaborator onboarding"
git push -u origin feat/web-COLLAB-ONBOARDING-doc-check
gh pr create --fill --base main --head feat/web-COLLAB-ONBOARDING-doc-check
```

PR의 collaboration policy 결과가 `FRONTEND_SELF_MERGE_ELIGIBLE`이고 모든 검사가 초록색인지 확인한다. 정확히
허용된 두 파일뿐이면 `koregy`가 직접 **Create a merge commit**으로 병합할 수 있다. 이것이 Q-GIT-003=B의
첫 실제 self-merge 증거다. 병합 뒤 소유자가 `main` CI가 초록색인지 확인한다.

## 8. Frontend 팀원 — 금지 범위 차단 리허설

이 리허설은 정책이 경계 밖 변경을 자동 병합 후보로 분류하지 않는지 확인한다. 실제 계약을 바꾸지 않는다.

```powershell
git switch main
git pull --ff-only origin main
git switch -c feat/web-COLLAB-ONBOARDING-forbidden-dry-run
```

`contracts/COLLAB_SCOPE_DRY_RUN.md`를 만들고 아래 내용만 넣는다.

```markdown
# COLLAB scope dry run

Test-only marker. This is not an actual public contract and contains no personal data.
```

그 다음:

```powershell
git add contracts/COLLAB_SCOPE_DRY_RUN.md
git commit -m "test(collab): exercise owner-review boundary"
git push -u origin feat/web-COLLAB-ONBOARDING-forbidden-dry-run
gh pr create --fill --draft --base main --head feat/web-COLLAB-ONBOARDING-forbidden-dry-run
```

기대 결과는 collaboration policy의 `OWNER_REVIEW_REQUIRED`다. 검사 자체는 성공할 수 있지만 이는 self-merge
승인이 아니다. 절대 병합하지 않고 PR을 **Close pull request**로 닫은 뒤 remote branch를 삭제한다.

```powershell
git push origin --delete feat/web-COLLAB-ONBOARDING-forbidden-dry-run
git switch main
git pull --ff-only origin main
git branch -D feat/web-COLLAB-ONBOARDING-forbidden-dry-run
```

마지막으로 `main`에 `contracts/COLLAB_SCOPE_DRY_RUN.md`가 없음을 확인한다. 이 리허설에서는 구현 노트를
추가하지 않는다. merge되지 않는 일회성 정책 시험이기 때문이다.

## 9. 완료 판정과 문제별 대응

| 항목 | 완료 증거 | 실패 시 행동 |
|---|---|---|
| App 범위 | 사람 확인: `Only select repositories / Sejong_AI` | `All`이면 수정·Save; 예상 밖 permission이면 중단 |
| 팀원 보안 | `koregy`의 코드 없는 2FA/복구 완료 확인 | 팀원이 직접 설정; 인증정보 공유 금지 |
| PR #1 | Ready 전환, green checks, merge commit, remote main 반영 | red/conflict/예상 밖 diff면 병합 중단 |
| Cloud | no-secret 환경, 허용 diff만 담은 `codex/**` Draft PR | secret/금지 파일/Ready PR이면 중단·Draft 전환 |
| 팀원 허용 PR | baseline PASS, `FRONTEND_SELF_MERGE_ELIGIBLE`, self-merge, main green | 범위·CI 실패면 owner 검토 |
| 팀원 금지 PR | `OWNER_REVIEW_REQUIRED`, PR close, marker가 main에 없음 | 병합됐으면 즉시 owner에게 알리고 revert |

COLLAB-001을 Done으로 바꾸는 것은 위 증거를 소유자 Codex 작업이 검증·문서화한 뒤다. 완료 전에도 제품
backend/data 작업은 local-only 경계 안에서 계속할 수 있지만, Cloud가 Docker/DB/DeepSeek 검증을 했다고
주장하거나 공개 배포 준비가 끝났다고 간주하면 안 된다.
