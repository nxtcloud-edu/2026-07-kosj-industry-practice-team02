# IMP-20260721-001 — COLLAB-001 private GitHub bootstrap and hosted CI evidence

- Date/Time (KST): 2026-07-21T05:37:58+09:00
- Task ID: COLLAB-001-EXTERNAL-BOOTSTRAP
- Type: implementation-platform-security
- Status: Done — documentation/evidence synchronization; COLLAB-001 remains In Progress
- Author/Agent: 사용자(외부 계정·GitHub 상태 검증), Codex(권위 문서 동기화·검증)
- Branch: `codex/COLLAB-001-bootstrap-evidence`
- Base commit: `5e09deccc7205503df07d938b6d4a88f4d5a327e`
- Related plan/ADR/RFP: COLLAB-001 execution plan, ADR-0019, D-047~D-055, TASKS COLLAB-001

## 1. 사용자 요청과 완료 기준

### 요청

승인된 Task 4 bootstrap과 partial Task 5 범위를 현재 권위 문서에 동기화한다. Task 6~7은 완료로
기록하지 않으며, 제품 코드·workflow·계약·DB·data·prompt·dependency는 변경하지 않는다.

### Acceptance Criteria

- private owner/repository, ordinary initial push, matching `main` SHA, private visibility, hosted CI와
  collaborator/variable/Actions evidence를 non-secret 기록한다.
- approved plan의 Task 4, partial Task 5와 Task 8 owner/name checkbox를 갱신한다.
- MFA/recovery, 첫 Task 7 PR-only/no-direct-main-push, repository-limited Codex App, Cloud Draft
  PR/manual merge와 나머지 teammate onboarding/rehearsal을 Pending으로 남기고 COLLAB-001을
  In Progress로 유지한다.
- manifest collaboration-only patch increments, implementation note/INDEX, focused docs/JSON/secret/diff
  verification과 self-review를 완료한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자(외부 GitHub 상태 확인), Frontend collaborator `koregy`, Codex(문서 동기화) |
| When — 언제 | 2026-07-21 KST, approved Task 4 bootstrap 및 partial Task 5 evidence 이후 |
| Where — 어디서 | private GitHub source repository, local `codex/COLLAB-001-bootstrap-evidence` worktree, authoritative collaboration docs |
| What — 무엇을 | private bootstrap·hosted CI·collaborator evidence와 pending Cloud/onboarding boundary를 동기화 |
| Why — 왜 | stale `remote 0/push 0/hosted Actions 0` 진술이 실제 운영 상태와 충돌하지 않게 하고 사람 승인 경계를 보존 |
| How — 어떻게 | verified facts만 plan/source-of-truth/decision log/handoff/contributor guidance에 반영, secret/URL/CI log content 제외 |
| How much — 어느 정도 | docs/metadata only; repo guidance `1.7.0→1.7.1`, documentation `2.9.0→2.9.1`; product behavior 0 |

## 3. 시작 전 상태

- 관련 파일: COLLAB-001 plan, ADR-0019, `README.md`, `CODEX_FILE_INDEX.md`, TASKS, CONTRIBUTING,
  `docs/15_DEPLOYMENT_AND_OPERATIONS.md`, handoff, ambiguity register, source-of-truth, decision log,
  CHANGELOG, manifest, implementation-note INDEX.
- 기존 동작: local collaboration automation은 완료됐지만 tracked docs는 remote/push/hosted Actions가 0이라고
  기록했다. 제품 실행·공개 계약·DB/data 상태는 unchanged다.
- 발견한 충돌/부채: external bootstrap/CI evidence와 stale local-only closeout claims가 충돌했다.
- Git 상태: branch `codex/COLLAB-001-bootstrap-evidence`, base `5e09dec`; this docs-only task starts from
  the verified pushed `main` SHA.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| COLLAB-EXT-001 | Human-only | teammate MFA/recovery | repository API로 검증 불가; Pending 유지 | Task 5 closeout |
| COLLAB-EXT-004 | Human rehearsal | first PR-only/no-direct-main-push flow | repository warning만 확인됨; first Task 7 onboarding PR에서 증명 | Task 5 remains partial |
| COLLAB-EXT-002 | External access | App installation can access this repository and other repositories | selected-repository-only constraint is not satisfied; user narrows/confirms `Sejong_AI` only | Task 6 remains Pending |
| COLLAB-EXT-003 | Rehearsal | Cloud environment/Draft PR/manual merge and teammate onboarding | evidence 0; no completion inference | Tasks 6~7 pending |

## 5. 설계 결정과 대안

### 선택

D-055 operational-evidence row와 minimum authoritative/current documents에 exact non-secret facts를
기록한다. private URL, authentication details, CI log contents, unrelated App repository names/IDs는
기록하지 않는다.

### 이유

기존 승인 architecture를 바꾸지 않고 실제 remote/CI 상태를 재현 가능하게 하며, GitHub Free의
human-policy boundary와 Codex Cloud least-access requirement를 분명히 유지한다.

### 고려했지만 선택하지 않은 대안

- Task 6~7까지 Done: Cloud/onboarding rehearsal evidence와 App single-repository restriction이 없으므로 기각.
- private URLs 또는 authentication/CI-log details 기록: product reproduction에 불필요하고 노출 범위를 넓히므로 기각.
- 새 ADR: architecture change가 아닌 operational evidence이므로 D-055와 implementation note로 충분.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| COLLAB-001 plan/TASKS | Task 4, partial Task 5, Task 8 owner/name completion과 Tasks 6~7 pending evidence | 실행 상태의 정답화 |
| CONTRIBUTING/handoff/ambiguity | collaborator onboarding 및 Cloud restriction guidance 갱신 | 실행자에게 stale pre-bootstrap 안내 방지 |
| `README.md`, `CODEX_FILE_INDEX.md`, `docs/15_DEPLOYMENT_AND_OPERATIONS.md` | current bootstrap, partial Task 5와 pending rehearsal 상태 | 현재 시작점·운영 상태 정합 |
| TEAM_DECISIONS/PROJECT_PLAN/DECISION_LOG | source-of-truth current state 및 D-055 | approved operational evidence 계보 |
| CHANGELOG/manifest | collaboration-only patch versions | version synchronization |
| implementation note/INDEX | this reproducible record | AGENTS note obligation |

### 데이터 흐름/상태 변화

시민 질문, KB, DB, provider, API, workflow와 application behavior는 불변이다. 변경된 것은 source-control
operational evidence와 human follow-up status뿐이다.

### 오류·빈 상태·롤백

MFA/recovery나 rehearsal evidence가 없으면 fail-closed로 pending을 유지한다. 문서 동기화가 잘못되면
merged PR 전체를 revert하거나 이 branch의 docs commits를 역순 revert한다. history rewrite/force push,
remote deletion, collaborator/App revoke는 하지 않는다.

## 7. 버전 전후

### 생성 시 매니페스트

- product_spec: 2.2.5
- repo_guidance: 1.7.0
- application: 0.3.0-pii-core
- web: 0.2.0-static-chat-shell
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.3.0-local
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 1.0.0-collaboration
- documentation: 2.9.0

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Repository guidance | 1.7.0 | 1.7.1 | external bootstrap/current contributor guidance |
| Application | 0.3.0-pii-core | unchanged | product code 0 |
| Web | 0.2.0-static-chat-shell | unchanged | UI behavior 0 |
| API | 2.0.1-draft | unchanged | contract/runtime 0 |
| DB schema | 0.3.0-local | unchanged | migration/data 0 |
| Official data | 0.0.0-not-populated | unchanged | data 0 |
| Mock data | 0.0.0-not-populated | unchanged | data 0 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | unchanged | provider/prompt 0 |
| Test suite | 1.0.0-collaboration | unchanged | no test behavior change |
| Docs | 2.9.0 | 2.9.1 | D-055/current evidence synchronization |

## 8. 명령과 테스트 증거

### External evidence command record (sanitized)

The user performed authenticated external commands; no token, masked-token display, email, raw API
payload, unrelated repository name/ID or CI-log content was copied here. Command endpoints use only the
approved owner/repository identifier.

```powershell
$repo = 'tskwak111/Sejong_AI'
$sha = '5e09deccc7205503df07d938b6d4a88f4d5a327e'
```

| Command shape | Summarized actual result |
|---|---|
| `gh api user --jq .login` | intended active login `tskwak111`; successful later API operations prove sufficient access. Interactive auth output was not copied |
| `gh repo view $repo --json nameWithOwner,visibility,isEmpty,defaultBranchRef` | before push: `PRIVATE`, empty, default branch absent; freshly after push: `PRIVATE`, non-empty, default branch `main` |
| Before-push private-target `ls-remote` command intentionally omitted; `git ls-remote origin refs/heads/main` after push | after: `5e09deccc7205503df07d938b6d4a88f4d5a327e refs/heads/main`; before-push empty state is covered by the safe repo-view row |
| `python -B scripts/check_git_history_secrets.py --repo .`; `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1 -RepositoryRoot .`; `git fsck --full` | fresh reachable-history finding 0, current-tree finding 0, and fsck exit 0 (existing dangling unreachable objects only) |
| `git push -u origin main` | initial ordinary push only; no `--force`, `--all` or `--mirror`; local and remote `main` matched the recorded SHA |
| `$collab = gh api "repos/$repo/collaborators/koregy/permission" \| ConvertFrom-Json; $collab.permission`; `$invitations = gh api "repos/$repo/invitations" \| ConvertFrom-Json; @($invitations \| Where-Object { $_.invitee.login -eq 'koregy' }).Count` | permission `write`; pending invitation count `0` for `koregy` |
| `$vars = gh variable list --repo $repo --json name,value \| ConvertFrom-Json; $target = @($vars \| Where-Object { $_.name -eq 'FRONTEND_COLLABORATOR_LOGIN' }); $target.Count; $target[0].value` | count `1`; `FRONTEND_COLLABORATOR_LOGIN=koregy`; installed local `gh` lacks `variable get`, so compatible `variable list` verification was used |
| `$perm = gh api "repos/$repo/actions/permissions/workflow" \| ConvertFrom-Json; $perm.default_workflow_permissions; $perm.can_approve_pull_request_reviews` | default workflow permission `read`; pull-request review approval `false` |
| `gh repo edit tskwak111/Sejong_AI --description "Sejong_AI — private source; main 직접 push 금지, PR + green CI 후 사람 병합"`; `gh repo view tskwak111/Sejong_AI --json description,visibility` | description read back exactly as set and visibility remained `PRIVATE`; this is a human-policy warning, not technical enforcement or a rehearsal |
| `gh run list --repo $repo --commit $sha --limit 20 --json databaseId,workflowName,status,conclusion,event,headSha`; `gh run watch 29776352718 --repo $repo --exit-status --interval 10` | safe run list observed both run IDs completed with conclusion success; the watch waited for the in-progress Frontend CI `29776352718`, which passed its full frozen frontend/browser gate |

### Exact local validation commands

```powershell
$manifest = Get-Content -Raw 'versions/manifest.json' | ConvertFrom-Json
if (
  $manifest.versions.repo_guidance -ne '1.7.1' -or
  $manifest.versions.documentation -ne '2.9.1' -or
  $manifest.versions.test_suite -ne '1.0.0-collaboration'
) { throw 'MANIFEST_VERSION_INVARIANT_FAILED' }
'manifest exact invariants PASS'
```

Actual result: `manifest exact invariants PASS`.

```powershell
$statusPaths = @(
  'README.md', 'CODEX_FILE_INDEX.md', 'TASKS.md', 'CONTRIBUTING.md', 'CHANGELOG.md',
  'docs/11_AMBIGUITY_REGISTER.md', 'docs/15_DEPLOYMENT_AND_OPERATIONS.md',
  'docs/source-of-truth/TEAM_DECISIONS.md', 'docs/source-of-truth/PROJECT_PLAN.md',
  'docs/handoffs/HANDOFF-20260720-FRONTEND-COLLABORATOR.md',
  'docs/superpowers/plans/2026-07-20-github-codex-cloud-collaboration-transition.md',
  'docs/implementation-notes/IMP-20260721-001-collab-001-private-github-bootstrap-and-hosted-ci-evidence.md'
)
$stalePattern = @(
  ('Task 5 is verified' + ' except'),
  ('Task 5 verified' + ' except'),
  ('verified' + ' Task 5'),
  ('remote·push·Actions·collaborator.*pend' + 'ing')
) -join '|'
& rg -n -i -- $stalePattern $statusPaths
if ($LASTEXITCODE -eq 0) { throw 'STALE_CURRENT_COLLABORATION_STATUS_FOUND' }
if ($LASTEXITCODE -ne 1) { throw 'STALE_STATUS_SEARCH_FAILED' }
'stale current-status search PASS (0 matches)'
```

Actual result: `stale current-status search PASS (0 matches)`. A separate historical search
`rg -n -i -- 'remote 0|push 0|hosted Actions 0'` against the collaboration plan and this note returns
only the plan-creation/pre-push/local-closeout checkpoints and the note's description of the stale
starting state; these are historical evidence, not current-status claims.

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `python scripts/new_implementation_note.py --title "COLLAB-001 private GitHub bootstrap and hosted CI evidence" --task-id COLLAB-001-EXTERNAL-BOOTSTRAP --type implementation-platform-security` | PASS | note and INDEX row generated | terminal |
| `python -B scripts/check_repository_docs.py --repository-root .` | PASS | active Markdown/JSON links and tracked files | terminal |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1 -RepositoryRoot .` | PASS | current-tree secret finding 0; values not printed | terminal |
| `python -B -m unittest -v scripts.tests.test_repository_docs scripts.tests.test_github_collaboration_config` | PASS | 32 passed, 1 expected symlink-platform skip | terminal |
| exact manifest PowerShell invariant above, `git diff --check`, `git fsck --full` | PASS | required versions exact; only repository's pre-existing dangling unreachable objects reported by fsck | terminal |
| exact focused stale-current-status `rg` above | PASS | 0 stale current-status matches; expected historical checkpoints documented separately | terminal, this note |

### 미실행 검증과 이유

- Task 6 Cloud environment, docs/test-only task, Draft PR/manual merge: App installation is not yet restricted
  to `Sejong_AI`; no rehearsal evidence.
- Task 7 teammate clone/baseline/self-merge/forbidden-scope run: not performed.
- MFA/recovery: account-human-only confirmation, not repository API evidence.
- Task 5 PR-only/no-direct-main-push: warning is present, but the first Task 7 onboarding PR rehearsal is not performed.
- Docker/Supabase/DeepSeek actual: unrelated local-only owning tasks; this docs-only task changes none.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: citizen text, PII, email, token, DSN and authentication values are not added.
- Security: private URLs and CI-log content are excluded. Actions remain read-only; Cloud restriction is a
  pending least-privilege action, not a completed control.
- Accessibility: no UI change.
- Performance/cost: no runtime/dependency/cost change; GitHub Free governance remains human-policy based.

## 10. 데이터와 출처 영향

- 공식 데이터: unchanged, `0.0.0-not-populated`.
- mock/AI 생성: unchanged; no mock/official data mixed.
- schema/lineage: DB/API/data lineage unchanged; D-055 is source-control evidence lineage only.
- verified date: 2026-07-21 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- `tskwak111/Sejong_AI` is private and `main` is aligned at
  `5e09deccc7205503df07d938b6d4a88f4d5a327e`; hosted policy/Frontend CI evidence is PASS.
- `koregy` accepted write access and repository variable are verified, but Task 5 remains partial:
  teammate MFA/recovery and the first Task 7 PR-only/no-direct-main-push rehearsal need human evidence.
- The connected Codex App installation can access other repositories. Before Cloud work, the user must
  narrow and confirm **Only select repositories** to `Sejong_AI`; do not treat this as Cloud or PR evidence.
- User/team must still perform Cloud Draft PR/manual merge and all teammate onboarding/self-merge/forbidden-scope rehearsals.
- This private source remote does not approve public deployment, remote DB, backup, secret upload or DeepSeek use.

## 12. AI 내부 구현 세부 — 인간이 굳이 이해하지 않아도 되는 내용

- Markdown wording, table row placement, INDEX row and manifest timestamp formatting were synchronized
  without changing public contracts or application behavior.

## 13. 인수인계·재현·롤백

### 재현

Read D-055, COLLAB-001 plan Task 4~8, CONTRIBUTING and frontend handoff. Confirm private visibility,
matching local/remote `main`, collaborator/variable/default Actions permission and hosted run status
using authenticated human tools without copying credentials or private URLs into tracked files.

### 롤백

If this integrated branch is merged and an operational fact is disproved, revert the merged PR. Before
merge, revert all documentation commits on this branch in reverse order. Do not force push, rewrite shared
history, delete the remote, revoke collaborator/App access or change Cloud settings without separate human authorization.

### 다음 개발자 시작점

First restrict and confirm the Codex App to `Sejong_AI` only, then run the explicit Task 6 Cloud rehearsal.
After that, the Frontend teammate performs Task 7 according to the handoff. Its first onboarding PR also
proves Task 5 PR-only/no-direct-main-push behavior; record each external result before marking COLLAB-001 Done.

## 14. 남은 위험·미해결 질문·다음 단계

- Task 5 remains partial: teammate MFA/recovery and the first Task 7 PR-only/no-direct-main-push rehearsal remain unverified.
- App least-privilege restriction, Cloud environment/Draft PR/manual merge and all Task 7 rehearsals remain pending.
- GitHub Free cannot technically replace human scope review; continue PR-only, CI evidence and small reverts.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
