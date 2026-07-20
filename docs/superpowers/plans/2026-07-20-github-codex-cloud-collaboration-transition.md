# GitHub·Codex Cloud Collaboration Transition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` or
> `superpowers:subagent-driven-development` after this plan is approved. Do not create a remote,
> push, invite a collaborator, install the Codex GitHub app or add workflows before approval.

**Goal:** Move the current clean local `main` to a private personal GitHub repository, onboard one
frontend owner, and configure a secret-free Codex Cloud Draft-PR workflow without changing product
behavior or opening any remote/public runtime.

**Architecture:** Keep one private monorepo as the source-control authority. Classify PRs by PR author and
changed paths, let the frontend collaborator self-merge only frontend-only green PRs, and keep
contracts/backend/DB/data/security/dependencies under user review. Codex Cloud produces branches and
Draft PRs; Windows Docker/Supabase and DeepSeek synthetic actual gates remain local-only.

**Tech Stack:** Git/GitHub private repository, GitHub Actions with official actions pinned to reviewed
commits, Python 3.12 stdlib scope classifier, Node 24.12.0, pnpm 11.13.0, existing Next.js/Vitest/
Playwright toolchain, Codex Cloud.

## Status and approval boundary

- Plan ID: `COLLAB-001`
- Status: **In Progress — Tasks 1~4 complete; Task 5 partial (MFA/recovery and the first
  PR-only/no-direct-main-push rehearsal pending); Task 6 partial (App scope confirmed, Cloud
  environment/Draft PR pending); Task 7 pending**
- Approved written design:
  `docs/superpowers/specs/2026-07-20-github-codex-cloud-collaboration-design.md`
- Decision/ADR: D-047~D-057 / ADR-0019
- Local authority at plan creation: branch `main`, HEAD
  `177dac810468f3cd5aaa4929a971cbde21b4deba`, remote 0.
- External evidence state on 2026-07-21: approved owner `tskwak111`, private repository `Sejong_AI`,
  and Frontend collaborator `koregy` are verified operational identifiers. `origin/main` and local
  `main` resolve to `5e09deccc7205503df07d938b6d4a88f4d5a327e`; the initial ordinary push used only
  `git push -u origin main`. Hosted policy run `29776352710` and frozen Frontend CI run `29776352718`
  passed on that SHA. Private URLs and authentication details are intentionally not recorded.
- Q-GIT-004=A/D-053 preserves the current history and SHAs. Execution starts only after the user says
  `계획 승인, 구현 시작` or equivalent.
- This plan does not authorize product code, public deployment, remote DB, schema migration, official
  seed, data deletion, new production dependency, secret upload, DeepSeek Cloud use or `/ready=200`.

## Inputs required during execution

These are operational identifiers, not architecture questions. Do not place them in secret fields.

- GitHub personal account login/owner
- available private repository name; default proposal `sejong-minwon-ai`
- frontend collaborator GitHub login
- confirmation that the collaborator accepted the invitation
- confirmation that Codex GitHub access is restricted to the one repository

Authentication tokens, API keys and passwords are never requested in chat or committed. The user
completes browser authentication directly.

## Global constraints

- Preserve existing Git history unless the pre-push audit finds a secret/PII blocker.
- Never print a discovered secret value; report only pattern type, path and commit.
- Never push if the working tree/history audit has unresolved Critical findings.
- Use private visibility and verify it after creation and before collaborator invitation.
- Do not treat private GitHub as a public/product deployment or a remote DB authorization.
- Do not upload ignored local env, `.tools`, `.worktrees`, Docker state, browser artifacts or dumps.
- GitHub Actions and Codex Cloud receive no DeepSeek key, DB DSN or context-token secret.
- The first remote commit must contain the approved collaboration docs and no unreviewed product code.
- GitHub Free limitations are documented; CI is advisory evidence and the team obeys PR-only rules.
- Every task ends with focused verification, diff review and an implementation note.

The read-only pre-push audit completed before plan execution found no credential/content-secret blocker:
163 reachable commits were inspected, the ignored local LLM key's exact value appeared in history 0
times, and high-risk credential patterns were 0. It did find an actual-looking author/committer email
identity across the reachable history. Q-GIT-004=A/D-053 confirms that the identity belongs to the user
and may be visible to the private Frontend collaborator, so preserve the history and SHAs and do not
perform a noreply rewrite. Plan approval and local automation do not authorize guessed account state:
do not create a remote or push until the exact owner/repository is confirmed and the final integrated
pre-push gate passes. Never use `git push --mirror`, and do not push extra local branches until their
commits are reviewed independently.

---

## Task 1: Freeze the local source-control baseline and audit the full history

**Files:**

- Read: `.gitignore`, tracked `.env*`, `SECURITY.md`, `scripts/check_secret_patterns.ps1`
- Create: `scripts/check_git_history_secrets.py`, `scripts/tests/test_git_history_secrets.py`
- Modify: `.gitignore` only for verified missing credential-container patterns such as `*.pfx`, `*.jks`,
  `*.keystore` and personal auth config; preserve tracked keyless root `.npmrc`
- Append evidence to the COLLAB implementation note
- Do not modify history in the normal PASS path

- [x] **Step 1: Capture the exact baseline**

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
git remote -v
git log -10 --oneline --decorate
git fsck --full
```

Expected: `main`, known HEAD, clean worktree except this approved documentation transition once
committed locally, remote 0 before creation, `git fsck` success.

- [x] **Step 2: Verify ignored/runtime boundaries**

```powershell
git ls-files -- '.env' '.env.*' 'apps/*/.env' 'apps/*/.env.*' '.tools/**' '.worktrees/**' '*.dump' '*.sql.gz'
git check-ignore -v .env apps/api/.env apps/web/.env.local .tools .worktrees
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
```

Expected: only keyless example env files are tracked; local secret/runtime paths are ignored; scanner
passes without echoing values.

- [x] **Step 3: Scan all reachable history safely**

Use tracked blob names and a redacted pattern scanner that reports only commit/blob/path and pattern
category. Do not use a command that prints matched values. At minimum inspect:

```powershell
git log --all --full-history --format='%H' --name-status -- '.env' '*.pem' '*.key' '*.p12' '*.pfx' '*credential*' '*secret*'
git rev-list --objects --all
```

The implementation must add or use a value-redacting history scanner before push. RED tests must
prove a synthetic token is detected while the token itself is absent from stdout/stderr. Scan common
GitHub, DeepSeek/OpenAI-style bearer keys, private-key headers, database URLs with credentials,
JWT-like tokens and actual-question sentinel patterns.

If the ignored local key is compared exactly, the scanner must keep it in its own process memory and
stream/read Git blob bytes for comparison. It must never pass the key through Git/subprocess arguments,
environment variables, temporary files, shell history or logs. RED tests inspect mocked child argv/env
and prove the synthetic token is absent there as well as stdout/stderr.

- [x] **Step 4: Gate the outcome**

- PASS: Critical 0, continue.
- Possible false positive: document path/type and independently inspect without copying values.
- Confirmed secret/PII: stop before remote creation; rotate the credential first and request explicit
  approval for history rewrite/notification. Do not solve it with a deletion-only commit.
- Author identity metadata: Q-GIT-004=A/D-053 is satisfied. Preserve history and record consent without
  the email value; do not perform a noreply rewrite.

## Task 2: Add a dependency-free collaboration scope policy and TDD coverage

**Files:**

- Create: `scripts/check_collaboration_scope.py`
- Create: `scripts/check_collaboration_note_append.py`
- Create: `scripts/tests/test_collaboration_scope.py`
- Modify: `scripts/README.md`
- Modify: `CONTRIBUTING.md`

**Interface:**

```text
python -B scripts/check_collaboration_scope.py \
  --base-sha <full-commit-sha> --head-sha <full-commit-sha> \
  --pr-author <github-login> --frontend-login <github-login>
```

Stable output contains only counts, classification and JSON-escaped path names; no file contents.
Exit 0 means classification succeeded and returns either `FRONTEND_SELF_MERGE_ELIGIBLE` or
`OWNER_REVIEW_REQUIRED`. Exit 2 means invalid SHA/input, missing configuration or Git operational
failure. The workflow fails policy only when the PR author is the configured Frontend collaborator and
the successful classification is `OWNER_REVIEW_REQUIRED`. Owner/Codex PRs remain green classification
evidence and still require human merge under their own policy.

- [x] **Step 1: Write RED classification tests**

Cover:

- frontend login + `apps/web/src/**` only → `FRONTEND_SELF_MERGE_ELIGIBLE`
- frontend login + `tools/web-e2e/e2e/**` only → eligible
- frontend login + exactly one newly added `IMP-YYYYMMDD-NNN-web-*.md` and one append-only matching
  INDEX row → eligible; existing note/INDEX row modifications or deletion → required
- `apps/web/AGENTS.md`, `apps/web/.env.example`, README/config and package metadata → required even
  though the teammate may propose them for owner review
- `apps/web/package.json`, any lockfile, `.github/**`, contract/generated type, API, DB, migration,
  official/staging data or policy/ADR → `OWNER_REVIEW_REQUIRED`
- mixed allowed+forbidden → required
- missing/blank PR author or frontend login → operational error exit 2
- owner/Codex PR author → `OWNER_REVIEW_REQUIRED` for human merge, not frontend self-merge
- rename is eligible only when old and new paths both satisfy the exact allowlist; deletion/path escape/
  unknown status → required or operational error as specified by stable tests
- base/head accept only validated 40/64-hex commit SHAs that resolve to commits; Git invocation uses
  `git diff --name-status -z <base> <head> --`
- newline/ANSI/control characters in untrusted paths are JSON-escaped; output never includes file
  contents or environment values

- [x] **Step 2: Run focused tests and confirm RED**

```powershell
.\apps\api\.venv\Scripts\python.exe -B -m unittest -v scripts.tests.test_collaboration_scope
```

Expected: failure because the classifier does not exist.

- [x] **Step 3: Implement minimal stdlib classifier**

Use `subprocess.run` with argument arrays and `git diff --name-status -z`. Normalize repository-relative
POSIX paths, validate full commit SHAs and commit existence, reject NUL/path escape/unknown status, and
apply deny overrides before allow prefixes. The scope classifier does not call GitHub APIs or read file
contents. A separate append validator reads only the unified diff for the one new implementation note
and INDEX, proving no existing row/content was replaced.

- [x] **Step 4: Verify and self-review**

```powershell
.\apps\api\.venv\Scripts\python.exe -B -m unittest -v scripts.tests.test_collaboration_scope
.\apps\api\.venv\Scripts\python.exe -B -m unittest -v scripts.tests.test_repository_scaffold
git diff --check
```

## Task 3: Add PR templates and an always-reporting GitHub Actions gate

**Files:**

- Create: `.github/PULL_REQUEST_TEMPLATE.md`
- Create: `.github/ISSUE_TEMPLATE/contract-gap.yml`
- Create: `.github/workflows/collaboration-policy.yml`
- Create: `.github/workflows/frontend-ci.yml`
- Create: `.github/OWNERSHIP.md`
- Create: `scripts/check_repository_docs.py`
- Create: `scripts/tests/test_repository_docs.py`
- Modify: `SECURITY.md`
- Modify: `tools/web-e2e/playwright.config.ts` — remove Windows-only `corepack.cmd` assumption
- Test: `scripts/tests/test_github_collaboration_config.py`
- Test: existing/new portability assertion for the E2E web-server command

- [x] **Step 1: Write RED static workflow tests**

Require:

- `pull_request` includes `opened`, `synchronize`, `reopened`, `ready_for_review`; Draft PR is not excluded
- `push` on `main` provides direct-push after-the-fact detection, plus manual `workflow_dispatch`
- workflow-level `paths:` is absent and the policy workflow always starts on every PR
- checkout fetches enough history for a base/head diff
- PR author `github.event.pull_request.user.login`, full base/head SHAs and
  `vars.FRONTEND_COLLABORATOR_LOGIN` are passed as arguments, never interpolated into a generated shell
  command. `github.actor` is audit metadata only and cannot decide self-merge eligibility.
- no `pull_request_target`, write token or secret echo; untrusted PR code is never executed in a
  write-capable/secret-bearing context
- permissions default to `contents: read`
- checkout uses `persist-credentials: false`
- the policy job executes the classifier/append validator from the trusted base SHA and reads only the
  head diff; frontend test jobs execute the untrusted head with read-only token and secret 0
- official GitHub actions are pinned to reviewed full commit SHAs at implementation time
- every PR policy gate runs scope classification, shared-contract generation drift, current-tree secret
  patterns, tracked active Markdown local-link validation and tracked JSON parsing; these commands are
  not hidden behind frontend paths or self-merge eligibility
- frontend gate runs frozen install, web lint/typecheck/unit/build, production
  dependency boundary and Playwright E2E
- no Docker, Supabase reset, DeepSeek call, remote DB or deployment step
- one final job/check always reports reached/skipped/failure so path filtering cannot leave the visible
  gate absent; aggregator uses `if: always()` and fails if any required upstream failed
- the Playwright web-server command chooses `corepack.cmd` only on Windows and `corepack` on POSIX;
  current unconditional `corepack.cmd` must be proven RED in a portability test before correction
- initial CI does not upload Playwright traces/screenshots/videos. A later artifact policy must be
  failure-only, short-retention and scan/redact synthetic-only artifacts before upload.

- [x] **Step 2: Confirm RED**

```powershell
.\apps\api\.venv\Scripts\python.exe -B -m unittest -v scripts.tests.test_github_collaboration_config
```

- [x] **Step 3: Implement workflows without new repository dependency**

Use the repository variable to identify the PR author, not the event actor. Frontend test execution is
decided independently by changed paths, not by self-merge classification. Use repository-pinned
Node/Python versions and existing lockfiles. Initially avoid third-party path
filter/cache actions. The workflow may use official `checkout`, `setup-node` and `setup-python` only,
after their exact commit SHAs are verified against official repositories. A hosted runner egress block
is not claimed; minimize network by using secret 0, write token 0, `--ignore-scripts`, pinned official
actions, `NEXT_TELEMETRY_DISABLED=1` and only locked dependency/Chromium installation.

Implement `scripts/check_repository_docs.py` with Python stdlib only. It reads tracked active files,
excludes `legacy/`, `.git/`, `.worktrees/` and generated/runtime directories, verifies repository-local
Markdown targets and parses tracked JSON without echoing file contents. TDD must cover Unicode paths,
anchors/query suffixes, missing targets, malformed JSON and ignored/legacy exclusions. The always-run
policy job invokes the trusted-base scope/docs checkers against the head tree, runs
`corepack pnpm --filter @sejong-ai/shared-contracts generate:check`, and runs the existing value-redacting
secret scanner through `pwsh -NoProfile -File scripts/check_secret_patterns.ps1`. Any missing command or
operational error fails the gate rather than silently skipping it.

Make `tools/web-e2e/playwright.config.ts` choose the executable from `process.platform` (or an
equivalent argument-safe existing mechanism) so local Windows and Cloud/Linux start the same pinned
Web package. Do not replace the current production `next start` E2E server with a development server.

Suggested frontend commands:

```bash
corepack enable
corepack prepare pnpm@11.13.0 --activate
test "$(node --version)" = "v24.12.0"
test "$(corepack pnpm --version)" = "11.13.0"
corepack pnpm install --frozen-lockfile --ignore-scripts
corepack pnpm --filter @sejong-ai/shared-contracts generate:check
corepack pnpm --filter @sejong-ai/shared-contracts test
corepack pnpm --filter @sejong-ai/web lint
corepack pnpm --filter @sejong-ai/web typecheck
corepack pnpm --filter @sejong-ai/web test
corepack pnpm --filter @sejong-ai/web build
node scripts/check_web_bundle_secrets.mjs apps/web/.next
corepack pnpm --dir tools/web-e2e install --frozen-lockfile --ignore-scripts
corepack pnpm --dir tools/web-e2e exec playwright install --with-deps chromium
corepack pnpm --dir tools/web-e2e test
node scripts/check_web_prod_dependency_boundary.mjs
```

The first candidate runner is `ubuntu-latest` for Free quota efficiency with `--with-deps chromium`.
The documented fallback is `windows-latest` with `install chromium`. Both preserve production
`next build` then `next start`. Do not make the separate `verify_database.ps1` or
`verify_data_seed.ps1` actual gates a Cloud CI completion condition. Root `verify.ps1` is Windows-only
but does not itself start Docker; its pure subchecks may be represented by platform-neutral commands.

In the build step only, set equal synthetic sentinel values for `SEJONG_WEB_SECRET_SENTINEL`, `DATABASE_URL`,
`SUPABASE_SERVICE_ROLE_KEY`, `LLM_API_KEY`, `CONTEXT_TOKEN_SECRET` and `DEEPSEEK_API_KEY`, then run the
build. Clear the five server-secret variables after build; pass only the same
`SEJONG_WEB_SECRET_SENTINEL` to the immediately following
`check_web_bundle_secrets.mjs apps/web/.next` scan. The value is fixed synthetic CI text, never a
repository or Actions secret.

- [x] **Step 4: Parse and verify locally**

Run the new static tests, existing frontend commands, secret scan, package validator and `git diff
--check`. Review workflow permissions and every action SHA before commit.

## Task 4: Create and verify the private GitHub source remote

**External state:** user personal GitHub account. This task changes external state and begins only after
plan approval, Task 1 PASS and interactive user authentication. Q-GIT-004 is already resolved by D-053.

- [x] **Step 1: Authenticate without sharing credentials**

The user signs in through GitHub CLI browser flow or GitHub UI. Never paste a token into chat,
PowerShell history, `.env` or documentation.

- [x] **Step 2: Create private repository**

Preferred CLI shape, substituting the confirmed owner/name:

```powershell
gh repo create <owner>/sejong-minwon-ai --private --source . --remote origin
```

If `gh` is unavailable, create an empty private repository in GitHub UI without README/license/
`.gitignore`, then:

```powershell
git remote add origin https://github.com/<owner>/sejong-minwon-ai.git
```

- [x] **Step 3: Verify before first push**

```powershell
git remote -v
gh repo view <owner>/sejong-minwon-ai --json nameWithOwner,visibility,defaultBranchRef
git status --short
```

Expected: exact intended owner/name, `PRIVATE`, no unexpected remote, reviewed local commit.

- [x] **Step 4: Push without rewriting history**

```powershell
git push -u origin main
git ls-remote --heads origin main
```

Never use `--force`, `--all` or `--mirror` for the first push. Confirm remote `main` resolves to the
reviewed local commit. The two local `codex/*` branches contain six commits not in `main` and are not
uploaded until independently reviewed.

## Task 5: Configure collaborator and repository variables

- [x] Invite the exact frontend GitHub login with collaborator write access.
- [x] Confirm the invited Frontend collaborator accepted write access.
- [x] Set repository variable `FRONTEND_COLLABORATOR_LOGIN` to that exact login.
- [x] Keep Actions workflow permissions read-only by default; do not enable broad write tokens.
- [x] Confirm repository visibility remains private after settings changes.
- [ ] Teammate confirms MFA/recovery appropriate to their account.
- [x] Record login identifiers only; do not record emails, phone numbers or authentication details.
- [x] Record the `main` direct-push prohibition in the repository description/onboarding.
- [ ] Rehearse PR-only/no-direct-main-push behavior in the first Task 7 teammate onboarding PR.

Because GitHub Free private branch protection is not assumed, the warning alone is not technical
enforcement or rehearsal evidence. Do not advertise CI as an enforced security boundary.

## Task 6: Connect and constrain Codex Cloud

2026-07-21 correction: connector visibility of public repositories cannot distinguish **All
repositories** from **Only select repositories**, because a GitHub App always has at least read-only
access to public GitHub repositories. The user confirmed **Only select repositories / `Sejong_AI`**
on 2026-07-21. This completes the App-scope gate only; it is not Cloud environment, docs/test-only task,
Draft-PR or manual-merge rehearsal evidence, which remain pending.

- [x] User opened GitHub App settings and confirmed **Only select repositories / `Sejong_AI`**.

**Remaining human browser steps:**

1. Open [Codex](https://chatgpt.com/codex) and connect GitHub.
2. Create a Cloud environment for the repository.
3. Pin Node `24.12.0`, Python `3.12.13` and pnpm `11.13.0` through repository files/setup.
4. Leave agent internet access off unless a task proves a narrow allowlist is necessary.
5. Add no DeepSeek key, DB DSN, context-token secret or citizen fixture.

The setup script may install existing locked dependencies because setup has internet access. It must
not print environment values and must not start Docker, a database or an external LLM request. Prefer:

```bash
corepack enable
corepack prepare pnpm@11.13.0 --activate
test "$(node --version)" = "v24.12.0"
test "$(corepack pnpm --version)" = "11.13.0"
corepack pnpm install --frozen-lockfile --ignore-scripts
python -m pip install --disable-pip-version-check --user uv==0.11.28
UV_BIN="$(python -c 'import site; print(site.USER_BASE)')/bin/uv"
test "$("$UV_BIN" --version)" = "uv 0.11.28"
"$UV_BIN" sync --project apps/api --frozen
```

Validate the exact Cloud image first; adjust only after capturing non-secret failure evidence. Do not
depend on a temporary setup-script `export` surviving into the agent phase; use the resolved persistent
UV path or a Cloud environment PATH setting verified again in the agent task.

- [ ] Run a docs/test-only Cloud task with explicit allowed/forbidden paths.
- [ ] Confirm Codex honors `AGENTS.md`, creates a `codex/...` branch and Draft PR.
- [ ] Confirm it does not merge, request secrets, call DeepSeek or claim local Docker evidence.
- [ ] User reviews and merges the first Cloud PR manually.

Reusable Cloud prompt:

```text
TASK <ID>. Read AGENTS.md and the linked source-of-truth/ADR/plan first.
Allowed files: <exact paths>. Forbidden: contracts/**, apps/api/**, database/**, supabase/**,
data/official/**, data/staging/** and security/privacy source-of-truth unless this task explicitly owns
them. No secrets, DeepSeek call, Docker/remote DB, deployment or
merge. Implement one vertical slice with tests, run only cloud-valid checks, write an implementation
note, self-review the diff, push a codex/<task>-<slug> branch and open a Draft PR. Mark every Windows/
Docker/local-only verification as pending for the user.
```

## Task 7: Onboard the frontend teammate with a no-product-change rehearsal

- [ ] Team member clones the private repository and reads the handoff.
- [ ] They reproduce the pinned runtime and current frontend baseline.
- [ ] They open `feat/web-COLLAB-ONBOARDING-doc-check` with exactly one newly added
  `docs/implementation-notes/IMP-*-web-*.md` and only its new INDEX row appended; no existing note or
  INDEX row is modified.
- [ ] Scope classification reports frontend self-merge eligible.
- [ ] Frontend CI passes and screenshots/logs contain no secret or citizen text.
- [ ] Team member performs the first permitted self-merge.
- [ ] That onboarding PR proves PR-only/no-direct-main-push behavior required to close Task 5.
- [ ] User confirms `main` is green and no protected path changed.
- [ ] Open a second dry-run PR that intentionally touches a temporary forbidden test fixture only in
  an isolated branch; prove `OWNER_REVIEW_REQUIRED`, then close it without merge and without putting the
  forbidden file on `main`.

## Task 8: Close out documentation and evidence

**Files:**

- Local closeout: this plan, `TASKS.md`, `scripts/README.md`, `SECURITY.md`, `CONTRIBUTING.md`,
  `docs/handoffs/HANDOFF-20260720-FRONTEND-COLLABORATOR.md`, `CODEX_FILE_INDEX.md`, `CHANGELOG.md`
  and `versions/manifest.json`
- External closeout after Tasks 4~7: actual non-secret GitHub identifiers/evidence and the final
  collaboration implementation note/INDEX

- [x] Record actual repository owner/name without access tokens.
- [ ] Record remote/CI/Cloud test PR URLs only if the user wants URLs in tracked docs; private URLs are
  not required for product reproduction.
- [ ] Mark COLLAB-001 Done only after remote, invite, CI and Cloud Draft PR rehearsal pass.
- [x] Historical local-only closeout recorded remote 0, push 0 and hosted Actions 0 before external
  bootstrap; this was superseded by the 2026-07-21 Task 4/partial Task 5 evidence below. Cloud and
  onboarding rehearsals remain pending; do not invent their evidence.
- [x] Synchronize local scanner/workflow interfaces, security limits, contributor/handoff guidance,
  file index, changelog and collaboration-only versions.
- [x] Keep DATA-SEED-002, PII-CONSUMER, `00700`, public deployment and local-only gates at their actual
  prior states.
- [x] Run the scoped repository-doc/package/current-tree-secret/diff gates and review the final docs-only
  diff. Hosted policy and frozen Frontend CI passed; Task 5 MFA/recovery and the Task 7-owned first
  PR-only/no-direct-main-push rehearsal plus Tasks 6~7 Cloud/onboarding rehearsals remain pending.

## Verification matrix

| Gate | Local Windows | GitHub Actions | Codex Cloud | Required before COLLAB-001 Done |
|---|---:|---:|---:|---:|
| worktree/history secret audit | yes | no | no | yes |
| scope classifier tests | yes | yes | yes | yes |
| shared contract drift | yes | yes | yes | yes |
| web lint/typecheck/unit/build | yes | yes | yes | yes |
| Playwright E2E | yes | yes | optional Cloud | yes local+Actions |
| API pure tests | existing owner gate | future CI | allowed when task needs | no collaboration-only change |
| Docker/Supabase actual | yes only | no | no | no; remains local successor gate |
| DeepSeek synthetic actual | yes only | no | no | no |
| public deploy/remote DB | forbidden | forbidden | forbidden | no |

## Version change plan

- product spec: remains `2.2.5`; no local collaboration-automation product change
- repository guidance: `1.6.2 → 1.7.0`
- test suite: `0.9.0-pii-core → 1.0.0-collaboration`
- documentation: `2.8.3 → 2.9.0`
- application/web/API/contracts/DB/data/prompts/dependencies: unchanged by the local collaboration
  automation

## Risks and rollback

| Risk | Early signal | Response/rollback |
|---|---|---|
| secret in history | pre-push scanner finding | no remote creation/push; rotate and separately approve history cleanup |
| author email metadata exposure | consent record missing or scope expands beyond private collaborator | D-053 preserves current history for the approved private collaborator only; stop and reapprove any broader visibility |
| repository accidentally public | visibility check not `PRIVATE` | do not invite/push further; immediately set private and audit access |
| frontend crosses boundary | classifier `OWNER_REVIEW_REQUIRED` | no self-merge; split PR or owner review |
| CI false green/skipped | summary missing or expected command absent | no merge; fix workflow and rerun same SHA |
| GitHub Free direct push | commit on main without PR | pause merges; inspect/revert if needed; retrain, consider Pro |
| Cloud asks for secret/local proof | task cannot pass without it | mark local verification pending; never upload secret |
| remote diverges | non-fast-forward/unknown commit | stop, fetch/read-only inspect; never force push |
| teammate blocked on contract | local invented type/mock proposal | close/split change; open contract Issue and wait for owner contract PR |

Removing `origin` is not a data-erasure rollback after a push. If collaboration is abandoned, revoke
collaborator and Codex app access, archive or delete the private GitHub repository through an explicit
human action, retain the local Git history, and rotate any credential that may have been exposed.

## Human approval and actions

The user must:

- preserve current history under Q-GIT-004=A/D-053 and do not broaden identity visibility without
  reapproval;
- approve this execution plan;
- authenticate to GitHub and confirm owner/repository/collaborator identifiers;
- accept any GitHub account billing/plan change — none is planned;
- restrict the Codex GitHub app to the one repository;
- manually merge Codex Cloud PRs;
- run/confirm local-only Docker/Supabase/DeepSeek gates when their owning tasks reach that stage;
- separately approve production dependencies, public contracts, DB migrations/data deletion and
  deployment.

AI may autonomously implement the classifier, tests, workflow syntax, templates and documentation
inside the approved plan, but may not invent human account identifiers, authentication, approvals or
successful external-state evidence.

## Progress record

- 2026-07-20: Q-GIT-001=A, Q-OWN-001=A, Q-GIT-002=A, Q-GIT-003=B,
  Q-CLOUD-001=A and Q-COLLAB-001=A recorded; written design approved.
- 2026-07-20: full-history read-only audit found credential/content secret Critical 0 and one
  author-email identity decision.
- 2026-07-20: Q-GIT-004=A/D-053 preserved current history and SHAs.
- 2026-07-20: the user explicitly said `COLLAB-001 계획 승인, 구현 시작`; D-054 records
  execution approval. Local Tasks 1~3 and documentation closeout may proceed. Tasks 4~7 still require
  verified GitHub account identifiers, browser authentication, collaborator acceptance and rehearsal
  evidence and must not be reported complete before those external checks actually pass.
- 2026-07-21: Tasks 1~3 local implementation, integration and independent review closed with
  Critical/Important 0. History/current-tree secret gates, scope/append classification, repository-doc
  validation, pinned workflow/templates and cross-platform Playwright startup are ready locally. Task 8
  local documentation/version synchronization and the integrated Python 3.12 gate passed 102 tests with
  two Windows platform skips; API 1,318 tests, contract 37 tests, Web 6 tests, production build and
  Playwright 9 tests also passed. Fresh history/current-tree scans, repository-doc/package validation,
  YAML parse, Ruff/compile/fsck/diff checks passed. **At this local closeout checkpoint**, hosted Actions
  evidence remained external and Tasks 4~7 were unchecked; the later Task 4/partial Task 5 evidence
  below supersedes that temporary remote/push/hosted-Actions state.
- 2026-07-21: final whole-diff review found one Important candidate-scanner resource-bound gap. Commit
  `264518a` added Git stdout/stderr/deadline and repository per-file/aggregate limits with behavioral
  oversized/stall tests; final rereview closed Critical 0 / Important 0 and marked the branch ready to merge.
- 2026-07-21: Task 4 external bootstrap is verified: `tskwak111/Sejong_AI` is private, non-empty and
  defaults to `main`; initial ordinary push only set `origin/main` to
  `5e09deccc7205503df07d938b6d4a88f4d5a327e`. Both hosted runs on that SHA passed (policy
  `29776352710`, frozen Frontend CI `29776352718`). Task 5 evidence verifies accepted `koregy` write
  access, `FRONTEND_COLLABORATOR_LOGIN=koregy`, read-only default Actions permissions and the
  direct-push warning in the repository description. Task 5 remains partial: teammate MFA/recovery and
  the first Task 7 PR-only/no-direct-main-push rehearsal are human-only Pending.
- 2026-07-21: App-scope evidence interpretation corrected by D-056. Public repository visibility is
  normal even for selected-repository installation and does not prove over-broad scope. Human UI
  confirmation of `Only select repositories / Sejong_AI` was later completed by D-057. Cloud
  environment, docs/test-only task, `codex/...` Draft PR/manual merge and all Task 7 teammate
  onboarding/self-merge/forbidden-scope rehearsals remain Pending. COLLAB-001 stays In Progress. Exact owner and teammate steps are in
  `docs/handoffs/HANDOFF-20260721-OWNER-GITHUB-CLOUD-CHECKLIST.md`.
- 2026-07-21: user completed the App-scope check and merged PR #1. GitHub evidence confirms merge
  commit `ce8a6085fb57670ca74e009ed45e3d02d784c24b`; post-merge Collaboration policy `29782433649`
  and Frontend CI `29782433682` both passed on that SHA. Task 6 is partial. Teammate MFA/recovery is a
  recommended account and repository-supply-chain control before their first push, but does not block
  Cloud or backend work; no authentication value is collected.
