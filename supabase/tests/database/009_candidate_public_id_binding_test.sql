BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;

SELECT plan(36);

SELECT has_function(
  'app_api', 'approve_kb_candidate_with_public_id',
  ARRAY['uuid', 'text', 'text', 'text', 'text'],
  'backend-only explicit public-id approval capability exists'
);

SELECT ok(
  pg_catalog.to_regprocedure(
    'app_api.approve_kb_candidate(uuid,text,text,text)'
  ) IS NOT NULL,
  'generic four-argument approval signature remains unchanged'
);

SELECT is(
  (
    SELECT pg_catalog.pg_get_function_result(functions.oid)
    FROM pg_catalog.pg_proc AS functions
    WHERE functions.oid = pg_catalog.to_regprocedure(
      'app_api.approve_kb_candidate_with_public_id(uuid,text,text,text,text)'
    )
  ),
  'text'::text,
  'explicit binding returns only the activated public id'
);

SELECT ok(
  (
    SELECT owners.rolname = 'sejong_schema_owner'
      AND functions.prosecdef
      AND functions.proconfig = ARRAY['search_path=pg_catalog, pg_temp']::text[]
    FROM pg_catalog.pg_proc AS functions
    JOIN pg_catalog.pg_roles AS owners ON owners.oid = functions.proowner
    WHERE functions.oid = pg_catalog.to_regprocedure(
      'app_api.approve_kb_candidate_with_public_id(uuid,text,text,text,text)'
    )
  ),
  'explicit binding is schema-owner SECURITY DEFINER with fixed search_path'
);

SELECT ok(
  NOT EXISTS (
    SELECT 1
    FROM pg_catalog.pg_proc AS functions
    CROSS JOIN LATERAL pg_catalog.aclexplode(
      COALESCE(functions.proacl, pg_catalog.acldefault('f', functions.proowner))
    ) AS privileges
    WHERE functions.oid = pg_catalog.to_regprocedure(
      'app_api.approve_kb_candidate_with_public_id(uuid,text,text,text,text)'
    )
      AND privileges.grantee = 0
      AND privileges.privilege_type = 'EXECUTE'
  )
  AND NOT pg_catalog.has_function_privilege(
    'anon',
    'app_api.approve_kb_candidate_with_public_id(uuid,text,text,text,text)',
    'EXECUTE'
  )
  AND NOT pg_catalog.has_function_privilege(
    'authenticated',
    'app_api.approve_kb_candidate_with_public_id(uuid,text,text,text,text)',
    'EXECUTE'
  )
  AND pg_catalog.has_function_privilege(
    'sejong_backend',
    'app_api.approve_kb_candidate_with_public_id(uuid,text,text,text,text)',
    'EXECUTE'
  ),
  'only the backend role can execute the explicit binding capability'
);

SELECT ok(
  NOT pg_catalog.has_schema_privilege('sejong_backend', 'app_private', 'USAGE')
  AND NOT pg_catalog.has_table_privilege(
    'sejong_backend', 'app_private.kb_candidates', 'SELECT'
  )
  AND NOT pg_catalog.has_table_privilege(
    'sejong_backend', 'app_private.kb_documents', 'UPDATE'
  ),
  'explicit binding adds no direct private schema or table access'
);

CREATE TEMP TABLE binding_cases (
  label text PRIMARY KEY,
  event_id uuid NOT NULL,
  failure_id uuid NOT NULL,
  candidate_id uuid NOT NULL,
  created_by text NOT NULL,
  title text NOT NULL,
  answer_summary text NOT NULL,
  data_origin app_private.data_origin NOT NULL,
  source_title text NOT NULL,
  source_url text NOT NULL
) ON COMMIT DROP;

INSERT INTO binding_cases VALUES
  (
    'exact', 'a6700000-0000-4000-8000-000000000001',
    'b6700000-0000-4000-8000-000000000001',
    'c6700000-0000-4000-8000-000000000001', 'OPERATOR-LOCAL-001',
    '침대 프레임 배출 수수료',
    '공식 품목표의 침대 프레임 수수료는 1인용침대 8,000원, 2인용침대 10,000원으로 표시됩니다.',
    'OFFICIAL', '배출항목선택',
    'https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305'
  ),
  (
    'wrong-id', 'a6700000-0000-4000-8000-000000000002',
    'b6700000-0000-4000-8000-000000000002',
    'c6700000-0000-4000-8000-000000000002', 'OPERATOR-LOCAL-001',
    '침대 프레임 배출 수수료',
    '공식 품목표의 침대 프레임 수수료는 1인용침대 8,000원, 2인용침대 10,000원으로 표시됩니다.',
    'OFFICIAL', '배출항목선택',
    'https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305'
  ),
  (
    'mismatch', 'a6700000-0000-4000-8000-000000000003',
    'b6700000-0000-4000-8000-000000000003',
    'c6700000-0000-4000-8000-000000000003', 'OPERATOR-LOCAL-001',
    '침대 프레임 배출 수수료', 'canonical identity drift',
    'OFFICIAL', '배출항목선택',
    'https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305'
  ),
  (
    'mock', 'a6700000-0000-4000-8000-000000000004',
    'b6700000-0000-4000-8000-000000000004',
    'c6700000-0000-4000-8000-000000000004', 'OPERATOR-LOCAL-001',
    '침대 프레임 배출 수수료',
    '공식 품목표의 침대 프레임 수수료는 1인용침대 8,000원, 2인용침대 10,000원으로 표시됩니다.',
    'MOCK', '배출항목선택',
    'https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305'
  ),
  (
    'self', 'a6700000-0000-4000-8000-000000000005',
    'b6700000-0000-4000-8000-000000000005',
    'c6700000-0000-4000-8000-000000000005', 'PM-LOCAL-001',
    '침대 프레임 배출 수수료',
    '공식 품목표의 침대 프레임 수수료는 1인용침대 8,000원, 2인용침대 10,000원으로 표시됩니다.',
    'OFFICIAL', '배출항목선택',
    'https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305'
  ),
  (
    'collision', 'a6700000-0000-4000-8000-000000000006',
    'b6700000-0000-4000-8000-000000000006',
    'c6700000-0000-4000-8000-000000000006', 'OPERATOR-LOCAL-002',
    '침대 프레임 배출 수수료',
    '공식 품목표의 침대 프레임 수수료는 1인용침대 8,000원, 2인용침대 10,000원으로 표시됩니다.',
    'OFFICIAL', '배출항목선택',
    'https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305'
  ),
  (
    'generic', 'a6700000-0000-4000-8000-000000000007',
    'b6700000-0000-4000-8000-000000000007',
    'c6700000-0000-4000-8000-000000000007', 'OPERATOR-LOCAL-003',
    '일반 대형폐기물 안내', '일반 대형폐기물 답변',
    'OFFICIAL', '일반 공식 출처', 'https://example.invalid/00670/generic'
  );

INSERT INTO binding_cases (
  label, event_id, failure_id, candidate_id, created_by, title,
  answer_summary, data_origin, source_title, source_url
)
SELECT
  drift.label, drift.event_id, drift.failure_id, drift.candidate_id,
  exact.created_by, exact.title, exact.answer_summary, exact.data_origin,
  exact.source_title, exact.source_url
FROM binding_cases AS exact
CROSS JOIN (
  VALUES
    ('drift-title',
     'a6700000-0000-4000-8000-000000000008'::uuid,
     'b6700000-0000-4000-8000-000000000008'::uuid,
     'c6700000-0000-4000-8000-000000000008'::uuid),
    ('drift-question',
     'a6700000-0000-4000-8000-000000000009'::uuid,
     'b6700000-0000-4000-8000-000000000009'::uuid,
     'c6700000-0000-4000-8000-000000000009'::uuid),
    ('drift-category',
     'a6700000-0000-4000-8000-000000000010'::uuid,
     'b6700000-0000-4000-8000-000000000010'::uuid,
     'c6700000-0000-4000-8000-000000000010'::uuid),
    ('drift-procedure',
     'a6700000-0000-4000-8000-000000000011'::uuid,
     'b6700000-0000-4000-8000-000000000011'::uuid,
     'c6700000-0000-4000-8000-000000000011'::uuid),
    ('drift-documents',
     'a6700000-0000-4000-8000-000000000012'::uuid,
     'b6700000-0000-4000-8000-000000000012'::uuid,
     'c6700000-0000-4000-8000-000000000012'::uuid),
    ('drift-processing',
     'a6700000-0000-4000-8000-000000000013'::uuid,
     'b6700000-0000-4000-8000-000000000013'::uuid,
     'c6700000-0000-4000-8000-000000000013'::uuid),
    ('drift-fee',
     'a6700000-0000-4000-8000-000000000014'::uuid,
     'b6700000-0000-4000-8000-000000000014'::uuid,
     'c6700000-0000-4000-8000-000000000014'::uuid),
    ('drift-department',
     'a6700000-0000-4000-8000-000000000015'::uuid,
     'b6700000-0000-4000-8000-000000000015'::uuid,
     'c6700000-0000-4000-8000-000000000015'::uuid),
    ('drift-source-title',
     'a6700000-0000-4000-8000-000000000016'::uuid,
     'b6700000-0000-4000-8000-000000000016'::uuid,
     'c6700000-0000-4000-8000-000000000016'::uuid),
    ('drift-source-url',
     'a6700000-0000-4000-8000-000000000017'::uuid,
     'b6700000-0000-4000-8000-000000000017'::uuid,
     'c6700000-0000-4000-8000-000000000017'::uuid),
    ('drift-verified-at',
     'a6700000-0000-4000-8000-000000000018'::uuid,
     'b6700000-0000-4000-8000-000000000018'::uuid,
     'c6700000-0000-4000-8000-000000000018'::uuid),
    ('drift-caution',
     'a6700000-0000-4000-8000-000000000019'::uuid,
     'b6700000-0000-4000-8000-000000000019'::uuid,
     'c6700000-0000-4000-8000-000000000019'::uuid)
) AS drift(label, event_id, failure_id, candidate_id)
WHERE exact.label = 'exact';

INSERT INTO app_private.interaction_events (
  id, intent, answer_status, fallback_reason, source_count, used_source_ids,
  response_time_ms, is_test, request_id
)
SELECT
  cases.event_id, 'BULKY_WASTE', 'FALLBACK', 'INSUFFICIENT_GROUNDING',
  0, '[]'::jsonb, 10, true, cases.event_id
FROM binding_cases AS cases;

INSERT INTO app_private.failed_questions (
  id, interaction_event_id, masked_question, intent, fallback_reason,
  candidate_eligible, status, created_at, text_expires_at
)
SELECT
  cases.failure_id, cases.event_id, '[MASKED] 00670 synthetic fixture',
  'BULKY_WASTE', 'INSUFFICIENT_GROUNDING', true, 'REASON_CONFIRMED',
  TIMESTAMPTZ '2026-07-22 00:00:00+00',
  TIMESTAMPTZ '2026-08-21 00:00:00+00'
FROM binding_cases AS cases;

INSERT INTO app_private.kb_candidates (
  id, failed_question_id, title, representative_question, data_origin,
  category, answer_summary, procedure_steps, required_documents,
  processing_time, fee, department, source_title, source_url,
  last_verified_at, caution, created_by, review_status
)
SELECT
  cases.candidate_id, cases.failure_id, cases.title,
  CASE WHEN cases.label = 'generic'
    THEN '일반 대형폐기물은 어떻게 배출하나요?'
    ELSE '침대 2인용 프레임 수수료가 얼마예요?'
  END,
  cases.data_origin, 'BULKY_WASTE', cases.answer_summary,
  CASE WHEN cases.label = 'generic'
    THEN '["일반 절차를 확인합니다."]'::jsonb
    ELSE '["공식 품목표에서 침대 프레임의 1인용침대 또는 2인용침대 항목을 확인합니다.","해당 수수료로 공식 배출 절차를 진행합니다."]'::jsonb
  END,
  '[]'::jsonb, NULL,
  CASE WHEN cases.label = 'generic'
    THEN '별도 확인'
    ELSE '1인용침대 8,000원; 2인용침대 10,000원'
  END,
  CASE WHEN cases.label = 'generic'
    THEN '일반 담당부서'
    ELSE '세종특별자치시시설관리공단'
  END,
  cases.source_title, cases.source_url,
  CASE WHEN cases.label = 'generic'
    THEN DATE '2026-07-22'
    ELSE DATE '2026-07-18'
  END,
  CASE WHEN cases.label = 'generic'
    THEN NULL
    ELSE '공식 품목표의 1인용침대·2인용침대 항목을 그대로 따릅니다. 매트리스 포함 가격이나 실제 규격을 단정하지 않습니다.'
  END,
  cases.created_by, 'PENDING_APPROVAL'
FROM binding_cases AS cases;

UPDATE app_private.kb_candidates AS candidates
SET title = '침대 프레임 수수료 안내'
FROM binding_cases AS cases
WHERE cases.label = 'drift-title' AND candidates.id = cases.candidate_id;

UPDATE app_private.kb_candidates AS candidates
SET representative_question = '침대 1인용 프레임 수수료가 얼마예요?'
FROM binding_cases AS cases
WHERE cases.label = 'drift-question' AND candidates.id = cases.candidate_id;

UPDATE app_private.kb_candidates AS candidates
SET category = 'LOCAL_TAX_GENERAL'
FROM binding_cases AS cases
WHERE cases.label = 'drift-category' AND candidates.id = cases.candidate_id;

UPDATE app_private.kb_candidates AS candidates
SET procedure_steps = '["다른 절차를 확인합니다."]'::jsonb
FROM binding_cases AS cases
WHERE cases.label = 'drift-procedure' AND candidates.id = cases.candidate_id;

UPDATE app_private.kb_candidates AS candidates
SET required_documents = '["추가 서류"]'::jsonb
FROM binding_cases AS cases
WHERE cases.label = 'drift-documents' AND candidates.id = cases.candidate_id;

UPDATE app_private.kb_candidates AS candidates
SET processing_time = '즉시'
FROM binding_cases AS cases
WHERE cases.label = 'drift-processing' AND candidates.id = cases.candidate_id;

UPDATE app_private.kb_candidates AS candidates
SET fee = '별도 수수료'
FROM binding_cases AS cases
WHERE cases.label = 'drift-fee' AND candidates.id = cases.candidate_id;

UPDATE app_private.kb_candidates AS candidates
SET department = '다른 담당 기관'
FROM binding_cases AS cases
WHERE cases.label = 'drift-department' AND candidates.id = cases.candidate_id;

UPDATE app_private.kb_candidates AS candidates
SET source_title = '다른 공식 출처'
FROM binding_cases AS cases
WHERE cases.label = 'drift-source-title' AND candidates.id = cases.candidate_id;

UPDATE app_private.kb_candidates AS candidates
SET source_url = 'https://example.invalid/00670/drift'
FROM binding_cases AS cases
WHERE cases.label = 'drift-source-url' AND candidates.id = cases.candidate_id;

UPDATE app_private.kb_candidates AS candidates
SET last_verified_at = DATE '2026-07-17'
FROM binding_cases AS cases
WHERE cases.label = 'drift-verified-at' AND candidates.id = cases.candidate_id;

UPDATE app_private.kb_candidates AS candidates
SET caution = '다른 주의 사항'
FROM binding_cases AS cases
WHERE cases.label = 'drift-caution' AND candidates.id = cases.candidate_id;

SELECT throws_ok(
  $$SELECT app_api.approve_kb_candidate_with_public_id(
    'c6700000-0000-4000-8000-000000000002', 'PM-LOCAL-001', 'APPROVER',
    '공식 품목표 확인', 'KB-WASTE-99'
  )$$,
  'P1003', 'INVALID_WORKFLOW_STATE', 'wrong reserved public id is rejected'
);

SELECT ok(
  (
    SELECT review_status = 'PENDING_APPROVAL' AND activated_kb_id IS NULL
    FROM app_private.kb_candidates
    WHERE id = 'c6700000-0000-4000-8000-000000000002'
  )
  AND NOT EXISTS (
    SELECT 1 FROM app_private.audit_logs
    WHERE target_id = 'c6700000-0000-4000-8000-000000000002'
  ),
  'wrong-id failure rolls back candidate and audit state'
);

SELECT throws_ok(
  $$SELECT app_api.approve_kb_candidate_with_public_id(
    'c6700000-0000-4000-8000-000000000003', 'PM-LOCAL-001', 'APPROVER',
    '공식 품목표 확인', 'KB-WASTE-03'
  )$$,
  'P1003', 'INVALID_WORKFLOW_STATE', 'canonical identity mismatch is rejected'
);

SELECT ok(
  (
    SELECT review_status = 'PENDING_APPROVAL' AND activated_kb_id IS NULL
    FROM app_private.kb_candidates
    WHERE id = 'c6700000-0000-4000-8000-000000000003'
  )
  AND NOT EXISTS (
    SELECT 1 FROM app_private.kb_documents
    WHERE public_id = 'KB-C6700000000040008000000000000003'
  ),
  'identity failure creates no generated ACTIVE row'
);

SELECT throws_ok(
  $$SELECT app_api.approve_kb_candidate_with_public_id(
    'c6700000-0000-4000-8000-000000000004', 'PM-LOCAL-001', 'APPROVER',
    '공식 품목표 확인', 'KB-WASTE-03'
  )$$,
  'P1003', 'INVALID_WORKFLOW_STATE', 'MOCK candidate is rejected'
);

SELECT ok(
  (
    SELECT review_status = 'PENDING_APPROVAL' AND activated_kb_id IS NULL
    FROM app_private.kb_candidates
    WHERE id = 'c6700000-0000-4000-8000-000000000004'
  )
  AND NOT EXISTS (
    SELECT 1 FROM app_private.audit_logs
    WHERE target_id = 'c6700000-0000-4000-8000-000000000004'
  ),
  'MOCK failure rolls back every workflow write'
);

SELECT throws_ok(
  pg_catalog.format(
    $query$SELECT app_api.approve_kb_candidate_with_public_id(
      %L::uuid, 'PM-LOCAL-001', 'APPROVER', '필드별 정본 확인', 'KB-WASTE-03'
    )$query$,
    cases.candidate_id::text
  ),
  'P1003', 'INVALID_WORKFLOW_STATE', 'title drift is rejected'
)
FROM binding_cases AS cases
WHERE cases.label = 'drift-title';

SELECT throws_ok(
  pg_catalog.format(
    $query$SELECT app_api.approve_kb_candidate_with_public_id(
      %L::uuid, 'PM-LOCAL-001', 'APPROVER', '필드별 정본 확인', 'KB-WASTE-03'
    )$query$,
    cases.candidate_id::text
  ),
  'P1003', 'INVALID_WORKFLOW_STATE', 'representative question drift is rejected'
)
FROM binding_cases AS cases
WHERE cases.label = 'drift-question';

SELECT throws_ok(
  pg_catalog.format(
    $query$SELECT app_api.approve_kb_candidate_with_public_id(
      %L::uuid, 'PM-LOCAL-001', 'APPROVER', '필드별 정본 확인', 'KB-WASTE-03'
    )$query$,
    cases.candidate_id::text
  ),
  'P1003', 'INVALID_WORKFLOW_STATE', 'category drift is rejected'
)
FROM binding_cases AS cases
WHERE cases.label = 'drift-category';

SELECT throws_ok(
  pg_catalog.format(
    $query$SELECT app_api.approve_kb_candidate_with_public_id(
      %L::uuid, 'PM-LOCAL-001', 'APPROVER', '필드별 정본 확인', 'KB-WASTE-03'
    )$query$,
    cases.candidate_id::text
  ),
  'P1003', 'INVALID_WORKFLOW_STATE', 'procedure steps drift is rejected'
)
FROM binding_cases AS cases
WHERE cases.label = 'drift-procedure';

SELECT throws_ok(
  pg_catalog.format(
    $query$SELECT app_api.approve_kb_candidate_with_public_id(
      %L::uuid, 'PM-LOCAL-001', 'APPROVER', '필드별 정본 확인', 'KB-WASTE-03'
    )$query$,
    cases.candidate_id::text
  ),
  'P1003', 'INVALID_WORKFLOW_STATE', 'required documents drift is rejected'
)
FROM binding_cases AS cases
WHERE cases.label = 'drift-documents';

SELECT throws_ok(
  pg_catalog.format(
    $query$SELECT app_api.approve_kb_candidate_with_public_id(
      %L::uuid, 'PM-LOCAL-001', 'APPROVER', '필드별 정본 확인', 'KB-WASTE-03'
    )$query$,
    cases.candidate_id::text
  ),
  'P1003', 'INVALID_WORKFLOW_STATE', 'processing time drift is rejected'
)
FROM binding_cases AS cases
WHERE cases.label = 'drift-processing';

SELECT throws_ok(
  pg_catalog.format(
    $query$SELECT app_api.approve_kb_candidate_with_public_id(
      %L::uuid, 'PM-LOCAL-001', 'APPROVER', '필드별 정본 확인', 'KB-WASTE-03'
    )$query$,
    cases.candidate_id::text
  ),
  'P1003', 'INVALID_WORKFLOW_STATE', 'fee drift is rejected'
)
FROM binding_cases AS cases
WHERE cases.label = 'drift-fee';

SELECT throws_ok(
  pg_catalog.format(
    $query$SELECT app_api.approve_kb_candidate_with_public_id(
      %L::uuid, 'PM-LOCAL-001', 'APPROVER', '필드별 정본 확인', 'KB-WASTE-03'
    )$query$,
    cases.candidate_id::text
  ),
  'P1003', 'INVALID_WORKFLOW_STATE', 'department drift is rejected'
)
FROM binding_cases AS cases
WHERE cases.label = 'drift-department';

SELECT throws_ok(
  pg_catalog.format(
    $query$SELECT app_api.approve_kb_candidate_with_public_id(
      %L::uuid, 'PM-LOCAL-001', 'APPROVER', '필드별 정본 확인', 'KB-WASTE-03'
    )$query$,
    cases.candidate_id::text
  ),
  'P1003', 'INVALID_WORKFLOW_STATE', 'source title drift is rejected'
)
FROM binding_cases AS cases
WHERE cases.label = 'drift-source-title';

SELECT throws_ok(
  pg_catalog.format(
    $query$SELECT app_api.approve_kb_candidate_with_public_id(
      %L::uuid, 'PM-LOCAL-001', 'APPROVER', '필드별 정본 확인', 'KB-WASTE-03'
    )$query$,
    cases.candidate_id::text
  ),
  'P1003', 'INVALID_WORKFLOW_STATE', 'source URL drift is rejected'
)
FROM binding_cases AS cases
WHERE cases.label = 'drift-source-url';

SELECT throws_ok(
  pg_catalog.format(
    $query$SELECT app_api.approve_kb_candidate_with_public_id(
      %L::uuid, 'PM-LOCAL-001', 'APPROVER', '필드별 정본 확인', 'KB-WASTE-03'
    )$query$,
    cases.candidate_id::text
  ),
  'P1003', 'INVALID_WORKFLOW_STATE', 'verification date drift is rejected'
)
FROM binding_cases AS cases
WHERE cases.label = 'drift-verified-at';

SELECT throws_ok(
  pg_catalog.format(
    $query$SELECT app_api.approve_kb_candidate_with_public_id(
      %L::uuid, 'PM-LOCAL-001', 'APPROVER', '필드별 정본 확인', 'KB-WASTE-03'
    )$query$,
    cases.candidate_id::text
  ),
  'P1003', 'INVALID_WORKFLOW_STATE', 'caution drift is rejected'
)
FROM binding_cases AS cases
WHERE cases.label = 'drift-caution';

SELECT ok(
  (
    SELECT pg_catalog.count(*) = 12
      AND pg_catalog.bool_and(
        candidates.review_status = 'PENDING_APPROVAL'
        AND candidates.activated_kb_id IS NULL
      )
    FROM app_private.kb_candidates AS candidates
    JOIN binding_cases AS cases ON cases.candidate_id = candidates.id
    WHERE cases.label LIKE 'drift-%'
  )
  AND NOT EXISTS (
    SELECT 1
    FROM app_private.audit_logs AS audits
    JOIN binding_cases AS cases ON cases.candidate_id = audits.target_id
    WHERE cases.label LIKE 'drift-%'
  )
  AND NOT EXISTS (
    SELECT 1 FROM app_private.kb_documents
    WHERE public_id = 'KB-WASTE-03'
  ),
  'every per-field drift failure rolls back candidate, audit and ACTIVE state'
);

SELECT throws_ok(
  $$SELECT app_api.approve_kb_candidate_with_public_id(
    'c6700000-0000-4000-8000-000000000005', 'PM-LOCAL-001', 'APPROVER',
    '공식 품목표 확인', 'KB-WASTE-03'
  )$$,
  'P1003', 'INVALID_WORKFLOW_STATE', 'self review is mapped to stable workflow failure'
);

SELECT ok(
  (
    SELECT review_status = 'PENDING_APPROVAL' AND activated_kb_id IS NULL
    FROM app_private.kb_candidates
    WHERE id = 'c6700000-0000-4000-8000-000000000005'
  )
  AND NOT EXISTS (
    SELECT 1 FROM app_private.audit_logs
    WHERE target_id = 'c6700000-0000-4000-8000-000000000005'
  ),
  'self-review failure leaves no partial approval or audit'
);

SELECT is(
  app_api.approve_kb_candidate_with_public_id(
    'c6700000-0000-4000-8000-000000000001', 'PM-LOCAL-001', 'APPROVER',
    '공식 품목표와 canonical 값 확인', 'KB-WASTE-03'
  ),
  'KB-WASTE-03'::text,
  'exact canonical candidate activates with the reserved public id'
);

SELECT results_eq(
  $$
    SELECT
      documents.public_id, documents.data_origin::text, documents.category::text,
      documents.service_name, documents.answer_summary,
      documents.procedure_steps, documents.required_documents,
      documents.processing_time, documents.fee, documents.department,
      documents.source_title, documents.source_url, documents.last_verified_at,
      documents.caution, questions.question_example
    FROM app_private.kb_documents AS documents
    JOIN app_private.kb_question_examples AS questions
      ON questions.kb_document_id = documents.id
    WHERE documents.public_id = 'KB-WASTE-03'
  $$,
  $$VALUES (
    'KB-WASTE-03'::text, 'OFFICIAL'::text, 'BULKY_WASTE'::text,
    '침대 프레임 배출 수수료'::text,
    '공식 품목표의 침대 프레임 수수료는 1인용침대 8,000원, 2인용침대 10,000원으로 표시됩니다.'::text,
    '["공식 품목표에서 침대 프레임의 1인용침대 또는 2인용침대 항목을 확인합니다.","해당 수수료로 공식 배출 절차를 진행합니다."]'::jsonb,
    '[]'::jsonb, NULL::text,
    '1인용침대 8,000원; 2인용침대 10,000원'::text,
    '세종특별자치시시설관리공단'::text, '배출항목선택'::text,
    'https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305'::text,
    DATE '2026-07-18',
    '공식 품목표의 1인용침대·2인용침대 항목을 그대로 따릅니다. 매트리스 포함 가격이나 실제 규격을 단정하지 않습니다.'::text,
    '침대 2인용 프레임 수수료가 얼마예요?'::text
  )$$,
  'reserved ACTIVE row and question preserve every canonical field exactly'
);

SELECT ok(
  (
    SELECT review_status = 'APPROVED'
      AND reviewed_by = 'PM-LOCAL-001'
      AND review_comment = '공식 품목표와 canonical 값 확인'
      AND activated_kb_id IS NOT NULL
    FROM app_private.kb_candidates
    WHERE id = 'c6700000-0000-4000-8000-000000000001'
  )
  AND (
    SELECT action = 'CANDIDATE_APPROVED'
      AND changed_field_names =
        '["review_status","reviewed_by","review_comment","approved_at","activated_kb_id"]'::jsonb
    FROM app_private.audit_logs
    WHERE target_id = 'c6700000-0000-4000-8000-000000000001'
  ),
  'exact success updates candidate and metadata-only audit together'
);

SELECT throws_ok(
  $$SELECT app_api.approve_kb_candidate_with_public_id(
    'c6700000-0000-4000-8000-000000000006', 'PM-LOCAL-001', 'APPROVER',
    '공식 품목표 확인', 'KB-WASTE-03'
  )$$,
  'P1003', 'INVALID_WORKFLOW_STATE', 'reserved public-id collision is rejected'
);

SELECT ok(
  (
    SELECT review_status = 'PENDING_APPROVAL' AND activated_kb_id IS NULL
    FROM app_private.kb_candidates
    WHERE id = 'c6700000-0000-4000-8000-000000000006'
  )
  AND NOT EXISTS (
    SELECT 1 FROM app_private.kb_documents
    WHERE public_id = 'KB-C6700000000040008000000000000006'
  )
  AND NOT EXISTS (
    SELECT 1 FROM app_private.audit_logs
    WHERE target_id = 'c6700000-0000-4000-8000-000000000006'
  ),
  'collision rolls back generated row, candidate mutation and audit atomically'
);

SELECT is(
  app_api.approve_kb_candidate(
    'c6700000-0000-4000-8000-000000000007', 'PM-LOCAL-001', 'APPROVER',
    '일반 공식 출처 확인'
  ),
  'KB-C6700000000040008000000000000007'::text,
  'generic four-argument approval keeps its UUID-derived public id behavior'
);

SELECT ok(
  EXISTS (
    SELECT 1 FROM app_private.kb_documents
    WHERE public_id = 'KB-WASTE-03' AND status = 'ACTIVE'
  )
  AND EXISTS (
    SELECT 1 FROM app_private.kb_documents
    WHERE public_id = 'KB-C6700000000040008000000000000007' AND status = 'ACTIVE'
  ),
  'reserved and generic approvals coexist without changing generic flow'
);

SELECT results_eq(
  $$
    SELECT
      (SELECT pg_catalog.count(*)::integer FROM app_private.kb_documents),
      (SELECT pg_catalog.count(*)::integer FROM app_private.kb_question_examples),
      (SELECT pg_catalog.count(*)::integer FROM app_private.audit_logs
       WHERE action = 'CANDIDATE_APPROVED')
  $$,
  $$VALUES (2::integer, 2::integer, 2::integer)$$,
  'only two successful approvals contribute documents, questions and audits'
);

SELECT is(
  (
    SELECT pg_catalog.count(*)::integer
    FROM pg_catalog.pg_proc AS functions
    WHERE functions.oid = pg_catalog.to_regprocedure(
      'app_api.approve_kb_candidate_with_public_id(uuid,text,text,text,text)'
    )
      AND functions.prosrc ~* '\mEXECUTE\M'
  ),
  0,
  'explicit binding contains no dynamic SQL'
);

SELECT * FROM finish();

ROLLBACK;
