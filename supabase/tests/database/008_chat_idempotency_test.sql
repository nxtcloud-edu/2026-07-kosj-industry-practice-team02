BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;

SELECT plan(23);

SELECT has_table(
  'app_private', 'chat_idempotency',
  'durable chat idempotency state is private'
);

SELECT results_eq(
  $$
    SELECT columns.column_name::text COLLATE "C"
    FROM information_schema.columns AS columns
    WHERE columns.table_schema = 'app_private'
      AND columns.table_name = 'chat_idempotency'
    ORDER BY columns.ordinal_position
  $$,
  $$
    SELECT expected.column_name COLLATE "C"
    FROM (VALUES
      ('idempotency_key'::text), ('request_digest'::text),
      ('claim_token'::text), ('lease_expires_at'::text), ('state'::text),
      ('response_json'::text), ('created_at'::text), ('updated_at'::text),
      ('completed_at'::text), ('abandoned_at'::text),
      ('expires_at'::text)
    ) AS expected(column_name)
  $$,
  'idempotency table has only bounded identity, state, safe response and timestamps'
);

SELECT is(
  (
    SELECT pg_catalog.count(*)::integer
    FROM information_schema.columns AS columns
    WHERE columns.table_schema = 'app_private'
      AND columns.table_name = 'chat_idempotency'
      AND columns.column_name IN (
        'question', 'raw_question', 'masked_question', 'prompt',
        'provider_body', 'context_token', 'request_id'
      )
  ),
  0,
  'idempotency storage has no question, provider, context-token or correlation-id column'
);

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
        'claim_chat_idempotency', 'complete_chat_idempotency',
        'abandon_chat_idempotency', 'purge_expired_chat_idempotency'
      )
    ORDER BY 1
  $actual$,
  $expected$
    SELECT expected.signature COLLATE "C"
    FROM (VALUES
      ('app_api.abandon_chat_idempotency(p_idempotency_key uuid, p_request_digest text, p_claim_token uuid)'::text),
      ('app_api.claim_chat_idempotency(p_idempotency_key uuid, p_request_digest text, p_claim_token uuid)'::text),
      ('app_api.complete_chat_idempotency(p_idempotency_key uuid, p_request_digest text, p_claim_token uuid, p_response_json jsonb)'::text),
      ('app_api.purge_expired_chat_idempotency()'::text)
    ) AS expected(signature)
    ORDER BY 1
  $expected$,
  'idempotency exposes exactly four fixed capabilities'
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
        'claim_chat_idempotency', 'complete_chat_idempotency',
        'abandon_chat_idempotency', 'purge_expired_chat_idempotency'
      )
      AND functions.prosecdef
      AND owners.rolname = 'sejong_schema_owner'
      AND functions.proconfig = ARRAY['search_path=pg_catalog, pg_temp']::text[]
  ),
  4,
  'all idempotency capabilities are owner-definer with fixed search_path'
);

SELECT ok(
  NOT pg_catalog.has_table_privilege(
    'sejong_backend', 'app_private.chat_idempotency', 'SELECT'
  )
  AND NOT pg_catalog.has_table_privilege(
    'sejong_backend', 'app_private.chat_idempotency', 'INSERT'
  )
  AND pg_catalog.has_function_privilege(
    'sejong_backend', 'app_api.claim_chat_idempotency(uuid,text,uuid)', 'EXECUTE'
  )
  AND NOT pg_catalog.has_function_privilege(
    'anon', 'app_api.claim_chat_idempotency(uuid,text,uuid)', 'EXECUTE'
  )
  AND NOT pg_catalog.has_function_privilege(
    'authenticated', 'app_api.claim_chat_idempotency(uuid,text,uuid)', 'EXECUTE'
  ),
  'backend uses only capabilities and browser roles cannot claim keys'
);

SELECT throws_ok(
  $$SELECT * FROM app_api.claim_chat_idempotency(
    'b1000000-0000-4000-8000-000000000001', 'NOT-A-HMAC',
    'b2000000-0000-4000-8000-000000000001'
  )$$,
  'P1010', 'INVALID_IDEMPOTENCY_INPUT', 'claim rejects a non-HMAC digest'
);

SELECT throws_ok(
  $$SELECT app_api.complete_chat_idempotency(
    'b1000000-0000-4000-8000-000000000001',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'b2000000-0000-4000-8000-000000000001',
    '{"context_token":"must-not-persist"}'::jsonb
  )$$,
  'P1010', 'UNSAFE_IDEMPOTENCY_RESPONSE',
  'completion rejects memory-only context tokens'
);

SELECT results_eq(
  $$SELECT disposition, response_json FROM app_api.claim_chat_idempotency(
    'b1000000-0000-4000-8000-000000000001',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'b2000000-0000-4000-8000-000000000001'
  )$$,
  $$VALUES ('ACQUIRED'::text, NULL::jsonb)$$,
  'first key and digest atomically claims work'
);

SELECT is(
  (
    SELECT lease_expires_at = created_at + interval '5 minutes'
    FROM app_private.chat_idempotency
    WHERE idempotency_key = 'b1000000-0000-4000-8000-000000000001'
  ),
  true,
  'a fresh claim receives an exact five-minute lease'
);

SELECT results_eq(
  $$SELECT disposition, response_json FROM app_api.claim_chat_idempotency(
    'b1000000-0000-4000-8000-000000000001',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'b2000000-0000-4000-8000-000000000002'
  )$$,
  $$VALUES ('IN_PROGRESS'::text, NULL::jsonb)$$,
  'same key and digest observes in-progress work'
);

SELECT results_eq(
  $$SELECT disposition, response_json FROM app_api.claim_chat_idempotency(
    'b1000000-0000-4000-8000-000000000001',
    'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
    'b2000000-0000-4000-8000-000000000003'
  )$$,
  $$VALUES ('CONFLICT'::text, NULL::jsonb)$$,
  'same key with a different digest is a conflict'
);

UPDATE app_private.chat_idempotency
SET lease_expires_at = pg_catalog.clock_timestamp() - interval '1 second'
WHERE idempotency_key = 'b1000000-0000-4000-8000-000000000001';

SELECT results_eq(
  $$SELECT disposition, response_json FROM app_api.claim_chat_idempotency(
    'b1000000-0000-4000-8000-000000000001',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'b2000000-0000-4000-8000-000000000004'
  )$$,
  $$VALUES ('ACQUIRED'::text, NULL::jsonb)$$,
  'same digest atomically reacquires an expired lease with a new token'
);

SELECT throws_ok(
  $$SELECT app_api.complete_chat_idempotency(
    'b1000000-0000-4000-8000-000000000001',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'b2000000-0000-4000-8000-000000000001',
    '{"answer_status":"SUCCESS"}'::jsonb
  )$$,
  'P1003', 'INVALID_WORKFLOW_STATE',
  'the old claim token cannot complete reacquired work'
);

SELECT lives_ok(
  $$SELECT app_api.complete_chat_idempotency(
    'b1000000-0000-4000-8000-000000000001',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'b2000000-0000-4000-8000-000000000004',
    '{"answer_status":"SUCCESS","summary":"official-template"}'::jsonb
  )$$,
  'claimed work can complete with a bounded safe response'
);

SELECT results_eq(
  $$SELECT disposition, response_json FROM app_api.claim_chat_idempotency(
    'b1000000-0000-4000-8000-000000000001',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'b2000000-0000-4000-8000-000000000007'
  )$$,
  $$VALUES (
    'COMPLETED'::text,
    '{"summary":"official-template","answer_status":"SUCCESS"}'::jsonb
  )$$,
  'completed work replays the safe response for the same digest'
);

SELECT is(
  (
    SELECT expires_at = created_at + interval '24 hours'
      AND claim_token IS NULL
      AND lease_expires_at IS NULL
      AND completed_at IS NOT NULL
      AND abandoned_at IS NULL
    FROM app_private.chat_idempotency
    WHERE idempotency_key = 'b1000000-0000-4000-8000-000000000001'
  ),
  true,
  'completed row clears lease ownership and preserves exact 24-hour retention'
);

SELECT lives_ok(
  $$
    SELECT * FROM app_api.claim_chat_idempotency(
      'b1000000-0000-4000-8000-000000000002',
      'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
      'b2000000-0000-4000-8000-000000000005'
    );
    SELECT app_api.abandon_chat_idempotency(
      'b1000000-0000-4000-8000-000000000002',
      'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
      'b2000000-0000-4000-8000-000000000005'
    )
  $$,
  'claimed work can be explicitly abandoned'
);

SELECT results_eq(
  $$SELECT disposition, response_json FROM app_api.claim_chat_idempotency(
    'b1000000-0000-4000-8000-000000000002',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'b2000000-0000-4000-8000-000000000006'
  )$$,
  $$VALUES ('ACQUIRED'::text, NULL::jsonb)$$,
  'same digest can reclaim explicitly abandoned work'
);

SELECT throws_ok(
  $$SELECT app_api.complete_chat_idempotency(
    'b1000000-0000-4000-8000-000000000002',
    'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd',
    'b2000000-0000-4000-8000-000000000006',
    '{"answer_status":"SUCCESS"}'::jsonb
  )$$,
  'P1003', 'INVALID_WORKFLOW_STATE',
  'completion requires the exact claimed digest'
);

UPDATE app_private.chat_idempotency
SET created_at = expired.reference_time - interval '25 hours',
    expires_at = expired.reference_time - interval '1 hour'
FROM (SELECT pg_catalog.clock_timestamp() AS reference_time) AS expired
WHERE idempotency_key = 'b1000000-0000-4000-8000-000000000001';

SELECT results_eq(
  $$SELECT purged_count, purged_ids FROM app_api.purge_expired_chat_idempotency()$$,
  $$VALUES (
    1::integer,
    ARRAY['b1000000-0000-4000-8000-000000000001'::uuid]
  )$$,
  'purge deletes and reports only expired idempotency rows'
);

SELECT is(
  (
    SELECT pg_catalog.count(*)::integer
    FROM app_private.chat_idempotency
    WHERE idempotency_key = 'b1000000-0000-4000-8000-000000000001'
  ),
  0,
  'purged key is absent from private storage'
);

SELECT is(
  (
    SELECT pg_catalog.count(*)::integer
    FROM app_private.chat_idempotency
    WHERE idempotency_key = 'b1000000-0000-4000-8000-000000000002'
  ),
  1,
  'unexpired key remains after bounded purge'
);

SELECT * FROM finish();

ROLLBACK;
