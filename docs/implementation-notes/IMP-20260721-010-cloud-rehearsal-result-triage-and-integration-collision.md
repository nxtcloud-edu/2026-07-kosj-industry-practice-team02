# IMP-20260721-010 — cloud rehearsal result triage and integration collision

- Date/Time (KST): 2026-07-21T09:30:25+09:00
- Task ID: COLLAB-CLOUD-REHEARSAL-001-TRIAGE
- Type: documentation-github-cloud-evidence
- Status: Done — old Cloud run held; owner-review Draft PR #2 green/manual merge and rerun 002 pending
- Author/Agent: Codex primary agent
- Branch: codex/COLLAB-001-post-merge-evidence
- Base commit: 4b473e2
- Related plan/ADR/RFP: COLLAB-001 approved plan/spec, ADR-0019, D-047~D-057, TASKS COLLAB-001

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 Codex Cloud의 첫 docs-only rehearsal 응답을 전달했다. 응답의 실제 GitHub 상태와 변경 범위를
검증하고 지금 무엇을 해야 하는지 판정한다.

### Acceptance Criteria

- Cloud 보고와 실제 remote branch/PR 상태를 구분한다.
- reported two-file diff, commit, 검사 성공/실패를 과장 없이 기록한다.
- 존재하지 않는 secret-check 명령과 note ID 충돌을 찾아 publish/merge 가능 여부를 판정한다.
- 제품·계약·DB·data·secret에 변경을 가하지 않는다.
- 다음 재실행 순서와 인간 행동을 명확히 남긴다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | Codex Cloud agent가 실행·보고, 사용자가 결과 전달, primary Codex가 GitHub/local integration 검증 |
| When — 언제 | 2026-07-21 09:30 KST, 첫 Cloud docs-only run 직후 |
| Where — 어디서 | `sejong-ai-cloud-docs`, private GitHub `tskwak111/Sejong_AI`, local post-merge docs worktree |
| What — 무엇을 | internal commit/make_pr와 실제 remote PR을 구분하고 scanner·note sequence 충돌을 판정 |
| Why — 왜 | 미생성 PR을 생성됐다고 오인하거나 충돌하는 문서 ID를 merge하는 일을 막기 위해 |
| How — 어떻게 | user report, `git ls-remote`, `gh pr list`, `origin/main` tree/index, generator 로직을 대조 |
| How much — 어느 정도 | external mutation 0; status/plan/note/INDEX/changelog/manifest docs only; product/API/DB/data 0 |

## 3. 시작 전 상태

- 관련 파일: collaboration plan/TASKS, owner Cloud checklist, implementation-note generator/INDEX,
  local notes 003~010, remote `origin/main`.
- 기존 동작: Cloud가 새 note와 INDEX append를 internal commit `b080a89`에 기록하고 `make_pr` metadata를
  만들었으나, 실제 PR 생성은 사용자의 Cloud UI action 이후에 일어난다.
- 발견한 충돌/부채: prompt의 `scripts/check_current_tree_secrets.py`는 저장소에 없고 실제 active-tree
  scanner는 `scripts/check_secret_patterns.ps1`이다. Cloud의 `IMP-20260721-003`은 remote main만 보면 다음
  번호지만, 아직 게시되지 않은 local integration branch의 기존 003과 충돌한다.
- Git 상태: remote main `ce8a608...`; Cloud ref 0, new PR 0. local branch는 origin/main ahead 2와 기존
  docs 변경을 보존하며 external write 0.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| CLOUD-TRIAGE-001 | Verified | `make_pr`가 실제 GitHub PR인가 | 아니오; remote ref/PR 없음 | Task 6 remains partial |
| CLOUD-TRIAGE-002 | Internal risk | concurrent sequential note ID | local docs를 먼저 통합한 뒤 refreshed main에서 generator 재실행 | merge conflict/traceability |
| CLOUD-TRIAGE-003 | Verified bug | requested secret script absent | 실제 `pwsh ... check_secret_patterns.ps1 -RepositoryRoot .` 사용 | Cloud gate reproducibility |
| CLOUD-TRIAGE-004 | Human pending | actual Draft PR/manual merge | corrected rerun 뒤 사용자 검토 | completion evidence |

## 5. 설계 결정과 대안

### 선택

현재 Cloud output의 Create/Open PR을 누르거나 merge하지 않는다. 먼저 local post-merge documentation
branch를 owner-reviewed PR로 통합해 note sequence와 corrected command를 remote main에 올린다. 그 다음
Cloud rehearsal을 refreshed main에서 새로 실행하고 generator가 remote 기준 다음 번호를 할당하게 한다.

### 이유

Cloud commit은 remote에 없으므로 Draft PR evidence가 아니며, 현재 내용을 게시하면 local 003과 identity가
충돌한다. old base에서 임의 renumber/rebase를 시키는 것보다 authoritative main을 먼저 갱신한 재실행이
가장 재현 가능하고 diff가 작다.

### 고려했지만 선택하지 않은 대안

- 지금 Create PR 후 merge: note ID collision과 known failed gate를 main에 싣게 되어 제외.
- Cloud note를 임의 010/011로 수동 rename: local sequence가 아직 remote authority가 아니고 INDEX append
  conflict가 남아 제외.
- 실패를 성공으로 고쳐 적기: 실제 미실행을 은폐하므로 금지.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| TASKS/COLLAB plan | internal run과 actual remote absence, hold/rerun order | status truthfulness |
| owner checklist/frontend handoff/source-of-truth | old run explicit HOLD, corrected rehearsal 002, canonical setup link, dynamic `origin/main` comparison | reviewer-found stale instructions 제거 |
| IMP-007 | saved Cloud environment를 Task 6 evidence로 교정 | task ownership accuracy |
| CHANGELOG/manifest | triage 기록, docs 2.10.1 | lineage |
| this note/INDEX | 6W1H evidence and next action | request-level handoff |

### 데이터 흐름/상태 변화

```text
Cloud internal commit/make_pr
  → GitHub remote ref 0 / PR 0
  → known scanner failure + concurrent ID collision
  → publish/merge HOLD
  → local docs owner-review integration
  → refreshed-main Cloud rerun
  → actual Draft PR
  → human review/merge
```

### 오류·빈 상태·롤백

- 현재 external write가 없어 rollback은 불필요하다. Cloud task는 publish하지 않고 폐기한다.
- 실수로 PR을 만들었으면 merge하지 않고 close한다.
- 실수로 merge했다면 history rewrite 대신 revert PR을 사용하고 note identity를 별도 corrective note로 복구한다.

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
- documentation: 2.10.0

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.3.0-pii-core | unchanged | product code 0 |
| Web | 0.2.0-static-chat-shell | unchanged | frontend code 0 |
| API | 2.0.1-draft | unchanged | contract/backend 0 |
| DB schema | 0.3.0-local | unchanged | migration/data write 0 |
| Official data | 0.0.0-not-populated | unchanged | official record 0 |
| Mock data | 0.0.0-not-populated | unchanged | fixture 0 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | unchanged | LLM call 0 |
| Test suite | 1.0.0-collaboration | unchanged | tests unchanged |
| Docs | 2.10.0 | 2.10.1 | Cloud result triage/status/next order |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| Cloud report review | PARTIAL | docs PASS, diff PASS, missing scanner FAIL, status PASS | user-provided summary |
| `git ls-remote --heads origin codex/COLLAB-CLOUD-REHEARSAL-001-doc-check` | PASS | output 0: remote ref absent | terminal |
| `gh pr list --repo tskwak111/Sejong_AI --state all ...` | PASS | only merged PR #1; new PR 0 | terminal |
| `origin/main` note/index/tree inspection | PASS | remote has 001~002; local committed 003~004 plus pending 005~010 | terminal |
| `new_implementation_note.py` sequence inspection | PASS | filesystem max+1; concurrent branches can collide | source inspection |
| final docs/secret/diff/JSON/note-ID checks | PASS | docs exit 0; secret finding 0; diff error 0; JSON valid; local duplicate ID 0 | terminal |
| fresh remote branch/PR absence gate | PASS | matching branch 0, matching PR 0 | GitHub/terminal |
| independent whole-diff review | initial FAIL → fixed | Critical 0; Important 3 fixed; Minor 1 fixed | review agent / active docs |
| local integration publish | PASS / human pending | branch push and Draft PR #2 created; policy/Frontend CI PASS; merge 0 | private GitHub metadata |

### 미실행 검증과 이유

- Cloud commit `b080a89` diff contents: no remote ref/PR exists, so primary agent cannot independently fetch it;
  two-file claim remains user-provided Cloud evidence.
- Windows/Docker/Supabase/DeepSeek: docs-only Cloud scope에서 실행 금지/불필요.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문 원문·secret·credential 수집/저장 0.
- Security: failed gate를 숨기지 않고 nonexistent path를 바로잡으며 actual remote evidence 없이는 PR 성공을
  주장하지 않는다.
- Accessibility: UI/product 변경 0.
- Performance/cost: local read-only/GitHub metadata checks만 수행; provider/API/DB cost 0.

## 10. 데이터와 출처 영향

- 공식 데이터: unchanged, source/approval/record 0.
- mock/AI 생성: unchanged.
- schema/lineage: DB/data unchanged; documentation evidence only.
- verified date: 2026-07-21 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 현재 Cloud 화면에서 **Create/Open pull request를 누르지 말고 merge도 하지 않는다**.
- 이 run은 agent execution 증거로는 유효하지만 remote branch/Draft PR 증거는 아니다.
- local docs integration이 remote main에 들어간 뒤 corrected prompt로 Cloud를 다시 실행한다.
- 재실행에서도 Draft PR은 사용자만 검토/merge하며 secret/Docker/DB/DeepSeek는 사용하지 않는다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- note generator는 local filesystem의 최대 sequence를 사용하므로 서로 다른 unshared branches에서 동시에
  실행하면 같은 ID를 고를 수 있다. 이번 충돌은 제품 설계가 아니라 integration ordering으로 해결한다.

## 13. 인수인계·재현·롤백

### 재현

`git ls-remote`로 Cloud branch absence를 확인하고 `gh pr list`로 actual PR 목록을 확인한다. remote main과
local integration branch의 notes/INDEX를 비교하고 generator의 `next_sequence` filesystem scan을 확인한다.

### 롤백

현재 Cloud task를 publish하지 않는다. 이미 PR을 만들었다면 close without merge한다. 본 local triage docs는
필요 시 단일 docs revert로 되돌린다.

### 다음 개발자 시작점

owner-review Draft PR #2를 사람이 검토·merge한 후 remote main을 확인한다. 그 다음 owner checklist의
corrected Cloud rehearsal 002 prompt를 새 task에서 실행한다.

## 14. 남은 위험·미해결 질문·다음 단계

- Cloud commit/branch 내용은 remote에 없으므로 independent patch review가 아직 불가능하다.
- local documentation branch는 final review와 Draft PR #2 hosted checks를 통과했지만 인간 merge가 남았다.
- independent review에서 old-run publish 지시, superseded setup script, hardcoded current main SHA와 Task 5/6
  오기를 발견해 corrected rerun/dynamic authority/Task 6 wording으로 교정했다.
- 다음 한 단계: 기존 Cloud 결과 화면은 건드리지 않고 사용자가 Draft PR #2를 검토·merge한다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증 — docs/secret/diff/JSON/note-ID and fresh remote absence gates PASS
- [x] source-of-truth/계약/버전 동기화 — collaboration status only; public contracts unchanged
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
