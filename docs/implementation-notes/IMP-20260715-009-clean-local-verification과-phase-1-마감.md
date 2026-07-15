# IMP-20260715-009 — clean local verification과 Phase 1 마감

- Date/Time (KST): 2026-07-15 14:40~21:31
- Task ID: DEV-001D, DEV-002B
- Type: implementation / security / documentation
- Status: Done — corrected fresh-worktree default/warm-offline 24/24, actual API/Web smoke와 최종 독립 review(P0/P1/P2 0, Ready Yes) 완료
- Author/Agent: `/root/dev001d_verify_implement`; 최종 통합 책임 `/root`
- Branch: `codex/DEV-001-repo-scaffold`
- Base commit: `cb5bdf3ef41202d2a173dd418234e387d6802eb0`
- Related plan/ADR/RFP: [PLAN-20260715-002](../plans/PLAN-20260715-002-phase-1-scaffold-health-contract.md), ADR-0009, SER-001~003, QUR-001~002, COR-001~002

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 승인한 Phase 1의 마지막 수직 흐름으로 exact local toolchain, Web/API/계약/보안 검증을 하나의 Windows PowerShell 5.1 호환 명령에 묶고, warm-cache offline 재현과 fail-fast·비밀 비노출·환경 복원을 자동 검증한다. 제품 기능, DB, 공식 데이터, provider와 배포는 추가하지 않는다.

### Acceptance Criteria

- 공개 옵션은 `-Offline` 하나이고 저장소 루트가 아닌 현재 디렉터리에서도 같은 root를 찾는다.
- PowerShell 5.1+, Node 24.12.0, pnpm 11.13.0, uv 0.11.28, API Python 3.12.13을 먼저 검사한다.
- frozen pnpm/uv, root/Web/API/계약, secret/browser bundle, package와 diff gate를 24개 stable 단계로 fail-fast 실행한다.
- child 실패는 원 종료코드를 보존하고 운영 예외는 2이며, 성공·실패 child 원문과 예외 내용·비밀값·경로를 출력하지 않는다.
- pnpm 재검증/offline 값과 Web build의 여섯 synthetic 환경값은 기존 값과 부재 상태까지 정확히 복원한다.
- 기본 gate와 warm `-Offline` gate가 모두 종료코드 0이어야 한다.
- README, 첫 실행 체크리스트, task/plan/changelog/version과 구현 노트를 동기화한다.
- actual uvicorn/Next HTTP smoke, staged fresh-worktree gate와 최종 read-only review 증거를 이 노트에 추가한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 구현 agent가 TDD로 writer gate를 만들고, 독립 review agent와 root가 P1을 제기·검증했다. 사용자는 local-first 수동 gate를 승인했다. |
| When — 언제 | 2026-07-15 KST, Phase 1 Task 1~6 commit 이후 Task 7에서 수행했다. |
| Where — 어디서 | 격리 worktree의 `scripts/`, root 문서·task·plan·version과 구현 노트에서 수행했다. |
| What — 무엇을 | PS 5.1-compatible 단일 검증 runner, 16개 focused test, 실행·보안 문서를 추가했다. |
| Why — 왜 | CI와 remote가 없는 현재 단계에서도 새 개발자가 한 명령으로 exact local 상태와 drift를 판정하고, 진단 과정에서 값·경로를 유출하지 않게 하기 위해서다. |
| How — 어떻게 | missing-file RED→최소 GREEN→실제 default/offline gate→독립 review P1을 focused RED→GREEN→통합 재검증 순서로 처리했다. |
| How much — 어느 정도 | runner 24단계, focused test 16개, 공통 합성 fixture 17개·fixture 검증 27개·structure guard 6개. 새 dependency·DB/data/prompt 변경 0건이며, 전체 리뷰에서 발견한 공개 응답 스키마 drift만 API patch revision으로 보정했다. |

## 3. 시작 전 상태

- 관련 파일: root workspace·lock, Web/API/contract test와 scanner는 Task 1~6에서 각각 실행 가능했으나 단일 runner가 없었다.
- 기존 동작: 개발자가 여러 명령을 수동 조합해야 했고 warm offline, fail-fast 종료코드, synthetic build 환경 복원과 전체 순서를 한 번에 증명할 수 없었다.
- 발견한 충돌/부채:
  - `scripts/verify.ps1` 부재로 Phase 1 clean local gate가 재현되지 않았다.
  - DB migration과 승인 seed는 아직 없으므로 `/ready=503`이 의도한 상태이며 200으로 바꾸면 안 된다.
  - CI·remote가 사용자 결정으로 보류돼 local gate가 현재 유일한 통합 경계다.
- Git 상태: base `cb5bdf3`, 작업 시작 시 tracked/untracked 변경 0건이었다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| VERIFY-OFFLINE | B/운영 | 빈 cache에서도 offline이 동작해야 하는가 | 아니오. 먼저 default frozen gate를 실행한 warm cache 검증으로 명시 | README, checklist, runner |
| VERIFY-OUTPUT | B/보안 | 하위 명령 출력을 진단용으로 전달할지 | 성공/실패 모두 원문을 억제하고 stable step/exit만 출력 | 경로·비밀 유출 감소, 직접 명령 재현 필요 |
| VERIFY-HTTP | B/통합 | runner가 서버를 띄워 smoke할지 | runner는 서버를 띄우지 않으며 root가 별도 actual HTTP smoke | 삭제/프로세스 lifecycle 없음 |
| VERIFY-DB | 확정 경계 | readiness를 200으로 바꿀지 | DB-001·승인 seed 전 503 유지 | 공개 동작 변경 없음 |
| VERIFY-CI | 인간 보류 | remote/CI에도 연결할지 | local manual만; 사용자가 Git 연결을 요청할 때 재결정 | infra·비용 0 |

## 5. 설계 결정과 대안

### 선택

- `scripts/verify.ps1` 하나가 `$PSScriptRoot`로 repo root를 찾고 exact preflight 뒤 24개 stable ID를 순차 실행한다.
- repo-local `.tools/uv/uv.exe`를 PATH보다 먼저 사용하고 없을 때만 `uv`를 native resolver에서 찾는다.
- 모든 native 호출 전 executable을 application으로 단일 해석하고 `LASTEXITCODE`를 초기화한다. child 출력은 메모리에서 판정만 하고 재출력하지 않는다.
- `PNPM_CONFIG_VERIFY_DEPS_BEFORE_RUN`은 모든 실행에서 임시 false, `PNPM_CONFIG_OFFLINE`은 offline에서만 임시 true로 설정하며 기존 값/부재를 snapshot·restore·assert한다.
- Web build 동안 여섯 server/sentinel 이름을 같은 synthetic 값으로 설정하고 build 직후 복원한다. browser scan 시 sentinel 이름만 별도 scope로 다시 설정한다.
- completion PASS는 runner env와 location 복원이 성공하고 최종 exit가 0일 때만 출력한다.

### 이유

현재 운영 대상은 Windows local-first이고 PowerShell 5.1이 이미 security scanner의 최소 계약이다. 같은 shell에서 native exit를 명시적으로 다루면 pnpm/uv/Node/Python의 플랫폼별 wrapper 차이와 값 노출을 통제할 수 있다.

### 고려했지만 선택하지 않은 대안

- root npm script: Python/API와 PowerShell scanner까지 다시 shell로 감싸며 exact native exit 경계가 약해져 선택하지 않았다.
- Bash/Makefile: 현재 Windows PS 5.1 기준과 맞지 않아 선택하지 않았다.
- runner 내 uvicorn server launch: process cleanup과 port 충돌이 gate 책임을 넓혀 별도 smoke로 유지했다.
- child 출력 전달: 진단은 편하지만 실패한 도구가 env·경로·입력 내용을 출력할 수 있어 억제했다.
- 새 task-runner dependency: 0원·dependency 최소 원칙과 맞지 않아 추가하지 않았다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `scripts/verify.ps1` | exact preflight, frozen/default+offline, 24단계 gate, native exit/출력 경계, 환경 snapshot/restore | 단일 재현 명령과 보안 진단 경계 |
| `scripts/tests/test_verify_runner.py` | 단계/명령 wiring, PS 5.1 parser, unknown option, exit 37, exception 2, output secrecy, build/runner env success·failure 복원 테스트 16개 | TDD와 review 회귀 방지 |
| `README.md` | 단일 gate와 warm offline 의미, 별도 HTTP smoke 안내 | 신규 개발자 시작점 |
| `FIRST_RUN_CHECKLIST.md` | exact runtime/env/default/offline/HTTP checklist | 첫 실행 누락 방지 |
| `scripts/README.md` | 24단계 구성, 종료코드·출력·옵션 정책 | runner 운영 계약 |
| `TASKS.md` | DEV-002B 추가, 중간에는 root evidence 대기 Review로 추적하고 final evidence 후 Phase 1 parent/child를 Done으로 전환 | 중간 허위 Done 방지와 최종 closure |
| `CHANGELOG.md` | local gate·환경 복원을 추가하고 root 최종 증거를 중간 Pending에서 완료 이력으로 전환 | 변경 요약 |
| `docs/plans/PLAN-20260715-002-*` | Task 7 writer Review에서 corrected fresh/smoke/review 증거 후 final Done으로 전환, 실제 버전 반영 | 계획 대비 결과 추적 |
| `versions/manifest.json` | app/test/docs/repo guidance checkpoint | 버전 계약 동기화 |
| `contracts/openapi-v1.yaml`, health/readiness Pydantic·route·generated TS | `/health`와 ready-state `/ready` 200 응답을 required closed schema로, FALLBACK을 추가 필드 거부로 정렬 | 최종 전체 리뷰 P1/P2 계약 drift 제거 |
| shared/API contract tests와 `invalid-fallback-extra-property.json` | 양 계약·Pydantic·생성물에 동일한 부정 fixture와 구조 회귀 추가 | 재발 방지와 공식/mock 데이터 비혼합 |

### 데이터 흐름/상태 변화

1. runner가 argument와 PS/runtime version을 검사한다.
2. pnpm 재검증/offline env를 process scope에서 snapshot 후 설정한다.
3. frozen install/sync 후 root, Web, API, contract 순서로 실행한다.
4. Web build에서 synthetic 값 여섯 개를 잠시 주입하고 정확히 복원한다.
5. 계약 생성물 diff, repository secret, browser artifact, package, whitespace diff를 검사한다.
6. 모든 환경과 working directory가 복원된 뒤에만 completion PASS를 출력한다.

질문·답변·PII·실제 secret은 읽거나 저장하지 않는다. runner 로그는 단계 ID와 PASS/FAIL/exit code만 남긴다.

### 오류·빈 상태·롤백

- child exit 1~255는 같은 code로 fail-fast 종료한다.
- missing executable, version mismatch, argument, invocation·restore 예외는 내용 없이 code 2다.
- default cache 접근이 불가능하면 임의 버전으로 진행하지 않는다. managed sandbox의 uv user-cache 접근 거부는 격리 밖 동일 명령으로 원인을 분리했다.
- `.next`가 없거나 secret/bundle scanner가 operational error를 내면 gate는 실패한다.
- runner는 파일 삭제와 server launch를 하지 않는다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | `0.0.4-contract-drift-gates` | `0.1.0` | Phase 1 writer scaffold gate 구현 |
| Web | `0.1.0` | `0.1.0` | 동작 변경 없음 |
| API | `2.0.0-draft` | `2.0.1-draft` | health/readiness 200·FALLBACK strictness의 patch drift 보정 |
| Shared contracts | `0.2.0` | `0.2.1` | 생성 TypeScript·fixture/structure guard 동기화 |
| DB schema | `0.2.0-draft` | `0.2.0-draft` | migration 0건 |
| Official data | `0.0.0-not-populated` | 동일 | 공식 데이터 0건 |
| Mock data | `0.0.0-not-populated` | 동일 | mock 0건 |
| Prompt set | `0.0.2-deepseek-v4-flash-selected` | 동일 | provider 호출·prompt 변경 0건 |
| Test suite | `0.4.0-contract-drift-gates` | `0.4.2-readiness-contract` | runner regression 16개와 응답 계약 회귀 추가 |
| Repo guidance | `1.3.0` | `1.4.0` | 첫 실행·단일 gate 계약 |
| Docs | `2.3.8` | `2.3.10` | Task 7 운영 문서와 최종 계약 보정 기록 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `python -B -m unittest scripts.tests.test_verify_runner -v` | RED, exit 1 | 최초 9/9 fail; `verify.ps1` 부재 | 이 노트 TDD 기록 |
| 같은 focused 명령 | GREEN, exit 0 | 최소 구현 9/9 pass | `scripts/tests/test_verify_runner.py` |
| cacheprovider focused 회귀 | RED→GREEN | 1 fail→focused/all pass | pytest command wiring |
| review 보강 focused 실행 | RED→GREEN | 동적 harness 교정 후 4 fail; 이후 14 중 12 pass/2 fail; focused 2 pass | native/env 회귀 |
| uv label·completion PASS focused 실행 | RED→GREEN | 2 fail→full 16/16 pass | root review 회귀 |
| `.\apps\api\.venv\Scripts\python.exe -B -m unittest discover -s scripts/tests -p 'test_*.py' -v` | exit 0 | 35 tests OK, Windows symlink 권한 skip 1 | final writer verification |
| `powershell.exe ... -File scripts/verify.ps1` | exit 0 | 최신 24/24 stable 단계 pass | writer current worktree |
| `powershell.exe ... -File scripts/verify.ps1 -Offline` | exit 0 | 최신 warm-cache 24/24 pass | writer current worktree |
| fresh read-only runner/test review | Ready | P0 0, P1 0; optional P2 test mutation-resistance | `/root/dev001d_verify_review` |
| 전체 Phase 1 read-only review | 보정 필요 | P0 0, P1 2, P2 1: `/ready` 200 schema·FALLBACK extra·`/health` closed schema | `/root/phase1_final_review` |
| shared contract TDD | RED→GREEN | 최초 35/37, 보정 후 37/37 pass; fixture 27·structure 6 | shared contract tests |
| API contract TDD | RED→GREEN | 최초 26/28, 보정 후 28/28 focused; full 44 pass+4 subtests | API tests |
| Python/생성물 품질 gate | exit 0 | ruff format/check, mypy 13 files, generate/check, direct TS compile | 보정 후 current worktree |
| corrected fresh default gate | exit 0 | snapshot `2f8c573`, 24/24 pass | `PHASE1-FINAL-VERIFY-2` |
| corrected fresh warm `-Offline` gate | exit 0 | 같은 snapshot, 24/24 pass | `PHASE1-FINAL-VERIFY-2` |
| actual API HTTP smoke | exit 0 | health 200, pre-DB ready 503, Retry-After 30, UUID, marker 로그 0 | corrected snapshot |
| actual Web HTTP smoke | exit 0 | HTML/RSC 200, service name, env/marker 노출 0, env 복원 | corrected snapshot |
| 최종 독립 계약 재리뷰 | Ready Yes | prior P1 2·P2 1 해결, 최종 P0/P1/P2 0 | `/root/phase1_final_review` |
| 활성 문서 일관성 감사 | P2 보정→Ready | API `-draft` suffix 두 곳 보정, P0/P1 0 | `/root/phase1_docs_consistency_review` |
| PS 5.1 AST parse | exit 0 | parser error 0 | focused test |
| fail-fast synthetic child | exit 37 | later `SYNC-API` 시작 0, child output 노출 0 | focused test |
| default repository secret/browser scan | exit 0 | finding 0 | 통합 runner |
| `git diff --check` | exit 0 | whitespace error 0 | 통합 runner |

### 실제 통합에서 확인한 하위 결과

1차 staged fresh snapshot에서 default와 warm `-Offline` 24/24가 모두 통과했고, 그 뒤 전체 리뷰 계약 보정의 current-worktree 하위 gate는 shared 37/37, API 44 pass+4 subtests, runner discover 35 OK(Windows symlink 권한 skip 1), ruff/mypy/generate/TS compile을 통과했다. 보정이 포함된 snapshot `2f8c573`을 cache 없는 새 worktree에 checkout해 default와 warm `-Offline` 24/24를 다시 통과시켰다. actual API smoke는 `/health=200`, pre-DB `/ready=503`, exact Retry-After·SERVICE_UNAVAILABLE·UUID request id·민감 marker 로그 0을, actual Web smoke는 HTML/RSC 200, 서비스명 렌더, synthetic marker·서버 전용 변수명 응답/로그 노출 0과 runtime env 복원을 확인했다. 첫 Web smoke harness는 공백이 있는 절대 `next` 인자 경로가 Windows `Start-Process`에서 분리돼 기동 전에 실패했으며 프로세스·로그·환경을 정리한 뒤 상대 경로로 같은 검사를 성공시켰다. 최종 임시 로그와 잔여 서버 프로세스는 0, snapshot tracked diff는 0이었다. 기존 FastAPI TestClient의 Starlette/httpx2 deprecation warning 1건은 dependency 변경 승인이 필요한 후속 위험이며 실패로 숨기지 않는다.

### 최종 검증과 의도적 미실행

- 보정 후 staged fresh-worktree default/warm-offline gate와 actual API/Web HTTP 재-smoke: 모두 완료했다.
- 최종 read-only 재리뷰: 이전 P1 2건과 P2 1건 해결, 최종 P0/P1/P2 0과 Ready Yes를 파일·라인 근거로 확인했다.
- remote CI: 사용자가 원격 Git 연결을 보류했으므로 없음.
- DB reset/migration: DB-001 범위이고 현재 Blocked다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 질문 원문, body, header, cookie, PII를 읽거나 출력하지 않는다. 실제 시민 데이터 0건이다.
- Security: 성공·실패 child output, exception message, executable/path와 synthetic 값을 출력하지 않는다. 여섯 Web env와 두 pnpm env는 process scope에서 기존 값·부재를 정확히 복원한다. repository secret/browser artifact scan이 마지막 gate에 포함된다.
- Accessibility: 시민 UI 변경 없음. 기존 semantic/390·430px 검증을 그대로 재실행한다.
- Performance/cost: 외부 API·LLM·인프라 비용 0원. default/warm offline은 local CPU와 cache만 사용한다. child 출력 억제로 실패 진단 시 해당 단계 명령을 직접 재실행해야 한다.

## 10. 데이터와 출처 영향

- 공식 데이터: 추가·수정·승인 0건. ACTIVE KB는 아직 populated가 아니다.
- mock/AI 생성: 테스트가 쓰는 문자열은 synthetic control 값이며 시민·공식 데이터가 아니다.
- schema/lineage: DB schema·standalone chat JSON Schema·공식 데이터는 변경하지 않았다. OpenAPI는 `2.0.1-draft` patch로 health/readiness/FALLBACK strictness를 보정했고 generated TypeScript·Pydantic·공통 fixture를 함께 동기화했다.
- verified date: 2026-07-15 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- `/ready=503`은 DB와 승인 seed 전 의도한 상태다. Phase 1 성공을 위해 200으로 바꾸지 않았다.
- `-Offline`은 warm-cache 검증이지 빈 PC 설치 보장이 아니다. 처음에는 default gate가 필요하다.
- runner는 보안을 위해 child 원문을 숨긴다. 실패 단계의 직접 명령은 `scripts/README.md`와 source에서 확인한다.
- 실제 배포, remote/CI, DB migration·삭제, 공식 데이터 승인, 공개/실사용 DeepSeek와 새 production dependency는 여전히 별도 승인 대상이다.
- Phase 1은 보정 후 fresh-worktree·actual HTTP 재-smoke·최종 read-only 재리뷰까지 모두 통과해 Done으로 판정했다. DB-001과 승인 seed는 별도 Blocked 상태다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- native executable 이름은 `Get-Command -CommandType Application` 결과 중 PATH 우선 첫 항목만 사용한다. absolute path는 leaf 존재를 먼저 확인한다.
- `LASTEXITCODE`를 각 호출 전 null로 초기화해 PS 5.1 command-not-found stale code를 성공으로 오인하지 않는다.
- uv version은 semantic exact prefix와 공식 metadata shape 전체를 anchored regex로 검증한다.
- dot-source 시 helper만 로드하고 main을 실행하지 않아 환경 success/failure 복원 테스트를 실제 process 안에서 수행한다.
- pytest cacheprovider는 local cache ACL warning을 없애기 위해 runner에서 비활성화하며 테스트 결과 자체에는 영향이 없다.

## 13. 인수인계·재현·롤백

### 재현

1. exact runtime을 `README.md`와 `.node-version`, `.python-version`, `uv.toml`에서 확인한다.
2. 저장소 임의 디렉터리에서 default runner를 실행한다.
3. default가 통과해 cache가 준비됐으면 `-Offline`을 실행한다.
4. 실패하면 마지막 stable step ID를 확인하고 `scripts/verify.ps1`의 해당 명령을 직접 실행한다. 값·질문 원문을 issue/log에 복사하지 않는다.
5. root는 staged fresh worktree에서 같은 두 gate와 별도 uvicorn HTTP smoke를 실행한다.

### 롤백

commit 전에는 이 note의 변경 목록을 기준으로 Task 7과 최종 계약 보정 diff만 제거한다. commit 후에는 history를 삭제하지 말고 최종 Task 7 commit을 `git revert`한다. rollback 목표는 Task 1~6의 API `2.0.0-draft`이며 DB/data/prompt는 건드리지 않는다.

### 다음 개발자 시작점

`README.md`의 단일 로컬 검증과 `FIRST_RUN_CHECKLIST.md`를 먼저 수행한다. Phase 2 제품 구현 전에는 DB-001·DATA-001 의존성과 `/ready=503` 경계를 다시 확인한다.

## 14. 남은 위험·미해결 질문·다음 단계

- Windows symlink scanner test 1개는 현재 사용자 권한에서 skip될 수 있다.
- FastAPI TestClient deprecation warning은 승인된 dependency 목록 안의 후속 호환성 판단이 필요하다.
- offline 성공은 현재 machine cache에 한정되며 clean machine/off-network bootstrap을 보장하지 않는다.
- remote/CI가 없으므로 branch 보호와 서버측 gate는 적용되지 않는다.
- focused wiring test 일부는 source 문자열 위치를 사용하므로 helper declaration과 main invocation을 AST로 분리하는 mutation-resistance 보강은 optional P2다. 실제 unknown-option·env·native 동작은 동적 테스트가 별도로 고정한다.
- 다음 단계는 인간 승인과 공식 데이터 준비가 충족될 때 DB-001·DATA-SEED-001부터 Phase 2 계획을 별도로 승인받는 것이다. 현재 DB-001은 계속 Blocked다.

## 15. 자체 리뷰

- [x] 사용자 승인 범위 내 runner/문서 구현
- [x] TDD RED→GREEN과 최신 default/offline gate
- [x] 공개 API patch drift 보정과 DB/data/prompt 무변경 확인
- [x] 개인정보 원문·비밀·child output 노출 없음
- [x] 구현 노트와 INDEX 갱신
- [x] root fresh-worktree·actual HTTP·final read-only review 증거 append
