# IMP-20260718-004 — patched Supabase CLI와 DB-001 local baseline 완료

- Date/Time (KST): 2026-07-18T07:45:10+09:00
- Task ID: DB-001-T10-QSEC006
- Type: security/implementation/verification
- Status: Done
- Author/Agent: Codex root coordinator와 task별 구현·검증·문서 subagent
- Branch: codex/db-001-layered-enforcement
- Base commit: f8d4f9b (`f8d4f9bc404d013aec62e355f05b440aa053323c` evidence code HEAD)
- Remediated final-code evidence HEAD: 73f300b (`73f300b9a90ad386ece555db3dc14fe1d18e6ba6`)
- Related plan/ADR/RFP: DB-001 parent plan, Q-SEC-006 patched CLI plan, ADR-0008/0011/0012/0013/0014,
  D-018/D-025/D-031/D-032, RFP SER-001/SER-002/SER-003, TASK DB-001

## 1. 사용자 요청과 완료 기준

### 요청

사용자는 Q-SEC-006=A, Q-TOOL-001=A와 `수정 계획 승인, 구현 시작`으로 수정 실행계획을 승인하고,
병렬 agent를 활용해 DB-001의 남은 안전한 local/private 구현과 검증을 계속하도록 요청했다.

### Acceptance Criteria

- official Supabase CLI v2.109.1 source/tag/commit, Go 1.25.11, two-file patch와 runtime hash가 고정된다.
- 두 독립 clean build의 SHA-256이 같고 runner는 patched runtime만 사용하며 stock/PATH fallback이 없다.
- actual DB publish는 exact one `127.0.0.1:54322 -> 5432/tcp`이고 wildcard/null/multiple이 0이다.
- fresh pgTAP 282, backend integration 8/8, 6단계 compensation/absence/reset/replay가 통과한다.
- final project/all container count는 0/0이고 volume delete/prune은 0회다.
- 제품/API/migration/schema/data/prompt/dependency/readiness/privacy 동작은 바뀌지 않는다.
- DB-001은 local/private로만 Done이며 A-021/Q-SEC-003과 public/remote/`00700` 차단은 유지한다.
- 버전·상태·보고서·handoff·구현 노트를 동기화하고 final verification을 통과한 뒤 commit한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 Q-SEC-006/Q-TOOL-001과 수정 계획을 승인했고, Codex coordinator가 task별 구현·독립 review·actual gate·closeout을 조정했다. AI/Data·Backend 작성과 PM 공식 데이터 승인은 별도 책임으로 남는다. |
| When — 언제 | 2026-07-17~18 KST. Actual DB/root/static evidence와 remediation final-code DB evidence를 수집했고 final specification/quality docs reviews도 0/0/0으로 완료했다. Final verification은 pending이다. |
| Where — 어디서 | `codex/db-001-layered-enforcement` linked worktree, Windows PowerShell 5.1, Docker Desktop 4.62.0/Engine 29.2.1, local PostgreSQL 17.6, ignored `.tools/` runtime. |
| What — 무엇을 | exact-source patched Supabase CLI 공급망, short-root path budget, reproducible runtime pin, patched-only DB runner, fresh disposable DB gate와 local baseline status/version/handoff를 구현·검증했다. |
| Why — 왜 | stock CLI의 HostIP 생략이 IPv6 wildcard `::`까지 게시해 local DB 안전 gate를 막았고, gate 완화 없이 DB-001과 다음 데이터 수직 흐름을 열어야 했기 때문이다. |
| How — 어떻게 | test-first two-file patch, manifest property closure, two independent builds, SHA-256 pin, pre-mutation path validation, actual Docker inspect before reset, 6-stage replay와 layered root/static gates를 사용했다. |
| How much — 어느 정도 | patch 2 upstream files/1,824 bytes, runtime 103,027,200 bytes, 6 forward+6 compensation, 6 pgTAP files/282 assertions, integration 8/8, final runner 50/50·patched 24/24, actual binding 1개, final container 0/0, 공식/mock seed 0, 외부 인프라 비용 0원. |

## 3. 시작 전 상태

- 관련 파일: patched CLI source/runtime manifests와 bootstrap/test, DB runner/test, six migrations와
  compensations, DB report/handoff, active status/version/security/ops 문서.
- 기존 동작: Q-SEC-004/005 Docker 설정 뒤에도 stock HostIP-omitted publish가
  `127.0.0.1`+`::`였고 DB runner는 reset 전에 fail closed했다. DB schema manifest는
  `0.2.0-draft`, DB-001은 Blocked였다.
- 발견한 충돌/부채: PowerShell 5.1 장경로 cleanup 실패, legacy partial checkout 격리 필요,
  A-021의 privileged function 21개 public hardening, official seed 0, off-device backup/remote CI 없음.
- Git 상태: Task 5 Step 1 시작 시 tracked/untracked 0, evidence code HEAD
  `f8d4f9bc404d013aec62e355f05b440aa053323c`, container all/project 0/0이었다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-SEC-006 / A-024 | A/Resolved | explicit IPv4 loopback patched CLI 여부 | A / D-031 / ADR-0013; local에서 구현·actual 검증 | tooling/runtime/DB gate |
| Q-TOOL-001 / A-025 | A/Resolved | Windows checkout 장경로 대응 | A / D-032 / ADR-0014; `.tools/s/a`,`s/b`와 248 cap | build workspace/cleanup |
| Q-SEC-003 / A-021 | B/Open | privileged function 21개 public hardening | 무응답 기본 B; local만 허용, `00700` 금지 | remote/public/admin/API/backend credential 차단 |
| DATA-001 | Human pending | 공식 KB 20·기관 3+·매핑 10~12 승인 | AI/Data·Backend 작성, PM 전수 승인, 목표 2026-07-20 | seed/readiness/chat 흐름 |
| Final docs reviews | Resolved | final cumulative specification과 quality documentation re-review 모두 APPROVED 0/0/0 | reviews complete | closeout commit에 포함 |

## 5. 설계 결정과 대안

### 선택

- official `v2.109.1`의 `apps/cli-go`만 직접 build하고 local DB start의 한 `HostIP` 필드만 수정했다.
- source manifest와 runtime manifest를 분리하고 두 independent build hash가 같을 때만 runtime을 pin했다.
- checkout root를 `.tools/s/a`,`s/b`로 줄이고 projected absolute path를 tool/network/mutation 전에 검사했다.
- DB runner는 patched binary와 `-VerifyOnly`만 사용하며 actual Docker state를 reset 전에 검사한다.

### 이유

exact gate를 약화하지 않고 변경 범위를 local tooling 한 곳으로 제한하며, 재현 가능한 입력·출력 hash와
stock rollback reference를 동시에 보존하기 위해서다.

### 고려했지만 선택하지 않은 대안

- Docker 전역 binding 정책 추가 변경: Q-SEC-004/005에서 IPv6 wildcard가 남아 불충분했다.
- stock/PATH CLI fallback: 동일 취약 동작으로 되돌아가므로 금지했다.
- WSL/container build, native delete, global Git 설정: 새 환경·삭제 표면을 늘리므로 도입하지 않았다.
- `db diff` shadow DB patch: DB-001 runner 호출 경로가 아니어서 승인 범위에서 제외했다.
- legacy long-root 자동 삭제: 안전 경계와 인간 승인이 없어 quarantine 상태로 유지했다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| patched CLI patch/source/runtime/bootstrap/tests | exact upstream·Go·patch·workspace·build·runtime hash, PS5.1 fail-closed workflow와 TDD | 재현 가능한 loopback-only CLI authority |
| `scripts/verify_database.ps1`와 tooling tests | patched runtime만 선택하고 verify→network→start→actual inspect→reset 순서 강제 | stock/PATH escape와 unsafe mutation 차단 |
| `73f300b` runner remediation | child를 process-tree 단위 timeout/종료·dispose하고 descendant cleanup mutation tests 추가 | timeout 뒤 orphan descendant와 local runtime 잔존 차단 |
| existing DB migrations/rollbacks/tests | 변경 없음; 6/6 lineage와 282/8/8을 fresh replay | 실행 권위 보존과 regression 증명 |
| `versions/manifest.json`, `TASKS.md` | repo 1.5, DB 0.3-local, tests 0.5, docs 2.4; DB-001 local Done과 satisfied dependency만 제거 | evidence 뒤 local milestone 승격 |
| active architecture/security/test/ops/decision docs | exact hashes/binding/counts/cleanup와 local/public 경계 동기화 | 상충하는 blocked/candidate 설명 제거 |
| DB report/handoff/spec/plans | fresh·post-remediation·final verification evidence, 재현·rollback·다음 DATA flow와 closeout 완료 기록 | 인수인계와 계획 사실성 |

### 데이터 흐름/상태 변화

질문·답변·PII 데이터는 이 작업 흐름에 들어오지 않았다. DB gate는 synthetic/disposable data만 사용해
reset 1 → pgTAP → newest-first compensation 6 → absence → reset/replay 2 → pgTAP → integration을
실행하고 synthetic cleanup 뒤 종료했다. 공식/mock persistent row는 0이며 `/ready=503`이다.

### 오류·빈 상태·롤백

manifest/hash/path/binding 중 하나라도 다르면 DB reset·credential·SQL 전에 stable failure로 중단한다.
unsafe runtime은 runner-owned cleanup으로 container 0을 확인한다. binary가 없으면 tracked manifests와
bootstrap `-Install`로 재현한다. official seed 없음과 readiness 503은 오류가 아니라 현재 정상 빈 상태다.

## 7. 버전 전후

### 생성 시 매니페스트

- product_spec: 2.2.0
- repo_guidance: 1.5.0
- application: 0.1.0
- web: 0.1.0
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.3.0-local
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 0.5.0-db-baseline
- documentation: 2.4.0

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.0 | 2.2.0 | 제품 범위 변화 없음 |
| Repo guidance | 1.4.0 | 1.5.0 | patched tooling/runner authority |
| Application | 0.1.0 | 0.1.0 | 앱 변화 없음 |
| Web | 0.1.0 | 0.1.0 | Web 변화 없음 |
| API | 2.0.1-draft | 2.0.1-draft | 공개 wire 변화 없음 |
| Shared contracts | 0.2.1 | 0.2.1 | 계약 변화 없음 |
| DB schema | 0.2.0-draft | 0.3.0-local | 기존 six-migration baseline의 fresh local 검증 |
| Official data | 0.0.0-not-populated | 동일 | 공식 seed 0 |
| Mock data | 0.0.0-not-populated | 동일 | mock seed 0 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM/prompt 변화 없음 |
| Test suite | 0.4.2-readiness-contract | 0.5.0-db-baseline | patched/runner regression과 fresh actual DB baseline |
| Docs | 2.3.23 | 2.4.0 | local baseline/report/handoff milestone |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| Git/Docker/containers/`bootstrap_patched_supabase.ps1 -VerifyOnly` preflight | PASS; clean, running, Engine 29.2.1, 0/0, verify exit 0 | complete 16.105s; verify 10.033s | `.superpowers/sdd/qsec006-task-5-db-evidence.md` |
| `scripts/verify_database.ps1` | PASS, 15 stable phases exit 0 | 90.508s | DB evidence/report |
| 두 `docker inspect` 구조 검사 | exact one `127.0.0.1:54322`; wildcard/null/multiple/extra 0 | binding 1개 | DB evidence/report |
| patched `stop`와 두 container query | PASS, final project/all 0/0, volume delete/prune 0 | stop 3.211s; capture/stop 7.206s | DB evidence/report |
| `scripts/verify.ps1` | PASS, exit 0 | 956.658s | DB evidence/report |
| package validator | PASS, required 12 files | 0.656s | DB evidence/report |
| repository secret scan | PASS, finding/value output 0 | 7.708s | DB evidence/report |
| combined patched+runner/stock unittest | 73/73 PASS (`24 + 49`) | 657.506s unittest; 658.421s wrapper | DB evidence/report |
| protected-path diff | PASS, product/API/schema/data/dependency diff 0 | 0.200s | DB evidence/report |
| `git diff --check` | PASS | 0.128s | DB evidence/report |
| candidate/reproducible build | two clean build hashes matched runtime SHA-256 | runtime 103,027,200 bytes | Task 3 report/runtime manifest |
| `73f300b` focused descendant cleanup regression | PASS | 1/1, 15.700s | remediation review evidence |
| `73f300b` full runner tooling | PASS | 50/50, 318.556s | remediation review evidence |
| `73f300b` patched tooling | PASS | 24/24, 262.368s | remediation review evidence |
| `73f300b` AST/parser, secret, protected boundary | PASS; AST error 0, secret finding 0, protected diff 0 | focused static gates | remediation review evidence |
| `73f300b` independent specification/quality review | APPROVED | Critical/Important/Minor 0/0/0 | remediation review package |
| final-code patched verify/preflight | PASS, Engine 29.2.1, container 0/0 | verify 7.728s; complete 13.894s | Task 5 DB evidence post-remediation section |
| final-code `scripts/verify_database.ps1` | PASS, all 15 stable phases | 102.746s | Task 5 DB evidence post-remediation section |
| final-code inspect/stop/cleanup | exact one `127.0.0.1:54322`, stop 0, final 0/0, volume/prune 0 | stop 2.512s; capture/stop 5.859s | Task 5 DB evidence post-remediation section |
| post-remediation evidence report snapshot | 196 lines, SHA-256 exact | `89D00A9BDB3E6A01961F66977A29A811C964ECAF3623D65FD51D0EC6054713F2` | historical pre-final-verification snapshot |
| final cumulative specification review | APPROVED | Critical/Important/Minor 0/0/0 | `.superpowers/sdd/qsec006-final-spec-review.md` |
| final quality documentation re-review | APPROVED | Critical/Important/Minor 0/0/0 | `.superpowers/sdd/qsec006-final-quality-rereview-docs.md` |
| final patched `-VerifyOnly` | PASS, exit 0 | 8.528s | Task 5 DB evidence final verification section |
| final `scripts/verify.ps1` | PASS, exit 0; all root/Web/API/contract phases | 866.976s | Task 5 DB evidence final verification section |
| final package / secret | PASS; package 12, secret finding 0 | 1.075s / 5.652s | Task 5 DB evidence final verification section |
| final combined tooling | 74/74 PASS (`24 + 50`) | 602.877s unittest; 603.617s wrapper | Task 5 DB evidence final verification section |
| final JSON / diff / protected+scripts | PASS, exit 0; protected+scripts diff 0 | 0.557s / 0.347s | Task 5 DB evidence final verification section |
| final dirty set / containers | exact authorized 21 modified + 1 note; project/all 0/0 | final check | Task 5 DB evidence final verification section |
| final evidence report authority | 234 lines, SHA-256 exact | `9EE2AC549A983921CC928892D803E46F713E311103928A25B5E47A901764DBFB` | `.superpowers/sdd/qsec006-task-5-db-evidence.md` |
| closeout JSON/exact manifest/KST assertion | PASS, `MANIFEST-EXACT PASS` | 12 exact version keys | this note와 closeout report |
| closeout package/secret/protected/authority-doc/diff quick gates | PASS; package 12, secret finding 0, protected/forbidden diff 0 | docs 편집 뒤 fresh quick run | `.superpowers/sdd/qsec006-task-5-closeout-report.md` |

### 미실행 검증과 이유

- 요구된 final verification과 reviews는 모두 실행·통과했고 이 note는 closeout commit에 포함됐다.
  자기 자신을 포함하는 commit SHA는 note 본문에 고정하지 않고 Git 이력을 권위로 사용한다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문 원문·답변·transcript·token·PII·credential·DSN을 저장하거나 문서에 복사하지 않았다.
  ignored `.env`의 비대상 bytes와 환경 복원 경계를 유지했다.
- Security: exact source/patch/runtime hash, short-root/reparse/path containment, patched-only runner,
  actual pre-reset inspect와 cleanup을 추가했다. A-021과 public credential 차단은 유지한다.
- Accessibility: 사용자 화면/DOM/CSS 변화가 없어 직접 영향 없음.
- Performance/cost: root/tooling build 검증은 길지만 local reproducibility를 우선한다. 외부 인프라 비용과
  새 production dependency는 0이다. build 재현은 네트워크·CPU 시간을 사용한다.

## 10. 데이터와 출처 영향

- 공식 데이터: 작성·승인·seed 모두 0; DATA-001 PM 전수 승인 전 생성하지 않았다.
- mock/AI 생성: persistent mock seed 0; DB gate는 synthetic test fixture만 사용하고 cleanup했다.
- schema/lineage: `00100`~`00600` forward와 6개 compensation bytes는 변경하지 않았다.
  executable authority는 `supabase/migrations/`, projection은 `database/schema-v1.draft.sql`이다.
- verified date: runtime/DB/root evidence 2026-07-18 KST. 공식 민원 데이터 확인일과는 무관하다.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- `0.3.0-local`은 disposable local/private 기준선이며 production/public 인증이 아니다.
- A-021/Q-SEC-003 기본값 B 때문에 remote/public deployment, public admin/API, public backend DB
  credential과 `00700`은 계속 금지된다.
- 공식 KB/기관/매핑은 PM 승인 전 0이고 `/ready=503`이 정상이다. 다음 인간 책임은 DATA-001 전수 승인이다.
- 원격 Git/CI, off-device backup, production TLS/rate limit/admin 보호가 없어 단일 PC 손실·공개 운영 위험이 남는다.
- patched executable은 ignored local artifact다. tracked manifests/bootstrap으로 다른 PC에서 재현해야 한다.
- runner descendant-cleanup finding은 `73f300b`와 독립 review, final-code DB gate로 해결됐다.
- final verification은 통과했고 note는 Done이며 closeout commit에 포함됐다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- PowerShell helper 분리, child event ordering, PS5.1 parser/timeout/process disposal, fixture JSONL capture.
- exact AST guard로 legacy checkout alias/descendant를 deny-only로 제한하고 `.tools/s` archive override를 거부한다.
- two-build candidate output과 atomic runtime install, stable `[PASS]/[FAIL]` 출력, environment save/restore.
- 공개 계약을 바꾸지 않는 테스트 fixture·명명·문서 링크와 status dependency 정리.

## 13. 인수인계·재현·롤백

### 재현

1. Windows PowerShell 5.1과 Docker Desktop/Engine 28+를 준비하고 container 0을 확인한다.
2. binary가 없으면 `scripts/bootstrap_patched_supabase.ps1 -Install`, 항상 `-VerifyOnly`를 실행한다.
3. `scripts/verify_database.ps1`을 실행하고 exact loopback, pgTAP/replay/integration을 확인한다.
4. patched binary로 `stop`하고 project/all container 0/0을 확인한다. volume은 삭제하지 않는다.
5. root/package/secret/combined tooling/protected diff/json/diff gate를 실행한다.

### 롤백

- closeout docs/version이 사실과 다르면 closeout commit을 `git revert`해 DB-001과 manifest를 이전
  blocked 상태로 복원한다. hard reset은 사용하지 않는다.
- runner가 실패하면 runner-switch commit을 revert하고 stock CLI로 DB를 실행하지 않는다.
- 필요 시 runtime-pin commit을 revert하고 safe-child 검증 뒤 owned ignored patched output만 제거한다.
- disposable local schema 복구는 patched runner의 `db reset --local`; compensation은
  `00600→00500→00400→00300→00200→00100` 순서로 disposable local에만 적용한다.
- shared/remote DB, 실제 데이터, official seed, Docker volume, public deployment는 이 rollback 범위가 아니다.

### 다음 개발자 시작점

1. Git 이력에서 `docs(db): complete safe local baseline` closeout commit과 clean status를 확인한다.
2. DATA-001 PM 승인을 확인한 뒤 DATA-SEED-001을 시작하고, seed 이후 READY-001에서만 `/ready=200`을 다룬다.

## 14. 남은 위험·미해결 질문·다음 단계

- Runner cleanup remediation와 code review 0/0/0, final-code DB revalidation은 완료됐다.
- Final closeout specification/quality docs reviews와 전체 final verification은 완료됐다.
- closeout commit까지 완료됐다. 자기참조 SHA는 Git 이력을 권위로 둔다.
- A-021/Q-SEC-003 B/High public-release blocker와 privileged function 21개 hardening 미결정.
- official KB/office/mapping 0, `/ready=503`, chat/admin vertical slice 미구현.
- ignored runtime 재빌드 시간·네트워크 필요, remote Git/CI·off-device backup 없음.
- 다음 안전한 제품 단계: DATA-001 승인 → DATA-SEED-001 → READY-001.

## 15. 자체 리뷰

- [x] 요청/승인 범위와 actual evidence 반영
- [x] final 테스트/검증 — Step 8 전체 PASS, containers 0/0
- [x] source-of-truth/계약/버전 동기화 — 공개 계약은 변경 없음
- [x] 개인정보 원문·credential·DSN 노출 없음
- [x] 구현 노트 INDEX 갱신 — Done
