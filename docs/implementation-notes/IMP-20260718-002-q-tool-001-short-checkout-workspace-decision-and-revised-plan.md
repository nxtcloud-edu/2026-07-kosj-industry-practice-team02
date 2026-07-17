# IMP-20260718-002 — Q-TOOL-001 short checkout workspace decision and revised plan

- Date/Time (KST): 2026-07-18 00:58 ~ 01:42
- Task ID: DB-001-T10-QTOOL001-DECISION-PLAN
- Type: decision-architecture-planning
- Status: Decision-only Done — revised implementation plan awaiting user approval
- Author/Agent: 사용자 결정, Codex root 문서화·계획 작성, independent plan/security reviewers
- Branch: `codex/db-001-layered-enforcement`
- Base commit: `92ff25d`
- Related: Q-TOOL-001, A-025, D-032, ADR-0013/0014, Q-SEC-006 patched CLI spec/plan, DB-001

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 Windows patched CLI build workspace 질문에 `Q-TOOL-001: A`라고 답했다. 선택 A는 두
checkout만 짧은 project-local `.tools/s/{a,b}`로 옮기고 기존 PowerShell 5.1 cleanup과 exact
source/toolchain/patch/hash 공급망을 유지하는 안이다.

### Acceptance Criteria

- A-025를 해결하고 새 결정 ID와 ADR을 기록한다.
- source-of-truth, ambiguity, decision log, discovery, RFP trace, TASKS를 동기화한다.
- 기존 approved spec과 implementation plan에 short-root/path-budget amendment를 정확히 반영한다.
- 공개 API, DB schema/migration/data, privacy, dependency, deployment를 바꾸지 않는다.
- 제품/tooling 코드는 수정하지 않고 수정 계획을 사용자 검토용으로 제시한다.
- 구현 노트와 INDEX, documentation version을 갱신하고 문서 정합성을 검증한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 option A를 확정했고 Codex root가 결정·ADR·계획을 동기화한다. |
| When — 언제 | 2026-07-18 KST, Task 3 long-path cleanup blocker 보고 직후다. |
| Where — 어디서 | isolated worktree `codex/db-001-layered-enforcement`의 tracked docs/spec/plan/ADR/version에서 수행한다. |
| What — 무엇을 | Q-TOOL-001=A를 D-032/ADR-0014로 확정하고 `.tools/s/a`, `.tools/s/b` 및 pre-checkout path budget 계획을 작성한다. |
| Why — 왜 | 관측 최대 299자 기존 checkout을 PS5.1이 부분 삭제했으며 destructive native delete나 새 Linux 공급망 없이 재현 build를 안전하게 재개해야 하기 때문이다. |
| How — 어떻게 | 기존 3개 대안을 비교한 인간 선택을 반영하고 manifest-pinned path limits, pre-mutation RED/GREEN, 독립 review gate를 기존 계획의 Task 2C로 삽입한다. |
| How much — 어느 정도 | documentation 2.3.22→2.3.23, tracked 문서/manifest 15개; product code/API/DB/data/test/container mutation 0. |

## 3. 시작 전 상태

- Git: clean branch `codex/db-001-layered-enforcement`, base `92ff25d`.
- Tasks 1/2/2A/2B: 구현·독립 review 완료, patched suite 최대 18/18와 stock 7/7 PASS.
- Task 3: runtime manifest/final binary 없음, containers all/project 0/0, DB mutation 0.
- source A legacy tree: `.git` 없음, extended-length read-only 열거 3,035 files, maximum absolute file
  path 299. source/compiler exact diagnostic build는 exit 0이지만 runtime authority가 아니다.
- current exact worktree root length 98, legacy checkout root 164, proposed `.tools/s/a` root 109,
  longest pinned relative path 134, projected maximum 244.
- A-025/Q-TOOL-001은 인간 결정 대기였고 미응답 기본값은 구현 중단이었다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| A-025/Q-TOOL-001 | A/Resolved | short root, native delete, Docker/WSL build 중 선택 | 사용자 A; D-032/ADR-0014 | Task 2C와 Task 3 순서 |
| Path cap | D/Internal | PS5.1 deletion에 적용할 conservative absolute path cap | 248; current 244, 4자 여유 | source manifest·bootstrap·tests |
| Legacy partial tree | Security/hygiene | 기존 299자 ignored artifact 처리 | 자동 삭제·reuse 금지, 별도 human-approved cleanup 전 격리 | disk space·handoff |
| A-021/Q-SEC-003 | B/Open | public privileged-function hardening | 기존 default B 유지 | public release만 차단 |

현재 local/private Task 2C 전에 남은 A/Blocker는 없다. 다만 사용자 지침에 따라 수정 실행계획의
명시적 승인 전 구현을 재개하지 않는다.

## 5. 설계 결정과 대안

### 선택

- checkout A/B는 정확히 `.tools/s/a`, `.tools/s/b`다.
- source manifest는 tool-root-relative `s/a`, `s/b`, pinned maximum relative file path 134,
  maximum absolute file path 248을 exact schema로 고정한다.
- bootstrap은 cleanup·directory creation·Go archive download/extraction·network fetch 전에 두 projected maximum을
  계산하고 248 초과 시 stable invalid failure로 중단한다.
- 기존 `Resolve-SafeChildPath`, reparse guard, `Remove-Item -Recurse -Force`, local
  `core.autocrlf=false`/`core.longpaths=true`를 유지한다.
- legacy `.tools/supabase-source/...`는 checkout/build/delete input이 아니다. 기존 archive override
  deny boundary는 유지해 그 tree의 파일이 input으로 들어오지 못하게 한다.

### 이유

현재 exact tree는 299자에서 244자로 줄어 보수적 248자 cap 안에 들어온다. 새 production
dependency·global setting·native destructive helper·container image가 필요 없고 ADR-0013의 공급망과
rollback을 유지한다.

### 고려했지만 선택하지 않은 대안

- Win32 extended-length delete: 기존 tree 정리가 가능하지만 destructive native/reparse/readonly/
  partial-failure 표면이 커 사용자가 선택하지 않았다.
- Docker/WSL build: Windows path 문제를 피하지만 image/digest/mount/output permission 공급망과
  추가 다운로드·환경 편차가 커 사용자가 선택하지 않았다.
- guard 완화, global Git, sparse/path exclusion: exact source와 fail-closed 경계를 약화해 제외했다.

## 6. 구현 상세

이번 요청에서는 제품/tooling 코드를 구현하지 않았다. 다음 문서 계약만 갱신했다.

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `docs/decisions/DECISION_LOG.md` | D-032 추가 | 인간 결정을 append-only 기록 |
| `docs/adr/0014-short-windows-patched-cli-checkout-roots.md` | workspace amendment ADR | architecture tradeoff·rollback·gate 기록 |
| `docs/adr/0013-project-local-patched-supabase-cli.md` | ADR-0014 amendment 연결 | 원 공급망 결정과 새 workspace 경계 연결 |
| `docs/adr/README.md` | ADR-0014 index 추가 | 신규 개발자 발견성 |
| `docs/11_AMBIGUITY_REGISTER.md` | A-025 resolved, Q-TOOL-001 solved 이동 | blocker 상태 정합성 |
| `docs/source-of-truth/TEAM_DECISIONS.md` | D-032 운영 경계 반영 | 최종 팀 기준 동기화 |
| `docs/source-of-truth/RFP_MATRIX.md` | SER-001 local loopback/tooling trace 보강 | source-of-truth 변경 추적 |
| `TASKS.md` | DB-001을 plan-approval 대기 상태로 변경 | 구현 재개 순서 명확화 |
| Q-SEC-006 spec/plan | short roots, path budget, Task 2C TDD/review 추가 | zero-context 실행 가능 계획 |
| discovery/version/note/index | 결정 증거·버전·handoff | 문서 완료 기준 |

### 데이터 흐름/상태 변화

데이터·DB·runtime 상태 변화는 없다. 향후 Task 2C에서 source manifest build-input hash는 바뀌지만
runtime manifest가 아직 없으므로 compatibility migration은 없다.

### 오류·빈 상태·롤백

path budget 초과는 checkout mutation 전
`[FAIL] step=VALIDATE-PATCHED-SUPABASE-CHECKOUT-WORKSPACE reason=invalid code=2`로 중단하도록 계획했다.
legacy tree는 empty-state cleanup 대상이 아니다. 계획이 승인되지 않으면 현재 fail-closed DB-001을
그대로 유지한다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product/Application/Web/API/shared | 기존 manifest 값 | 동일 | 사용자 동작·공개 계약 변화 없음 |
| DB schema | 0.2.0-draft | 0.2.0-draft | DB/runtime 미실행 |
| Official/Mock data | 0 / 0 | 0 / 0 | 데이터 작업 아님 |
| Prompt/Test suite | 0.0.2 / 0.4.2 | 동일 | 테스트 계획만 변경, suite 미실행·미승격 |
| Documentation | 2.3.22 | 2.3.23 | D-032/ADR-0014/spec/plan/trace 기록 |

## 8. 명령과 테스트 증거

| 명령/검증 | 실제 결과 | 시간/개수 | 증거 |
|---|---|---|---|
| `git status --short --branch` | 시작 시 clean, branch exact | 1 branch | terminal evidence |
| `git log -8 --oneline --decorate` | HEAD `92ff25d`; Tasks 2A/2B commits 확인 | 8 commits | terminal evidence |
| `rg`로 spec/ADR/plan/bootstrap/test path 검색 | legacy production destinations 2곳, current Task 2B/3 경계 확인 | tracked files | plan investigation |
| PowerShell path-length 산출 | root 98, old root 164, new root 109, relative 134, old 299, new 244 | 6 values | read-only calculation |
| `git status --short -- contracts database` | 변경 0 | 31 active contract/database files | scope check |
| `git diff --check` + changed-scope/new-file whitespace | exit 0; docs/version only 15 files, untracked new files 2 | 15/2 | final local validation |
| `apps/api/.venv/Scripts/python.exe -B scripts/validate_codex_package.py` | exit 0, 12 required files, manifest valid | 12 | package validator |
| Python JSON parse + docs/version token check | exit 0, docs 2.3.23, DB 0.2.0-draft | 2 axes | `versions/manifest.json`, version doc |
| `powershell.exe ... scripts/check_secret_patterns.ps1` | exit 0, secret candidate 0 | repository scan | secret gate |
| Task 2C order/token/placeholder self-review | exit 0, Task 2C heading precedes Task 3 by token order; required 23/23·security·staging tokens present | 1 plan block | plan self-review |
| changed Markdown relative-link scan | exit 0, broken 0 | 14 Markdown files | link gate |
| D-032/ADR-0014/A-025 status scan | exit 0, A/Blocker 0, A-025 Resolved | 9 authority/status files | decision sync |
| exact path projection command | exit 0, relative 134, A/B 244, short roots absent | 5 values | read-only workspace evidence |
| readable sequential decision-plan gates | diff/scope/package/manifest/secret/plan/status/link/note/projection 전 항목 exit 0 | 8 gates | final terminal evidence |

검증 meta-command 작성 과정에서 `Select-String` positional-argument 오류와 압축 PowerShell 문의
공백/흐름 오류가 발생해 일부 검사 자체가 실패했으며, 저장소 파일 문제는 아니었다. 모두
명시적 인자와 읽기 쉬운 다중 행 순차 명령으로 재작성했다. 첫 재작성에서도 version manifest의
중첩 `versions` 구조, 계획의 `## Task` heading, 구현 노트의 실제 인간/AI 구분 heading을 평면 필드나
다른 제목으로 가정한 validator 오류가 있었고, 파일의 실제 구조를 읽은 뒤 조건을 바로잡아 최종
gate 전부 exit 0을 확인했다. 전체 changed-file trailing-space scan은 RFP_MATRIX의 기존 Markdown hard-break
두 줄을 잡아, tracked added-lines는 `git diff --check`, untracked new files는 별도 trailing scan으로
정확히 분리했고 최종 exit 0이었다.

첫 독립 plan review는 Critical 0 / Important 6 / Minor 3을 보고했다. pre-Go extraction 권위 정렬,
TDD 순서, A/B main-flow order, 248 accept/delete·249 reject, legacy deny-only AST, parser/staging/projection
명령과 기존 Git argv harness의 exact 3-parameter/budget-stub 계약을 수정했다. 독립 security review는
Critical 0 / Important 2 / Minor 0을 보고했고 short-root junction sentinel 및 direct/reparse
`.tools/s` archive-override tests를 Task 2C 구현 전 gate에 추가했다. 보정 후 최종 plan review와
security review는 각각 Critical 0 / Important 0 / Minor 0, Approved/commit-ready로 판정했다.

### 미실행 검증과 이유

- Task 2C tooling tests: 수정 계획 승인 전 제품/tooling 코드를 작성하지 않았으므로 미실행.
- `-BuildCandidate`, Go build, Docker/DB: 계획 승인 전 재개 금지.
- runtime manifest/install/full DB/root gate: Task 2C와 Task 3 이후 단계.
- public/remote/login/link/push/prune/delete: 승인 범위 밖.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문 원문·PII·DeepSeek payload·DSN·credential에 접근하거나 저장하지 않았다.
- Security: native delete와 guard 완화를 거부하고 pre-mutation path budget을 추가 계획했다. legacy
  partial tree 자동 삭제를 금지했다. Task 2C는 inclusive 248 cleanup, short-root junction sentinel,
  direct/reparse `.tools/s` archive override와 legacy deny-only 경계를 구현 전에 검증한다.
- Accessibility: UI 변화 없음.
- Performance/cost: 외부 호출·다운로드·build 0, 비용 0원. 향후 path checks는 소수의 문자열 길이와
  정수 비교라 영향이 무시 가능한 수준이다.

## 10. 데이터와 출처 영향

- 공식 데이터/mock/DB row 변화: 0.
- schema/lineage: 0.2.0-draft 유지, seed 0.
- 근거: actual extended-length 3,035/max299 evidence와 exact current path projection 244.
- verified date: 2026-07-18 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Q-TOOL-001=A 결정은 반영됐다. 새 D-032/ADR-0014가 권위다.
- 수정 계획의 새 실행 단위는 Task 2C다. 사용자 `계획 승인, 구현 시작` 또는 동등한 명시적 승인
  전에는 tooling implementation과 Task 3을 재개하지 않는다.
- legacy long-path tree는 남아 있으며 자동 삭제하지 않는다.
- runtime manifest/final CLI/actual loopback/full DB gate는 여전히 없다. DB-001은 완료가 아니다.
- A-021/Q-SEC-003은 별도 public-release blocker로 남는다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- manifest property order, helper 이름, AST harness fixture, staged-set assertion은 승인된 248자 contract
  안에서 AI가 자율 처리할 수 있다.
- source manifest schema_version 1은 published consumer가 없고 validator/test와 원자 변경되므로 유지한다.

## 13. 인수인계·재현·롤백

### 재현

1. D-032, ADR-0014, amended spec, plan Task 2C를 읽는다.
2. `git status --short --branch`가 clean이고 HEAD가 이 decision-plan commit인지 확인한다.
3. 사용자의 수정 계획 승인 뒤에만 Task 2C RED부터 시작한다.
4. Task 2C three-file commit과 독립 review가 끝난 뒤 Task 3 preflight를 수행한다.

### 롤백

- 이 요청의 문서 commit을 revert하면 A-025 decision-pending 상태로 돌아가며 구현은 계속 중단한다.
- 향후 Task 2C는 해당 three-file commit만 revert한다. stock CLI나 legacy checkout을 fallback으로 쓰지 않는다.
- DB/data rollback은 없다. legacy tree는 rollback에서도 recursive delete하지 않는다.

### 다음 개발자 시작점

사용자에게 amended plan 승인을 먼저 받는다. 승인 전 `scripts/supabase-cli.local-patch.source.json`,
`scripts/bootstrap_patched_supabase.ps1`, tests 또는 `.tools`를 수정하지 않는다.

## 14. 남은 위험·미해결 질문·다음 단계

- 수정 실행계획 사용자 승인 대기.
- Task 2C 구현 전에 inclusive 248-character cleanup이 실제 PS5.1에서 통과하는지 characterization
  gate가 필요하다. 실패하면 구현하지 않고 Q-TOOL-001을 다시 연다.
- repository root가 현재보다 5자 이상 길면 248 cap에 걸릴 수 있으며 이는 의도된 fail-closed다.
- legacy partial checkout disk hygiene는 별도 승인 전 보류.
- Task 3 runtime hash/install, Task 4 runner, full DB/root gate 미완료.
- A-021/Q-SEC-003 public-release B/High 미해결.

## 15. 자체 리뷰

- [x] 사용자 A 선택과 완료/미완료 범위 구분
- [x] 문서 검증과 independent review 결과 반영
- [x] source-of-truth/ADR/ambiguity/RFP/TASKS/spec/plan/version 동기화
- [x] 개인정보 원문·비밀·DB 접근 없음
- [x] 구현 노트 INDEX 갱신
