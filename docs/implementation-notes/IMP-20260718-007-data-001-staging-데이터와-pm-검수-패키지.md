# IMP-20260718-007 — DATA-001 staging 데이터와 PM 검수 패키지

- Date/Time (KST): 2026-07-18T20:04:33+09:00
- Task ID: DATA-001
- Type: implementation/data-quality/governance-closeout
- Status: AI-executable scope complete / Human Review KEEP
- Author/Agent: Codex(Architecture·AI/Data·Backend·Security·Docs)
- Branch: `codex/data-001-staging-review`; worktree `.worktrees/data-001-staging-review`
- Base commit: `36da4b1`
- Related plan/ADR/RFP: DATA-001 staging plan / D-033 / A-026 / ADR-0015 / DAR-001·002 / SER-001·003

## 1. 사용자 요청과 완료 기준

### 요청

승인된 DATA-001 명세에 따라 AI/Data·Backend가 공식 출처 범위 안에서 KB 20·기관 3·지역×민원
매핑 12의 DRAFT와 hash-bound PM 검수 패키지를 만들고, 사람의 검수·승인·release/seed는 KEEP으로
남긴다. 이번 closeout은 그 결과의 거버넌스·버전·증거를 사실대로 동기화한다.

### Acceptance Criteria

- canonical staging은 `0.1.0-draft.1` DRAFT KB 20, office 3, mapping 12이며 PENDING manifest를 가진다.
- validator는 source/count/PII/mock/secret/order/hash/approval boundary를 fail closed로 검사한다.
- DATA-001 상태는 `Human Review KEEP`, PM review pending으로 기록한다.
- `official_data`는 `0.0.0-not-populated`을 유지하고 ACTIVE/release/seed/readiness를 만들지 않는다.
- `test_suite`는 `0.6.0-data-staging`, `documentation`은 `2.5.0`으로만 갱신한다.
- application/web/API/shared contracts/DB/mock/prompt, dependency, Docker/cloud은 변경하지 않는다.
- 실행한 검증과 full root gate 제한을 숨기지 않고 재현·rollback·handoff를 남긴다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자(PM)가 명세와 연속 AI 실행을 승인했고, AI/Data·Backend가 DRAFT를 작성했으며 PM은 아직 35 record 전수 검수자다. |
| When — 언제 | 2026-07-18 KST; source 확인일은 `2026-07-18`, PM 목표일은 기존 `2026-07-20`이다. |
| Where — 어디서 | canonical input은 `data/staging/data-001/0.1.0-draft.1/`; 검수 산출물은 `data/processed/...`; runtime/DB/official release에는 쓰지 않는다. |
| What — 무엇을 | internal schema 4개, dependency-free validator/CLI, DRAFT 20/3/12, PENDING manifest, report, PM packet, lineage와 closeout governance다. |
| Why — 왜 | 승인 전 자료가 시민 근거·seed·readiness로 섞이지 않으면서 PM이 exact hash-bound bytes를 검수하게 하기 위해서다. |
| How — 어떻게 | approved spec→독립 source audit→TDD schema/business validator→DRAFT authoring→prepare/validate→독립 review 보정→governance/version/evidence handoff 순서다. |
| How much — 어느 정도 | content record 35, content artifact 3+manifest 1, initial projection 19 KB/3 office/10 mapping, external cost·LLM/API call·DB mutation 0이다. |

## 3. 시작 전 상태

- 관련 파일: `docs/source-of-truth/`, ADR-0015, DATA-001 spec/plan, source registry 20행,
  `contracts/kb-record.schema.json`, DB read boundary, data policy/lineage documents.
- 기존 동작: official KB/office/mapping/release/seed 0, `/ready=503`, source registry만 존재했다.
- 발견·해소한 부채: staging artifact/schema/validator/PM packet 부재, 정부24 URL drift, TAX-02 범위,
  weak mapping 2건, validator의 값 노출·write boundary·registry contract·submission provenance/format 문제를
  Task 1~3 review에서 보정했다.
- Git: closeout base `36da4b1`; DATA-001 implementation commits are `89c42fa`, `919052b`,
  `a21f4fe`, `01f837e`, `6435cc2`, `99f975d`, `327dab2`, `dbb3844`, `211cd9f`, `f7b9157`, `36da4b1`.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-DATA-002/A-026 | Resolved | staging/approval artifact | D-033/ADR-0015 canonical JSON+hash-bound manifest | DRAFT/review boundary |
| DATA-MAP-001 | Human KEEP | 아름동×지방세, 도담동×대형폐기물 근거 약함 | staging 유지, PM packet은 REJECT 권고, initial projection 10 | 향후 routing/release |
| DATA-APPROVAL-001 | Human KEEP | record별 PM decision/comment | AI는 `PENDING_PM_REVIEW`까지만; PM이 author와 달리 결정 | promotion blocker |
| DATA-SRC-002 | Defaulted | TAX-02 source scope | 로그인 후 본인 고지 확인 경로로 한정 | 개인 결과/세액 추정 방지 |
| A-021/Q-SEC-003 | Unchanged | public DB function hardening | public release는 계속 차단 | 배포 only |

## 5. 설계 결정과 대안

### 선택

- public `contracts/`를 바꾸지 않고 `data/schemas/data-001/v1/`에 internal authoring contract를 둔다.
- Python 3.12 standard library의 `ValidationIssue`, `load_json_object`, `validate_schema`,
  `sha256_file`, `build_pending_manifest`, `validate_staging`, `write_json`과
  `_validate_runtime_staging_references`로 fail-closed validation을 제공한다.
- manifest는 세 content artifact만 SHA-256으로 묶고, PM review 전 state는
  `PENDING_PM_REVIEW`로 고정한다.
- `KB-WASTE-03`은 `WITHHOLD_FOR_REGRESSION`; 두 weak mapping은 `REJECT` 권고로 남긴다.

### 이유

공개 API/DB contract와 미승인 authoring contract를 분리하고, 답변/출처 payload를 오류나 report에
복사하지 않은 채 PM이 검토할 exact content와 hash를 재현할 수 있다.

### 고려했지만 선택하지 않은 대안

- public KB schema/OpenAPI 수정: 공개 계약 변경·인간 승인 필요라 제외했다.
- 새 JSON Schema dependency: 표준 라이브러리 범위로 충분하며 새 dependency 승인 범위를 피한다.
- direct SQL seed/official release/ACTIVE: PM 승인과 DATA-SEED-001 경계를 우회하므로 제외했다.
- weak mapping 전부 승인 권고 또는 TAX/WASTE 변동 사실 확정: source 범위 밖 추정이므로 제외했다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `data/schemas/data-001/v1/` | KB, office, mapping, approval-manifest internal JSON Schema 4개 | DRAFT field/state/type 제한 |
| `scripts/data_staging_validation.py` / `scripts/validate_data_staging.py` | schema/cross-file/privacy/source/hash/runtime boundary 검사와 prepare/validate CLI | reproducible fail-closed gate |
| `scripts/tests/test_data_staging_validation.py` / `scripts/verify.ps1` | 56 focused tests와 mandatory root `VALIDATE-DATA-001` integration | regression/runtime isolation, canonical path/reparse/privacy/source-matrix hardening |
| `data/schemas/data-001/v1/approved-source-matrix.json` / `docs/data-lineage/source-audits/` | exact source/content/registry/audit hash trust anchor와 sanitized tracked 감사 요약 4개 | PM 검수 전 coordinated drift와 mutable ignored audit 의존 제거 |
| `data/staging/...` | canonical DRAFT 20/3/12+PENDING manifest | PM이 검수할 exact input |
| `data/processed/...`, `docs/data-lineage/...` | value-free report, 35-row PM packet, source→draft→promotion lineage | human review and handoff |
| `data/official/kb_source_registry.csv` | 20 canonical IDs/order, date/author/status/reviewer boundary | source assignment audit |
| plan/spec/D-033/A-026/TASKS/readmes/manifest/changelog/INDEX | AI scope complete / Human Review KEEP와 versions | truthful governance closeout |

### 데이터 흐름/상태 변화

`source audit → DRAFT content → validation/hash → PENDING_PM_REVIEW → PM KEEP`까지만 구현됐다.
`data/official/releases/`, `supabase/seed.sql`, DB row, ACTIVE KB, citizen search, readiness는 0/미변경이다.

### 오류·빈 상태·롤백

validator failure는 stable code/artifact/safe-ID/field만 출력하고 PENDING manifest replacement와 report
write boundary를 fail closed한다. Hash mismatch는 PM approval을 무효로 하며 새 draft version을 요구한다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.0 | 2.2.0 | 제품 범위 변경 없음 |
| Repo guidance | 1.5.0 | 1.5.0 | repository policy 변경 없음 |
| Application | 0.1.0 | 0.1.0 | runtime 변경 없음 |
| Web | 0.1.0 | 0.1.0 | UI 변경 없음 |
| API | 2.0.1-draft | 2.0.1-draft | public API 변경 없음 |
| Shared contracts | 0.2.1 | 0.2.1 | public/shared contract 변경 없음 |
| DB schema | 0.3.0-local | 0.3.0-local | migration/DB mutation 없음 |
| Official data | 0.0.0-not-populated | 0.0.0-not-populated | DRAFT는 official release/seed가 아님 |
| Mock data | 0.0.0-not-populated | 0.0.0-not-populated | mock 변경 없음 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 0.0.2-deepseek-v4-flash-selected | LLM/prompt 변경 없음 |
| Test suite | 0.5.0-db-baseline | 0.6.0-data-staging | DATA-001 validation/test gate 추가 |
| Documentation | 2.4.2 | 2.5.0 | plan, lineage, PM handoff, closeout evidence |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 |
|---|---|---|---|
| `apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_patched_supabase_tooling.PatchedBootstrapContractTests.test_child_timeout_terminates_spawned_descendant -v` | PASS | 1 test, 15.189s | exact known child-timeout regression |
| `apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_data_staging_validation -q` | PASS | 56 tests, 20.773s | focused DATA-001 suite after Final Remediation 2 |
| `apps/api/.venv/Scripts/python.exe -B scripts/validate_data_staging.py validate --draft-dir data/staging/data-001/0.1.0-draft.1 --report <processed-report>` twice | PASS | report SHA-256 identical | `460c6e6613cdd18f5a3abace116da14dbb036b2d60855d835038c9cf9afd7d2d`, issues 0, warning only `PM_REVIEW_REQUIRED` |
| JSON/CSV parse + counts/manifest/report/hash comparison | PASS | KB 20, office 3, mapping 12, decisions 35, registry 20 | manifest/report/direct SHA-256 exact match |
| tracked runtime/operations staging-reference scan | PASS | issues 0 | apps/packages/database/scripts, Supabase config/seed/migrations, repo-wide PowerShell/config; case/comment/concat/split bypass tests included |
| `python -B scripts/validate_codex_package.py` | PASS | 12 required files | manifest valid |
| `check_secret_patterns.ps1` | PASS | findings 0 | no secret pattern output |
| PowerShell parser for `scripts/verify.ps1` | PASS | parse errors 0 | parser evidence |
| `git diff --check` | PASS | whitespace errors 0 | final diff gate rerun before commit |
| `scripts/verify.ps1` (non-offline, one fresh run) | INCONCLUSIVE | TEST-ROOT runner idle >7 min | started 19:54:05 KST; exact focused child test had passed; PID 421264 had CPU 0.171875 unchanged/no descendant/no further output after `TEST-ROOT`, so only that worktree-scoped runner was stopped and wrapper/tree became 0 |

### 미실행 검증과 이유

No second full root run was started: the requested single fresh non-offline run was attempted and is not PASS
evidence. PM source/content approval, DATA-SEED-001 promotion/import, DB seed, ACTIVE query, readiness 200,
public deployment, and performance/UI checks are outside this task and remain unexecuted.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: citizen question/PII/personal lookup result 0. Generalized examples only; public office phone/address
  is allowed only for the exact `(office id, field, value)` in the tracked approved source matrix. Manifest,
  registry and content strings are scanned before a value-free report can be emitted.
- Security: secret/mock/unsafe source/self-approval/hash mismatch/runtime staging reference fail closed; errors
  contain no payload values. No credential, dependency, Docker, cloud, DB, or external LLM action occurred.
- Accessibility: UI/runtime change 0. PM packet is textual/table-based; existing UI accessibility posture is unchanged.
- Performance/cost: local 35-record validator report deterministic; no stated product performance target changes;
  external cost is 0 won.

## 10. 데이터와 출처 영향

- Official data: `official_data=0.0.0-not-populated`; immutable release, SQL seed, DB rows, ACTIVE records and
  readiness remain absent. DRAFT does not become citizen evidence.
- mock/AI 생성: wording/question examples are AI-authored DRAFT constrained to audited official sources; no mock
  data mixes with official staging.
- schema/lineage: internal schema v1, draft `0.1.0-draft.1`, three hashes — KB
  `38d0c801b3dab3962b5cd01fe15a43a60121963b53e8b1f7ac65304d07267365`, offices
  `fe942ce476c7d78f5b17deb10fd3b53e5b673f3ae36cf67a042823ccd51a7af0`, mappings
  `a0fb8f3c423c0b0b199ed27cdb35cf40efa9011e7ae3d6736f420fc175ee4e1b` — match manifest/report.
- verified date: all audited source records use `2026-07-18`; changing links, prices, dates, hours, refunds and
  service availability require PM recheck before approval.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- PM must review all 35 records and official sources, enter every decision and non-empty comment, and be different
  from `AI-DATA-BACKEND` before changing the manifest to an approved/rejected state.
- `KB-WASTE-03` stays `WITHHOLD_FOR_REGRESSION` and is excluded from the initial release; the two weak mappings
  remain REJECT recommendations unless PM has stronger official evidence.
- PM must recheck TAX-03/05 official routes and 2026-variable waste fee/day/refund and office contact/hour facts.
- DATA-SEED-001 alone may create immutable release/seed/import; READY-001 alone may reconsider `/ready=200`.
- The full root gate has an unresolved TEST-ROOT hang despite the exact child-timeout regression passing; do not
  report the full `scripts/verify.ps1` suite as PASS until root cause is found and a fresh run exits 0.

## 12. AI 내부 구현 세부 — 인간이 굳이 이해하지 않아도 되는 내용

- `ValidationIssue` ordering, JSON-type-aware const/enum comparison, safe malformed-ID suppression, temporary
  fixture factories, atomic JSON writer, report destination containment, and CLI parser composition.
- test naming, schema formatting, duplicated helper reduction, and ignored `.superpowers/sdd/` task reports.

## 13. 인수인계·재현·롤백

### 재현

1. Read ADR-0015, the approved spec and plan, then inspect the four files under
   `data/staging/data-001/0.1.0-draft.1/`.
2. Run `apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_data_staging_validation -q`.
3. Run `apps/api/.venv/Scripts/python.exe -B scripts/validate_data_staging.py validate --draft-dir data/staging/data-001/0.1.0-draft.1 --report data/processed/data-001/0.1.0-draft.1/validation-report.json` twice and compare report hashes.
4. Have PM use `data/processed/data-001/0.1.0-draft.1/PM_REVIEW_PACKET.md`, enter decisions/comments against the
   current artifact hashes, then start a separately approved DATA-SEED-001 only after approval.

### Migration, rollback, recovery

This task creates no DB migration, no SQL seed, no official release and no data migration rollback. Before PM
approval, revert the DATA-001 commits to remove the unapproved draft/report/validator. Do not rewrite a human-reviewed
manifest; content correction creates a new draft version, recalculates the three content hashes, and requires fresh PM
review. DATA-SEED-001 owns immutable release/import compensation; READY-001 owns readiness recovery.

### 다음 개발자 시작점

Start with the tracked DATA-001 plan, `docs/data-lineage/DATA-001-0.1.0-draft.1.md`, the four tracked summaries under
`docs/data-lineage/source-audits/`, `data/schemas/data-001/v1/approved-source-matrix.json`, this note and the PM packet.
Preserve the canonical DRAFT bytes and use the hash comparison before any PM decision. Investigate the root
`TEST-ROOT` process hang before claiming a full root verification pass.

## 14. 남은 위험·미해결 질문·다음 단계

- Human PM review is KEEP; no automatic approval or promotion is authorized.
- Variable official facts and TAX legacy routes need human revalidation.
- The full root suite limitation is an environmental/tooling investigation item; focused DATA-001 and exact
  child-timeout tests pass, but root PASS is unavailable.
- A-021/Q-SEC-003 remains a separate public-release blocker.
- Next authorized product sequence: PM review → DATA-SEED-001 plan/approval → immutable release/import → READY-001.

## 15. 자체 리뷰

- [x] requested AI-executable DATA-001 scope and truthful Human Review KEEP status recorded
- [x] scoped tests/validation and full-root limitation documented with actual evidence
- [x] source-of-truth/ADR/contract/version/governance synchronization checked; TEAM_DECISIONS/PROJECT_PLAN unchanged because no drift
- [x] no privacy raw payload, secret, official release, DB/API/runtime/dependency/Docker/cloud change
- [x] implementation note INDEX updated
- [x] independent Task 4 review: Critical 0; reproducible command evidence corrected after its one Important finding
- [x] final closeout commit: `docs(data): hand off DATA-001 for PM review`
