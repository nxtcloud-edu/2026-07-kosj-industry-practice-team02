# DB-001 Local Baseline Verification Report

- Date: 2026-07-18 KST
- Branch: `codex/db-001-layered-enforcement`
- Final-code evidence HEAD: `73f300b9a90ad386ece555db3dc14fe1d18e6ba6`
- Current semantic version: `database_schema=0.3.0-local`
- Scope: disposable local/private Supabase PostgreSQL baseline only
- Verdict: PASS — verified disposable local/private baseline; production/public readiness 아님

## 결론

DB-001의 executable baseline은 6개 forward migration, 6개 matching compensation,
7 enum, 8 table, forced RLS/capability boundary, 원자 후보 workflow, ACTIVE+OFFICIAL 시민 read,
30일 text-only purge와 lazy typed FastAPI repository를 재현했다. 공식/mock persistent seed는
0이며 `/health=200`, `/ready=503`이 정상이다.

기존 stock runtime의 wildcard host publish 때문에 한때 차단됐지만, D-031/D-032의 patched CLI는
DB start HostIP만 explicit `127.0.0.1`로 지정하고 source/runtime hash를 분리 고정한다. runner는
stock/PATH fallback 없이 이 artifact만 검증하며 actual binding을 reset/status/env 전에 검사한다.
2026-07-18 fresh run에서 두 Docker inspect view가 모두 exact one
`127.0.0.1:54322 -> 5432/tcp`였고 전체 DB gate가 exit 0으로 완료됐다.

이 보고서는 production readiness 또는 public release 승인이 아니다. A-021/Q-SEC-003은
미해결 B/High public-release blocker이며 무응답 기본값 B를 적용한다. `00600` validator 외
privileged function 21개의 search-path hardening 전에는 remote/public 배포, public admin/API,
public backend DB credential을 금지하고 `00700`을 만들지 않는다.

## 실행 환경

| 구성요소 | 실제 버전 |
|---|---|
| Supabase CLI | `2.109.1` |
| Docker Server | `29.2.1` |
| PostgreSQL | `17.6` |
| Python | `3.12.13` |
| pytest / psycopg | `9.1.1` / `3.3.4` |

credential·DSN은 runner process memory/environment에서 사용하지만 값과 Supabase status 원문을
표시·로그·별도 영구 복사하지 않았다. Provisioning은 원자 `DATABASE_URL` 교체를 위해 `.env`
전체 bytes를 읽지만 provider/non-target 값을 파싱하지 않고 byte-identical하게 보존한다.

## Patched CLI 공급망

| 잠금 대상 | 실제 값 |
|---|---|
| source manifest SHA-256 | `c293e5ac32bae030eadf383d8d9511dc16eac834e51e996273ae8b7e39616657` |
| patch SHA-256 / bytes | `109c096480e8185d761e9ce8fba10e93efc55190c42eab978f769a6993833f7d` / 1,824 |
| runtime SHA-256 / bytes | `751068e73834c5da58ac7c5287a1d66a82ad356f508637b0478d6531cdb3941c` / 103,027,200 |
| upstream tag object / commit | `9d25ff8b5b0fba3c6f0ef000e7dd658c8d710c38` / `6d4c19870ed213ba7f682f117d0345c8a40bfa94` |
| Go archive SHA-256 | `b7401f1b41517428e537493316256fb7cf03c66a130a0103ab07f3a2152e2112` |
| runtime path | `.tools/supabase/v2.109.1-sejong-loopback/supabase.exe` |

## Forward migration SHA-256

| 파일 | SHA-256 |
|---|---|
| `20260716000100_private_schema.sql` | `c8005924b0c14c4890b24268ce5769c5b643d6c2f52cdbd7aa0894db204e0240` |
| `20260716000200_invariants_and_lineage.sql` | `07a653e32ea2a3e72d9ef098fd612efe9a3523033f59104cba3c1469dfa1e1e2` |
| `20260716000300_capabilities_and_functions.sql` | `ebb439a3261bd8fc36b1c807c9ce1d5ed0aac8f868ca9f9f9afc07cfcbd407c1` |
| `20260716000400_candidate_workflow.sql` | `284792c592ac9ecaeaeeb5358585f410442e7832eef7c2f1f483a28e58b8c7a5` |
| `20260716000500_indexes_and_read_interfaces.sql` | `f8463ac9b0ae8a418cf47d915c3d77a97a7ff8f183b66e0d5ebe18df140adb2f` |
| `20260717000600_deferred_active_question_trigger_security.sql` | `5da7dc579653717e99fcfb59d73ba68107e1cd54ab1428680894283ff855a807` |

## Compensation SHA-256

| 파일 | SHA-256 |
|---|---|
| `20260716000100_private_schema.rollback.sql` | `96f3f6a1502dbca3214d21cae654ed79ebe7f4536346c9009e7981dabe58e74d` |
| `20260716000200_invariants_and_lineage.rollback.sql` | `63635d89eb3f7056e35644fa9e02e0232033c21cb2745d481732b53ef7f48cdc` |
| `20260716000300_capabilities_and_functions.rollback.sql` | `2a75dcff963d3cfa2649d55a96a062bdde01062fd5e17b7faea39e5e7afbdd7e` |
| `20260716000400_candidate_workflow.rollback.sql` | `d9c2be6fddb3b4e635c5fa8f46e9d5ee455421395fea5fcb7cae7108e4f4074f` |
| `20260716000500_indexes_and_read_interfaces.rollback.sql` | `44b38bc0d6cd53e211828db43723f320beb727b225ef42fdc870fe9624cd3e28` |
| `20260717000600_deferred_active_question_trigger_security.rollback.sql` | `727ba5e28660e6507b9a98af5d7fe1745f97f644039a9c948b30bcbfa6e6d2d4` |

## DB schema와 동작 증거

| 검증 | 실제 결과 |
|---|---|
| first reset + full pgTAP | `Files=6, Tests=282`, PASS |
| 006-only compensation posture | validator INVOKER/owner/proconfig/ACL/body/trigger/private privilege 전체 PASS |
| compensated prior baseline | `Files=5, Tests=274`, PASS |
| full compensation | `00600→00500→00400→00300→00200→00100`, PASS |
| absence proof | DB-001 schema/role/object 부재 PASS; Supabase-owned 객체 보존 |
| second reset/replay + pgTAP | `Files=6, Tests=282`, PASS |
| real backend integration | 8/8 PASS |
| no-URL integration collection | exact 8 skips, reason `local DB gate only` |
| synthetic cleanup | 8 table groups row total 0 |

Full runner는 두 번의 reset을 수행한다. 첫 reset 뒤 pgTAP, local login provisioning,
`00600`부터 `00100`까지 compensation과 absence proof를 실행하고, 두 번째 reset으로 6개
forward migration을 replay한 뒤 pgTAP과 backend integration을 다시 실행했다.

## 2026-07-18 fresh actual gate

| 검증 | 실제 결과 |
|---|---|
| preflight | Git clean, Desktop running, Engine 29.2.1, all/project container 0/0 |
| patched `-VerifyOnly` | exit 0, 10.033s |
| full `scripts/verify_database.ps1` | exit 0, 90.508s; 모든 15 stable phase PASS |
| actual binding | 두 inspect payload 모두 exact one `127.0.0.1:54322 -> 5432/tcp`; wildcard/null/multiple/extra 0 |
| pgTAP | reset 1과 reset/replay 2 모두 exit 0; current suite 6 files/282 assertions |
| compensation/replay | `00600→00500→00400→00300→00200→00100`, absence proof, reset/replay PASS |
| backend integration | current 8 definitions, fresh phase exit 0 (8/8) |
| stop/cleanup | patched stop exit 0, 3.211s; final project/all 0/0; volume delete/prune 0 |

## 상태·동시성·보관 증거

- 두 연결 사유 확인은 한 번만 `NEW→REASON_CONFIRMED`에 성공하고 event의 최초 자동 reason을
  보존하며 failure reason/eligibility와 metadata audit만 원자 변경했다.
- 후보 생성은 confirmed `INSUFFICIENT_GROUNDING + eligible`에서만 성공했다.
- 두 동시 승인은 ACTIVE OFFICIAL KB 1, 질문 예시 1, candidate link 1, approval audit 1만
  만들고 loser는 안정된 `P1003`으로 종료했다.
- 자기 승인, 잘못된 역할/상태, MOCK 활성화, base-table 직접 접근은 거부됐다.
- purge는 30일 직전 0, 정각/직후 대상만 NULL 파기하고 반복 실행 `1→0→0`으로 멱등이며
  event/candidate FK를 보존했다.
- OUT_OF_SCOPE text와 FOLLOWUP failed row, raw 질문/답변/transcript/token/IP/device column은 0이다.

## Fresh 비DB 검증

| 검증 | 실제 결과 |
|---|---|
| root/Web/API/contract gate | PASS, exit 0, 956.658s |
| package validator | PASS, exit 0; required 12 files, 0.656s |
| secret scan | PASS, finding 0, value output 0, 7.708s |
| patched + runner/stock tooling | 73/73 PASS (`24 + 49`), 657.506s unittest |
| protected product/contract/schema/data/dependency diff | PASS, exit 0 |
| `git diff --check` | PASS, whitespace error 0 |
| health/readiness | `/health=200`, `/ready=503` |

## Post-remediation final-code evidence

Runner child process tree timeout/cleanup을 `73f300b fix(db): bound database child process trees`에서
보정했다. 독립 specification/quality review는 Critical/Important/Minor `0/0/0`으로 APPROVED다.

| 검증 | 실제 결과 |
|---|---|
| focused descendant cleanup regression | 1/1 PASS, 15.700s |
| full runner tooling | 50/50 PASS, 318.556s |
| patched tooling | 24/24 PASS, 262.368s |
| parser/AST·secret·protected boundary | PASS; AST error 0, secret finding 0, protected diff 0 |
| patched verify/final-code preflight | PASS; verify 7.728s, complete 13.894s, Engine 29.2.1, container 0/0 |
| final-code DB runner | exit 0, all 15 stable phases PASS, 102.746s |
| final-code actual binding | 두 inspect view 모두 exact one `127.0.0.1:54322 -> 5432/tcp` |
| final-code stop/cleanup | stop exit 0, 2.512s; capture/stop 5.859s; final project/all 0/0; volume/prune 0 |

Post-remediation의 역사적 evidence snapshot은 196-line
`.superpowers/sdd/qsec006-task-5-db-evidence.md`, SHA-256
`89D00A9BDB3E6A01961F66977A29A811C964ECAF3623D65FD51D0EC6054713F2`다. 이 focused final-code
revalidation은 이미 dirty인 승인된 closeout 문서를 변경·stage하지 않았고 root/full combined tooling을
다시 실행하지 않았다. 아래 final verification이 이를 이어 받아 전체 gate를 닫았다.

## Final verification evidence

| 검증 | 실제 결과 |
|---|---|
| patched `-VerifyOnly` | PASS, exit 0, 8.528s |
| root `scripts/verify.ps1` | PASS, exit 0, 866.976s |
| package validator / secret scan | PASS; required 12 / finding 0, 1.075s / 5.652s |
| combined tooling | 74/74 PASS (`24 + 50`), unittest 602.877s / wrapper 603.617s |
| JSON / diff | PASS, exit 0, 0.557s / 0.347s |
| protected product paths + scripts | diff 0 |
| final dirty set / Docker cleanup | authorized 21 modified + IMP-004 note 1; project/all container 0/0 |

최종 evidence authority는 234-line `.superpowers/sdd/qsec006-task-5-db-evidence.md`, SHA-256
`9EE2AC549A983921CC928892D803E46F713E311103928A25B5E47A901764DBFB`다. 이 보고서와 note를
포함하는 closeout commit까지 완료됐으며 실제 SHA는 Git 이력을 권위로 확인한다.

## Commits와 review

- `5266abc` — validator-only `00600` correction, compensation, pgTAP
- `04a944f` — six-stage runner and real integration gate
- `228d8cb` — integration cleanup/evidence hardening
- `290d8d3` — A-021 privileged-function search-path audit
- `85067d0` — Task 9 documentation closeout
- `6520b0c` + focused guard commits — short-root/path-budget and legacy deny-only boundary
- `b7a22e7` — reproducible patched runtime manifest pin
- `1a31be4`, `f8d4f9b` — patched-only DB runner and discovery-escape regression closure
- `73f300b` — bounded database child process trees and descendant cleanup regression
- final Task 9 specification review: Critical/Important/Minor `0/0/0`
- final Task 9 quality review: Critical/Important/Minor `0/0/0`
- initial Task 10 spec review: Critical/Important/Minor `0/1/1`
- initial Task 10 quality review: Critical/Important/Minor `1/4/0`; actual port finding reproduced,
  fail-closed runner implemented, Q-SEC-004/A-022 opened
- patched runner 뒤 fresh non-DB root/tooling/static와 actual safe runtime/full DB gate: PASS
- Q-SEC-004=A/D-029 실제 재검증: `default-local-port-binding` 적용·완전 재시작 뒤 HostIP 미지정
  probe는 `127.0.0.1`+`::`, explicit `127.0.0.1` probe는 단일 loopback. 두 probe 제거, DB mutation 0.
- Q-SEC-005=A/D-030 실제 재검증: `local-only-port-binding` 적용·재시작 뒤 HostIP 미지정 probe는
  다시 `127.0.0.1`+`::`, explicit `127.0.0.1` control은 단일 loopback. 두 probe 제거,
  running/all/project container `0/0/0`, DB mutation 0. 이 두 결과는 역사적 대조 근거다.
- `73f300b` remediation specification/quality review: APPROVED, Critical/Important/Minor `0/0/0`
- final cumulative specification review: APPROVED, Critical/Important/Minor `0/0/0`
- final quality documentation re-review: APPROVED, Critical/Important/Minor `0/0/0`

## 명령

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
apps/api/.venv/Scripts/python.exe -B scripts/validate_codex_package.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_patched_supabase_tooling scripts.tests.test_supabase_tooling -v
git diff --check
```

DB gate 전 `scripts/bootstrap_patched_supabase.ps1 -VerifyOnly`를 실행한다. direct stock `db start`,
PATH fallback, `db diff`, remote link/push는 승인된 경로가 아니다.

## 해석 제한과 다음 gate

- 공식 KB/기관 seed는 PM 승인 목표 2026-07-20 전까지 0이다.
- 이 보고서는 disposable local/private 기준선 근거이며 production/public readiness가 아니다.
- `0.3.0-local` 승격은 실제 loopback/full gate의 결과이며 새 migration/data/API 변경이 아니다.
- DATA-SEED-001은 DATA-001 승인 뒤 시작하고 READY-001은 그 뒤 `/ready=200` 전환을 검증한다.
- A-021/Q-SEC-003 답변 전에는 선택지 B를 유지한다. public 경계를 열려면 별도 인간 결정,
  reviewed forward migration/compensation/pgTAP/behavior replay, 배포·CORS·credential·backup
  승인이 모두 필요하다.
