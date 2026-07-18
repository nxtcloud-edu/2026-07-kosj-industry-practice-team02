# DATA-001 Staging and PM Review Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 공식 출처를 다시 확인한 KB 20건·기관 3건·지역×민원 매핑 12건을 미승인 staging으로 작성하고, 표준 라이브러리 검증기와 hash-bound manifest를 통해 PM이 exact content를 전수 검수할 수 있는 패키지를 만든다.

**Architecture:** `data/staging/data-001/0.1.0-draft.1/`의 네 JSON만 canonical 입력이고, `data/schemas/data-001/v1/`은 저장소 내부 데이터 계약이다. Python 3.12 표준 라이브러리 검증기는 schema·cross-file·PII·source·hash·승인 상태를 fail closed로 검사하고 `data/processed/`에 값 원문을 복사하지 않는 요약을 만든다. PM 승인, immutable official release, DB seed/import, ACTIVE 전환은 이 계획에서 수행하지 않는다.

**Tech Stack:** Python 3.12.13 standard library, `unittest`, JSON Schema 2020-12 문서 계약, PowerShell 5.1 root verification, Git.

## Global Constraints

- citizen evidence는 `ACTIVE + OFFICIAL`만 허용하며 staging은 어떤 runtime 검색·seed·readiness에도 사용하지 않는다.
- canonical draft 경로는 정확히 `data/staging/data-001/0.1.0-draft.1/`이다.
- content artifact는 정확히 `kb_records.json`, `offices.json`, `office_service_mappings.json`이며 manifest는 이 세 파일만 SHA-256으로 묶는다.
- staging count는 KB 20, office 3, mapping 12다.
- initial release 후보는 KB 19, office 3, mapping 10이며 `KB-WASTE-03`과 근거가 약한 mapping 2건은 승인 대상에서 제외한다.
- `KB-WASTE-03`은 정확히 `WITHHOLD_FOR_REGRESSION`이며 DATA-SEED initial release와 ACTIVE에서 제외한다.
- `아름동 × LOCAL_TAX_GENERAL`, `도담동 × BULKY_WASTE`는 근거가 보강되기 전 `REJECT` 권고다.
- 모든 content record는 `data_origin=OFFICIAL`, KB는 `status=DRAFT`, `created_by=AI-DATA-BACKEND`, 승인 필드는 null이다.
- 실제 시민 질문·PII·비밀·개인 조회 결과·내부 행정 데이터·mock을 넣지 않는다.
- 출처명·URL·확인일은 LLM이 생성하지 않으며 승인된 source audit의 1차 공식 출처만 사용한다.
- PM만 record disposition과 dataset approval을 확정한다. AI는 `PENDING_PM_REVIEW` 제출물까지만 만든다.
- 새 production/dev dependency, 공개 API, DB migration/seed, product code, LLM 호출, Docker/remote/cloud operation을 추가하지 않는다.
- JSON은 UTF-8, LF, 2-space indent, trailing newline, record ID lexical order를 사용한다.

---

## 계획 거버넌스

- Plan ID: `DATA-001-STAGING-PLAN`
- 상태: AI scope complete / Review (PM pending)
- 사용자 승인 근거: 2026-07-18 `명세 승인`과 “사람 작업은 KEEP하고 나머지는 계속 진행, 데이터는 AI가 초안 후 사용자 검토” 지시
- 승인된 명세: `docs/superpowers/specs/2026-07-18-data-001-staged-official-data-design.md`
- 결정: D-033 / A-026 / ADR-0015
- 실행 branch: `codex/data-001-staging-review`
- 실행 worktree: `.worktrees/data-001-staging-review`
- 구현 노트: `docs/implementation-notes/IMP-20260718-007-data-001-staging-데이터와-pm-검수-패키지.md`
- 인간 KEEP: PM 전수 source/content 검수, record별 decision/comment, `reviewed_by/reviewed_at`, APPROVED 상태 변경
- 별도 후속: DATA-SEED-001 immutable release·seed/import, REG-001 WASTE-03 최종 승인

## 목표와 비목표

목표:

- 내부 JSON schema 네 개와 dependency-free validator를 만든다.
- 공식 source audit 범위 안에서 KB 20·office 3·mapping 12 DRAFT를 작성한다.
- canonical source registry의 정부24 9개 URL, 확인일, 작성 상태, 작성자를 staging과 동기화한다.
- content hash를 가진 `PENDING_PM_REVIEW` manifest와 PM 검수 packet을 만든다.
- root gate에 staging validation을 연결하고 재현·롤백·lineage를 문서화한다.

비목표:

- PM을 대행한 승인, `APPROVED_FOR_INITIAL_RELEASE`, ACTIVE/official release/seed/DB mutation.
- 시민 답변·관리자 UI/API·검색·LLM·readiness 변경.
- source가 약한 mapping 2건을 추정으로 승인하거나 TAX-02에 세액·납기·연납 혜택을 추가.

## 사용자 가치와 인수 기준

- 사용자는 35개 DRAFT의 exact content와 공식 링크를 한 패킷에서 검토할 수 있다.
- `python -B scripts/validate_data_staging.py`가 KB 20/office 3/mapping 12, source registry exact ID set, PII/mock/secret 0, deterministic order, stale hash 0을 증명한다.
- manifest는 세 content artifact의 path/count/SHA-256을 가지며 state는 `PENDING_PM_REVIEW`, review/decision 필드는 미확정 상태다.
- validator error에는 stable rule code·파일·record ID·field만 있고 answer/source/secret 원문이 없다.
- staging을 runtime/seed/readiness가 참조하는 tracked code가 0건이다.
- `official_data` 버전과 DB/API/application version은 유지된다.

## 권위 근거

- RFP: DAR-001, DAR-002, SER-001, SER-003, SFR-004
- source-of-truth: TEAM_DECISIONS, PROJECT_PLAN §6, KB_GUIDE, APPROVAL_POLICY
- ADR: ADR-0001, ADR-0003, ADR-0015
- discovery: `docs/discovery/DATA_001_DISCOVERY_REPORT.md`
- source audit: 2026-07-18 전입·증명, 대형폐기물, 지방세, 기관·매핑 독립 감사

## 권위 파일 맵

| Path | 책임 |
|---|---|
| `data/schemas/data-001/v1/kb-records.schema.json` | KB staging root와 record 필드 계약 |
| `data/schemas/data-001/v1/offices.schema.json` | office staging root와 record 필드 계약 |
| `data/schemas/data-001/v1/office-service-mappings.schema.json` | mapping staging root와 record 계약 |
| `data/schemas/data-001/v1/approval-manifest.schema.json` | dataset state, content hash, PM disposition 계약 |
| `scripts/data_staging_validation.py` | schema subset, cross-file, PII/source/hash 검증 순수 함수 |
| `scripts/validate_data_staging.py` | stable-output CLI, manifest 준비, report 출력 |
| `scripts/tests/test_data_staging_validation.py` | RED/GREEN unit·contract·privacy·hash tests |
| `data/staging/data-001/0.1.0-draft.1/*.json` | canonical DRAFT 4개 artifact |
| `data/processed/data-001/0.1.0-draft.1/validation-report.json` | 원문 없는 deterministic validation summary |
| `data/processed/data-001/0.1.0-draft.1/PM_REVIEW_PACKET.md` | 사람이 검수할 35개 record·source·권고 decision |
| `docs/data-lineage/DATA-001-0.1.0-draft.1.md` | audit→draft→review→future promotion lineage |

## 내부 인터페이스

`ValidationIssue`는 frozen/orderable dataclass이며 필드는 `code: str`, `artifact: str`,
`record_id: str | None`, `field: str | None`다. 공개 내부 함수 signature는 다음과 같다.

- `load_json_object(path: Path) -> dict[str, object]`
- `validate_schema(instance: object, schema: dict[str, object], artifact: str) -> Sequence[ValidationIssue]`
- `sha256_file(path: Path) -> str`
- `build_pending_manifest(draft_dir: Path, submitted_at: str) -> dict[str, object]`
- `validate_staging(draft_dir: Path, schema_dir: Path, source_registry: Path) -> dict[str, object]`
- `write_json(path: Path, value: object) -> None`

`validate_staging` report는 정확히 다음 top-level key만 가진다.

```json
{
  "schema_version": 1,
  "draft_version": "0.1.0-draft.1",
  "valid": true,
  "counts": {"kb": 20, "office": 3, "mapping": 12},
  "approval_projection": {"initial_kb": 19, "initial_office": 3, "initial_mapping": 10, "withheld_kb": 1, "rejected_mapping": 2},
  "artifact_hashes": {},
  "issues": [],
  "warnings": ["PM_REVIEW_REQUIRED"]
}
```

issues는 `ValidationIssue`의 네 필드만 serialize한다. source/answer/question/phone/address 값은 report나 stderr에 복사하지 않는다.

## Source content matrix

| IDs | canonical source | 허용 범위 |
|---|---|---|
| MOVE-01..03 | `https://plus.gov.kr/search/searchdtl/?srvcId=13100000016&typeSn=01` | 전입신고 인터넷/방문, 본인·대리 경계, 즉시(근무시간 내 3시간), 수수료 없음; 특정 인증수단 단정 금지 |
| MOVE-04 | `https://plus.gov.kr/search/searchdtl/?srvcId=13110000039&typeSn=01` | 주민등록 관련 통보서비스 인터넷/방문과 통보 범위 |
| MOVE-05 | `https://www.law.go.kr/LSW/lsInfoP.do?lsId=001655&urlMode=lsInfoP` | 전입 후 14일 일반 원칙; 위반·과태료·개인 법률판단 금지 |
| CERT-01..03 | `https://plus.gov.kr/search/searchdtl/?srvcId=13100000015&typeSn=01` | 등본/초본 의미·인터넷/방문/무인, 공식 수수료·처리 표시와 조건부 서류 |
| CERT-04 | `https://plus.gov.kr/search/searchdtl/?srvcId=13100000014&typeSn=01` | 열람의 인터넷/방문, 즉시, 온라인 무료·방문 300원 |
| CERT-05 | `https://plus.gov.kr/portal/custcntr/utztngd/unmncvlcptissugd/` | 설치장소·가능민원 확인 경로; 전국 24시간/고정 수수료 단정 금지 |
| WASTE-01,02,05 | `https://www.sjwaste.kr/board?menuId=MENU00303&siteId=null` | 신청·결제·취소/환불 조건·요일·문의 경로; 일정 SLA 단정 금지 |
| WASTE-03,04 | `https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305` | 침대 프레임 8,000/10,000원, 매트 4,000/6,000/4,000원; 품목 혼동 금지 |
| TAX-01 | `https://www.wetax.go.kr/main.do` | 위택스 조회·납부 공식 경로, 전자납부번호 경로; 개인 결과 금지 |
| TAX-02 | `https://www.wetax.go.kr/login.do` | 본인 로그인 후 자동차세 고지 확인 경로만; 납기·세액·혜택 금지 |
| TAX-03 | `https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13100000056&tp_seq=01` | 지방세 납세증명 신청 경로·즉시·무료; 개인 체납 단정 금지 |
| TAX-04 | `https://plus.gov.kr/search/searchdtl/?srvcId=13100000084&typeSn=05` | 세목별 과세증명 경로·인터넷 무료/방문 조례; 개인 결과 금지 |
| TAX-05 | `https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13110000017&HighCtgCD=A09002&tp_seq=01` | 지방세 납부확인서 인터넷/방문·즉시·무료; 납부 완료 단정 금지 |

모든 `last_verified_at`은 `2026-07-18`이다. 정부24 tax legacy URL은 추정한 plus deep-link로 바꾸지 않고 PM이 official UI에서 재확인할 항목으로 packet에 표시한다.

## Office and mapping matrix

| public_id | region / official name | address / phone / hours | source |
|---|---|---|---|
| `OFFICE-AREUM` | 아름동 / 아름동 행정복지센터 | `(30100) 세종특별자치시 보듬3로 114(아름동)` / `044-301-6300` / `평일 09:00~18:00` | `https://www.sejong.go.kr/areum/sub02_02.do?cmsNo=1461` |
| `OFFICE-DODAM` | 도담동 / 도담동 행정복지센터 | `(30098) 세종특별자치시 보람로 77(도담동)` / `044-301-6200` / `평일 09:00~18:00` | `https://www.sejong.go.kr/dodam/sub02_02.do?cmsNo=1458` |
| `OFFICE-JOCHIWON` | 조치원읍 / 북세종 통합 행정복지센터 | `(30024) 세종특별자치시 조치원읍 새내16길 17` / `044-301-5000` / `평일 09:00~18:00` | `https://www.sejong.go.kr/jochiwon/sub02_02.do?cmsNo=1425` |

mapping은 각 office×4 intent 12행을 모두 staging한다. evidence URL은 정확히
`https://www.sejong.go.kr/areum/sub02_01.do?cmsNo=1460`,
`https://www.sejong.go.kr/dodam/sub02_01.do?cmsNo=1457`,
`https://www.sejong.go.kr/jochiwon/sub02_01.do?cmsNo=1424`다. department와 권고는 다음과 같다.

| region | MOVE | CERT | WASTE | TAX |
|---|---|---|---|---|
| 아름동 | 민원행정과 일반민원 / APPROVE | 민원행정과 일반민원 / APPROVE | 안전도시과 환경경제 / APPROVE | 민원행정과 세무부동산 / REJECT |
| 도담동 | 민원행정 / APPROVE | 민원행정 / APPROVE | 주민생활 / REJECT | 민원행정 / APPROVE |
| 조치원읍 | 민원행정과 일반민원 / APPROVE | 민원행정과 일반민원 / APPROVE | 안전도시과 청소환경 / APPROVE | 민원행정과 세무부동산 / APPROVE |

## Task 0: Isolate execution and record the approved start

**Files:**

- Create/Modify: this plan
- Modify: `docs/superpowers/specs/2026-07-18-data-001-staged-official-data-design.md`
- Modify: `docs/decisions/DECISION_LOG.md`
- Modify: `docs/11_AMBIGUITY_REGISTER.md`
- Modify: `TASKS.md`
- Modify: `docs/implementation-notes/IMP-20260718-007-data-001-staging-데이터와-pm-검수-패키지.md`
- Modify: `docs/implementation-notes/INDEX.md`

- [x] **Step 1: Commit the approved plan on main**

Run `git diff --check`, package validation, secret scan, then commit only plan/governance/note-start files with `docs(data): start approved DATA-001 staging plan`.

- [x] **Step 2: Create the isolated branch/worktree**

Invoke `superpowers:using-git-worktrees`, create `codex/data-001-staging-review` at `.worktrees/data-001-staging-review`, and prove it is ignored.

- [x] **Step 3: Run the clean no-Docker baseline**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
```

Expected: exit 0; DB/Docker is not started and `/ready=503` remains the approved no-seed state.

Actual: main plan commit `aa52c42`, branch/worktree created clean. Ignored `uv` and patched Supabase
runtime were copied byte-for-byte because ignored tools are not inherited by Git worktrees; hashes matched
their pinned sources. Focused root 85 tests and patched runtime 24 tests passed, then full
`scripts/verify.ps1` exited 0 through root/web/API/contract/secret/package/diff gates without Docker/DB.

## Task 1: Add internal staging schemas and schema validation

**Files:**

- Create: four files under `data/schemas/data-001/v1/`
- Create: `scripts/data_staging_validation.py`
- Create: `scripts/tests/test_data_staging_validation.py`
- Modify: `data/README.md`

**Interfaces:** Produces `ValidationIssue`, `load_json_object`, `validate_schema`, `sha256_file`, `write_json` for Task 2.

- [x] **Step 1: Write RED schema tests**

Tests must construct temporary JSON and assert these exact rule codes without inspecting secret values:

```python
def test_unknown_kb_field_is_rejected(self) -> None:
    issues = validate_schema(self.valid_kb() | {"unexpected": "x"}, self.kb_schema, "kb_records.json")
    self.assertIn("SCHEMA_ADDITIONAL_PROPERTY", {issue.code for issue in issues})

def test_question_examples_require_three_to_five_unique_items(self) -> None:
    record = self.valid_kb() | {"question_examples": ["하나", "둘"]}
    issues = validate_schema(record, self.kb_schema, "kb_records.json")
    self.assertIn("SCHEMA_MIN_ITEMS", {issue.code for issue in issues})

def test_invalid_date_and_non_https_url_are_rejected(self) -> None:
    record = self.valid_kb() | {"last_verified_at": "18-07-2026", "source_url": "http://example.test"}
    codes = {issue.code for issue in validate_schema(record, self.kb_schema, "kb_records.json")}
    self.assertEqual({"SCHEMA_DATE", "SCHEMA_HTTPS_URL"} - codes, set())
```

Also add separate tests for missing required, wrong type, enum, ID pattern, null allowance, root version mismatch, sorted issue order, and issue serialization with no offending value.

- [x] **Step 2: Run focused RED**

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_data_staging_validation -v
```

Expected: import or missing-schema failure caused by the absent implementation.

- [x] **Step 3: Add exact internal schemas**

Each root is an object with `schema_version=1`, `draft_version` pattern `^0\.1\.0-draft\.1$`, and `records`. Set `additionalProperties=false` at every object level. Use spec fields exactly. KB `question_examples` is 3..5 unique strings; all arrays use strings; category/region/intent/data origin/status use exact allowlists. Manifest `artifacts` has exactly 3 unique path records and `decisions` allows APPROVE/WITHHOLD/REJECT.

- [x] **Step 4: Implement only the tested JSON Schema subset**

Support object/array/string/integer/boolean/null, required, additionalProperties, const, enum, pattern, min/max length, min/max/unique items, ISO date/datetime and HTTPS URL. Sort returned issues by `(artifact, record_id or "", field or "", code)` and never attach the offending value.

- [x] **Step 5: Verify GREEN and commit**

Run focused unittest, root unittest discovery, secret scan, `git diff --check`; commit `feat(data): add DATA-001 staging contracts`.

## Task 2: Add cross-file, privacy, source, and hash validation CLI

**Files:**

- Modify: `scripts/data_staging_validation.py`
- Create: `scripts/validate_data_staging.py`
- Modify: `scripts/tests/test_data_staging_validation.py`
- Modify: `scripts/verify.ps1`
- Modify: `scripts/README.md`

**Interfaces:** Consumes Task 1 schema helpers. Produces `build_pending_manifest`, `validate_staging`, stable CLI and report.

- [x] **Step 1: Write RED business-rule tests**

Create temporary complete 20/3/12 fixtures and independently mutate them. Exact tests/rules:

```text
COUNT_KB / COUNT_OFFICE / COUNT_MAPPING
DUPLICATE_RECORD_ID / RECORD_ORDER
SOURCE_REGISTRY_ID_SET / SOURCE_DOMAIN_NOT_ALLOWED / SOURCE_METADATA_MISMATCH
ORPHAN_OFFICE_MAPPING / DUPLICATE_MAPPING_KEY / UNSUPPORTED_INTENT
PII_DETECTED / SECRET_DETECTED / MOCK_REFERENCE
KB_NOT_DRAFT / APPROVAL_METADATA_IN_DRAFT
MANIFEST_CONTENT_PATH_SET / MANIFEST_HASH_MISMATCH / MANIFEST_COUNT_MISMATCH
SELF_APPROVAL / WASTE_03_DECISION / INITIAL_PROJECTION_MISMATCH
RUNTIME_STAGING_REFERENCE
```

Privacy tests must prove a resident number, personal mobile, email, vehicle plate, detailed residential unit, and secret token are rejected while official office `044` telephone and office address fields pass.

- [x] **Step 2: Run RED**

Expected: missing `validate_staging`/CLI behavior failures.

- [x] **Step 3: Implement fail-closed business validation**

Allowed source hosts are exactly `plus.gov.kr`, `www.law.go.kr`, `law.go.kr`, `www.sjwaste.kr`, `www.wetax.go.kr`, `www.gov.kr`, `www.sejong.go.kr`. Only office `phone`/`address` fields may bypass personal-contact patterns. `map_url` may use `place.map.kakao.com` but never establishes provenance.

Static runtime-reference scan covers `apps/`, `packages/`, `supabase/seed.sql`, `supabase/migrations/`, and `database/`; comments mentioning the boundary are ignored, imports/path literals referring to `data/staging/` fail.

- [x] **Step 4: Implement manifest preparation and CLI**

```powershell
python -B scripts/validate_data_staging.py prepare --draft-dir data/staging/data-001/0.1.0-draft.1 --submitted-at 2026-07-18T18:00:00+09:00
python -B scripts/validate_data_staging.py validate --draft-dir data/staging/data-001/0.1.0-draft.1 --report data/processed/data-001/0.1.0-draft.1/validation-report.json
```

`prepare` hashes only three content files and atomically writes PENDING manifest. `validate` does not mutate staging. Success prints exactly `[PASS] step=VALIDATE-DATA-001`; failure prints issue code counts only and exits 1; usage error exits 2.

- [x] **Step 5: Add root gate and verify GREEN**

Add `VALIDATE-DATA-001` after `TEST-ROOT` using repository Python. Run focused tests plus `scripts/verify.ps1`; commit `feat(data): enforce DATA-001 review boundary`.

## Task 3: Author source-verified DRAFT artifacts and PM packet

**Files:**

- Modify: `data/official/kb_source_registry.csv`
- Create: four canonical JSON artifacts
- Create: validation report and PM review packet under `data/processed/data-001/0.1.0-draft.1/`
- Create: `docs/data-lineage/DATA-001-0.1.0-draft.1.md`

**Interfaces:** Consumes Task 2 CLI and matrices in this plan. Produces only PENDING review evidence; no release/seed.

- [x] **Step 1: Update source registry deterministically**

Keep 20 IDs/order. Set verification date `2026-07-18`, author `AI-DATA-BACKEND`, status `검수 대기`, reviewer blank. Replace MOVE-01..04 and CERT-01..05 with the exact plus URLs in the source matrix. Narrow TAX-02 title/scope. Do not invent TAX-03/05 plus links.

- [x] **Step 2: Author KB 20 records**

Use 5 records per category and 3..5 generalized questions each. Text must stay within the source matrix, preserve conditional documents/fees/times, and place personal lookup/legal/application limitations in `caution`. No contact number is copied into KB free text.

- [x] **Step 3: Author offices and 12 mappings**

Use the exact office/mapping matrix. All 12 candidates remain in staging; packet recommends 10 APPROVE and 2 REJECT. `map_url` uses the three official-page-provided Kakao links but provenance stays on sejong.go.kr.

- [x] **Step 4: Prepare manifest and run validation**

Run `prepare`, then `validate` twice. The second report and three hashes must be byte-identical to the first; counts 20/3/12, initial projection 19/3/10, issues 0, warning exactly `PM_REVIEW_REQUIRED`.

- [x] **Step 5: Generate PM packet and lineage**

Packet lists every record ID, service/office/mapping label, source link, verified date, safe-scope summary and recommended disposition. It clearly labels all content `미승인 DRAFT`, highlights WASTE-03 WITHHOLD and two mapping REJECT rows, and provides blank PM comment/check boxes. It must not claim PM approval.

- [x] **Step 6: Commit data draft**

Run focused/root tests, validator, secret scan, `git diff --check`; commit `data: prepare DATA-001 PM review package`.

## Task 4: Synchronize governance, versions, and final evidence

**Files:**

- Modify: this plan, approved spec status, D-033/A-026 status, TEAM_DECISIONS/PROJECT_PLAN only if implementation drift exists
- Modify: `TASKS.md`, `data/README.md`, `data/official/README.md`, `CODEX_FILE_INDEX.md`, `CHANGELOG.md`
- Modify: `versions/manifest.json`
- Complete: implementation note and INDEX

- [x] **Step 1: Set truthful task/version state**

Historical initial closeout set DRAFT 20/office 3/mapping 12 and validator PASS. Remediation 3 confirms the
current state as `AI scope complete / Review (PM pending)`: `official_data` remains `0.0.0-not-populated`,
`test_suite` is `0.7.0-data-trust-boundary`, `documentation` is `2.6.0`, and application/web/API/shared
contracts/DB/mock/prompt remain unchanged.

- [x] **Step 2: Run final verification evidence**

Invoke `superpowers:verification-before-completion`, then run focused unit, explicit staging validator, full `scripts/verify.ps1`, JSON parse, package validation, secret scan, `git diff --check`, and exact runtime staging-reference scan. Remediation 3 re-ran the exact verbose `TEST-ROOT` discovery once with live evidence: 171 tests passed in 511.715s (one Windows symlink capability skip). A fresh non-offline `scripts/verify.ps1` then passed end-to-end; its quiet `TEST-ROOT` stage took about 11 minutes before every remaining gate passed. The former “hang” was an early-stop/insufficient-observation conclusion, not a reproduced deterministic runner defect.

- [x] **Step 3: Independent review and remediation**

Invoke `superpowers:requesting-code-review`. Review against this plan, ADR-0015, privacy/source boundaries, validator bypasses, data scope and all 35 records. Resolve every Critical/Important finding and rerun Step 2.

Task 4 review found no Critical finding. Its one Important handoff finding (abbreviated command evidence in
IMP-20260718-007) was corrected to literal commands and full report hash; the historical spec version section was
labeled to avoid implying a current-manifest contradiction.

- [x] **Step 4: Closeout commit**

Completed 6W1H note, actual commands/results, versions, security/data/rollback/handoff, PM KEEP items. Committed with `docs(data): hand off DATA-001 for PM review`.

## 테스트 계획

- 단위: schema subset, cross-file, PII/secret, source allowlist, deterministic ordering/hash, manifest state.
- 계약: four JSON schemas and exact 20/3/12 artifacts.
- 통합: CLI prepare→validate→repeat, root verify integration.
- 보안/PII: representative patterns and official office public-contact allow case; logs contain no payload values.
- 회귀: WASTE-03 approval denial and 19/3/10 projection.
- runtime isolation: staging path imports/references 0.
- 접근성/성능: UI/runtime 없음; 35 records validator duration recorded, no performance target change.

## 위험과 롤백

- 변동 공식 사실: PM 승인 직전 링크·요금·기관 전화/시간을 다시 확인한다.
- tax legacy link: 추정 canonical을 쓰지 않고 packet에 사람 재확인 항목으로 남긴다.
- weak mappings: two REJECT recommendations stay out of future release unless new source and PM decision exist.
- rollback: approval 전에는 plan commits를 revert하고 staging/processed/schema/validator를 제거할 수 있다. official release/DB row가 없으므로 data migration rollback은 없다.
- recovery: content 변경 시 새 draft version을 만들고 새 hashes/PM review를 요구한다. 기존 reviewed manifest는 덮어쓰지 않는다.

## 인간이 승인해야 하는 사항 — KEEP

- 20 KB·3 office·12 mapping의 공식 source/content/표현/확인일 전수 검수.
- record별 APPROVE/WITHHOLD/REJECT와 비어 있지 않은 comment.
- TAX-03/05 canonical link와 2026 변동 사실 재확인.
- 기관 연락처·업무시간, 수수료·요일·환불 조건의 승인 직전 재확인.
- DATA-SEED-001 promotion/import 및 이후 readiness 변경.

## AI 내부 구현 세부

- schema helper 분리, fixture factory, stable rule code, atomic JSON writer, report ordering.
- 테스트 명명·formatting·내부 dataclass와 CLI parser 구성.
- 같은 공개 동작과 계약 안의 작은 중복 제거.

## 진행 기록

### Final Remediation 2 — canonical staging trust boundary

- [x] 개인정보·비밀·mock 검사를 manifest/registry/content의 모든 문자열에 적용하고, unknown property 보고는 고정 안전 경로만 사용한다. 기관 공개 연락처 예외는 추적된 승인 매트릭스의 exact `(office id, field, value)`에만 허용한다.
- [x] production CLI의 prepare/validate/migrate 입력을 canonical draft/registry로 고정하고, 입력·schema·승인 매트릭스의 symlink/junction/reparse 구성요소를 읽기 전에 거부한다. report는 canonical processed 경계에만 쓴다.
- [x] root verify는 canonical marker/schema 존재를 필수로 확인하고 staging 검증을 생략하지 않는다.
- [x] tracked runtime/operations code와 config 전체를 대소문자·slash·공백·문자열 결합 우회까지 fail-closed로 검사하며, validator/CLI/tests/root gate만 exact allowlist로 둔다.
- [x] 네 source audit의 개인정보 없는 tracked 요약과 hash-bound 승인 source matrix를 추가하고 KB/office/mapping/registry를 exact 비교한다.
- [x] duplicate JSON member, 네 artifact canonical bytes, schema 지원 keyword meta-validation을 TDD로 강제한다.
- [x] `TASKS.md`의 DATA-001 상태는 `Review`로 정규화하고 AI 완료/PM pending을 상세에 남긴다. lineage와 구현 노트의 재현·인계 경로를 tracked 근거로 갱신한다.

검증 체크포인트: 각 finding의 focused RED→GREEN, 전체 staging unittest, canonical validate 연속 2회와 report 결정성, JSON/CSV/schema/audit hash, secret/package/runtime/path 검사, PowerShell parser, `git diff --check`. 공식 release/seed/DB/API/product/version closeout은 변경하지 않는다.

독립 리뷰 후속: matrix는 파싱 전 validator code의 exact SHA-256 pin을 요구하고, report는 canonical validation report 한 경로만 허용한다. 네 audit도 production reparse preflight와 trusted hash reader를 통과하며, split PowerShell/config 경로와 한국어 비밀번호 값 회귀를 추가했다.

- 2026-07-18: Q-DATA-002=A, D-033/ADR-0015 승인.
- 2026-07-18: 사용자가 written spec을 승인하고 사람 작업 KEEP, 나머지 연속 진행, AI data draft 후 사용자 검토를 지시.
- 2026-07-18: 네 독립 source audit에서 신규 A/Blocker 0, mapping 10 APPROVE 권고/2 REJECT 권고 확인.
- 2026-07-18: `codex/data-001-staging-review` worktree baseline full gate PASS; Task 0 complete.
- 2026-07-18: Task 1 schemas/validator TDD complete; independent review found and fixed malformed-ID value exposure, boolean/integer equality, and unenforced numeric minimum. Re-review Spec PASS / Quality PASS at `a21f4fe`.
- 2026-07-18: Task 2 cross-file/privacy/source/hash/CLI gate complete. Independent review cycles closed one Critical and four Important findings, including Task 3 registry compatibility; final Spec PASS / Quality PASS at `327dab2` with 35 focused tests PASS.
- 2026-07-18: Task 3 DRAFT 20/3/12 and 35-row PM packet complete. Review corrected truthful submission provenance and canonical JSON bytes; final Spec PASS / Quality PASS at `f7b9157`, validator issues 0 with `PM_REVIEW_REQUIRED` only.

### Final Remediation 3 — root verification closeout

- [x] Removed no code and made no runner change: a single direct, unbuffered verbose root discovery established that `TEST-ROOT` completes rather than hangs (`171` tests, `511.715s`, exit `0`, one unavailable-symlink skip).
- [x] Ran one fresh non-offline full `scripts/verify.ps1` with a sufficient observation bound. `TEST-ROOT`, canonical `VALIDATE-DATA-001`, web/API/contract gates, both secret scans, package validation, and diff check all passed.
- [x] Re-ran the 62-test DATA-001 suite; canonical validation twice produced the same report SHA-256; PENDING, synthetic APPROVED, and synthetic REJECTED lifecycle coverage remains green through the focused lifecycle test.
- [x] Rechecked content/manifest/registry/matrix/audit pins and JSON/count boundaries. No official release, seed, ACTIVE record, runtime/API/DB/dependency change occurred.
- [x] Governance now records `AI scope complete / Review (PM pending)` and preserves PM approval as the only remaining DATA-001 gate.

## 결과와 회고

- 실제 결과: AI scope complete / Review (PM pending). DRAFT 20 KB·3 office·12 mapping과 PENDING manifest는 validator PASS이며 official release/seed/ACTIVE는 0이다.
- 계획과 달라진 점: Task 1·2 독립 리뷰에서 값 비노출, 검증 우회, 경로 쓰기 경계, canonical source registry 계약을 강화했고 Task 3에서 실제 제출 시각과 canonical JSON 바이트를 바로잡았다. Remediation 3는 충분한 단일 라이브 discovery와 fresh full gate로 기존 `TEST-ROOT` early-stop 기록을 해소했으며, runner defect를 발견하지 않아 코드 수정은 하지 않았다.
- 다음 단계: PM의 35-record 검수·decision/comment, 그 뒤 별도 DATA-SEED-001.
