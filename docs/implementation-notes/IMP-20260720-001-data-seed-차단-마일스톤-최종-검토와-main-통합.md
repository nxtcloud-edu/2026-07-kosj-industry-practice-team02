# IMP-20260720-001 — DATA-SEED 차단 마일스톤 최종 검토와 main 통합

- Date/Time (KST): 2026-07-20T03:22:23+09:00
- Task ID: DATA-SEED-001
- Type: implementation-and-handoff
- Status: Done for reviewed filesystem milestone / Actual DB Blocked
- Author/Agent: root coordinator, DATA-SEED implementation agents, independent Sol reviewers
- Branch: `codex/data-seed-001-initial-release` → local `main`
- Base/Head: `eb846902828941aab8643381447636885f61222d` → `b3dd8e6c0a6356527c32679d5c5c7d79158c7516`
- Related plan/ADR/RFP: [실행계획](../superpowers/plans/2026-07-19-data-seed-immutable-release-and-local-verification.md), [ADR-0016](../adr/0016-immutable-filesystem-official-release-and-empty-local-seed.md), [RFP matrix](../source-of-truth/RFP_MATRIX.md), [blocked actual report](../test-reports/DATA-SEED-001-LOCAL-VERIFICATION.md), [lineage](../data-lineage/DATA-SEED-001-0.1.0-initial.1.md)

## 1. 사용자 요청과 완료 기준

### 요청

- 승인된 DATA-SEED 계획을 에이전트로 병렬 검토·구현하고, 큰 작업이 끝날 때까지 계속 진행한다.
- 인간 결정이 필요한 작업은 보류하되 그 밖의 구현·검증·문서·통합은 마무리한다.
- 코드/API/DB/데이터/보안/버전/인수인계 증거를 구현 노트에 남긴다.

### Acceptance Criteria

- immutable `.1` release와 local dispatcher를 정확히 검증한다.
- 실제 DB 결과를 과장하지 않고 실패 시 `official_data=0.0.0-not-populated`와 readiness 차단을 유지한다.
- 최종 독립 리뷰의 Critical/Important를 0으로 만들고 표준 root gate를 feature HEAD와 병합된 main에서 통과시킨다.
- local main에 fast-forward 통합하고 원격이 없는 상태에서 push를 시도하지 않는다.
- 남은 인간 결정과 cleanup 잔여를 명시한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 범위·데이터·보안 결정을 승인했고, root가 조정했으며 구현/문서/독립 리뷰 에이전트가 분리 수행했다. |
| When — 언제 | 2026-07-19~20 KST, DATA-SEED 계획 승인 뒤 main 통합까지 수행했다. |
| Where — 어디서 | local Windows 저장소, 소유 `.worktrees/data-seed-001-initial-release`, Docker Desktop local 환경에서 수행했다. |
| What — 무엇을 | 19 KB/3 기관/10 매핑 immutable filesystem release, 생성·검증·seed runner, atomic cleanup 회귀, lineage와 차단 상태를 구현·검토·통합했다. |
| Why — 왜 | 승인된 공식 근거만 시민 답변에 사용하고, DB 적재 계약이 불충분할 때 fail-closed 하기 위해서다. |
| How — 어떻게 | TDD RED→GREEN, implementer/reviewer 분리, exact hash·scope gate, no-Docker root gate, actual local DB 진단, ff-only merge로 수행했다. |
| How much — 어느 정도 | feature는 base보다 22 commits 앞서 main에 통합됐다. filesystem release는 19/3/10이고, 관련 no-DB suite 195/195와 최종 root gate 2회가 통과했다. 외부 API 호출과 추가 비용은 0이다. |

## 3. 시작 전 상태

- 관련 파일: `scripts/data_seed_release.py`, `scripts/promote_data_seed.py`, `scripts/verify_data_seed.ps1`, `supabase/seed.sql`, `data/official/`, DATA-SEED 계획·ADR·lineage·버전 manifest.
- 기존 동작: 승인 staging은 있었지만 immutable official release와 actual local seed 증거가 없고 `official_data`는 not-populated였다.
- 발견한 충돌/부채:
  - PostgreSQL 17의 grantor별 membership option effective union과 immutable `.1`의 single-row guard가 충돌했다.
  - post-publication cleanup 중 두 번째 파일 삭제 실패가 부분 release를 canonical 경로로 복원했다.
  - post-staging-validation mutation 회귀와 계획의 raw token signature가 빠져 있었다.
- Git 상태: feature base `eb84690`, main clean, remote 없음. 통합 전 feature와 main 모두 clean이었다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| A-030 / Q-SEED-002 | A/Blocker | `.1` guard와 authoritative migration/pgTAP union 의미 충돌 보정 방식 | 답 전에는 A/B 모두 구현하지 않는다. 추천 A는 새 immutable `.2`; B는 DB membership 정규화 migration이다. | DATA-SEED actual DB, READY-001, AI-001 |
| A-021 / Q-SEC-003 | B/High public blocker | 기존 privileged DB function hardening | local milestone과 분리해 계속 공개/remote 배포를 차단한다. | public deployment/admin/API credential |
| Cleanup residual | Internal/환경 | Git worktree remove가 Windows 잔여 파일 때문에 디렉터리를 끝까지 지우지 못했고 재귀 삭제는 실행 정책이 차단했다. | 우회 삭제하지 않고 Git 등록·feature branch만 제거했다. | 디스크 공간만 영향, main/build/runtime 영향 없음 |

## 5. 설계 결정과 대안

### 선택

- immutable `.1` bytes, migrations, pgTAP, role/grant를 변경하지 않고 actual DB를 Blocked로 유지했다.
- publisher cleanup은 owned quarantine이 검증된 뒤 실패하면 canonical로 되돌리지 않고 noncanonical residual을 남겨 안전한 재시도를 허용한다.
- 현재 milestone은 filesystem publication과 fail-closed tooling으로 main에 통합하고 DB 성공으로 표현하지 않는다.

### 이유

- immutable/create-once 계약과 승인 evidence를 지키면서 부분 release 노출을 방지한다.
- Q-SEED-002 답 없이 `.2`나 migration 중 하나를 임의 선택하면 공개 데이터·보안 계약을 바꾸게 된다.

### 고려했지만 선택하지 않은 대안

- 기존 `.1` in-place 수정: immutable 계약 위반이라 폐기했다.
- grant/migration 즉시 정규화: 인간 승인이 필요한 보안·DB 변경이라 보류했다.
- 부분 cleanup 실패 시 손상 quarantine 복원: canonical 신뢰성을 깨므로 회귀 테스트로 금지했다.
- 실행 정책을 우회한 worktree 재귀 삭제: 사용자 파일 오삭제 위험과 정책 위반 가능성 때문에 수행하지 않았다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `data/official/releases/0.1.0-initial.1/` | approval/release manifest, 19/3/10 JSON, seed/compensation SQL 게시 | 승인된 filesystem release 고정 |
| `scripts/data_seed_release.py`, `scripts/data_seed_sql.py` | canonical projection, hash, SQL 생성·검증 | 재현 가능한 release 생성 |
| `scripts/promote_data_seed.py` | prepare/verify/activate와 fail-closed quarantine cleanup | immutable publication과 안전한 실패 복구 |
| `scripts/tests/test_promote_data_seed.py` | partial-delete canonical 복원 RED→GREEN 및 safe retry 회귀 | 최종 리뷰 Important 제거 |
| `scripts/tests/test_data_seed_release.py` | real staging validator 직후 mutation snapshot 회귀 | M2-01 공백 제거 |
| `scripts/verify_data_seed.ps1`, `scripts/verify_data_seed_db.py` | exact local/runtime/DB boundary gate | secret·port·identity·transaction 검증 |
| `scripts/verify.ps1` | active release no-Docker root stages | 기본 회귀에서 filesystem release 검증 |
| DATA-SEED ADR/plan/lineage/test report/decision docs | filesystem 완료와 actual DB Blocked를 분리 | 상태 과장 방지와 인수인계 |
| `versions/manifest.json` | tests `0.8.2`, docs `2.7.5`; official data 유지 | 실제 검증 범위만 patch 승격 |

### 데이터 흐름/상태 변화

`APPROVED staging → immutable filesystem .1 → byte-active local dispatcher`까지만 완료됐다. `[db.seed].enabled=false`이며 actual DB는 seed write 전에 membership contract에서 중단됐다. 시민 조회용 ACTIVE 데이터, `/ready` 성공, AI 답변 근거 승격은 발생하지 않았다.

### 오류·빈 상태·롤백

- prepare 실패 후 canonical release는 없어야 하고 residual은 고유 noncanonical quarantine에만 남는다.
- actual DB 실패 시 container/54322 listener는 0으로 정리하고 volume 2/network 1은 보존했다.
- main 통합은 fast-forward라 commit history가 보존된다. 데이터 롤백은 `.1` 삭제/수정이 아니라 후속 승인 release 또는 별도 compensation 절차를 사용해야 한다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.2.0 | unchanged | 앱 코드 무변경 |
| Web | 0.2.0-static-chat-shell | unchanged | UI 무변경 |
| API | 2.0.1-draft | unchanged | 공개 계약 무변경 |
| DB schema | 0.3.0-local | unchanged | migration 무변경 |
| Official data | 0.0.0-not-populated | unchanged | actual DB import 미도달 |
| Mock data | 0.0.0-not-populated | unchanged | mock 미사용 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | unchanged | LLM 미호출 |
| Test suite | 0.8.0-web-browser-gate | 0.8.2-data-seed-filesystem-gate | filesystem/root/atomic cleanup 회귀 추가 |
| Docs | 2.7.3 | 2.7.5 | blocked lineage, 리뷰 remediation, handoff 동기화 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| partial cleanup focused test (fix 전) | RED, exit 1, `True is not false` | 1 failure / 0.579s | prior ignored final review, IMP-008 |
| partial cleanup focused test (fix 후) | PASS | 1/1 / 0.936s | IMP-008 |
| cleanup + post-validator focused rerun | PASS | 2/2 / 1.679s | current terminal evidence |
| DATA-SEED no-DB combined suites | PASS | 195/195 / 68.113s | IMP-008 |
| independent final rereview | Approved | Critical 0 / Important 0 / Minor 1 | `.superpowers/sdd/cleanup-final-rereview.md` in removed worktree; summary in this note |
| `scripts/verify.ps1` at feature `b3dd8e6` | PASS, exit 0 | all stages | current task terminal evidence |
| `git merge --ff-only codex/data-seed-001-initial-release` | PASS | 22 commits, 46 paths in aggregate | local main history |
| `scripts/verify.ps1` on merged main | PASS, exit 0 | all stages incl. root/data/web/API/contracts/secrets/package/diff | current task terminal evidence |
| worktree cleanup | Git registration removed; residual directory deletion blocked | 2 policy rejections after `git worktree remove` left a nonregistered residual | current task terminal evidence |

### 미실행 검증과 이유

- Q-SEED-002 답변 뒤의 actual DB full cycle은 미실행이다. 현재 `.1` guard가 authoritative membership union과 충돌해 seed write 전에 의도적으로 차단된다.
- remote CI/push/PR은 미실행이다. remote 저장소가 없다.
- 외부 LLM/DeepSeek API는 호출하지 않았다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 시민 질문 원문이나 실제 개인정보를 생성·저장·로그하지 않았다. 외부 API 호출 0이다.
- Security: secret scan과 bundle scan이 통과했다. DSN/credential은 출력하지 않았고 public deployment blocker A-021을 유지했다. cleanup은 partial canonical 노출을 막는다.
- Accessibility: UI 변경이 없고 기존 Web lint/type/test/build regression이 통과했다.
- Performance/cost: 19/3/10 local 규모, 신규 production dependency 0, 외부 비용 0원. root gate 시간 외 런타임 성능 변화는 없다.

## 10. 데이터와 출처 영향

- 공식 데이터: PM 승인 evidence 기반 19 KB/3 official offices/10 mappings가 immutable filesystem `.1`에 있다. DB에는 적재되지 않았다.
- mock/AI 생성: mock 데이터와 AI 생성 공식 사실을 섞지 않았다. LLM 호출 0이다.
- schema/lineage: release schema 4개와 DATA-SEED lineage를 추가했다. DB schema/migration은 불변이다.
- verified date: release 고정 시각 `2026-07-19T09:20:31+09:00`; 구현·검증 2026-07-20 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- `Q-SEED-002` 답이 필요하다. 추천 A는 authoritative migration/pgTAP union을 유지하고 새 immutable `0.1.0-initial.2`를 별도 승인해 전체 actual cycle을 재실행하는 것이다.
- 답 전에는 DATA-SEED actual DB, READY-001, AI-001을 완료로 간주하면 안 된다.
- `Q-SEC-003`은 별도 공개 배포 blocker다. local 완료를 public readiness로 해석하면 안 된다.
- `.worktrees/data-seed-001-initial-release`의 Git 등록과 branch는 제거됐지만 잔여 디렉터리는 실행 정책 때문에 남았다. main과 런타임에는 영향이 없으며 필요 시 사용자가 파일 탐색기에서 해당 정확한 잔여 폴더만 삭제할 수 있다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- trusted quarantine 이후의 cleanup failure branch에서는 canonical restore를 호출하지 않는다.
- 최초 directory identity mismatch만 concurrent foreign replacement 보호를 위해 restore한다.
- snapshot 회귀는 real `_validate_current_staging` 반환 직후 source를 mutate하고 captured bytes가 불변임을 검증한다.
- root runner가 release verify와 local dispatcher verify를 직접 호출해 Docker 없이 stale publication을 잡는다.

## 13. 인수인계·재현·롤백

### 재현

1. 저장소 root에서 `powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\verify.ps1`을 실행한다.
2. `python -B scripts/promote_data_seed.py verify-release --repository-root . --release-version 0.1.0-initial.1`로 `issues=0`을 확인한다.
3. `python -B scripts/promote_data_seed.py verify-local-seed --repository-root . --release-version 0.1.0-initial.1`로 dispatcher active를 확인한다.
4. actual DB 재실행은 Q-SEED-002 결정과 successor plan 승인 뒤에만 수행한다.

### 롤백

- main은 ff-only로 통합됐다. 코드 회귀는 관련 commit을 새 revert commit으로 되돌리고 root gate를 재실행한다. `git reset --hard`는 사용하지 않는다.
- immutable `.1`은 in-place 수정·삭제하지 않는다. 데이터 보정은 새 release와 승인 evidence로 수행한다.
- DB write가 없었으므로 이번 통합에 대한 DB data rollback은 없다.

### 다음 개발자 시작점

- [A-030/Q-SEED-002](../11_AMBIGUITY_REGISTER.md)와 [blocked actual report](../test-reports/DATA-SEED-001-LOCAL-VERIFICATION.md)를 먼저 읽는다.
- 사용자가 A를 선택하면 `.2` successor spec/approval/manifest/test를 먼저 만들고, B를 선택하면 migration·pgTAP·rollback·security review를 먼저 계획한다.
- 어느 쪽이든 membership compatibility precheck를 RED부터 추가하고 actual cycle 전체를 처음부터 재실행한다.

## 14. 남은 위험·미해결 질문·다음 단계

- Blocker: A-030/Q-SEED-002.
- Public blocker: A-021/Q-SEC-003.
- Minor: Q-SEED-002 결정 전에는 generator와 migration/pgTAP 간 membership compatibility precheck의 정답을 고정할 수 없다.
- Operational residue: nonregistered worktree directory가 남아 디스크 공간을 사용한다.
- 다음 단계: 사용자의 Q-SEED-002 답을 decision log/ADR/plan에 반영한 뒤 승인된 방안만 구현한다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
