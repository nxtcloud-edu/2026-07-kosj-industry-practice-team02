BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;

SELECT plan(14);

SELECT results_eq(
  $actual$
    SELECT pg_catalog.format(
      '%I.%I(%s)', namespaces.nspname, functions.proname,
      pg_catalog.pg_get_function_identity_arguments(functions.oid)
    )::text COLLATE "C"
    FROM pg_catalog.pg_proc AS functions
    JOIN pg_catalog.pg_namespace AS namespaces
      ON namespaces.oid = functions.pronamespace
    WHERE namespaces.nspname = 'app_api'
      AND functions.proname IN (
        'list_failed_questions', 'get_failed_question',
        'list_kb_candidates', 'get_kb_candidate'
      )
    ORDER BY 1
  $actual$,
  $expected$
    SELECT expected.signature COLLATE "C"
    FROM (VALUES
      ('app_api.get_failed_question(p_failed_question_id uuid)'::text),
      ('app_api.get_kb_candidate(p_candidate_id uuid)'::text),
      ('app_api.list_failed_questions(p_reason text, p_status text)'::text),
      ('app_api.list_kb_candidates()'::text)
    ) AS expected(signature)
    ORDER BY 1
  $expected$,
  'local admin exposes exactly four typed read capabilities'
);

SELECT is(
  (
    SELECT pg_catalog.count(*)::integer
    FROM pg_catalog.pg_proc AS functions
    JOIN pg_catalog.pg_namespace AS namespaces
      ON namespaces.oid = functions.pronamespace
    JOIN pg_catalog.pg_roles AS owners ON owners.oid = functions.proowner
    WHERE namespaces.nspname = 'app_api'
      AND functions.proname IN (
        'list_failed_questions', 'get_failed_question',
        'list_kb_candidates', 'get_kb_candidate'
      )
      AND functions.prosecdef
      AND owners.rolname = 'sejong_schema_owner'
      AND functions.proconfig = ARRAY['search_path=pg_catalog, pg_temp']::text[]
  ),
  4,
  'all four reads are schema-owner SECURITY DEFINER with fixed search_path'
);

SELECT ok(
  NOT pg_catalog.has_function_privilege(
    'anon', 'app_api.list_failed_questions(text,text)', 'EXECUTE'
  )
  AND NOT pg_catalog.has_function_privilege(
    'authenticated', 'app_api.list_failed_questions(text,text)', 'EXECUTE'
  )
  AND pg_catalog.has_function_privilege(
    'sejong_backend', 'app_api.list_failed_questions(text,text)', 'EXECUTE'
  )
  AND pg_catalog.has_function_privilege(
    'sejong_backend', 'app_api.get_failed_question(uuid)', 'EXECUTE'
  )
  AND pg_catalog.has_function_privilege(
    'sejong_backend', 'app_api.list_kb_candidates()', 'EXECUTE'
  )
  AND pg_catalog.has_function_privilege(
    'sejong_backend', 'app_api.get_kb_candidate(uuid)', 'EXECUTE'
  ),
  'browser roles have no execute while the backend can execute every admin read'
);

SELECT ok(
  NOT pg_catalog.has_schema_privilege('sejong_backend', 'app_private', 'USAGE')
  AND NOT pg_catalog.has_table_privilege(
    'sejong_backend', 'app_private.failed_questions', 'SELECT'
  )
  AND NOT pg_catalog.has_table_privilege(
    'sejong_backend', 'app_private.kb_candidates', 'SELECT'
  ),
  'admin reads add no direct private schema or table privilege'
);

SELECT throws_ok(
  $$SELECT * FROM app_api.list_failed_questions('OUT_OF_SCOPE', NULL)$$,
  'P1010', 'INVALID_ADMIN_READ_FILTER', 'unsupported failure reason is rejected'
);
SELECT throws_ok(
  $$SELECT * FROM app_api.list_failed_questions(NULL, 'APPROVED')$$,
  'P1010', 'INVALID_ADMIN_READ_FILTER', 'unsupported failure status is rejected'
);

SELECT * FROM app_api.record_interaction(
  'a1000000-0000-4000-8000-000000000001', 'BULKY_WASTE', 'FALLBACK',
  'INSUFFICIENT_GROUNDING', ARRAY[]::text[], 10, NULL, NULL, true,
  '침대 프레임 수수료를 알려 주세요.'
);

SELECT results_eq(
  $$
    SELECT intent, fallback_reason, candidate_eligible, status
    FROM app_api.list_failed_questions('INSUFFICIENT_GROUNDING', 'NEW')
  $$,
  $$VALUES ('BULKY_WASTE'::text, 'INSUFFICIENT_GROUNDING'::text, true, 'NEW'::text)$$,
  'filtered failed-question list returns exact workflow metadata'
);

SELECT is(
  (
    SELECT masked_question
    FROM app_api.get_failed_question((
      SELECT failures.id
      FROM app_private.failed_questions AS failures
      JOIN app_private.interaction_events AS events
        ON events.id = failures.interaction_event_id
      WHERE events.request_id = 'a1000000-0000-4000-8000-000000000001'
    ))
  ),
  '침대 프레임 수수료를 알려 주세요.'::text,
  'failed-question detail returns the retained masked text only'
);

SELECT is(
  (
    SELECT pg_catalog.count(*)::integer
    FROM app_api.get_failed_question('a1000000-0000-4000-8000-000000000099')
  ),
  0,
  'missing failed-question detail returns zero rows'
);

SELECT app_api.confirm_failed_question_reason(
  (
    SELECT failures.id
    FROM app_private.failed_questions AS failures
    JOIN app_private.interaction_events AS events
      ON events.id = failures.interaction_event_id
    WHERE events.request_id = 'a1000000-0000-4000-8000-000000000001'
  ),
  'OPERATOR-LOCAL-001', 'OPERATOR', 'INSUFFICIENT_GROUNDING'
);

SELECT app_api.create_kb_candidate(
  (
    SELECT failures.id
    FROM app_private.failed_questions AS failures
    JOIN app_private.interaction_events AS events
      ON events.id = failures.interaction_event_id
    WHERE events.request_id = 'a1000000-0000-4000-8000-000000000001'
  ),
  'OPERATOR-LOCAL-001', 'OPERATOR', '침대 프레임 배출 안내',
  '침대 프레임은 어떻게 버리나요?', 'BULKY_WASTE',
  '신청 후 배출번호를 붙여 배출합니다.', '[]'::jsonb, '[]'::jsonb,
  NULL, '10,000원', '자원순환과', '세종시 대형폐기물 안내',
  'https://www.sejong.go.kr/example', DATE '2026-07-19', NULL, 'OFFICIAL'
);

SELECT results_eq(
  $$
    SELECT title, data_origin, category, status, created_by
    FROM app_api.list_kb_candidates()
  $$,
  $$VALUES (
    '침대 프레임 배출 안내'::text, 'OFFICIAL'::text, 'BULKY_WASTE'::text,
    'DRAFTED'::text, 'OPERATOR-LOCAL-001'::text
  )$$,
  'candidate list returns exact local workflow metadata'
);

SELECT is(
  (
    SELECT source_url
    FROM app_api.get_kb_candidate((SELECT id FROM app_private.kb_candidates))
  ),
  'https://www.sejong.go.kr/example'::text,
  'candidate detail returns server-stored official source metadata'
);

SELECT is(
  (
    SELECT pg_catalog.count(*)::integer
    FROM app_api.get_kb_candidate('a1000000-0000-4000-8000-000000000099')
  ),
  0,
  'missing candidate detail returns zero rows'
);

SELECT is(
  (
    SELECT pg_catalog.count(*)::integer
    FROM pg_catalog.pg_proc AS functions
    JOIN pg_catalog.pg_namespace AS namespaces
      ON namespaces.oid = functions.pronamespace
    WHERE namespaces.nspname = 'app_api'
      AND functions.proname IN (
        'list_failed_questions', 'get_failed_question',
        'list_kb_candidates', 'get_kb_candidate'
      )
      AND functions.prosrc ~* '\mEXECUTE\M'
  ),
  0,
  'admin read bodies contain no dynamic EXECUTE'
);

SELECT is(
  (
    SELECT pg_catalog.count(*)::integer
    FROM app_api.list_failed_questions('PERSONAL_LOOKUP', NULL)
  ),
  0,
  'valid empty filter returns zero rows without widening scope'
);

SELECT * FROM finish();

ROLLBACK;
