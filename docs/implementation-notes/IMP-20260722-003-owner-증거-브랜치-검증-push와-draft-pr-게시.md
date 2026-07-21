# IMP-20260722-003 — owner 증거 브랜치 검증 push와 Draft PR 게시

- Date/Time (KST): 2026-07-22T01:30:56+09:00
- Task ID: COLLAB-OWNER-PR-001
- Type: documentation-github-publication
- Status: Done
- Author/Agent: Codex (owner lane)
- Branch: codex/COLLAB-001-pr2-merge-evidence
- Base commit: 592e309
- Related plan/ADR/RFP: `COLLAB-001`, ADR-0019, collaboration transition plan, current execution lanes handoff

## 1. 사용자 요청과 완료 기준

### 요청

- 사용자가 현재 owner 브랜치를 검증하고 GitHub 작업 브랜치로 push한 뒤 owner-review PR을 만들라고 명시적으로 승인했다.

### Acceptance Criteria

- live remote `main`을 fetch하고 branch ahead/behind·범위·인증·private target을 확인한다.
- 문서·비밀·Git history·협업 scope 검증을 통과한다.
- `main` 직접 push 없이 현재 `codex/*` 브랜치를 origin에 게시한다.
- 대상 `main`의 Draft owner-review PR을 생성하고 자동 merge하지 않는다.
- exact branch/SHA/PR/check 결과와 인간 merge 책임을 기록한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자 승인자·merge reviewer, Codex local publisher, GitHub Actions reviewer |
| When — 언제 | 2026-07-22 KST |
| Where — 어디서 | local owner worktree, private `tskwak111/Sejong_AI`, Draft PR |
| What — 무엇을 | owner evidence/docs branch pre-push 검증·원격 게시·Draft PR 생성 |
| Why — 왜 | unpublished owner 문서를 remote main에 먼저 통합해 PR #4 note-ID 교정 기준선을 만들기 위해 |
| How — 어떻게 | fetch/auth/scope/diff/secret/history/docs/git 검증→explicit branch push→Draft PR |
| How much — 어느 정도 | pre-existing docs-only owner diff와 이 publication note; product/API/DB/data/deployment change 0 |

## 3. 시작 전 상태

- 관련 파일: `CHANGELOG.md`, `TASKS.md`, collaboration plan/checklists/guides/implementation notes/INDEX, `versions/manifest.json`.
- 기존 동작: PR #1~#3는 병합됐고 Cloud runtime verification도 완료. PR #4는 teammate note 012와 owner note 012의 논리 충돌 때문에 HOLD.
- 발견한 충돌/부채: owner 변경이 로컬에만 있으면 teammate/Cloud의 최신 remote main에서 보이지 않는다.
- Git 상태: fetch 직후 current branch `codex/COLLAB-001-pr2-merge-evidence`, HEAD `592e309`, `origin/main...HEAD=0 behind/8 ahead`, clean, same-head PR 없음. exact publication SHA는 이 note commit 뒤 확정한다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| PR-MODE-001 | Confirmed policy | owner/Codex PR 공개 단계 | Draft PR, human merge | GitHub main 변경 통제 |
| TARGET-001 | Verified | repository/base | private `tskwak111/Sejong_AI`, `main` | 외부 게시 범위 |

## 5. 설계 결정과 대안

### 선택

- 기존 non-default `codex/COLLAB-001-pr2-merge-evidence` 브랜치를 유지해 push한다.
- PR은 Draft로 만들고 사용자 검토/merge를 남긴다.
- GitHub app PR 생성 도구가 직접 노출되지 않아 authenticated `gh` CLI fallback을 사용한다.

### 이유

- 이미 검토 가능한 논리 커밋 계보가 있고, 새 브랜치나 history rewrite 없이 정상 push로 게시할 수 있다.

### 고려했지만 선택하지 않은 대안

- `main` 직접 push: PR-only 정책 위반으로 기각.
- force-push/rebase/squash: 기존 SHA·감사 계보를 바꾸므로 기각.
- PR #4 선병합: duplicate note ID를 만든 뒤 owner branch가 충돌하므로 기각.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| 이 구현 노트 | pre-push, push, Draft PR, hosted check evidence 기록 | 요청별 감사·재현 |
| `docs/implementation-notes/INDEX.md` | IMP-20260722-003 행 | 검색 계보 |
| `versions/manifest.json` | documentation 2.10.8→2.10.9 | 문서 게시 기록 버전 |
| GitHub branch/PR | exact 결과는 게시 뒤 이 note에 추가 | 외부 협업 기준선 |

### 데이터 흐름/상태 변화

- local commits가 private origin의 같은 `codex/*` branch로 복제되고 Draft PR이 `main`을 대상으로 생성된다.
- PR 생성 자체는 `main`, product runtime, DB, official data를 변경하지 않는다.

### 오류·빈 상태·롤백

- pre-push 검증 실패 시 push/PR을 만들지 않는다.
- push 후 PR 생성 실패 시 remote branch를 유지한 채 원인을 보고하고 중복 PR 없이 재시도한다.
- Draft PR 검토 실패 시 close-without-merge하거나 같은 branch에 정상 follow-up commit을 push한다.

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
- documentation: 2.10.8

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.3.0-pii-core | 동일 | 제품 코드 변경 없음 |
| Web | 0.2.0-static-chat-shell | 동일 | UI 동작 변경 없음 |
| API | 2.0.1-draft | 동일 | 공개 계약 변경 없음 |
| DB schema | 0.3.0-local | 동일 | migration 없음 |
| Official data | 0.0.0-not-populated | 동일 | seed 없음 |
| Mock data | 0.0.0-not-populated | 동일 | mock 변경 없음 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | provider 호출 없음 |
| Test suite | 1.0.0-collaboration | 동일 | 테스트 코드 변경 없음 |
| Docs | 2.10.8 | 2.10.9 | publication evidence note |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `gh --version`, `gh auth status` | gh 2.46.0, active authenticated owner account; credential value redacted | 시작 시점 | local CLI |
| `git fetch --prune origin`; repository/branch/PR queries | PRIVATE/main, current 0 behind/8 ahead, same-head PR 0 | 시작 시점 | Git/GitHub metadata |
| `python -B scripts/check_repository_docs.py` | PASS | publication 전 | local output |
| Windows PowerShell current-tree secret-pattern scan | PASS | publication 전 | local output |
| repository-doc/collaboration-scope/history-scanner unit tests | PASS: 65, skipped: 1, failure/error: 0 | 38.504s | local output |
| first/second proposed-path shell checks | 안전 중단: prefix anchor 오류, 이어서 한글 `core.quotePath` quoting 미정규화 | push 전 2회 | local output; repository diff 문제 아님 |
| corrected committed-tree gate | PASS: docs/current-tree secret/reachable-history secret/JSON/diff/fsck/note-ID/path allowlist | 15 paths | local output |
| collaboration scope | PASS with expected `OWNER_REVIEW_REQUIRED` | 15 changes/15 paths | local output |
| `git push -u origin codex/COLLAB-001-pr2-merge-evidence` | PASS; remote branch created and upstream set | SHA `5feff0b186747c6b5434a09bca0b511264ec78a5` | private origin |
| Draft PR creation and metadata query | PASS; PR #5 OPEN/Draft, `main` base, expected head, MERGEABLE | 15 files | GitHub |
| remote SHA comparison | PASS; local HEAD=remote branch=PR head `5feff0b...` at initial publication | 3-way exact | Git/GitHub metadata |
| hosted checks on evidence head `b6804cd` | Collaboration policy summary PASS, trusted candidate policy PASS, Frontend CI summary PASS, scope detection PASS; frontend/browser and main-only jobs SKIPPED as expected | PR #5 | GitHub Actions |

### 미실행 검증과 이유

- 제품 build/API/DB/Docker/DeepSeek actual은 proposed diff가 docs-only이므로 이 게시 요청의 완료 gate가 아니다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문 원문·개인정보·credential value를 기록하지 않는다.
- Security: private target, normal branch push, secret/history scanners, Draft/human merge boundary를 사용한다.
- Accessibility: UI 변경 없음.
- Performance/cost: GitHub Actions quota 외 runtime/provider 비용 영향 없음.

## 10. 데이터와 출처 영향

- 공식 데이터: 변경/seed 0.
- mock/AI 생성: 변경 0.
- schema/lineage: DB/data lineage 변경 없음; Git 문서/PR 계보만 갱신.
- verified date: 2026-07-22 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Draft PR은 사용자가 파일과 hosted checks를 검토해 Ready/merge해야 한다. Codex는 merge하지 않는다.
- PR #4는 owner PR merge와 teammate 012→014 correction 전까지 HOLD다.
- GitHub에 push되는 것은 tracked docs/history이며 ignored local env/Docker state는 포함되지 않는다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- initial publication commit은 `5feff0b186747c6b5434a09bca0b511264ec78a5`, Draft owner-review PR은 #5다.
- owner PR은 Collaboration policy상 `OWNER_REVIEW_REQUIRED`가 정상 기대값이다.
- 두 번의 path allowlist 중단은 ad-hoc PowerShell 검증식의 진단 오류였다. 첫 번째는 `docs/` prefix 뒤 `.*` 누락, 두 번째는 Git의 한글 경로 quoting 미정규화였고 `git -c core.quotePath=false`로 고친 전체 gate가 exit 0을 확인했다. 두 실패 모두 push 전에 발생했다.

## 13. 인수인계·재현·롤백

### 재현

1. fetch 후 `origin/main...HEAD` ahead/behind와 proposed file list를 확인한다.
2. 명시된 pre-push gates를 실행한다.
3. remote branch SHA와 local HEAD 일치를 확인한다.
4. Draft PR base/head/files/check status를 GitHub에서 확인한다.

### 롤백

- merge 전: Draft PR을 close하고 필요하면 remote 작업 브랜치를 삭제한다.
- merge 후: history rewrite 없이 merge commit을 대상으로 small revert PR을 만든다.

### 다음 개발자 시작점

- human owner가 Draft PR diff와 checks를 확인한 뒤 Ready로 전환·merge한다. post-merge green 뒤 PR #4 correction을 진행한다.

## 14. 남은 위험·미해결 질문·다음 단계

- PR #5는 Draft이며 hosted checks는 evidence head에서 green이다. 이 기록 자체의 final metadata-only commit도 push 뒤 같은 hosted checks를 다시 확인해야 하며 인간 review/merge는 Pending이다.
- PR #4와 MFA/recovery human-only evidence가 남아 있다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
