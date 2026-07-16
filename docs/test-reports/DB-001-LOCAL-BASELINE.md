# DB-001 Local Baseline Verification Report

- Date: 2026-07-17 KST
- Branch: `codex/db-001-layered-enforcement`
- Evidence baseline HEAD: `85067d04c3f498303d13426bf275e4196e8d5bdf`
- Current semantic version: `database_schema=0.2.0-draft`; `0.3.0-local`은 미승격 후보
- Scope: disposable local/private Supabase PostgreSQL candidate only
- Verdict: BLOCKED — Q-SEC-004/A-022 actual Docker port boundary

## 결론

DB-001의 executable candidate는 6개 forward migration, 6개 matching compensation,
7 enum, 8 table, forced RLS/capability boundary, 원자 후보 workflow, ACTIVE+OFFICIAL 시민 read,
30일 text-only purge와 lazy typed FastAPI repository를 재현했다. 공식/mock persistent seed는
0이며 `/health=200`, `/ready=503`이 정상이다.

그러나 이 결과는 안전한 final local baseline이 아니다. Task 10 quality review에서 기존 runtime의
wildcard host publish를 발견했다. 보정 runner는 Docker Engine 28+, 고정 optioned network와
container identity, HostConfig 요청과 actual `NetworkSettings.Ports`를 reset/status/env 전에
검증한다. Docker Desktop 4.62.0/Engine 29.2.1에서 stock CLI 2.109.1은 HostIP를 생략했고 actual
binding은 wildcard 두 종류로 판정돼 runner가 중단했다. reset/status/credential handling은
실행되지 않았고 stack stop 뒤 project container count 0을 확인했다.

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

## 과거 DB gate 결과 — 현재 완료 증거 아님

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

## 비DB 검증

| 검증 | 실제 결과 |
|---|---|
| local DB tooling contract | 31/31 PASS, 176.911s; partial-start cleanup·stopped inventory 포함 |
| Ruff format/check | PASS |
| strict Mypy | PASS |
| API pytest without DB URLs | 156 passed, 8 skipped; main import 4 subtests PASS |
| root/Web/API/contract gate | PASS |
| secret scan | finding 0, secret value output 0 |
| package validation / `PACKAGE_MANIFEST.json` | PASS / byte-for-byte unchanged |
| JSON/version validation | PASS |
| `git diff --check` | whitespace error 0 |
| health/readiness | `/health=200`, `/ready=503` |

## Commits와 review

- `5266abc` — validator-only `00600` correction, compensation, pgTAP
- `04a944f` — six-stage runner and real integration gate
- `228d8cb` — integration cleanup/evidence hardening
- `290d8d3` — A-021 privileged-function search-path audit
- `85067d0` — Task 9 documentation closeout
- final Task 9 specification review: Critical/Important/Minor `0/0/0`
- final Task 9 quality review: Critical/Important/Minor `0/0/0`
- initial Task 10 spec review: Critical/Important/Minor `0/1/1`
- initial Task 10 quality review: Critical/Important/Minor `1/4/0`; actual port finding reproduced,
  fail-closed runner implemented, Q-SEC-004/A-022 opened
- runner remediation 뒤 fresh non-DB root/tooling/static gate: PASS; actual safe runtime/full DB gate와
  independent completion review는 Q-SEC-004 해결 뒤 pending

## 명령

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
apps/api/.venv/Scripts/python.exe -B scripts/validate_codex_package.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
git diff --check
```

Q-SEC-004 해결 전 `verify_database.ps1`이나 direct Supabase start를 실행하지 않는다.

## 해석 제한과 다음 gate

- 공식 KB/기관 seed는 PM 승인 목표 2026-07-20 전까지 0이다.
- Q-SEC-004/A-022 해결, Docker restart/recreate, exact single loopback binding과 fresh full DB gate 전
  manifest를 `0.3.0-local`로 승격하지 않는다.
- 이 보고서의 282/282·8/8·rollback/replay는 port finding 전 역사적 기능 증거이며 현재 active
  local baseline이나 후속 dependency 해제 근거가 아니다.
- DATA-SEED-001은 DATA-001 승인 뒤 시작하고 READY-001은 그 뒤 `/ready=200` 전환을 검증한다.
- A-021/Q-SEC-003 답변 전에는 선택지 B를 유지한다. public 경계를 열려면 별도 인간 결정,
  reviewed forward migration/compensation/pgTAP/behavior replay, 배포·CORS·credential·backup
  승인이 모두 필요하다.
