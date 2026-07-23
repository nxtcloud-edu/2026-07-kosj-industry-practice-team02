BEGIN;

CREATE FUNCTION app_private.idempotency_response_is_safe(p_value jsonb)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
SET search_path = pg_catalog, pg_temp
AS $idempotency_response_is_safe$
  WITH RECURSIVE values_to_check(value) AS (
    VALUES (p_value)
    UNION ALL
    SELECT children.value
    FROM values_to_check AS parent
    CROSS JOIN LATERAL (
      SELECT objects.value
      FROM pg_catalog.jsonb_each(
        CASE WHEN pg_catalog.jsonb_typeof(parent.value) = 'object'
          THEN parent.value ELSE '{}'::jsonb END
      ) AS objects(key, value)
      UNION ALL
      SELECT arrays.value
      FROM pg_catalog.jsonb_array_elements(
        CASE WHEN pg_catalog.jsonb_typeof(parent.value) = 'array'
          THEN parent.value ELSE '[]'::jsonb END
      ) AS arrays(value)
    ) AS children
  )
  SELECT
    p_value IS NOT NULL
    AND pg_catalog.jsonb_typeof(p_value) = 'object'
    AND p_value <> '{}'::jsonb
    AND pg_catalog.octet_length(p_value::text) <= 65536
    AND NOT EXISTS (
      SELECT 1
      FROM values_to_check AS checked
      CROSS JOIN LATERAL pg_catalog.jsonb_object_keys(
        CASE WHEN pg_catalog.jsonb_typeof(checked.value) = 'object'
          THEN checked.value ELSE '{}'::jsonb END
      ) AS object_keys(key)
      WHERE pg_catalog.lower(object_keys.key) IN (
        'context_token', 'masked_question', 'prompt', 'provider_body',
        'question', 'raw_question', 'request_body', 'request_id', 'transcript'
      )
    )
$idempotency_response_is_safe$;

ALTER FUNCTION app_private.idempotency_response_is_safe(jsonb)
  OWNER TO sejong_schema_owner;
REVOKE ALL ON FUNCTION app_private.idempotency_response_is_safe(jsonb)
  FROM PUBLIC, anon, authenticated, sejong_backend;

CREATE TABLE app_private.chat_idempotency (
  idempotency_key uuid PRIMARY KEY,
  request_digest text NOT NULL
    CHECK (request_digest ~ '^[0-9a-f]{64}$'),
  claim_token uuid,
  lease_expires_at timestamptz,
  state text NOT NULL
    CHECK (state IN ('IN_PROGRESS', 'COMPLETED', 'ABANDONED')),
  response_json jsonb,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  completed_at timestamptz,
  abandoned_at timestamptz,
  expires_at timestamptz NOT NULL,
  CHECK (expires_at = created_at + interval '24 hours'),
  CHECK (
    (state = 'IN_PROGRESS'
      AND claim_token IS NOT NULL
      AND lease_expires_at IS NOT NULL
      AND response_json IS NULL
      AND completed_at IS NULL
      AND abandoned_at IS NULL)
    OR (state = 'COMPLETED'
      AND claim_token IS NULL
      AND lease_expires_at IS NULL
      AND app_private.idempotency_response_is_safe(response_json)
      AND completed_at IS NOT NULL
      AND abandoned_at IS NULL)
    OR (state = 'ABANDONED'
      AND claim_token IS NULL
      AND lease_expires_at IS NULL
      AND response_json IS NULL
      AND completed_at IS NULL
      AND abandoned_at IS NOT NULL)
  )
);

ALTER TABLE app_private.chat_idempotency OWNER TO sejong_schema_owner;
ALTER TABLE app_private.chat_idempotency ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.chat_idempotency FORCE ROW LEVEL SECURITY;
CREATE POLICY chat_idempotency_owner_all ON app_private.chat_idempotency
  FOR ALL TO sejong_schema_owner USING (true) WITH CHECK (true);

CREATE TRIGGER trg_chat_idempotency_set_updated_at
BEFORE UPDATE ON app_private.chat_idempotency
FOR EACH ROW EXECUTE FUNCTION app_private.set_updated_at();

CREATE FUNCTION app_api.claim_chat_idempotency(
  p_idempotency_key uuid,
  p_request_digest text,
  p_claim_token uuid
)
RETURNS TABLE (
  disposition text,
  response_json jsonb
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $claim_chat_idempotency$
DECLARE
  v_row app_private.chat_idempotency%ROWTYPE;
  v_inserted_key uuid;
  v_now timestamptz := pg_catalog.clock_timestamp();
BEGIN
  IF p_idempotency_key IS NULL
     OR p_claim_token IS NULL
     OR p_request_digest IS NULL
     OR p_request_digest !~ '^[0-9a-f]{64}$' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'INVALID_IDEMPOTENCY_INPUT';
  END IF;

  INSERT INTO app_private.chat_idempotency (
    idempotency_key, request_digest, claim_token, lease_expires_at, state,
    created_at, updated_at, expires_at
  ) VALUES (
    p_idempotency_key, p_request_digest, p_claim_token,
    v_now + interval '5 minutes', 'IN_PROGRESS',
    v_now, v_now, v_now + interval '24 hours'
  )
  ON CONFLICT (idempotency_key) DO NOTHING
  RETURNING idempotency_key INTO v_inserted_key;

  IF v_inserted_key IS NOT NULL THEN
    RETURN QUERY SELECT 'ACQUIRED'::text, NULL::jsonb;
    RETURN;
  END IF;

  SELECT rows.* INTO v_row
  FROM app_private.chat_idempotency AS rows
  WHERE rows.idempotency_key = p_idempotency_key
  FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
  END IF;

  v_now := pg_catalog.clock_timestamp();

  IF v_row.expires_at <= v_now THEN
    DELETE FROM app_private.chat_idempotency AS rows
    WHERE rows.idempotency_key = p_idempotency_key;
    INSERT INTO app_private.chat_idempotency (
      idempotency_key, request_digest, claim_token, lease_expires_at, state,
      created_at, updated_at, expires_at
    ) VALUES (
      p_idempotency_key, p_request_digest, p_claim_token,
      v_now + interval '5 minutes', 'IN_PROGRESS',
      v_now, v_now, v_now + interval '24 hours'
    );
    RETURN QUERY SELECT 'ACQUIRED'::text, NULL::jsonb;
    RETURN;
  END IF;

  IF v_row.request_digest IS DISTINCT FROM p_request_digest THEN
    RETURN QUERY SELECT 'CONFLICT'::text, NULL::jsonb;
    RETURN;
  END IF;

  IF v_row.state = 'COMPLETED' THEN
    RETURN QUERY SELECT 'COMPLETED'::text, v_row.response_json;
    RETURN;
  END IF;

  IF v_row.state = 'IN_PROGRESS' AND v_row.lease_expires_at > v_now THEN
    RETURN QUERY SELECT 'IN_PROGRESS'::text, NULL::jsonb;
    RETURN;
  END IF;

  UPDATE app_private.chat_idempotency AS rows
  SET claim_token = p_claim_token,
      lease_expires_at = v_now + interval '5 minutes',
      state = 'IN_PROGRESS',
      response_json = NULL,
      completed_at = NULL,
      abandoned_at = NULL
  WHERE rows.idempotency_key = p_idempotency_key;
  RETURN QUERY SELECT 'ACQUIRED'::text, NULL::jsonb;
END
$claim_chat_idempotency$;

CREATE FUNCTION app_api.complete_chat_idempotency(
  p_idempotency_key uuid,
  p_request_digest text,
  p_claim_token uuid,
  p_response_json jsonb
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $complete_chat_idempotency$
DECLARE
  v_now timestamptz := pg_catalog.clock_timestamp();
BEGIN
  IF p_idempotency_key IS NULL
     OR p_claim_token IS NULL
     OR p_request_digest IS NULL
     OR p_request_digest !~ '^[0-9a-f]{64}$' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'INVALID_IDEMPOTENCY_INPUT';
  END IF;
  IF NOT app_private.idempotency_response_is_safe(p_response_json) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'UNSAFE_IDEMPOTENCY_RESPONSE';
  END IF;

  UPDATE app_private.chat_idempotency AS rows
  SET state = 'COMPLETED',
      claim_token = NULL,
      lease_expires_at = NULL,
      response_json = p_response_json,
      completed_at = v_now,
      abandoned_at = NULL
  WHERE rows.idempotency_key = p_idempotency_key
    AND rows.request_digest = p_request_digest
    AND rows.claim_token = p_claim_token
    AND rows.state = 'IN_PROGRESS'
    AND rows.lease_expires_at > v_now
    AND rows.expires_at > v_now;

  IF NOT FOUND THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
  END IF;
END
$complete_chat_idempotency$;

CREATE FUNCTION app_api.abandon_chat_idempotency(
  p_idempotency_key uuid,
  p_request_digest text,
  p_claim_token uuid
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $abandon_chat_idempotency$
DECLARE
  v_now timestamptz := pg_catalog.clock_timestamp();
BEGIN
  IF p_idempotency_key IS NULL
     OR p_claim_token IS NULL
     OR p_request_digest IS NULL
     OR p_request_digest !~ '^[0-9a-f]{64}$' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'INVALID_IDEMPOTENCY_INPUT';
  END IF;

  UPDATE app_private.chat_idempotency AS rows
  SET state = 'ABANDONED',
      claim_token = NULL,
      lease_expires_at = NULL,
      response_json = NULL,
      completed_at = NULL,
      abandoned_at = v_now
  WHERE rows.idempotency_key = p_idempotency_key
    AND rows.request_digest = p_request_digest
    AND rows.claim_token = p_claim_token
    AND rows.state = 'IN_PROGRESS'
    AND rows.lease_expires_at > v_now
    AND rows.expires_at > v_now;

  IF NOT FOUND THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
  END IF;
END
$abandon_chat_idempotency$;

CREATE FUNCTION app_api.purge_expired_chat_idempotency()
RETURNS TABLE (
  purged_count integer,
  purged_ids uuid[]
)
LANGUAGE sql
VOLATILE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $purge_expired_chat_idempotency$
  WITH deleted AS (
    DELETE FROM app_private.chat_idempotency AS rows
    WHERE rows.expires_at <= pg_catalog.clock_timestamp()
    RETURNING rows.idempotency_key
  )
  SELECT
    pg_catalog.count(*)::integer,
    COALESCE(
      pg_catalog.array_agg(deleted.idempotency_key ORDER BY deleted.idempotency_key),
      ARRAY[]::uuid[]
    )
  FROM deleted
$purge_expired_chat_idempotency$;

ALTER FUNCTION app_api.claim_chat_idempotency(uuid, text, uuid)
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_api.complete_chat_idempotency(uuid, text, uuid, jsonb)
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_api.abandon_chat_idempotency(uuid, text, uuid)
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_api.purge_expired_chat_idempotency()
  OWNER TO sejong_schema_owner;

REVOKE ALL ON FUNCTION app_api.claim_chat_idempotency(uuid, text, uuid)
  FROM PUBLIC, anon, authenticated, sejong_backend;
REVOKE ALL ON FUNCTION app_api.complete_chat_idempotency(uuid, text, uuid, jsonb)
  FROM PUBLIC, anon, authenticated, sejong_backend;
REVOKE ALL ON FUNCTION app_api.abandon_chat_idempotency(uuid, text, uuid)
  FROM PUBLIC, anon, authenticated, sejong_backend;
REVOKE ALL ON FUNCTION app_api.purge_expired_chat_idempotency()
  FROM PUBLIC, anon, authenticated, sejong_backend;

GRANT EXECUTE ON FUNCTION app_api.claim_chat_idempotency(uuid, text, uuid)
  TO sejong_backend;
GRANT EXECUTE ON FUNCTION app_api.complete_chat_idempotency(uuid, text, uuid, jsonb)
  TO sejong_backend;
GRANT EXECUTE ON FUNCTION app_api.abandon_chat_idempotency(uuid, text, uuid)
  TO sejong_backend;
GRANT EXECUTE ON FUNCTION app_api.purge_expired_chat_idempotency()
  TO sejong_backend;

COMMIT;
