# IMP-20260719-006 — DATA-SEED immutable release 설계

- Date/Time (KST): 2026-07-19T02:06:19+09:00 시작, 2026-07-19T02:28:06+09:00 설계 보강
- Task ID: DATA-SEED-001-DESIGN
- Type: decision-design
- Status: Decision-only Done — written specification approval pending
- Author/Agent: Codex root; independent reviewer `data_seed_spec_review`
- Branch: `main`
- Base commit: `d486b9a`
- Related: Q-SEED-001, D-036, A-028, ADR-0015/0016, DATA-001 `0.1.0-draft.1`

## 1. 사용자 요청과 완료 기준

### 요청

사용자는 Q-SEED-001=A를 선택해 PM 승인 record를 immutable filesystem release와 기존 DB
schema용 transactional local seed로 승격하는 architecture를 확정했다. 동시에 사람이 해야 할
승인만 남기고 가능한 작업을 계속하라고 요청했다.

### Acceptance Criteria

- initial release `0.1.0-initial.1`과 exact projection 19 KB/3 office/10 mapping을 명시한다.
- mock, `KB-WASTE-03`, 거절 매핑 2건을 포함하지 않는다.
- DB/API/migration/readiness를 바꾸지 않는 서면 명세와 ADR만 작성한다.
- 승인 evidence→release→empty local seed의 hash/role/race/rollback 경계를 정의한다.
- 독립 설계 리뷰의 Critical/Important/Minor를 반영한다.
- 사용자의 명시적 `명세 승인` 전 계획/코드/release/seed/DB row를 만들지 않는다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자/PM이 architecture를 결정했고 Codex root가 명세·ADR을 작성했으며 독립 reviewer가 보안·DB 일관성을 검토했다. |
| When — 언제 | 2026-07-19 KST, PM confirmation 직후. |
| Where — 어디서 | `docs/superpowers/specs`, `docs/adr`, source-of-truth/decision/ambiguity/task 문서. 제품 코드·DB·data release는 제외. |
| What — 무엇을 | DATA-SEED-001의 initial immutable release, two-phase local activation, locked seed/compensation 설계. |
| Why — 왜 | 승인 evidence를 추적 가능한 official artifact로 승격하되 아직 비어 있는 local DB에서만 안전하게 재현하기 위해. |
| How — 어떻게 | canonical JSON/schema/hash, create-once release, 별도 dispatcher activation, transaction+role assertion+8-table exclusive locks+semantic projection hash. |
| How much — 어느 정도 | 초기 19/3/10 projection; 외부 API·새 dependency·DB migration·공식 data version 변경 0. |

## 3. 시작 전 상태

- `data/staging/data-001/0.1.0-draft.1/`에는 DRAFT KB 20, office 3, mapping 12와
  hash-bound approval manifest가 있었고 PM evidence materialization은 별도 DATA-001 작업이었다.
- `data/official/releases/`에는 active official release가 없고
  `versions/manifest.json.official_data`는 `0.0.0-not-populated`였다.
- `supabase/config.toml`의 `[db.seed].enabled=false`; 기존 DB는 FORCE RLS와
  `sejong_schema_owner`를 사용한다.
- `/ready=503`; retrieval/chat citizen behavior는 미구현이다.
- Git: `main`, base `d486b9a`; 이 노트 작업 전 제품 코드 변경 없음.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-SEED-001 | 인간 결정 | release/import 구조 | A: immutable filesystem + existing-schema transaction seed | ADR-0016/spec |
| A-028 | A/Blocker | written spec/plan 승인 | architecture만 해결; spec 승인 후 plan, plan 승인 후 구현 | release/seed/DB 차단 |
| REVIEW-C1 | 보안 | advisory lock을 application capability가 따르지 않음 | 8개 table `ACCESS EXCLUSIVE` lock과 locked pre/postcondition | concurrent write/delete race 차단 |
| REVIEW-C2 | 복구 | release rename+dispatcher replace는 cross-path atomic 불가 | prepare와 activate-local-seed의 two-phase recovery | Windows crash/failure 의미 명확화 |
| REVIEW-I3/I4 | 권한·도구 | FORCE RLS principal과 실제 import command 불명확 | exact local `postgres@127.0.0.1:54322/postgres` DSN, repository verifier만 지원; before/after `SET LOCAL ROLE` assertion; db.seed=false 유지 | manual seed 금지 |
| REVIEW-I5 | 데이터 무결성 | public ID count만으로 compensation 검증 부족 | 모든 seed-owned column/example의 bidirectional SQL equality와 repository canonical semantic hash | altered row 삭제 방지 |
| REVIEW-I6/I7 | 계약·버전 | release schemas와 successor semantics 부족 | 4개 strict schema; exact initial version-only | 미래 transition 별도 승인 |

## 5. 설계 결정과 대안

### 선택

초기 버전은 exact `0.1.0-initial.1`이다. 승인된 19/3/10만 canonical release JSON과 seed로
투영한다. release publication과 `supabase/seed.sql` activation은 두 단계로 분리한다. DB import와
compensation은 repository verifier가 migration-only disposable local DB에서만 수행하며,
exact local postgres session과 `sejong_schema_owner` 전환을 assertion한 뒤 8개 table exclusive
lock을 잡고 full semantic projection을 검증한다. SQL은 parent process를 증명한다고 주장하지
않고 session/database/role/catalog facts만 강제한다.

### 이유

새 DB release-ledger migration 없이도 승인 hash와 official bytes를 재현할 수 있다. Table lock은
advisory lock을 모르는 기존 capability와의 race를 막고, full semantic hash는 같은 ID의 변조 row를
보상 스크립트가 삭제하는 것을 막는다. Two-phase는 Windows에서 두 경로를 한 번에 atomic하게
바꿀 수 없다는 실제 제약을 정직하게 표현한다.

### 고려했지만 선택하지 않은 대안

- DB release ledger/function: public security/migration 범위를 키워 initial local release에는 과도하다.
- `supabase db reset` 자동 seed: 현재 `[db.seed].enabled=false` 정책을 바꾸고 reset 의미를 넓혀 제외했다.
- advisory lock만 사용: application capability가 같은 lock을 잡지 않아 race가 남으므로 폐기했다.
- ID/count-only compensation: same-ID field 변조를 검출하지 못해 폐기했다.
- direct `supabase/seed.sql` 편집: immutable lineage와 prepare/activate recovery가 없어 폐기했다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `docs/superpowers/specs/2026-07-19-data-seed-immutable-release-design.md` | initial-only contract, strict schemas, two-phase activation, role/table locks, semantic hash, acceptance tests | 실행 전 검토 가능한 source spec |
| `docs/adr/0016-immutable-filesystem-official-release-and-empty-local-seed.md` | architecture와 안전/rollback consequence 기록 | architecture decision permanence |
| `docs/decisions/DECISION_LOG.md` | D-036 | 사용자 결정 추적 |
| `docs/11_AMBIGUITY_REGISTER.md` | A-028 상태와 승인 gate | 구현 차단 조건 명시 |
| source-of-truth/TASKS | exact 19/3/10, initial-only pending state | 중복 문서의 수량·상태 정합 |

### 데이터 흐름/상태 변화

이번 작업은 문서 결정만 변경한다. 미래 흐름은 approved staging bytes → prepared immutable release
→ verified local dispatcher → locked empty-local import이다. 이번 작업에서 official artifact, seed SQL,
DB row, ACTIVE retrieval 상태는 생성되지 않았다.

### 오류·빈 상태·롤백

- prepare 실패 전 publish: release 없음, dispatcher 불변.
- activation 실패: verified prepared release는 유지하고 prior dispatcher를 복원·검증.
- import 실패: 한 transaction rollback; table lock 아래 zero partial row 검증.
- compensation: operational/reference row 또는 semantic mismatch가 있으면 zero delete.
- 문서 롤백: 이 decision 문서 변경 commit을 revert. 데이터/DB cleanup 없음.

## 7. 버전 전후

| 축 | Before | After this design batch | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.0 | 2.2.1 | PM projection와 initial seed architecture 정합 |
| Application/Web/API | 기존 | unchanged | runtime/wire 미구현 |
| DB schema | 0.3.0-local | unchanged | migration 없음 |
| Official data | 0.0.0-not-populated | unchanged | release/seed 구현 전 |
| Mock/Prompt | 기존 | unchanged | 범위 밖 |
| Test suite | 0.7.0-data-trust-boundary | unchanged by design | 테스트는 계획 승인 뒤 |
| Docs | 2.6.1 | 2.7.0 integrated target | decision/spec/plan/notes batch |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 증거 |
|---|---|---|
| `git status --short --branch`, `git log -3 --oneline` | main/base와 의도한 문서 변경 확인 | terminal output |
| `rg`/`Get-Content` on schema, migrations, config, source-of-truth | FORCE RLS, role ownership, table columns, `db.seed=false` 확인 | inspected repository files |
| independent `data_seed_spec_review` | Critical 2, Important 6, Minor 2 발견; 모두 명세/ADR에 반영 | agent final review |
| independent final spec review | PASS, Critical 0 / Important 0 / Minor 0 | all prior findings closed |
| `pnpm view @playwright/test ...` 및 공식 문서 조회 | WEB 병렬 계획용 별도 evidence; DATA-SEED runtime에는 사용 안 함 | terminal/web evidence |

### 미실행 검증과 이유

DATA-SEED unit/DB/replay 검증은 구현 자체가 아직 승인되지 않아 실행 대상이 없다. 승인 전 release,
seed, compensation 또는 DB mutation을 시험 삼아 생성하지 않았다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 시민 질문/답변/PII가 설계 artifact, SQL, log에 들어가지 않는다. authored generalized
  question example만 future official release 대상이다.
- Security: exact approval hash, strict path/schema, role assertion, exclusive table locks, fail-closed
  semantic comparison을 설계했다. 새 grant/SECURITY DEFINER/migration은 없다.
- Accessibility: UI 변경 없음.
- Performance/cost: 19/3/10 local-only 규모, Python stdlib/기존 PostgreSQL만 계획; 외부 비용 0원.

## 10. 데이터와 출처 영향

- 공식 데이터: PM 승인 projection은 19 KB/3 office/10 mapping이나 이번 작업에서는 여전히 release되지 않음.
- 제외: `KB-WASTE-03`, `OFFICE-AREUM:LOCAL_TAX_GENERAL`,
  `OFFICE-DODAM:BULKY_WASTE`, 모든 mock.
- schema/lineage: 미래 `data/schemas/data-seed/v1/` 4개 strict schema와 release lineage를 명세함.
- verified date: source record의 existing `last_verified_at`를 보존하며 이 설계가 공식 출처 내용을
  새로 검증했다고 주장하지 않는다.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- Q-SEED-001=A는 architecture만 승인했다. 현재 필요한 인간 동작은 서면 spec의 `명세 승인`이다.
- 명세 승인 뒤에도 실행계획을 별도로 제시하고 `계획 승인, 구현 시작`을 받아야 한다.
- initial-only empty-local 설계이며 이미 운영 row가 있는 DB 업데이트/공개 배포에는 사용할 수 없다.
- official data version과 `/ready`는 아직 바뀌지 않았다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- serializer/helper/fixture 명칭, lexical ordering implementation, SQL literal helper 분리는 승인된
  contract 안에서 자율 처리 가능하다.
- release/dispatcher temp sibling 파일명은 secret/record content를 포함하지 않도록 내부에서 정한다.

## 13. 인수인계·재현·롤백

### 재현

1. ADR-0015와 DATA-001 staging schema/approval manifest를 읽는다.
2. ADR-0016과 DATA-SEED spec의 trust boundary, two-phase, DB lock 순서를 검토한다.
3. `supabase/config.toml`의 seed disabled와 migration의 owner/FORCE RLS를 확인한다.
4. 사용자의 명세 승인 전 구현 계획이나 release artifact를 만들지 않는다.

### 롤백

설계 문서 commit을 revert한다. 이번 작업은 제품 코드/DB/data release를 만들지 않아 별도 복구가 없다.

### 다음 개발자 시작점

사용자가 `명세 승인`하면 `superpowers:writing-plans`로 schema/generator/SQL/real-DB replay를
TDD task로 분해하고 다시 계획 승인을 받는다.

## 14. 남은 위험·미해결 질문·다음 단계

- A-028: written spec과 plan human gate.
- A-021/Q-SEC-003: public DB function search-path hardening; local seed blocker는 아니지만 public release blocker.
- Initial release 이후 correction/update DB transition은 별도 architecture가 필요하다.
- real DB import/compensation/replay 성능과 lock behavior는 구현 승인 뒤 실제 disposable DB에서 증명해야 한다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 설계 독립 리뷰와 발견 사항 반영, final review 0/0/0
- [x] source-of-truth/결정/모호성 정합
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 연결
- [x] 승인 전 제품 코드·release·seed·DB mutation 없음
