# IMP-20260717-009 — Q-SEC-005 A local-only port binding and DB-001 completion

- Date/Time (KST): 2026-07-17T10:52:18+09:00
- Task ID: DB-001-T10-QSEC005
- Type: decision-security-implementation
- Status: Blocked — Q-SEC-005=A/D-030 applied; Q-SEC-006/A-024 human supply-chain decision required
- Author/Agent: Codex `/root`
- Branch: `codex/db-001-layered-enforcement`
- Base commit: `b94372a`
- Related plan/ADR/RFP: DB-001 plan/spec, ADR-0011, D-029/D-030, A-023/A-024,
  Q-SEC-005/Q-SEC-006, DAR-001/002/003, SER-001/002/003

## 1. 사용자 요청과 완료 기준

### 요청

사용자는 `Q-SEC-005: A`라고 명시해 Docker Desktop의 더 강한
`local-only-port-binding` 전역 설정, 완전 재시작, actual probe, 조건부 DB-001 계속 진행을
승인했다.

### Acceptance Criteria

- Docker Desktop의 `PortBindingBehavior` 한 값만 `local-only-port-binding`으로 바꾼다.
- Docker를 재시작하고 설정 유지와 Engine 28+를 확인한다.
- Supabase DB보다 먼저 HostIP 생략 disposable probe의 actual resolved binding을 확인한다.
- exact single `127.0.0.1`이 아니면 DB start/reset/status/credential/SQL 없이 중단한다.
- explicit `127.0.0.1` control로 원인 경계를 다시 확인하고 모든 probe를 제거한다.
- 승인과 실제 결과를 결정·모호성·source-of-truth·계획·보고서·handoff에 동기화한다.
- 제품 코드, 공개 계약, migration, 공식/mock data, manifest version을 변경하지 않는다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자 결정자, Codex `/root`; 독립 에이전트는 이전 사용량 한도로 이번 순차 runtime 작업에 참여하지 못함 |
| When — 언제 | 2026-07-17 KST, blocked-security checkpoint `b94372a` 뒤 |
| Where — 어디서 | Windows Docker Desktop 4.62.0/Engine 29.2.1 user settings, DB-001 isolated worktree |
| What — 무엇을 | Q-SEC-005=A/D-030 적용, Docker 재시작, HostIP 생략/explicit probe, 실패 원인과 Q-SEC-006 분리 |
| Why — 왜 | Supabase local PostgreSQL port가 IPv4·IPv6 외부 interface에 노출되지 않았음을 DB mutation 전에 증명하기 위해 |
| How — 어떻게 | offline settings 한 값 변경 → hidden Docker start → condition poll → 두 disposable `sleep` probe inspect/remove → fail closed |
| How much — 어느 정도 | 외부 설정 값 1개, probe 2개 생성·제거, persistent container/data 0, DB/제품 코드/migration/version 변경 0, 비용 0원 |

## 3. 시작 전 상태

- 관련 파일: ambiguity/decision/team decision, DB-001 plan/spec/report/handoff/TASKS,
  `scripts/verify_database.ps1`, 이전 IMP-008.
- 기존 동작: `default-local-port-binding`에서 HostIP 생략 publish가 actual
  `127.0.0.1`+`::`였고 explicit `127.0.0.1`만 단일 loopback이었다.
- 발견한 충돌/부채: stock Supabase CLI 2.109.1은 DB PortBindings의 HostIP를 비운다.
- Git 상태: clean `b94372a`에서 시작했다.
- Docker 시작 상태: Engine API는 내려가 있었고 container는 없었으며 설정은
  `default-local-port-binding`, 275 bytes, SHA-256
  `c8d6e9725d785fdb869201b6cf4ef07f2967e39c7e267c09e5f047920d8c07fa`였다.
- 개인정보/비밀: 질문·답변·DSN·API key·env value를 읽거나 출력하지 않았다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| A-023/Q-SEC-005 | Resolved decision, remediation insufficient | `local-only-port-binding` 전역 적용 | D-030, 설정 유지 | HostIP 생략 actual은 여전히 `127.0.0.1`+`::` |
| A-024/Q-SEC-006 | A/Blocker Human | explicit HostIP를 넣는 project-local patched CLI와 새 Go toolchain/source/diff/binary pin | 무응답 C: DB runtime 보류 | DB-001 Task 10, local tooling supply chain, manifest, 후속 DB dependency |
| A-021/Q-SEC-003 | B/High Deferred | privileged function 21개 public hardening | default B: local/private만 | public/remote release 차단 |

## 5. 설계 결정과 대안

### 선택

승인대로 `local-only-port-binding` 한 값을 적용하고 Docker Desktop을 재시작했다. HostIP 생략
probe가 exact gate에 실패해 Supabase runner는 실행하지 않았다. explicit control만 반복 통과해
남은 root cause를 stock CLI의 빈 HostIP 요청으로 좁히고 Q-SEC-006/A-024를 열었다.

### 이유

설정 이름이나 요청값이 아니라 Docker `NetworkSettings.Ports`의 actual mapping이 보안 경계다.
세 환경 보정이 같은 결과를 만들었고 explicit HostIP만 두 번 단일 loopback을 만들었으므로 guard를
완화하거나 네 번째 환경 변경을 추측으로 시도하지 않는다.

### 고려했지만 선택하지 않은 대안

- `127.0.0.1`+`::`를 안전으로 인정: IPv6 wildcard를 허용하므로 거부.
- Docker Desktop IPv4-only 전역 설정을 즉시 추가: 모든 새 network의 IPv6를 끄고 효과가
  미입증인 네 번째 환경 시도라 인간 결정 전 보류.
- patched CLI를 즉시 빌드: 현재 Go toolchain이 없고 새 source/build/binary 공급망이므로 인간 승인 전 보류.
- Windows Firewall만 신뢰: Docker actual single-loopback 계약을 충족하지 않아 거부.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `%APPDATA%/Docker/settings-store.json` | `PortBindingBehavior=local-only-port-binding`; 다른 7개 key 값 유지 | Q-SEC-005=A 실행 |
| ambiguity/decision/team/task/ADR | D-030, A-023 resolved-insufficient, A-024/Q-SEC-006 open | 인간 승인과 실패 효과 분리 |
| plan/spec/report/handoff/active guides | current blocker·probe·supply-chain gate 동기화 | stale “Q-SEC-005 unanswered” 제거 |
| IMP-009와 INDEX | 6W1H·명령·버전·보안·rollback 기록 | 요청별 구현 노트 의무 |

### 데이터 흐름/상태 변화

Docker Desktop user-level port policy만 바뀌었다. 두 probe는 기존 local Supabase PostgreSQL image로
`sleep`만 실행했고 즉시 제거했다. Supabase DB start/reset/status, credential provisioning, SQL,
seed, API, DeepSeek 호출은 0회다.

### 오류·빈 상태·롤백

- Docker Desktop hidden launcher PID는 먼저 종료됐지만 backend 두 개가 초기화 중이었고 약 38초 뒤
  Engine `29.2.1`이 응답했다. 임의 sleep 성공을 가정하지 않고 Docker API condition으로 확인했다.
- `local-only-port-binding`은 설정 파일/재시작 뒤 유지됐지만 actual IPv6 wildcard를 제거하지 못했다.
- 두 probe의 `finally` 제거 뒤 running/all/project container는 `0/0/0`이다.
- 현재 승인된 `local-only-port-binding`은 유지한다. rollback 요청 시 Docker를 완전히 종료하고
  이전 `default-local-port-binding` 한 값으로 복원한 뒤 재시작한다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.0 | 2.2.0 | 제품 범위 불변 |
| Repo guidance | 1.4.0 | 1.4.0 | DB/tooling 완료 아님 |
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
| settings JSON parse/key drift assertion | PASS | 8 key, setting 외 값 불변 | user settings store |
| settings before→after | `default-local` 275 bytes/`c8d6e9...07fa` → `local-only` 272 bytes/`a2830a...4fc8` | 값 1개 | file SHA-256 |
| Docker start + API condition poll | PASS | 약 38초, Engine 29.2.1 | Docker CLI |
| local probe image check | PASS | existing `public.ecr.aws/supabase/postgres:17.6.1.143`; pull 0 | Docker image inspect |
| HostIP omitted probe `-p 54329:5432` | requested `HostIp=""`; resolved `127.0.0.1:54329`+`:::54329` | FAIL exact-local; removed | Docker inspect |
| explicit control `-p 127.0.0.1:54329:5432` | requested/resolved exact single `127.0.0.1:54329` | PASS control; removed | Docker inspect |
| Go toolchain check | missing | `go` command unavailable | PowerShell |
| installed stock CLI check | version 2.109.1, executable SHA-256 `22c0f28f013411c7a7b880116cd33636edb955a64278914692eea010bcc98dc7` | read-only | `.tools/` |
| final Docker inventory | running/all/project `0/0/0`; Desktop running; `local-only-port-binding` | DB mutation 0 | Docker CLI |
| repo static verification | PASS | diff check, package required 12, secret finding 0, protected diff 0, manifest exact 4축, changed Markdown 27/control 0/broken link 0, current blocker refs 5 | Git/scripts |

### 미실행 검증과 이유

- `scripts/verify_database.ps1`: HostIP 생략 probe가 IPv6 wildcard를 남겨 실행 금지.
- pgTAP/rollback/replay/integration: reset 전 보안 gate가 통과하지 않아 실행 금지.
- root full gate: 제품 코드가 바뀌지 않았고 blocked documentation 정적 검증 뒤 체크포인트만 만든다.
- remote/public DB·배포·backup: 미승인·범위 밖.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 시민 질문·답변·transcript·PII·DSN·secret 접근/저장/출력 0.
- Security: `local-only` 전역 정책은 유지되지만 empty HostIP의 IPv6 wildcard 때문에 DB는 계속
  차단한다. exact guard는 완화하지 않았다.
- Accessibility: UI/제품 변경 없음.
- Performance/cost: local image probe 2회, 외부 API/유료 인프라 0원.

## 10. 데이터와 출처 영향

- 공식 데이터: 0, 변경 없음.
- mock/AI 생성: persistent 0, 변경 없음.
- schema/lineage: 6 forward+6 compensation byte 불변.
- 출처: Docker Desktop 4.62.0/Engine 29.2.1 actual inspect, Docker official settings/port docs,
  repository-pinned Supabase CLI 2.109.1.
- verified date: 2026-07-17 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Q-SEC-005=A는 정확히 적용됐지만 exact local을 달성하지 못했다.
- Q-SEC-006/A-024에서 official v2.109.1을 최소 patch하고 새 Go local toolchain·source tag/commit·
  diff·binary hash를 pin하는 공급망을 승인할지 결정해야 한다.
- 무응답 시 `local-only-port-binding`을 유지하되 Supabase DB와 후속 DB 작업은 차단한다.
- A-021/Q-SEC-003 기본값 B 때문에 이 blocker가 해결돼도 public/remote release는 금지된다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- HostIP omitted requested mapping과 Docker resolved mapping은 별도 경계다.
- explicit control의 반복 성공은 API/DB schema가 아니라 CLI create request가 남은 원인임을 보여준다.
- patched CLI가 승인되더라도 변경은 DB PortBinding HostIP 한 위치, exact source/diff/hash allowlist,
  actual probe와 runner gate로 제한해야 한다.

## 13. 인수인계·재현·롤백

### 재현

1. `PortBindingBehavior=local-only-port-binding`, Engine 29.2.1, container 0을 확인한다.
2. Supabase를 시작하지 말고 HostIP omitted disposable probe를 inspect한다.
3. actual `127.0.0.1`+`::`를 확인하고 probe를 제거한다.
4. explicit `127.0.0.1` control의 단일 mapping을 확인하고 제거한다.
5. Q-SEC-006 답변 전 DB start/reset을 실행하지 않는다.

### 롤백

Docker Desktop을 완전히 종료하고 user settings의 `PortBindingBehavior`를
`default-local-port-binding`으로 되돌린 뒤 재시작한다. repo rollback은 이 blocked docs commit을
revert한다. DB/data compensation은 필요 없다.

### 다음 개발자 시작점

먼저 Q-SEC-006/A-024 답변을 확인한다. A 승인 전에는 Go 설치, CLI source clone/build/patch,
Supabase DB start/reset을 하지 않는다. A 승인 시 source/diff/toolchain/binary pin 계획과 TDD test를
먼저 작성하고 explicit actual probe 뒤에만 full DB gate를 실행한다.

## 14. 남은 위험·미해결 질문·다음 단계

- A-024/Q-SEC-006 local tooling supply-chain blocker.
- A-021/Q-SEC-003 public-release blocker와 privileged function 21개 hardening.
- official seed/READY/chat/admin/backup/public deploy 미완료.
- off-device backup 없음과 단일 PC 손실 위험.
- 다음 단계: Q-SEC-006 인간 결정 → 조건부 CLI source/toolchain TDD → exact probe → full DB/root gate.

## 15. 자체 리뷰

- [x] 요청과 Q-SEC-005=A 적용 결과 기록
- [x] actual omitted probe와 explicit control 실행·제거
- [x] 개인정보 원문·secret/env value 노출 없음
- [x] 버전·DB·데이터·공개 계약 불변
- [x] 구현 노트 INDEX 생성
- [x] blocked-state active docs 정적 검증과 INDEX 상태 갱신
- [ ] Q-SEC-006 답변 뒤 actual safe runtime/full gate
