# IMP-20260720-008 — Q-SEED-002 A·Q-PII-002 A·Q-SEC-003 A 결정과 successor correction 계획

- Date/Time (KST): 2026-07-20T20:44:30+09:00
- Task ID: DATA-SEED-002-DESIGN-PLAN
- Type: decision-architecture-planning-security
- Status: Decision-only Done / DATA-SEED-002 specification and plan in Review
- Author/Agent: human product owner; Codex `/root`; read-only audit agents `decision_crosscheck`, `seed_successor_audit`
- Branch: main
- Base commit: f9af78d
- Related plan/ADR/RFP: D-044, D-045, D-046; ADR-0004, ADR-0017, ADR-0018; `docs/superpowers/specs/2026-07-20-data-seed-002-successor-release-correction-design.md`; `docs/superpowers/plans/2026-07-20-data-seed-002-successor-release-correction.md`; SFR-006, DAR-003, SER-002

## 1. 사용자 요청과 완료 기준

### 요청

- `Q-SEED-002=A`: immutable `.1`을 수정하지 않고, PostgreSQL 17 membership-option 판정을 교정한 successor `.2` release를 설계한다.
- `Q-PII-002=A`: 마스킹이 안전하게 완료되지 않으면 향후 시민 API가 HTTP 200의 `PRIVACY_UNRESOLVED` 안전 응답을 반환하도록 결정한다.
- `Q-SEC-003=A`: SECURITY DEFINER 함수 22개의 고정 `search_path` hardening을 확정하되 `00700` 구현은 public 준비 단계까지 보류한다.
- 세 결정을 권위 문서에 반영하고 Q-SEED-002 명세와 실행계획을 작성한다.

### Acceptance Criteria

- 세 결정이 결정 로그, ADR, 모호성 레지스터, source-of-truth와 운영·보안 문서에서 같은 의미로 표현된다.
- Q-SEED-002는 `.1`과 v1 schema를 byte-immutable하게 보존하고 `.2`의 식별자, lineage, schema, SQL 의미론, 상태 전이, 검증 절차를 재현 가능하게 고정한다.
- 후속 실행계획은 TDD, 독립 검토, 실제 PostgreSQL 17 전체 cycle, rollback과 문서 동기화를 포함한다.
- 이번 요청에서는 제품 코드, 공개 계약, DB schema/migration, 공식 release, seed dispatcher를 변경하지 않는다.
- Q-PII-002의 소비자 계약·DB 변경과 Q-SEC-003의 `00700`은 별도 승인 경계로 남긴다.
- 구현 노트와 INDEX, 버전 매니페스트를 갱신하고 저장소 검증을 통과한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 인간 제품 책임자가 A/A/A를 확정했고 Codex와 두 read-only audit agent가 반영·교차검토했다. 실제 `.2` 실행의 데이터 작성 책임은 AI/Data·Backend, 승인 책임은 PM(`PM-LOCAL-001`)이다. |
| When — 언제 | 결정 효력 시각은 2026-07-20T20:41:24+09:00(11:41:24Z), 문서 작업은 2026-07-20 KST에 수행했다. DATA-SEED 완료 목표는 2026-07-20이며 실제 실행은 별도 계획 승인 뒤다. |
| Where — 어디서 | source-of-truth, decision/ADR, security/privacy/operations, data-lineage, Q-SEED spec/plan, tasks/version/note 문서만 변경했다. |
| What — 무엇을 | successor `.2`, privacy fail-closed 소비자 결과, public-prep security hardening의 세 결정을 기록하고 DATA-SEED-002의 실행 가능한 명세와 계획을 만들었다. |
| Why — 왜 | `.1`의 단일-row membership 판정이 PostgreSQL 17에서 역할 옵션이 여러 membership row로 나뉘는 합법적 상태를 거부하지만 승인된 immutable release는 덮어쓸 수 없기 때문이다. 동시에 PII 실패와 public hardening 경계를 확정해 이후 구현의 임의 해석을 막기 위해서다. |
| How — 어떻게 | 권위 순서와 실제 파일·해시·migration·pgTAP을 대조하고, immutable successor profile/v2 schema/정확한 세 `EXISTS` 판정/TDD 실제 DB cycle을 문서화했다. |
| How much — 어느 정도 | 결정 3건, 신규 ADR 2건, Q-SEED spec 1건, 6-task 계획 1건과 관련 활성 문서를 동기화했다. 코드·계약·DB·공식 데이터는 0건 변경했고 새 비용·의존성은 없다. |

## 3. 시작 전 상태

- 관련 파일: `scripts/data_seed_sql.py`, `scripts/verify_data_seed_db.py`, `scripts/verify_data_seed.ps1`, `supabase/migrations/20260716000300_capabilities_and_functions.sql`, `supabase/tests/database/003_capabilities_test.sql`, `.1` release와 v1 schemas, active contracts/DB/privacy/security 문서.
- 기존 동작: `.1`은 19 KB/3 office/10 mapping의 승인된 immutable release이며 `supabase/seed.sql`과 byte-identical하다. 로컬 DB는 empty-seed라 readiness 503이고 official data version은 `0.0.0-not-populated`이다.
- 발견한 충돌/부채: 생성기와 verifier는 membership option 세 개가 한 row에 함께 있어야 한다고 판정하지만 migration은 옵션별 row의 합집합을 인정한다. 현재 pgTAP은 관측된 두-row 상태는 통과하나 `INHERIT+SET`을 한 row에 묶는 narrower predicate다. PostgreSQL 17의 합법적 분리 membership에서 실제 cycle이 차단되며 후속 plan은 pgTAP도 migration 의미로 정렬한다.
- Git 상태: 원격 없는 `main`, 기준 commit `f9af78d`; 작업 시작 전의 관련 코드·release는 유지하고 문서 변경만 축적했다.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-SEED-002 / D-044 | A/Blocker → resolved | `.1` 덮어쓰기와 `.2` successor 중 선택 | A: `.1`·v1 불변, `.2` 신규 release | data release identity, generator/verifier, dispatcher, readiness |
| Q-PII-002 / D-045 | B/High → resolved | 마스킹 미해결 시 시민 API 결과 | A: 향후 HTTP 200 `PRIVACY_UNRESOLVED`; 원문·failed row·provider 호출 없음 | 공개 API, DB enum/function, interaction semantics |
| Q-SEC-003 / D-046 | B/High → resolved/deferred | 22개 privileged function의 `search_path` | A 확정, `00700`은 public 준비 단계로 보류 | migration, pgTAP, public deployment gate |
| 실행 승인 | Human gate | Q-SEED-002 계획 실행 여부 | 이번 요청은 명세·계획까지만; 사용자 승인 전 실행 금지 | code, data, DB actual cycle |

## 5. 설계 결정과 대안

### 선택

- DATA-SEED: correction lineage를 가진 immutable `.2`를 신규 생성하고 `.1`·v1 schema를 그대로 보존한다.
- PII: future consumer는 안전 완료가 아니면 정상 답변 대신 명시적인 `PRIVACY_UNRESOLVED`를 반환한다.
- Security: 22개 함수에 property-only fixed `search_path` migration을 적용하기로 결정하되 public 준비 단계까지 실행하지 않는다.

### 이유

- 이미 승인·해시 고정된 release를 수정하면 감사 가능성과 rollback 기준이 무너진다.
- 개인정보 마스킹 불확실성을 일반 grounding fallback으로 숨기면 보안 사건과 지식 부족을 구별할 수 없다.
- privileged function hardening은 public 전 필수지만 현재 local-only slice에 끼워 넣으면 Q-SEED 실행 범위를 불필요하게 확장한다.

### 고려했지만 선택하지 않은 대안

- `.1` in-place 수정: 승인·해시·lineage 불변성을 훼손하므로 배제했다.
- privacy 실패를 500 또는 기존 4개 fallback 중 하나로 매핑: 시민 UX와 운영 관찰성 중 하나를 희생하고 실패 의미를 왜곡하므로 배제했다.
- `00700` 즉시 구현: 결정은 필요하지만 이번 successor seed 문서 작업과 독립적이며 사용자가 public 준비 단계로 보류를 명시했다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| decision/ADR/ambiguity | D-044~046, ADR-0017/0018와 ADR-0004 addendum, resolved 상태 | 인간 결정의 단일 추적 경로 확보 |
| source-of-truth·security/privacy·operations | 결정과 현재 미적용 경계를 동기화 | 확정 의도와 현재 runtime을 혼동하지 않기 위해 |
| Q-SEED specification | `.2` identity, predecessor hashes, v2 schema, membership union, state machine, rollback 고정 | 실행자의 재해석 방지 |
| Q-SEED plan/TASKS | 6개 TDD task, dependency, acceptance, actual DB cycle, review gate | 승인 뒤 바로 실행 가능한 순서 제공 |
| version/changelog/index/note | product spec·docs 버전과 변경 계보 갱신 | 인수인계와 감사 가능성 |

### 데이터 흐름/상태 변화

이번 요청에서 runtime 상태 변화는 없다. 계획 승인 뒤 후보 `.2`를 격리 생성·검증하고, 기술 검토와 PM 승인 근거를 결합한 후 canonical publish → dispatcher activate → 실제 DB seed/verify/replay/cleanup/readiness cycle 순서로 진행한다.

### 오류·빈 상태·롤백

- 현재 empty-local과 readiness 503을 유지한다.
- `.2` 실행 중 canonical publication 전 실패하면 owned candidate만 폐기한다. dispatcher 교체 자체가 실패하면 captured exact `.1` byte로 복구한다. `.2`가 정상 활성화된 뒤 actual DB 검증이 실패하면 known-broken `.1`로 되돌리지 않고 `.2` release와 dispatcher를 보존하며 `official_data`만 미승격 상태로 둔다. 이후 artifact 결함은 별도 승인된 `.3`으로 교정한다.
- 문서 결정 철회는 새 결정/ADR supersession으로 기록하며 역사 기록을 덮어쓰지 않는다.

## 7. 버전 전후

### 생성 시 매니페스트
- product_spec: 2.2.3
- repo_guidance: 1.5.0
- application: 0.3.0-pii-core
- web: 0.2.0-static-chat-shell
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.3.0-local
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 0.9.0-pii-core
- documentation: 2.7.11

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.3 | 2.2.4 | 세 결정과 successor correction 명세 |
| Application | 0.3.0-pii-core | 동일 | runtime 미변경 |
| Web | 0.2.0-static-chat-shell | 동일 | UI 미변경 |
| API | 2.0.1-draft | 동일 | Q-PII consumer contract 미적용 |
| Shared contracts | 0.2.1 | 동일 | 공개 계약 미변경 |
| DB schema | 0.3.0-local | 동일 | migration 미추가 |
| Official data | 0.0.0-not-populated | 동일 | `.2` 미생성·미활성화 |
| Mock data | 0.0.0-not-populated | 동일 | mock 미변경 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM 경로 미변경 |
| Test suite | 0.9.0-pii-core | 동일 | 테스트 코드 미변경 |
| Docs | 2.7.11 | 2.7.12 | 결정·ADR·명세·계획·인수인계 동기화 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| 권위 문서·코드·schema·migration·release 해시 감사 | PASS | `.1` 7 artifacts, v1 schemas 4 artifacts, 19/3/10 | 본 노트와 successor spec의 immutable baseline 표 |
| `git diff --exit-code --` protected runtime paths | PASS | exit 0 | 최종 작업 로그 |
| `python -m json.tool versions/manifest.json`; package validator | PASS | manifest 1, required files 12 | 최종 작업 로그 |
| secret-pattern scan | PASS | exit 0 | 최종 작업 로그 |
| `scripts/verify.ps1 -Offline` | PASS | 모든 emitted step PASS, `verification=complete` | 최종 작업 로그 |
| 독립 명세·계획 기술 리뷰 | PASS | Critical/Important/Minor 0/0/0 | `qseed_plan_review` final rereview |
| 독립 결정·권위 문서 일관성 리뷰 | PASS | Critical/Important/Minor 0/0/0 | `decision_sync_review` final rereview |

### 미실행 검증과 이유

- successor `.2` 생성, DB seed/replay/cleanup/readiness는 사용자에게 명세·계획 승인만 요청받은 단계이며 실행 승인 전이므로 수행하지 않았다.
- Q-PII consumer contract/DB migration과 Q-SEC `00700` pgTAP도 각각 별도 구현 승인 경계에 있어 실행하지 않았다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: Q-PII-002 안전 실패 의미를 확정했지만 runtime·저장·외부 전송 동작은 바꾸지 않았다. 질문 원문이나 개인정보를 문서에 넣지 않았다.
- Security: Q-SEC-003 hardening을 public 필수 gate로 결정했으나 migration은 보류했다. 현재 public 배포 금지 상태는 유지된다.
- Accessibility: 사용자 UI 변경이 없어 영향이 없다.
- Performance/cost: 문서 변경뿐이며 새 dependency, 외부 API 호출, 운영 비용이 없다. 후속 실제 cycle은 local Docker/PostgreSQL 17을 사용한다.

## 10. 데이터와 출처 영향

- 공식 데이터: 기존 `.1` 19 KB/3 office/10 mapping과 승인 manifest/hash를 읽기만 했고 수정·재발행하지 않았다. `.2`는 아직 존재하지 않는다.
- mock/AI 생성: mock 데이터 없음. 후속 `.2`는 내용 자체를 새로 생성하는 것이 아니라 승인된 `.1` content를 correction lineage로 재포장하며 `시연용 샘플` 경계를 그대로 보존해야 한다.
- schema/lineage: v1은 immutable. 후속 v2 release-manifest schema가 predecessor `.1`, predecessor manifest SHA-256, D-044, correction code를 강제한다.
- verified date: 기존 content approval의 날짜·검토자는 보존하며 이 요청의 결정 효력 시각은 2026-07-20T20:41:24+09:00이다.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 이번 요청은 세 결정을 확정하고 명세·계획을 작성한 단계다. `.2` release 생성이나 DB 실행은 아직 하지 않았다.
- Q-SEED-002 실행 전 새 명세와 계획에 대한 인간 승인이 필요하다. 승인 문구 예: `명세·계획 승인, Q-SEED-002 구현 시작`.
- Q-PII-002는 정책만 확정됐다. 향후 공개 API와 DB enum/function을 함께 변경하는 consumer 명세·forward migration 승인이 별도로 필요하다.
- Q-SEC-003은 구현 방향까지 확정됐지만 `00700`은 public 준비 단계로 의도적으로 보류됐다. 그 전에는 public 배포할 수 없다.
- 공식 data approval 주체는 PM(`PM-LOCAL-001`), 작성 영역은 AI/Data·Backend이며 자기승인 금지 원칙을 유지한다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- successor profile 자료구조, schema dispatch helper, fixture 이름, 테스트 파일 분리는 승인된 계약·해시·상태 머신을 지키는 범위에서 구현 에이전트가 결정할 수 있다.
- 문서 링크·명명·formatting과 결정적 timestamp 주입 방식은 비공개 구현 세부다.

## 13. 인수인계·재현·롤백

### 재현

1. 권위 순서대로 source-of-truth, D-044~046, ADR-0017/0018, Q-SEED spec과 plan을 읽는다.
2. `.1` release 및 v1 schema의 크기·SHA-256을 spec 표와 대조한다.
3. 생성기/verifier의 단일-row 판정, migration의 세 `EXISTS`, pgTAP의 현재 `INHERIT+SET` 결합 predicate를 비교한다.
4. `versions/manifest.json`, `TASKS.md`, ambiguity register에서 현재 상태가 `.2` 미실행·public blocked인지 확인한다.

### 롤백

- 아직 runtime이나 데이터 변경이 없으므로 이 문서 변경 commit을 revert하면 된다.
- 결정 자체를 번복해야 한다면 D-044~046을 삭제·수정하지 말고 새 decision/ADR로 supersede한다.

### 다음 개발자 시작점

- 인간이 명세·계획을 승인하면 `docs/superpowers/plans/2026-07-20-data-seed-002-successor-release-correction.md` Task 1부터 TDD로 실행한다.
- `.1`, v1 schema, current contracts, current migrations를 수정하려는 diff가 생기면 즉시 중단한다.

## 14. 남은 위험·미해결 질문·다음 단계

- DATA-SEED-002 실행 승인 대기: 승인 전 candidate `.2`, v2 schema, generator/verifier code를 만들지 않는다.
- Q-PII-002의 `PRIVACY_UNRESOLVED`는 결정됐지만 공개 계약/DB 소비자 명세와 migration 순서가 아직 작성·승인되지 않았다.
- Q-SEC-003 `00700`은 public 준비 단계까지 보류되어 public deployment blocker로 남는다.
- 실제 PostgreSQL 17 환경은 후속 계획에서 seed → verify → replay → cleanup → readiness를 모두 통과해야 하며, 문서 검증만으로 그 결과를 예단하지 않는다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
