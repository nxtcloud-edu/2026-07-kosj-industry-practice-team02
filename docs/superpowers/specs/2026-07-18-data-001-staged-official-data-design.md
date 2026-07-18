# DATA-001 staged official data design

- Status: Review — Q-DATA-002=A selected; written specification awaits user review
- Date: 2026-07-18 KST
- Decision: D-033 / ADR-0015
- Scope: DATA-001 authoring, validation, submission, PM approval artifact boundary
- Out of scope: official release generation, SQL seed/import, DB mutation, readiness 200, chat/admin code

## 1. Goal

AI/Data·Backend가 공식 출처에 근거한 KB 20건, 기관 3건, 지역×민원 매핑 12건을 안전한
staging artifact로 작성하고, 작성자와 다른 PM이 검토한 exact content에만 승인 결정을 남길 수
있게 한다. 승인 전 데이터는 어떤 시민 답변·seed·readiness·성과 지표에도 사용하지 않는다.

## 2. Non-goals

- 이 명세에서 official release나 `supabase/seed.sql`을 만들지 않는다.
- DB table, migration, public API, UI, 검색, LLM provider 동작을 바꾸지 않는다.
- PM 검수를 AI가 대신하거나 자동 승인하지 않는다.
- 실제 시민 질문, 개인정보, 내부 행정 데이터, 민간·블로그 출처를 수집하지 않는다.
- `KB-WASTE-03`을 초기 ACTIVE로 만들지 않는다.

## 3. Repository boundary

```text
data/
  staging/
    data-001/
      0.1.0-draft.1/
        kb_records.json
        offices.json
        office_service_mappings.json
        approval_manifest.json
  official/
    kb_source_registry.csv
    releases/                 # DATA-SEED-001이 후속 생성; DATA-001에서는 생성 금지
  processed/                  # validator가 만든 재현 가능 report; canonical 입력 아님
  mock/                       # staging·official과 완전 분리
```

`data/staging/`은 공식 출처를 바탕으로 작성 중인 미승인 자료다. `data/official/`은 source
registry와 후속 immutable release만 둔다. staging 파일을 official 디렉터리로 복사하는 것만으로
승격되지 않으며, hash-bound PM 승인과 DATA-SEED-001 promotion gate가 모두 필요하다.

## 4. Artifact responsibilities

| Artifact | 책임 | Canonical 여부 |
|---|---|---|
| `kb_records.json` | KB 20건의 구조화 DRAFT 내용·출처·작성자 | DATA-001 KB authoring canonical |
| `offices.json` | 아름동·도담동·조치원읍 공식 기관 3건 | DATA-001 office authoring canonical |
| `office_service_mappings.json` | 3개 지역×4 intent의 매핑 후보 12건 | DATA-001 mapping authoring canonical |
| `approval_manifest.json` | artifact hash/count, 제출 정보, 레코드별 PM 결정·comment | DATA-001 approval evidence canonical |
| `kb_source_registry.csv` | 20개 KB의 source assignment·확인 추적 index | source registry canonical; approval evidence 아님 |
| validator report | schema/error/count/hash summary | generated evidence; 입력 아님 |

네 JSON은 UTF-8, LF, 2-space indent, trailing newline을 사용하고 key와 record order를
deterministic하게 유지한다. 레코드는 public ID lexical order로 정렬한다.

## 5. KB draft contract

각 KB record는 다음을 필수로 가진다.

```text
id
data_origin = OFFICIAL
category
service_name
question_examples (3~5개, PII 없음)
answer_summary
procedure_steps (array)
required_documents (array)
processing_time (string|null)
fee (string|null)
department
provider
source_title
source_url
source_service_id (string|null)
last_verified_at
caution (string|null)
status = DRAFT
created_by = AI-DATA-BACKEND
approved_by = null
approved_at = null
```

`provider`는 포털 제공자/제도 소관을 source title에 혼합하지 않도록 별도 보존한다.
`source_service_id`는 정부24 `srvcId`처럼 URL 변경 감지에 유용한 공식 ID만 허용한다.
질문 예시는 일반화된 비개인 문장만 허용한다. source title, URL, date는 LLM이 생성할 수 없다.

기존 `contracts/kb-record.schema.json`과 필드 의미를 맞추되, 구현 계획에서는 provider,
data_origin, DRAFT/ACTIVE conditional과 질문 예시 3~5개를 표현할 repository data contract를
정확히 정의한다. 공개 OpenAPI 변경은 아니다.

## 6. Office draft contract

각 office record는 다음을 필수로 가진다.

```text
public_id
data_origin = OFFICIAL
region = 아름동 | 도담동 | 조치원읍
office_name
address
phone
opening_hours (string|null)
map_url (string|null)
provider
source_title
source_url
last_verified_at
created_by = AI-DATA-BACKEND
```

주소·전화는 기관의 공개 정보이며 source URL과 확인일이 없는 값은 허용하지 않는다. 지도 URL은
공식 기관 페이지가 제공하는 외부 목적지일 수 있지만 provenance source는 세종시 공식 페이지다.

## 7. Mapping draft contract

각 mapping은 다음을 가진다.

```text
office_public_id
intent
department_label (string|null)
evidence_source_url
last_verified_at
created_by = AI-DATA-BACKEND
```

`office_public_id`는 `offices.json`의 record를 참조하고 intent는 네 지원 분야만 허용한다.
복합키 `(office_public_id, intent)`는 유일해야 한다. 아름동×지방세와 도담동×대형폐기물은
source audit의 B/High 항목이므로 PM이 `department_label`과 1차 문의 범위를 명시적으로
승인하거나 해당 mapping을 withholding해야 한다.

## 8. Approval manifest contract

manifest는 다음 dataset metadata를 가진다.

```text
schema_version = 1
dataset_id = sejong-data-001
draft_version
state = DRAFT | PENDING_PM_REVIEW | APPROVED_FOR_INITIAL_RELEASE | REJECTED
created_by = AI-DATA-BACKEND
submitted_at (datetime|null)
reviewed_by (string|null)
reviewed_at (datetime|null)
review_comment (string|null)
artifacts[] = {path, record_count, sha256} # 세 content artifact만 포함
decisions[] = {record_type, record_id, decision, comment}
```

허용 decision은 `APPROVE_INITIAL_RELEASE`, `WITHHOLD_FOR_REGRESSION`, `REJECT`다.
`artifacts[]`는 `kb_records.json`, `offices.json`, `office_service_mappings.json`만 정확히 한 번씩
포함한다. manifest 자체는 자기참조 hash 대상이 아니며, 세 content artifact의 hash에 검수 metadata와
record decision을 결합하는 승인 증거다.
PENDING_PM_REVIEW 이상에서는 모든 artifact path/count/SHA-256이 필수다. APPROVED 상태에서는
`reviewed_by=PM`, non-empty review comment, review time과 모든 record decision이 필수이며
`reviewed_by != created_by`를 강제한다. artifact가 한 byte라도 바뀌면 hash mismatch로 승인을
무효화하고 새 draft version과 PM 재검수를 요구한다.

`APPROVED_FOR_INITIAL_RELEASE`는 모든 record가 승인됐다는 뜻이 아니라, 35개 record 각각의 처분이
완료되어 승인된 부분집합을 initial release 후보로 보낼 수 있다는 dataset 상태다. WASTE-03은 정확히
`WITHHOLD_FOR_REGRESSION`, source가 약한 mapping은 PM 결정에 따라 `REJECT`일 수 있다. dataset
전체를 승격할 수 없으면 manifest state를 `REJECTED`로 둔다.

## 9. State flow

```text
source audit
→ staging DRAFT 작성
→ schema/cross-file/PII/source validation
→ artifact hash와 PENDING_PM_REVIEW manifest 생성
→ PM record-by-record review
→ APPROVED_FOR_INITIAL_RELEASE 또는 REJECTED
→ 별도 DATA-SEED-001 promotion/import
```

AI/Data·Backend는 DRAFT 작성과 제출까지만 수행한다. PM만 승인/반려 결정을 확정한다.
DATA-001 완료는 승인 manifest와 검수 누락 0을 뜻하지만, DB seed 완료를 뜻하지 않는다.

## 10. Initial and final KB gates

현재 일반 요구의 최종 20 ACTIVE와 회귀 예외를 다음처럼 분리한다.

| Gate | KB | Office | Mapping | WASTE-03 |
|---|---:|---:|---:|---|
| staging 작성 완료 | 20 | 3 | 12 | DRAFT |
| initial PM approval | 19 | 3 | 10~12 | `WITHHOLD_FOR_REGRESSION` |
| DATA-SEED initial release | 19 | 3 | 10~12 | 포함 금지 |
| REG-001 이후 최종 상태 | 20 ACTIVE | 3+ | 10~12 | 관리자 후보→별도 승인으로 ACTIVE |

초기 release 준비 상태를 20 ACTIVE로 검사하지 않는다. 최종 DAR-001 20 ACTIVE는 REG-001 이후
검사한다. WASTE-03을 staging approval만으로 seed에 포함하면 회귀 시나리오 실패다.

## 11. Validation behavior

Validator는 다음 중 하나라도 발견하면 non-zero로 종료하고 manifest 제출을 막는다.

- schema 위반, unknown field, 잘못된 enum/date/URL
- KB 20·office 3·mapping 12 staging count 불일치
- 중복 public ID·mapping composite key·question example
- office reference가 없는 mapping
- source title/URL/date/provider 누락
- PII pattern, 실제 시민 식별자, 비밀 pattern
- `data_origin != OFFICIAL` 또는 mock path/reference
- DRAFT에서 ACTIVE/PENDING/approved metadata 사용
- WASTE-03 초기 approval decision 누락 또는 잘못된 승인
- artifact hash/count 불일치
- 작성자와 승인자 동일

오류 메시지는 파일, record ID, field, stable rule code만 출력하고 전체 answer/source payload나
비밀값을 로그에 복사하지 않는다.

## 12. Source quality rules

- 정부24 9행은 현재 `plus.gov.kr` canonical URL로 교체하고 legacy URL은 lineage note에만 남긴다.
- KB-TAX-02는 로그인 후 본인 고지 확인·납부 경로로 범위를 제한한다. 납기·세액·연납 혜택은
  2026 최신 공식 전용 출처와 PM 재승인 없이는 넣지 않는다.
- 대형폐기물 요금·요일·환불과 기관 연락처·업무시간은 PM 승인 직전에 다시 열어 확인한다.
- 무인발급 시간·수수료·가능민원을 전국 고정값으로 단정하지 않는다.
- 검색 결과, 블로그, 민간 안내 페이지는 source로 채택하지 않는다.
- canonical source registry 파일명은 `data/official/kb_source_registry.csv`다.

## 13. Test strategy for the later implementation plan

1. Schema fixtures: valid minimal/full record와 unknown/missing/wrong-type RED fixtures.
2. Cross-file fixtures: orphan mapping, duplicate ID, count drift, invalid intent.
3. Approval fixtures: self approval, empty comment, missing decision, stale hash, WASTE-03 wrong decision.
4. Privacy fixtures: representative PII/secret patterns, official public office contact allow case.
5. Determinism: repeated validation produces byte-identical normalized output/report and hashes.
6. Repository boundary: staging path를 seed/readiness/citizen code가 참조하지 않음을 정적 검사.
7. Source registry: 20 IDs exact set, canonical URL/date/provider/writer/reviewer completeness report.
8. Promotion handoff fixture: initial approved set is KB 19, office 3, mapping 10~12, WASTE-03 0.

No new production dependency is authorized. Existing Ajv dependency or Python standard library may be used;
the implementation plan must select one exact validator path and test it TDD-first.

## 14. Failure, rollback, and recovery

- Validation failure leaves staging unchanged and produces no approval transition.
- PM rejection keeps the draft immutable for audit and requires a new draft version for corrections.
- Hash mismatch invalidates approval; it never auto-updates the manifest decision.
- DATA-001 rollback removes only the unapproved draft version and generated report after confirming no human
  review evidence is needed. Approved manifests are not rewritten.
- Official release/DB rollback is explicitly outside this spec and belongs to DATA-SEED-001.

## 15. Version impact

- documentation: `2.4.1 → 2.4.2`
- product/application/web/API/shared contracts/DB schema/official data/mock data/prompt/test: unchanged
- `official_data` remains `0.0.0-not-populated` until PM approval and DATA-SEED-001 promotion succeed.

## 16. Acceptance criteria

The written design is ready for implementation planning only when the user approves this exact specification.
The subsequent DATA-001 plan must produce:

- four staging artifacts with 20/3/12 records;
- automated fail-closed validation and human-readable summary;
- hash-bound manifest ready for PM review;
- canonical source registry references;
- no official release, DB seed, ACTIVE row, readiness change, product code, or new production dependency.
