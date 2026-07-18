# DB-001 발견 감사와 안전 설계 인터뷰

- 기준 commit: 2a4e26b
- 감사일: 2026-07-16 KST
- 현재 상태: Q-DB-002/Q-SEC-006/Q-TOOL-001과 수정 계획 승인 완료; DB-001 구현·검증 완료,
  `database_schema=0.3.0-local` disposable local/private 기준선 활성. A-021/Q-SEC-003은 별도 public-release blocker
- 역사적 감사 범위: 2026-07-16 문서·논리 SQL·로컬 도구 상태의 읽기 전용 감사. 이후 결과는 10~14절에 append-only 기록

## 1. 결론

DB 실행 기술은 Docker local stack과 Supabase CLI 버전 SQL로 확정됐고, 2026-07-16 사용자는 안전 불변조건을 DB와 백엔드 양쪽에서 강제하는 접근 A와 그 서면 설계 명세를 승인했다. [DB-001 실행계획](../superpowers/plans/2026-07-16-db-001-layered-enforcement.md)의 별도 사용자 승인 전에는 CLI 설치·image pull·container 시작·migration 생성/적용을 하지 않는다.

추천은 접근 A다. 승인 전환·보관 파기·상태 전이는 DB function/trigger와 제약으로 원자적으로 강제하고, RLS/GRANT로 브라우저 역할을 차단하며, 백엔드에서도 같은 정책을 이중 검증한다.

## 2. 실제 저장소 상태

| 영역 | 실제 상태 | 판정 |
|---|---|---|
| 논리 스키마 | database/schema-v1.draft.sql 0.2.0-draft | 참고본이며 실행 금지 |
| 객체 수 | enum 6개, table 8개, index 5개 | 실제 CREATE 문 기준 |
| 실행 계보 | supabase/migrations 없음 | 미구현 |
| local config/test | supabase/config.toml과 supabase/tests 없음 | 미구현 |
| 권한 | RLS/POLICY/GRANT/REVOKE 없음 | backend-only 미충족 |
| 승인 전환 | 원자적 DB function/trigger 없음 | race/direct-write 방어 없음 |
| 보관 파기 | 30일 check만 있고 purge function/job 없음 | 실행·멱등성 미구현 |
| Supabase CLI | PATH·package·.tools에 없음 | 미설치 |
| Docker | 29.2.1 Linux engine은 2026-07-16 host 검증에서 정상 | stack 시작은 미실행 |
| seed | official/mock 모두 not-populated | ready=503 유지 |

실제 SQL의 CREATE 문을 기준으로 kb_documents, kb_question_examples, offices, office_service_mappings, interaction_events, failed_questions, kb_candidates, audit_logs의 8개 table을 확인했다.

## 3. 비협상 데이터 경계

- local/private DB만 사용하며 remote link·db push는 별도 승인 전 금지한다.
- 시민 검색은 ACTIVE KB만 허용한다.
- raw 질문·답변 transcript·context token·IP·기기 ID를 DB에 저장하지 않는다.
- OUT_OF_SCOPE 질문 텍스트는 어떤 table에도 저장하지 않는다.
- FOLLOWUP은 실패가 아니므로 failed_questions 행을 만들지 않는다.
- PERSONAL_LOOKUP과 LEGAL_JUDGMENT는 source-of-truth가 허용한 경우에만 보수적으로 마스킹한 텍스트를 최대 30일 저장할 수 있으며 candidate_eligible은 false다.
- masked_question은 created_at+30일에 NULL로 만들고 행·비텍스트 메타데이터·후보 연결은 유지한다.
- 작성자는 자기 후보를 승인할 수 없다.
- 공식 출처·확인일·별도 승인자가 완비된 ACTIVE만 시민 경로에 노출한다.
- 승인 seed가 없으므로 DB 연결만 성공해도 ready=200으로 바꾸지 않는다.

## 4. 구현 전에 닫아야 할 공백

1. public schema 직접 노출 여부와 anon/authenticated 차단 방식
2. 후보 승인→ACTIVE 생성→감사 로그를 한 transaction으로 묶는 함수 계약
3. 직접 write가 상태 머신과 자기 승인 금지를 우회하지 못하게 할 trigger/check
4. retention purge 함수의 경계시각·멱등성·고정 search_path·복구 후 재실행
5. rollback SQL 저장 위치와 destructive 실행 승인 gate
6. reset/replay, pgTAP 권한 테스트, synthetic-only fixture
7. logical draft version과 timestamp migration lineage·manifest version의 관계

전체 정규화는 이번 DB-001에서 보류한다. 출처·actor·감사 데이터를 추가 table로 광범위하게 분해하는 작업은 현재 20건 MVP의 안전 불변조건을 먼저 닫은 뒤 실제 필요 증거가 생길 때 검토한다.

## 5. 선택지

### 접근 A — DB 원자성 + backend 이중 검증

- DB function이 후보 row를 잠그고 actor/role/status/공식 필드/별도 승인자를 검사한 뒤 ACTIVE KB·후보 상태·감사 로그를 한 transaction에서 변경한다.
- trigger/check가 우회 쓰기를 차단하고 RLS/GRANT는 anon/authenticated를 거부한다.
- backend service도 같은 정책을 검증하고 안전한 오류로 변환한다.
- 장점: race와 직접 SQL 우회에 강하다.
- 단점: SQL·migration·rollback 테스트가 늘어난다.

### 접근 B — backend 중심

- DB는 기본 FK/check/RLS/GRANT만 두고 승인·파기·감사 transaction을 application service가 수행한다.
- 장점: Python 코드에서 단순하고 빠르다.
- 단점: 다른 writer와 직접 DB write의 정책 우회·race 위험이 더 크다.

추천과 답변 부재 기본값은 접근 A다.

결정: 2026-07-16 사용자 답변 `Q-DB-002: A`. D-025와 ADR-0011에 반영했다.

## 6. Q-DB-002

Q-DB-002. 승인·보관·권한 불변조건을 DB와 백엔드 중 어디까지 강제할지 결정
- 왜 지금 필요한가: 답에 따라 migration의 function/trigger/RLS/GRANT, repository API, transaction·rollback·테스트 구조가 달라지며 잘못 고르면 자기 승인·미승인 ACTIVE·30일 파기 누락을 직접 SQL로 우회할 수 있다.
- 선택지 A / 장점 / 단점: DB function/trigger/RLS/GRANT로 원자적으로 강제하고 백엔드도 이중 검증 / 모든 writer와 race에 강함 / SQL과 migration 테스트가 늘어남.
- 선택지 B / 장점 / 단점: DB는 기본 제약·권한만 두고 백엔드 transaction을 중심으로 강제 / Python에서 단순하고 빠름 / 직접 DB write와 동시성 우회 위험이 더 큼.
- 당신의 추천안: A. 공공 민원 데이터의 승인·보관 경계는 DB에서 우회 불가능하게 하고 백엔드는 사용자 친화 오류와 방어적 검증을 담당한다.
- 답을 받지 못할 때 사용할 기본값: A를 설계안으로 기록하되 migration·container·데이터 적용은 시작하지 않는다.
- 영향을 받는 파일·계약·데이터·배포: supabase/config.toml, supabase/migrations, supabase/tests, database/rollbacks, API repository/service, TASKS, manifest, local backup/restore; 공개 API wire와 원격 배포는 변경하지 않는다.

답변 예시: Q-DB-002: A — DB에서 승인·파기·권한을 원자적으로 막고 백엔드도 이중 검증해줘.

## 7. 도구 설치 추천과 공식 근거

- 구현 직전에 공식 release metadata에서 exact stable version을 다시 확인한다. 감사 시점의 숫자를 미리 고정하지 않는다.
- Windows amd64 공식 release asset을 .tools/supabase/<exact-version>에 두고 release SHA-256 digest를 tracked bootstrap manifest에 고정해 exact 비교한다.
- 공식 digest를 독립 확인할 수 없으면 설치를 중단한다. latest·beta·global npm install은 사용하지 않는다.
- 현재 pnpm install은 ignore-scripts이므로 CLI postinstall에 기대지 않는 공식 binary bootstrap을 우선한다.
- 사용자가 [DB-001 실행계획](../superpowers/plans/2026-07-16-db-001-layered-enforcement.md)을 승인한 뒤에만 install, image pull, supabase init/start를 수행한다.
- stack 출력에는 local secret key가 포함될 수 있으므로 원문을 구현 노트·로그에 전달하지 않는다.

공식 링크:

- https://supabase.com/docs/guides/local-development
- https://supabase.com/docs/guides/local-development/cli/getting-started
- https://supabase.com/docs/guides/deployment/database-migrations
- https://supabase.com/docs/reference/cli/supabase-db
- https://github.com/supabase/cli/releases

## 8. 향후 DB-001 인수 기준

- empty local DB reset/replay와 명시적 보상 rollback/replay가 통과한다.
- 승인 function은 자기 승인·잘못된 role/status·공식 필드 누락을 거부하고 성공 시 ACTIVE KB·후보·감사 로그를 원자적으로 일치시킨다.
- anon/authenticated direct access는 0이고 backend 역할만 최소 권한을 가진다.
- OUT_OF_SCOPE text 0, FOLLOWUP failed row 0, raw 질문 0을 확인한다.
- PERSONAL_LOOKUP/LEGAL_JUDGMENT 텍스트를 개선 분석상 필요한 경우에만 마스킹해 저장할 수 있다. 저장한 경우 candidate=false이며 30일 경계의 NULL 파기가 멱등 동작하고, 미저장도 허용한다.
- ACTIVE 시민 노출은 공식 승인 record만 가능하고 official/mock seed 0이면 ready=503이다.
- backup restore 후 서비스 개방 전에 retention purge를 재실행한다.
- 적용 전 SQL·rollback·권한 matrix를 인간에게 제시해 승인받는다.

## 9. 이번 감사의 변경·비변경

발견 문서·레지스터·백로그·상태 문서만 갱신한다. 제품 코드, 공개 계약, 논리 SQL, migration, DB, seed, env, key, container, image, 외부 서비스는 변경하거나 실행하지 않는다.

## 10. 현재 상태 추가 기록 — 2026-07-16 KST

1~9절은 기준 commit `2a4e26b` 당시의 역사적 발견 증거로 보존한다. 이후 사용자는 DB-001 실행계획과 Q-SEC-002=A/Q-WF-001=A를 승인했고, Tasks 0~5에서 pinned local CLI와 migration `00100`~`00300`을 구현·검증했다. 현재 migration은 3/5이며 기존 172/172 pgTAP 검증 결과는 구현 노트 008에 기록돼 있다. 적용된 세 migration은 수정하지 않고 Task 6은 새 `00400` workflow migration, Task 7은 `00500` read/index migration으로 진행한다. 공식/mock seed는 여전히 0이고 `/ready=503` 경계는 유지된다.

## 11. Local baseline 후보 차단 상태 추가 기록 — 2026-07-17 KST

1~10절은 각 기준 시점의 역사적 발견/진행 증거로 보존한다. 이후 `00100~00500`을
수정하지 않고 `00600` validator posture correction을 추가해 forward/compensation 각 6개,
7 enum·8 table, pgTAP 282, backend integration 8/8, 역순 compensation/absence/reset/replay와
synthetic 8-table zero를 과거 실행에서 검증했다. 그러나 Task 10 quality review가 actual Docker
port의 wildcard publish를 발견했고 fail-closed runner가 reset 전에 중단했으므로 이 결과는
현재 local baseline 완료 증거가 아니다. manifest는 `database_schema=0.2.0-draft`를 유지하고
`0.3.0-local`은 Q-SEC-006=A/D-031의 patched CLI 구현 뒤 exact loopback/full gate를 통과해야 하는 후보다.
공식/mock seed는 0, `/ready=503`은 계속 정상이다. 상세 증거는
`docs/test-reports/DB-001-LOCAL-BASELINE.md`와
`docs/handoffs/HANDOFF-20260717-DB-001-LOCAL-BASELINE.md`에 있다.

A-024/Q-SEC-006의 인간 결정은 A/D-031/ADR-0013으로 해결됐다. Q-SEC-004=A/D-029와
Q-SEC-005=A/D-030의 두 Docker Desktop 보정은 actual IPv6 wildcard를 남겨 완료 근거가 아니다.
명시적 `127.0.0.1` control만 단일 loopback이었고 로컬 Go toolchain은 아직 없다. 서면 설계·별도
실행계획·source/toolchain/binary hash·actual full gate 전까지 DB runtime과 manifest 승격을
차단한다. A-021/Q-SEC-003은 별도 public-release blocker다.
미응답 기본값 B에 따라 remote/public 배포, public admin/API, public backend DB credential을
차단하며 `00700`은 인간 결정 전 구현하지 않는다.

## 12. Q-SEC-006 구현 중 Windows build workspace blocker — 2026-07-18 KST

Task 1은 exact source/patch contract, Task 2는 PS5.1 bootstrap, Task 2A는 다중 `git.exe`
결과의 단일 PATH application 선택, Task 2B는 checkout-local `core.longpaths=true`를 구현했고
각 task가 focused/full regression과 독립 review를 통과했다. 실제 Task 3은 official Go 1.25.11,
exact origin/tag object/peeled commit, 두 checkout, local longpaths, exact 2-file patch와 module
boundary까지 전진했다. 별도 exact pinned diagnostic `go build`도 exit 0과 약 103 MB executable을
만들어 source/patch/compiler 계약 자체가 유효함을 확인했다. 이 diagnostic output은 runtime pin이
아니며 사용하지 않는다.

이후 bounded full retry는 `VERIFY-SUPABASE-SOURCE-A operational code=2`로 중단됐다. 실제 상태는
source A의 `.git`만 제거되고 extended-length 열거 기준 3,035 files와 관측 최대 299자 tracked file이
남았으며 source B는 exact HEAD와 local
longpaths를 유지했다. production `Remove-OwnedPath`는 safe-child/reparse validation 뒤 PowerShell
5.1 `Remove-Item -Recurse -Force`를 사용한다. 따라서 재실행의 기존 checkout cleanup이 장경로에서
부분 실패한 것이 확정 원인이다. tracked Git은 clean, final/candidate/runtime manifest는 없고
containers all/project 0/0, DB mutation 0이다.

세 번째 별도 tooling boundary이므로 임의 native delete나 build-root 변경을 구현하지 않았다.
A-025/Q-TOOL-001에서 short project-local checkout root(추천), native long-path deletion, container/WSL
build를 비교한다. 인간 결정·계획/ADR 갱신·TDD/review 뒤에만 Task 3을 재개한다. DB schema 0.2.0-draft,
official/mock data 0, `/ready=503`, public-release blocker A-021은 그대로다.

## 13. Q-TOOL-001=A 결정과 수정 계획 — 2026-07-18 KST

사용자는 `Q-TOOL-001: A`를 명시했다. D-032/ADR-0014에 따라 두 generated checkout만
`.tools/s/a`, `.tools/s/b`로 줄이고 source manifest가 tool-root-relative `s/a`, `s/b`, pinned
maximum relative file path 134자, maximum absolute file path 248자를 고정한다. 현재 exact worktree에서
longest upstream file의 투영 absolute path는 244자다. bootstrap은 cleanup·directory 생성·Go archive
download/extraction·network fetch 전에 두 destination의 projected maximum을 검증하고 초과 시
fail closed해야 한다.

Win32 extended-length delete, Docker/WSL build, global Git setting, sparse checkout/path exclusion은
도입하지 않는다. 기존 `.tools/supabase-source/6d4c19870ed213ba7f682f117d0345c8a40bfa94/`
partial tree는 runtime authority가 아니며 새 bootstrap이 checkout/build input으로 사용하거나 자동 삭제하지 않는다. 수정 계획 승인,
Task 2C TDD와 독립 review 뒤에만 Task 3을 재개한다. API/DB schema/migration/data/privacy/dependency,
containers 0/0, `/ready=503`, A-021 public blocker는 변하지 않는다.

## 14. Patched runtime과 fresh local 기준선 검증 — 2026-07-18 KST

사용자는 수정 계획을 `수정 계획 승인, 구현 시작`으로 승인했다. 이후 short checkout/path-budget,
source/patch/runtime manifest 분리, 두 독립 build의 동일 SHA-256, patched-only DB runner를 구현했다.
tracked source manifest SHA-256은
`c293e5ac32bae030eadf383d8d9511dc16eac834e51e996273ae8b7e39616657`, 1,824-byte patch는
`109c096480e8185d761e9ce8fba10e93efc55190c42eab978f769a6993833f7d`, 103,027,200-byte runtime은
`751068e73834c5da58ac7c5287a1d66a82ad356f508637b0478d6531cdb3941c`다. stock CLI와 legacy
partial tree는 입력·삭제 대상으로 사용하지 않았다.

2026-07-18 fresh disposable gate는 Docker Engine 29.2.1에서 `NetworkSettings.Ports`와
`HostConfig.PortBindings` 모두 정확히 하나의 `127.0.0.1:54322 -> 5432/tcp`를 확인했다.
첫 reset/pgTAP, 6개 compensation newest-first, absence proof, 두 번째 reset/replay/pgTAP,
backend integration 8/8이 통과했다. 현재 SQL suite는 6 files/282 assertions이며 final
project/all container count는 0/0, volume delete/prune은 0회다. root gate, package validator,
secret scan, combined tooling 73/73와 protected-path diff도 통과했다.

따라서 DB-001은 `database_schema=0.3.0-local`의 disposable local/private 기준선으로 완료됐다.
이 승격은 새 migration/schema/data/API/dependency 변화가 아니라 기존 six-migration executable
authority의 actual local 검증 결과다. 공식/mock seed는 0이고 `/ready=503`이 정상이다.
A-021/Q-SEC-003 기본값 B, remote/public/admin/API/backend credential/`00700` 차단은 그대로다.
이후 runner descendant cleanup finding은 `73f300b`에서 bounded process tree로 보정됐다. focused
1/1, runner 50/50, patched 24/24, 독립 review 0/0/0과 102.746s final-code DB gate가 통과했고 exact
loopback·container 0/0·volume/prune 0을 재확인했다. 최종 closeout docs reviews는 진행 중이다.
