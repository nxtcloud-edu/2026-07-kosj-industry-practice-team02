# IMP-20260717-008 — Q-SEC-004 A 승인과 IPv6 wildcard 재조사

- Date/Time (KST): 2026-07-17T10:12:50+09:00
- Task ID: DB-001-T10-QSEC004
- Type: decision/security/investigation
- Status: Blocked — Q-SEC-004=A/D-029 applied; Q-SEC-005/A-023 human decision required
- Author/Agent: Codex `/root`
- Branch: `codex/db-001-layered-enforcement`
- Base commit: `53edf18`
- Related plan/ADR/RFP: DB-001 plan/spec, ADR-0011, D-029, A-022/A-023,
  Q-SEC-004/Q-SEC-005, DAR-001/002/003, SER-001/002/003

## 1. 사용자 요청과 완료 기준

### 요청

사용자는 Q-SEC-004의 추천안 A를 `ㅇㅇ 승인할게. 계속 ㄱㄱ`로 명시 승인하고 DB-001 Task 10을
계속 진행하라고 요청했다.

### Acceptance Criteria

- Docker Desktop의 승인된 `default-local-port-binding` 설정만 변경하고 완전 재시작한다.
- Supabase DB를 시작하기 전에 HostIP 미지정 일회용 probe의 actual resolved binding을 확인한다.
- exact single `127.0.0.1`이 아니면 DB reset/status/credential 처리 없이 중단한다.
- 대조 probe로 explicit `127.0.0.1` 경계가 실제 단일 loopback인지 확인한다.
- probe container를 모두 제거하고 DB/데이터/manifest/dependency를 변경하지 않는다.
- 승인 결과와 새 blocker를 decision log, ambiguity register, source-of-truth, plan/report/handoff에
  동기화한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자 승인자, Codex `/root`; 초기 병렬 reviewer의 port finding을 이어받음 |
| When — 언제 | 2026-07-17 KST, `53edf18` blocked checkpoint 뒤 |
| Where — 어디서 | Docker Desktop 4.62.0/Engine 29.2.1, Windows user settings store, DB-001 worktree docs |
| What — 무엇을 | Q-SEC-004=A 적용, 완전 재시작, 두 disposable port probe, IPv6 wildcard blocker 분리 |
| Why — 왜 | 개발용 DB port가 LAN/IPv6에 공개되기 전에 exact loopback을 증명하기 위해 |
| How — 어떻게 | Docker 완전 stop → 단일 설정 키 적용 → start → HostIP 미지정/명시 probe inspect → 즉시 제거 → fail-closed 문서화 |
| How much — 어느 정도 | 외부 설정 키 1개, probe 2개 생성·제거, persistent container/data 0, repo product code/migration/version 변경 0, 외부 비용 0원 |

## 3. 시작 전 상태

- 관련 파일: `docs/11_AMBIGUITY_REGISTER.md`, `docs/decisions/DECISION_LOG.md`,
  `docs/source-of-truth/TEAM_DECISIONS.md`, DB-001 plan/spec/report/handoff, `scripts/verify_database.ps1`.
- 기존 동작: Docker Desktop 설정은 기본 `default-port-binding`이었고 project/all container는 0이었다.
- 기존 blocker: stock Supabase CLI 2.109.1은 DB PortBindings에 HostPort만 넣고 HostIP를 비운다.
- Git 상태: clean `53edf18`에서 시작했다.
- 개인정보/비밀: 질문·답변·DSN·API key·env value를 읽거나 출력하지 않았다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| A-022/Q-SEC-004 | Resolved | `default-local-port-binding` 전역 변경 승인 | D-029, 설정 유지 | IPv4 loopback은 적용됐으나 exact gate 실패 |
| A-023/Q-SEC-005 | A/Blocker Human | IPv6 wildcard까지 막는 `local-only-port-binding` 전역 정책 또는 patched CLI | 무응답 C: Supabase DB runtime 보류 | DB-001 Task 10, manifest, 후속 DB dependency |
| A-021/Q-SEC-003 | B/High Deferred | privileged function 21개 public hardening | default B: local/private만 | public/remote release 차단 |

## 5. 설계 결정과 대안

### 선택

Q-SEC-004=A에 따라 Docker Desktop user settings의 `PortBindingBehavior`를
`default-local-port-binding`으로 설정하고 완전 재시작했다. actual probe가 exact 기준을
충족하지 않아 Supabase DB runner는 실행하지 않았다. Q-SEC-005/A-023을 새 인간 blocker로 열었다.

### 이유

설정 이름이나 요청값이 아니라 Docker의 실제 `NetworkSettings.Ports`가 보안 경계다. HostIP
미지정 probe는 `127.0.0.1`과 `::`를 함께 만들었고, explicit `127.0.0.1` probe는 단일
loopback이었다. 따라서 root cause는 stock CLI의 HostIP 생략과 Docker Desktop IPv6 해석 경계다.

### 고려했지만 선택하지 않은 대안

- runner의 exact 기준을 `127.0.0.1`+`::`로 완화: IPv6 wildcard 공개를 허용하므로 거부.
- 승인 없이 `local-only-port-binding` 적용: 명시적인 LAN publish까지 막는 더 큰 전역 영향이라 보류.
- project-patched Supabase CLI: 새 binary/digest/build/review 공급망이 필요해 인간 승인 전 보류.
- Windows Firewall만 의존: actual Docker inspect 계약을 충족하지 않고 관리자 OS 상태에 의존해 거부.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `%APPDATA%/Docker/settings-store.json` | `PortBindingBehavior=default-local-port-binding` 1개 적용·재시작 뒤 유지 | Q-SEC-004=A 실행 |
| ambiguity/decision/team/task/ADR | D-029, A-022 resolved-insufficient, A-023/Q-SEC-005 open blocker | 인간 결정과 실제 실패를 분리 |
| plan/spec/report/handoff/active guides | current blocker와 probe 증거 동기화 | stale “Q-SEC-004 unanswered” 제거 |
| 이 노트와 INDEX | 6W1H·명령·버전·보안·rollback 기록 | 요청별 구현 노트 의무 |

### 데이터 흐름/상태 변화

Docker Desktop user-level port policy만 바뀌었다. 두 probe는 기존 local Supabase PostgreSQL image를
사용해 `sleep`만 실행했고 즉시 `docker rm -f`로 제거했다. Supabase DB start/reset/status,
credential provisioning, SQL, seed, API, DeepSeek 호출은 0회다.

### 오류·빈 상태·롤백

- `computer-use`의 Orca runtime이 실행되지 않아 UI 자동화는 불가능했다.
- Docker Desktop CLI에는 settings 변경 명령이 없어 공식 settings-store 위치를 사용했다.
- 공식 lowercase JSON key는 user store에서 무시·제거됐다. 실제 store의 PascalCase 형식에 맞춘
  `PortBindingBehavior`는 재시작 뒤 유지됐다. 첫 시도는 다른 설정을 바꾸지 않고 원본으로 복원됐다.
- Docker stop/start CLI가 엔진 상태 변경 뒤 반환하지 않는 현상이 있어 status로 종료/시작을
  확인하고 남은 exact CLI process만 종료했다. Docker backend/container에는 강제 종료를 하지 않았다.
- rollback이 필요하면 Docker Desktop을 완전히 종료하고 `PortBindingBehavior` 키를 제거한 뒤
  재시작한다. 현재 승인된 더 안전한 IPv4 기본값이므로 Q-SEC-005 결정 전 자동 rollback하지 않는다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.0 | 2.2.0 | 제품 범위 불변 |
| Repo guidance | 1.4.0 | 1.4.0 | DB 완료 아님 |
| Application/Web | 0.1.0 / 0.1.0 | 동일 | 제품 코드 불변 |
| API/shared | 2.0.1-draft / 0.2.1 | 동일 | 공개 계약 불변 |
| DB schema | 0.2.0-draft | 0.2.0-draft | exact loopback/full gate 미통과 |
| Official/mock data | 0.0.0-not-populated / 동일 | 동일 | seed/data 0 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM 미사용 |
| Test suite | 0.4.2-readiness-contract | 동일 | 완료 baseline 미승격 |
| Documentation | 2.3.14 | 2.3.14 | blocked decision sync, release 승격 아님 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `orca status --json` / `orca computer capabilities --json` | Orca runtime not running / `runtime_unavailable` | UI write 0 | terminal |
| `docker desktop --help` | settings mutation command 없음 | read-only | terminal |
| initial settings parse | `portBindingBehavior` missing, default snapshot은 `default-port-binding` | 220 bytes, SHA-256 `531741...41fb` | user settings/analytics snapshot |
| lowercase key attempt | JSON 자체는 valid였지만 start 뒤 key 제거·원본 복원 | persistent change 0 | terminal |
| PascalCase key + complete restart | `PortBindingBehavior=default-local-port-binding` 유지 | 275 bytes, SHA-256 `c8d6e9...07fa` | user settings store |
| HostIP omitted probe `-p 54329:5432` | requested HostIP empty; resolved `127.0.0.1:54329` + `:::54329` | FAIL exact-local; probe removed | Docker inspect |
| explicit probe `-p 127.0.0.1:54329:5432` | requested/resolved exact single `127.0.0.1:54329` | PASS control; probe removed | Docker inspect |
| final Docker inventory | running/all/project container count `0/0/0`; Desktop running | DB mutation 0 | Docker CLI |
| `git diff --check` | PASS | exit 0; INDEX line-ending warning만 있음 | Git |
| Codex package validator | PASS | required file 12개, version manifest valid | `scripts/validate_codex_package.py` |
| tracked secret pattern scan | PASS | exit 0, finding 0 | `scripts/check_secret_patterns.ps1` |
| JSON/version assertion | 첫 검사 명령은 중첩 `versions`를 평면으로 읽어 `KeyError`; 스키마에 맞춘 수정 명령 PASS | `repo_guidance=1.4.0`, `database_schema=0.2.0-draft`, `test_suite=0.4.2-readiness-contract`, `documentation=2.3.14` | manifest 2개 |
| protected-scope diff | PASS | package/version/contracts/migrations/rollbacks/seed/product code/runner/tooling test diff 0 | Git |
| changed Markdown static check | PASS | `core.quotePath=false` 기준 staged Markdown 26개, control character 0, broken local link 0 | working tree |
| stale active-blocker wording search | PASS | stale current-state match 0 | active docs |
| final Docker inventory/settings | Desktop running, `default-local-port-binding`, running/all/project `0/0/0` | DB mutation 0 | Docker CLI |

### 미실행 검증과 이유

- `scripts/verify_database.ps1`: actual HostIP 미지정 probe가 IPv6 wildcard를 남겨 실행 금지.
- pgTAP/rollback/replay/integration: reset 전 보안 gate가 통과하지 않아 실행 금지.
- root full gate: repo product code가 바뀌지 않았고 이번 blocked 문서 sync 완료 뒤 static gate만 수행한다.
- remote/public DB·배포·backup: 미승인·범위 밖.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 시민 질문·답변·transcript·PII·DSN·secret 접근/저장/출력 0.
- Security: IPv4 기본 publish는 loopback으로 강화됐지만 IPv6 wildcard 때문에 DB는 계속 차단한다.
  exact guard는 완화하지 않았다.
- Accessibility: UI/제품 변경 없음.
- Performance/cost: 기존 local image probe 2회, 외부 API/유료 인프라 0원.

## 10. 데이터와 출처 영향

- 공식 데이터: 0, 변경 없음.
- mock/AI 생성: persistent 0, 변경 없음.
- schema/lineage: 6 forward+6 compensation byte 불변.
- 출처: Docker Desktop 4.62.0/Engine 29.2.1 actual inspect와 Docker 공식 port/settings 문서.
- verified date: 2026-07-17 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Q-SEC-004=A는 적용됐지만 exact local을 달성하지 못했다.
- Q-SEC-005/A-023에서 더 강한 `local-only-port-binding` 전역 정책을 승인할지 결정해야 한다.
- 이 정책은 앞으로 다른 container가 명시적으로 LAN 공개를 요청해도 loopback으로 제한할 수 있다.
- 무응답 시 current setting을 유지하되 Supabase DB와 후속 DB 작업은 계속 차단한다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- 설정의 source-of-truth는 이름이 아니라 재시작 뒤 settings-store 유지와 actual inspect 결과다.
- probe는 고정 이름·기존 image·비업무 포트 54329·`sleep` entrypoint만 사용했다.
- explicit probe는 patched CLI 대안이 기술적으로 가능함을 보여주지만 공급망 승인은 별도다.

## 13. 인수인계·재현·롤백

### 재현

1. `PortBindingBehavior`와 Docker Desktop/Engine 버전을 확인한다.
2. Supabase를 시작하지 말고 HostIP 미지정 disposable probe의 HostConfig/NetworkSettings를 inspect한다.
3. `::`, `0.0.0.0`, mixed binding이면 probe를 제거하고 즉시 중단한다.
4. Q-SEC-005 승인 뒤에만 정책 변경·완전 재시작·probe를 반복한다.
5. exact single `127.0.0.1` 뒤에만 `scripts/verify_database.ps1` normal path를 실행한다.

### 롤백

Docker Desktop을 완전히 종료하고 user settings의 `PortBindingBehavior` 키를 제거한 뒤 재시작한다.
repo rollback은 이 blocked docs commit을 revert한다. DB/data compensation은 필요 없다.

### 다음 개발자 시작점

먼저 Q-SEC-005/A-023 답변을 확인한다. 답변 전에는 Supabase DB를 시작하지 않는다. A 승인 시
`local-only-port-binding` 단일 변경과 complete restart 뒤 disposable probe부터 실행한다.

## 14. 남은 위험·미해결 질문·다음 단계

- A-023/Q-SEC-005 local completion blocker.
- A-021/Q-SEC-003 public-release blocker와 privileged function 21개 hardening.
- official seed/READY/chat/admin/backup/public deploy 미완료.
- off-device backup 없음과 단일 PC 손실 위험.
- 다음 단계: Q-SEC-005 인간 결정 → safe probe → full DB/root/static gate → independent review.

## 15. 자체 리뷰

- [x] 요청과 Q-SEC-004=A 적용 결과 기록
- [x] actual probe와 explicit control probe 실행·제거
- [x] source-of-truth/결정/모호성/계획/보고서/handoff 상태 동기화
- [x] 개인정보 원문·secret/env value 노출 없음
- [x] 버전·DB·데이터·공개 계약 불변
- [x] 구현 노트 INDEX 갱신
- [x] package/JSON/secret/diff/Markdown/protected-scope 정적 검증
- [ ] Q-SEC-005 답변 뒤 actual safe runtime/full gate
