# 4일 local/private 핵심 개선 루프 MVP 실행계획

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` for
> independent code tasks and `superpowers:test-driven-development` for every behavior change.

- Plan ID: MVP-001-PLAN
- Status: **Approved / In Progress — Q-MVP-001=A and immediate execution**
- Window: 2026-07-22 02:10 KST ~ 2026-07-25
- Goal: local/private 19→20 ACTIVE 개선 루프와 시민/admin 최소 UI 완주
- Design: `docs/superpowers/specs/2026-07-22-four-day-local-private-core-loop-mvp-design.md`

## Global constraints

- Start base is fetched `origin/main` merge commit `9044ddb`.
- Never edit immutable `.1`, existing migrations `00100~00600`, raw approved facts, or `legacy/`.
- No actual citizen/provider call, remote DB, public deploy, secret output, volume deletion or new production dependency.
- Do not weaken raw-question 0, ACTIVE-only, server-bound source, self-approval, official/mock, keyboard/contrast gates.
- Every task: RED → minimal GREEN → focused test → full relevant gate → diff review → note/version update.
- Frontend collaborator never edits contract/package/lockfile/backend/DB/data/security paths.
- A human-only action is kept pending without stopping safe independent tasks.

## Date and role schedule

| Date | Owner / Backend·Data·Security | Frontend collaborator | PM/QA | Exit gate |
|---|---|---|---|---|
| 7/22 Wed | PR #5 post-merge baseline repair, PR #4 correction support, DATA-SEED-002 Tasks 1~5 | PR #4 `012→014`, then fixture-only `/chat` states | Q-MVP docs review, no new decision | canonical staging/release checks green; `.2` independently reviewable |
| 7/23 Thu | DATA actual cycle, 19 ACTIVE, PII/chat contract freeze, pure chat core/context | fixture UI complete; typed client prep after owner contract | verify 19 official rows and contract copy | DATA actual PASS; contract drift 0; chat core unit/privacy green |
| 7/24 Fri | `/api/v1/chat`, events, admin read/write API, 20th candidate backend | actual `/chat` integration, minimal `/admin` | author/reviewer role rehearsal | chat E2E + candidate submit/review atomic tests green |
| 7/25 Sat | final integration, security/sample/demo fixes | 390/430/desktop/accessibility fixes | sample 20, regression 1, final rehearsal | 20 ACTIVE, all local gates green, deferred items explicitly listed |

## Dependency graph

```text
Task 0 baseline/PR4
  -> Task 1 DATA-SEED-002 -> Task 2 19-row readiness
  -> Task 3 contract freeze -> Task 4 chat core -> Task 5 API chat
Task 3 -> Task 6 frontend fixture -> Task 7 frontend actual
Task 5 -> Task 8 event/admin -> Task 9 20th ACTIVE regression
Task 7 + Task 9 -> Task 10 sample/security/demo closeout
```

### Task 0: Restore the integrated main baseline and correct PR #4

**Files:**
- Modify: `scripts/check_collaboration_scope.py`
- Modify: `scripts/tests/test_collaboration_scope.py`
- Modify only if needed: staging validator focused tests
- Remote teammate branch: rename note `IMP-20260721-012-*` to `IMP-20260721-014-*` and matching INDEX row

- [x] Add a RED test proving policy literals/test fixtures cannot make canonical DATA staging invalid,
  while a real runtime import/path use still fails.
- [x] Change the collaboration policy representation so it does not contain an active staging path token;
  do not weaken the staging scanner allow/deny rules.
- [x] Confirm the earlier `jsonschema` finding was false: the repository already uses its strict validator,
  so no dependency or replacement was required.
- [x] Run focused collaboration/staging validation, `.1` release/dispatcher, docs and secret checks.
  The broad `scripts/tests` discovery remains a later root closeout gate because the initial environment run
  exceeded the task window and mixed unrelated local-runtime prerequisites.
- [x] Rebase/correct PR #4 note ID and verify its exact two-file docs-only scope. Head `37dfc8b`,
  CLEAN/MERGEABLE, hosted summaries green; human/team member merge remains pending.

### Task 1: Execute approved DATA-SEED-002 Tasks 1~5

**Files:** exactly those listed in
`docs/superpowers/plans/2026-07-20-data-seed-002-successor-release-correction.md` Tasks 1~5.

- [ ] Freeze `.1`/v1 byte fingerprints and add dual closed release profiles.
- [ ] Add successor three-`EXISTS` SQL/verifier semantics and align one pgTAP predicate.
- [ ] Add strict v2 schemas and `.2`-only create/activate state machine.
- [ ] Bind root/DB runners to `.2` while preserving cleanup/output allowlists.
- [ ] Generate twice, independent reviewer Critical/Important 0, publish create-once `.2`, activate dispatcher.
- [ ] Focused Python tests and protected-path fingerprint checks pass.

### Task 2: Run the disposable actual DB cycle and promote 19 ACTIVE

**Files:** DATA-SEED-002 Task 6 report/lineage/docs/version files only.

- [ ] Bootstrap and verify the pinned patched Supabase runtime without revealing network credentials.
- [ ] Run exactly `scripts/verify_data_seed.ps1 -ReleaseVersion 0.1.0-initial.2` from absent owned runtime.
- [ ] Require pgTAP/integration/replay/compensation/19-3-10/cleanup PASS.
- [ ] On complete PASS set only `official_data=0.1.0-initial.2`; keep `/ready=503` until application probe Task 5.
- [ ] On failure retain `.2`, do not promote version, record reached stages, and continue only non-DB work.

### Task 3: Freeze PII consumer, chat, and minimal admin contracts

**Files:**
- Modify: `contracts/openapi-v1.yaml`, `contracts/chat-response.schema.json`
- Modify/generated: `packages/shared-contracts/**`
- Modify: `apps/api/src/sejong_ai_api/contracts/**`, matching fixtures/tests
- Modify: `versions/manifest.json`, ADR/design/note

- [ ] Write RED contract fixtures for `PRIVACY_UNRESOLVED`, admin list/detail/create/submit/review envelopes,
  exhaustive generated TS and strict Pydantic parity.
- [ ] Add the response enum and exact no-source/no-context/no-office/candidate-false invariants.
- [ ] Complete admin response schemas without changing path names.
- [ ] Bump API to `3.0.0-draft` and shared contracts to `0.3.0` in the same change.
- [ ] No DB migration in this milestone for privacy metadata; reserved public `00700` remains untouched.

### Task 4: Implement the pure deterministic chat domain

**Files:**
- Create: `apps/api/src/sejong_ai_api/chat/{classification,retrieval,grounding,response,context,service}.py`
- Create: matching `apps/api/tests/chat/**` fixtures/tests
- Modify only for ports: DB repository protocol/fakes

- [ ] RED tests for all 6 intents, ambiguous FOLLOWUP, 5 fallback reasons, lexical ranking and stable ties.
- [ ] RED privacy spies: raw sentinel reaches no classifier/retriever/repository/provider/log/error.
- [ ] Implement ACTIVE/OFFICIAL-only retrieval and server-bound source/office conversion.
- [ ] Implement template SUCCESS and high-risk field omission; no provider SDK.
- [ ] Implement 900-second signed context with value-free claims and silent invalid reset.
- [ ] Validate sample 20 expectations at pure-service level.

### Task 5: Implement `/api/v1/chat` and readiness

**Files:**
- Create: `apps/api/src/sejong_ai_api/api/chat.py`
- Modify: `apps/api/src/sejong_ai_api/main.py` and dependency composition/config
- Create/modify: route, contract, privacy, logging and DB integration tests

- [ ] RED route tests for SUCCESS/FOLLOWUP/FALLBACK/PRIVACY/503/idempotency.
- [ ] Connect redactor → service → repository and metadata event matrix.
- [ ] Map DB unavailable to 503 only when no safe template/snapshot exists.
- [ ] Enable `/ready=200` only when DB responds and required 19 ACTIVE+office projection exists.
- [ ] Ensure request body/raw question and context token are absent from access/error logs.

### Task 6: Frontend fixture-first `/chat` in parallel

**Owner:** Frontend collaborator. **Allowed paths:** current collaboration allowlist only.

- [ ] Build controlled fixture states for SUCCESS/FOLLOWUP/all fallback including privacy, empty office, 503.
- [ ] Implement input, region, transcript, source/office cards, retry/duplicate-submit prevention.
- [ ] Keep all transcript/token state in memory; browser storage/cookie/analytics 0.
- [ ] Unit/E2E at 390/430/desktop, keyboard/focus/contrast/no-horizontal-overflow.
- [ ] PR stays frontend-only and uses next reserved implementation-note ID.

### Task 7: Connect actual typed frontend client

**Files:** owner prepares shared-contract package boundary; collaborator changes web/E2E only.

- [ ] Owner exposes generated shared types with frozen workspace/lockfile change and review.
- [ ] Collaborator replaces fixture transport with typed fetch while preserving test transport injection.
- [ ] Treat 200 policy outcomes separately from 503; do not display stale transcript as sent.
- [ ] Render source metadata byte-for-value; never synthesize URLs/dates.

### Task 8: Implement event/admin minimum

**Files:** API admin contracts/routes/services/repository reads and `apps/web/src/app/admin/**`.

- [ ] RED tests for failed list/detail/expired text/filters and role gate.
- [ ] RED tests for reason confirm, candidate PII recheck, submit, self-approval rejection, approve/reject.
- [ ] Add typed repository read methods and minimal admin routes; public mode router disabled.
- [ ] Add local role switch UI with explicit demo-only label and audit metadata view.
- [ ] Confirm OUT_OF_SCOPE/FOLLOWUP/PRIVACY failed row 0 and 30-day text purge behavior.

### Task 9: Promote the 20th ACTIVE KB through the product loop

**Data:** `KB-WASTE-03`, existing PM-approved official source only.

- [ ] Start from the canonical bed-frame question and record `INSUFFICIENT_GROUNDING` masked failure.
- [ ] OPERATOR confirms reason and authors candidate; `PM-LOCAL-001` or other different APPROVER reviews.
- [ ] Transactionally create exactly one ACTIVE/OFFICIAL 20th KB; audit snapshot text 0.
- [ ] Re-run same question and require SUCCESS, expected fee/source, source count >=1.
- [ ] Record runtime lineage separately from immutable initial `.2` artifact.

### Task 10: Saturday acceptance and closeout

**Files:** evaluation report, security report, demo runbook, version/task/source-of-truth/note updates.

- [ ] Run all 20 sample questions and publish numerator/denominator for success/source/fallback/followup/privacy.
- [ ] Run regression 1, ACTIVE-only/DRAFT-hidden, raw sentinel, secret/history/browser-bundle gates.
- [ ] Run API lint/type/full tests, web lint/type/unit/build/E2E, DB pgTAP/integration and root offline verify.
- [ ] Rehearse provider-off local demo from clean start through admin improvement.
- [ ] Record 100-user, automatic backup, DeepSeek tuning, advanced UI, public deploy as deferred—not passed.
- [ ] Independent spec and code/data/security review must report Critical 0, Important 0.

## Daily stop conditions

- Raw question, secret, DSN, token or PII appears in output/storage/provider: stop and security review.
- `.1`/v1 byte changes or official fact drift: stop; never regenerate in place.
- New architecture/public/remote/dependency decision: keep that lane pending and continue safe lanes.
- DATA actual failure: preserve evidence and continue contract/frontend fixtures; do not claim 19 ACTIVE.
- Contract changes after frontend actual integration: stop merging UI until generated drift is green.

## Plan self-review

- Every user priority 1~8 maps to Tasks 0~10.
- Human account/PM gates are separated from AI-executable work.
- Deferred items remain in the final project backlog and are not counted as Saturday PASS.
- No `TBD`, placeholder acceptance criterion, secret, private URL, raw question corpus or unapproved dependency.
