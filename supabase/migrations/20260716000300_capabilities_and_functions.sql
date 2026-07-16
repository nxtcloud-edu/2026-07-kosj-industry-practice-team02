BEGIN;

DO $bootstrap_roles$
DECLARE
  v_role pg_catalog.pg_roles%ROWTYPE;
BEGIN
  SELECT roles.* INTO v_role
  FROM pg_catalog.pg_roles AS roles
  WHERE roles.rolname = 'sejong_schema_owner';

  IF NOT FOUND THEN
    CREATE ROLE sejong_schema_owner
      NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  ELSIF v_role.rolcanlogin
     OR v_role.rolsuper
     OR v_role.rolcreatedb
     OR v_role.rolcreaterole
     OR v_role.rolreplication
     OR v_role.rolbypassrls
     OR EXISTS (
       SELECT 1 FROM pg_catalog.pg_auth_members AS memberships
       WHERE memberships.member = v_role.oid
     )
     OR EXISTS (
       SELECT 1 FROM pg_catalog.pg_db_role_setting AS settings
       WHERE settings.setrole = v_role.oid
     ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'UNSAFE_SEJONG_SCHEMA_OWNER_ROLE';
  END IF;

  SELECT roles.* INTO v_role
  FROM pg_catalog.pg_roles AS roles
  WHERE roles.rolname = 'sejong_backend';

  IF NOT FOUND THEN
    CREATE ROLE sejong_backend
      NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  ELSIF v_role.rolcanlogin
     OR v_role.rolsuper
     OR v_role.rolcreatedb
     OR v_role.rolcreaterole
     OR v_role.rolreplication
     OR v_role.rolbypassrls
     OR EXISTS (
       SELECT 1 FROM pg_catalog.pg_auth_members AS memberships
       WHERE memberships.member = v_role.oid
     )
     OR EXISTS (
       SELECT 1 FROM pg_catalog.pg_db_role_setting AS settings
       WHERE settings.setrole = v_role.oid
     ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'UNSAFE_SEJONG_BACKEND_ROLE';
  END IF;
END;
$bootstrap_roles$;

ALTER ROLE sejong_schema_owner
  NOLOGIN NOCREATEDB NOCREATEROLE;
ALTER ROLE sejong_backend
  NOLOGIN NOCREATEDB NOCREATEROLE;

DO $grant_runner_schema_owner$
BEGIN
  EXECUTE pg_catalog.format(
    'GRANT sejong_schema_owner TO %I WITH INHERIT TRUE',
    CURRENT_USER
  );
  EXECUTE pg_catalog.format(
    'GRANT sejong_schema_owner TO %I WITH SET TRUE',
    CURRENT_USER
  );
END;
$grant_runner_schema_owner$;

DO $validate_runner_memberships$
DECLARE
  v_current_user_oid oid := (
    SELECT roles.oid FROM pg_catalog.pg_roles AS roles
    WHERE roles.rolname = CURRENT_USER
  );
  v_schema_owner_oid oid := (
    SELECT roles.oid FROM pg_catalog.pg_roles AS roles
    WHERE roles.rolname = 'sejong_schema_owner'
  );
  v_backend_oid oid := (
    SELECT roles.oid FROM pg_catalog.pg_roles AS roles
    WHERE roles.rolname = 'sejong_backend'
  );
BEGIN
  IF NOT EXISTS (
       SELECT 1 FROM pg_catalog.pg_auth_members AS memberships
       WHERE memberships.roleid = v_schema_owner_oid
         AND memberships.member = v_current_user_oid
         AND memberships.admin_option
     )
     OR NOT EXISTS (
       SELECT 1 FROM pg_catalog.pg_auth_members AS memberships
       WHERE memberships.roleid = v_schema_owner_oid
         AND memberships.member = v_current_user_oid
         AND memberships.inherit_option
     )
     OR NOT EXISTS (
       SELECT 1 FROM pg_catalog.pg_auth_members AS memberships
       WHERE memberships.roleid = v_schema_owner_oid
         AND memberships.member = v_current_user_oid
         AND memberships.set_option
     )
     OR NOT EXISTS (
       SELECT 1 FROM pg_catalog.pg_auth_members AS memberships
       WHERE memberships.roleid = v_backend_oid
         AND memberships.member = v_current_user_oid
         AND memberships.admin_option
         AND NOT memberships.inherit_option
         AND NOT memberships.set_option
     )
     OR EXISTS (
       SELECT 1 FROM pg_catalog.pg_auth_members AS memberships
       WHERE memberships.roleid = v_backend_oid
         AND memberships.member = v_current_user_oid
         AND (memberships.inherit_option OR memberships.set_option)
     ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001', MESSAGE = 'UNSAFE_MIGRATION_ROLE_MEMBERSHIP';
  END IF;
END;
$validate_runner_memberships$;

DO $grant_database_create$
BEGIN
  EXECUTE pg_catalog.format(
    'GRANT CREATE ON DATABASE %I TO sejong_schema_owner',
    pg_catalog.current_database()
  );
END;
$grant_database_create$;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;

ALTER SCHEMA app_private OWNER TO sejong_schema_owner;
ALTER SCHEMA app_api OWNER TO sejong_schema_owner;

ALTER TYPE app_private.intent_code OWNER TO sejong_schema_owner;
ALTER TYPE app_private.answer_status OWNER TO sejong_schema_owner;
ALTER TYPE app_private.fallback_reason OWNER TO sejong_schema_owner;
ALTER TYPE app_private.kb_status OWNER TO sejong_schema_owner;
ALTER TYPE app_private.candidate_status OWNER TO sejong_schema_owner;
ALTER TYPE app_private.admin_role OWNER TO sejong_schema_owner;
ALTER TYPE app_private.data_origin OWNER TO sejong_schema_owner;

ALTER TABLE app_private.kb_documents OWNER TO sejong_schema_owner;
ALTER TABLE app_private.kb_question_examples OWNER TO sejong_schema_owner;
ALTER TABLE app_private.offices OWNER TO sejong_schema_owner;
ALTER TABLE app_private.office_service_mappings OWNER TO sejong_schema_owner;
ALTER TABLE app_private.interaction_events OWNER TO sejong_schema_owner;
ALTER TABLE app_private.failed_questions OWNER TO sejong_schema_owner;
ALTER TABLE app_private.kb_candidates OWNER TO sejong_schema_owner;
ALTER TABLE app_private.audit_logs OWNER TO sejong_schema_owner;

ALTER FUNCTION app_private.is_nonempty_text(text)
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_private.is_text_array(jsonb)
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_private.is_unique_text_array(jsonb)
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_private.is_allowed_audit_changed_fields(jsonb)
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_private.set_updated_at()
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_private.validate_interaction_event_sources()
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_private.validate_failed_question_event()
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_private.validate_interaction_event_failure()
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_private.validate_kb_candidate_failure()
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_private.validate_failed_question_candidate()
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_private.lock_kb_question_parents()
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_private.validate_active_kb_question()
  OWNER TO sejong_schema_owner;

REVOKE ALL PRIVILEGES ON SCHEMA app_private, app_api
  FROM PUBLIC, anon, authenticated, sejong_backend;
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA app_private
  FROM PUBLIC, anon, authenticated, sejong_backend;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA app_private
  FROM PUBLIC, anon, authenticated, sejong_backend;
REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA app_private, app_api
  FROM PUBLIC, anon, authenticated, sejong_backend;
GRANT USAGE ON SCHEMA app_api TO sejong_backend;

ALTER TABLE app_private.kb_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.kb_documents FORCE ROW LEVEL SECURITY;
CREATE POLICY kb_documents_owner_all ON app_private.kb_documents
  FOR ALL TO sejong_schema_owner USING (true) WITH CHECK (true);

ALTER TABLE app_private.kb_question_examples ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.kb_question_examples FORCE ROW LEVEL SECURITY;
CREATE POLICY kb_question_examples_owner_all
  ON app_private.kb_question_examples
  FOR ALL TO sejong_schema_owner USING (true) WITH CHECK (true);

ALTER TABLE app_private.offices ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.offices FORCE ROW LEVEL SECURITY;
CREATE POLICY offices_owner_all ON app_private.offices
  FOR ALL TO sejong_schema_owner USING (true) WITH CHECK (true);

ALTER TABLE app_private.office_service_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.office_service_mappings FORCE ROW LEVEL SECURITY;
CREATE POLICY office_service_mappings_owner_all
  ON app_private.office_service_mappings
  FOR ALL TO sejong_schema_owner USING (true) WITH CHECK (true);

ALTER TABLE app_private.interaction_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.interaction_events FORCE ROW LEVEL SECURITY;
CREATE POLICY interaction_events_owner_all ON app_private.interaction_events
  FOR ALL TO sejong_schema_owner USING (true) WITH CHECK (true);

ALTER TABLE app_private.failed_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.failed_questions FORCE ROW LEVEL SECURITY;
CREATE POLICY failed_questions_owner_all ON app_private.failed_questions
  FOR ALL TO sejong_schema_owner USING (true) WITH CHECK (true);

ALTER TABLE app_private.kb_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.kb_candidates FORCE ROW LEVEL SECURITY;
CREATE POLICY kb_candidates_owner_all ON app_private.kb_candidates
  FOR ALL TO sejong_schema_owner USING (true) WITH CHECK (true);

ALTER TABLE app_private.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_private.audit_logs FORCE ROW LEVEL SECURITY;
CREATE POLICY audit_logs_owner_all ON app_private.audit_logs
  FOR ALL TO sejong_schema_owner USING (true) WITH CHECK (true);

CREATE FUNCTION app_api.record_interaction(
  p_request_id uuid,
  p_intent text,
  p_answer_status text,
  p_fallback_reason text,
  p_used_source_ids text[],
  p_response_time_ms integer,
  p_selected_region text,
  p_routed_office_public_id text,
  p_is_test boolean,
  p_masked_question text
)
RETURNS TABLE (interaction_id uuid, failed_question_id uuid)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $record_interaction$
DECLARE
  v_intent app_private.intent_code;
  v_answer_status app_private.answer_status;
  v_fallback_reason app_private.fallback_reason;
  v_source_count integer;
  v_used_source_ids jsonb;
  v_source_public_id text;
  v_source_row_id uuid;
  v_routed_office_id uuid;
  v_existing_routed_office_public_id text;
  v_interaction_id uuid;
  v_failed_question_id uuid;
  v_existing app_private.interaction_events%ROWTYPE;
BEGIN
  IF pg_catalog.current_setting('transaction_isolation')
     IS DISTINCT FROM 'read committed' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'INVALID_INTERACTION';
  END IF;

  IF p_request_id IS NULL
     OR p_intent IS NULL
     OR p_intent NOT IN (
       'MOVE_IN_RESIDENT_REGISTRATION',
       'CERTIFICATE_ISSUANCE',
       'BULKY_WASTE',
       'LOCAL_TAX_GENERAL',
       'OUT_OF_SCOPE',
       'UNKNOWN'
     )
     OR p_answer_status IS NULL
     OR p_answer_status NOT IN (
       'SUCCESS', 'FOLLOWUP', 'FALLBACK', 'SYSTEM_ERROR'
     )
     OR (
       p_fallback_reason IS NOT NULL
       AND p_fallback_reason NOT IN (
         'INSUFFICIENT_GROUNDING',
         'PERSONAL_LOOKUP',
         'LEGAL_JUDGMENT',
         'OUT_OF_SCOPE'
       )
     )
     OR p_used_source_ids IS NULL
     OR p_response_time_ms IS NULL
     OR p_response_time_ms < 0
     OR (
       p_selected_region IS NOT NULL
       AND p_selected_region NOT IN ('아름동', '도담동', '조치원읍')
     )
     OR p_is_test IS NULL
     OR (
       p_routed_office_public_id IS NOT NULL
       AND (
         p_routed_office_public_id <> pg_catalog.btrim(p_routed_office_public_id)
         OR pg_catalog.btrim(p_routed_office_public_id) = ''
       )
     )
     OR (
       p_masked_question IS NOT NULL
       AND (
         p_masked_question <> pg_catalog.btrim(p_masked_question)
         OR pg_catalog.btrim(p_masked_question) = ''
       )
     ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'INVALID_INTERACTION';
  END IF;

  v_source_count := pg_catalog.cardinality(p_used_source_ids);

  IF (v_source_count > 0 AND pg_catalog.array_ndims(p_used_source_ids) <> 1)
     OR EXISTS (
       SELECT 1
       FROM pg_catalog.unnest(p_used_source_ids) AS sources(public_id)
       WHERE sources.public_id IS NULL
          OR sources.public_id <> pg_catalog.btrim(sources.public_id)
          OR pg_catalog.btrim(sources.public_id) = ''
     )
     OR (
       SELECT pg_catalog.count(*) <> pg_catalog.count(DISTINCT sources.public_id)
       FROM pg_catalog.unnest(p_used_source_ids) AS sources(public_id)
     ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'INVALID_INTERACTION';
  END IF;

  IF p_answer_status = 'SUCCESS' THEN
    IF p_intent NOT IN (
         'MOVE_IN_RESIDENT_REGISTRATION',
         'CERTIFICATE_ISSUANCE',
         'BULKY_WASTE',
         'LOCAL_TAX_GENERAL'
       )
       OR p_fallback_reason IS NOT NULL
       OR v_source_count < 1
       OR p_masked_question IS NOT NULL THEN
      RAISE EXCEPTION USING
        ERRCODE = 'P1010', MESSAGE = 'INVALID_INTERACTION';
    END IF;
  ELSIF p_answer_status = 'FOLLOWUP' THEN
    IF p_intent NOT IN (
         'MOVE_IN_RESIDENT_REGISTRATION',
         'CERTIFICATE_ISSUANCE',
         'BULKY_WASTE',
         'LOCAL_TAX_GENERAL',
         'UNKNOWN'
       )
       OR p_fallback_reason IS NOT NULL
       OR v_source_count <> 0
       OR p_masked_question IS NOT NULL THEN
      RAISE EXCEPTION USING
        ERRCODE = 'P1010', MESSAGE = 'INVALID_INTERACTION';
    END IF;
  ELSIF p_answer_status = 'FALLBACK' THEN
    IF p_fallback_reason = 'OUT_OF_SCOPE' THEN
      IF p_intent <> 'OUT_OF_SCOPE'
         OR v_source_count <> 0
         OR p_masked_question IS NOT NULL THEN
        RAISE EXCEPTION USING
          ERRCODE = 'P1010', MESSAGE = 'INVALID_INTERACTION';
      END IF;
    ELSIF p_fallback_reason IN (
      'INSUFFICIENT_GROUNDING', 'PERSONAL_LOOKUP', 'LEGAL_JUDGMENT'
    ) THEN
      IF p_intent NOT IN (
           'MOVE_IN_RESIDENT_REGISTRATION',
           'CERTIFICATE_ISSUANCE',
           'BULKY_WASTE',
           'LOCAL_TAX_GENERAL'
         )
         OR v_source_count <> 0 THEN
        RAISE EXCEPTION USING
          ERRCODE = 'P1010', MESSAGE = 'INVALID_INTERACTION';
      END IF;
    ELSE
      RAISE EXCEPTION USING
        ERRCODE = 'P1010', MESSAGE = 'INVALID_INTERACTION';
    END IF;
  ELSE
    IF p_fallback_reason IS NOT NULL
       OR v_source_count <> 0
       OR p_masked_question IS NOT NULL THEN
      RAISE EXCEPTION USING
        ERRCODE = 'P1010', MESSAGE = 'INVALID_INTERACTION';
    END IF;
  END IF;

  v_intent := p_intent::app_private.intent_code;
  v_answer_status := p_answer_status::app_private.answer_status;
  IF p_fallback_reason IS NOT NULL THEN
    v_fallback_reason := p_fallback_reason::app_private.fallback_reason;
  END IF;
  v_used_source_ids := pg_catalog.to_jsonb(p_used_source_ids);

  -- A committed request is an immutable idempotency record. Compare it before
  -- consulting mutable ACTIVE/OFFICIAL provenance, and never compare retained
  -- question text, which may already have been purged.
  SELECT events.* INTO v_existing
  FROM app_private.interaction_events AS events
  WHERE events.request_id = p_request_id
  FOR SHARE;

  IF FOUND THEN
    IF v_existing.routed_office_id IS NOT NULL THEN
      SELECT offices.public_id INTO v_existing_routed_office_public_id
      FROM app_private.offices AS offices
      WHERE offices.id = v_existing.routed_office_id;
    END IF;

    IF v_existing.intent IS DISTINCT FROM v_intent
       OR v_existing.answer_status IS DISTINCT FROM v_answer_status
       OR v_existing.fallback_reason IS DISTINCT FROM v_fallback_reason
       OR v_existing.source_count IS DISTINCT FROM v_source_count
       OR v_existing.used_source_ids IS DISTINCT FROM v_used_source_ids
       OR v_existing.response_time_ms IS DISTINCT FROM p_response_time_ms
       OR v_existing.selected_region IS DISTINCT FROM p_selected_region
       OR v_existing_routed_office_public_id
          IS DISTINCT FROM p_routed_office_public_id
       OR v_existing.is_test IS DISTINCT FROM p_is_test THEN
      RAISE EXCEPTION USING
        ERRCODE = 'P1010', MESSAGE = 'INVALID_INTERACTION';
    END IF;

    v_interaction_id := v_existing.id;
    SELECT failures.id INTO v_failed_question_id
    FROM app_private.failed_questions AS failures
    WHERE failures.interaction_event_id = v_interaction_id
    FOR SHARE;

    RETURN QUERY SELECT v_interaction_id, v_failed_question_id;
    RETURN;
  END IF;

  -- New writes always lock sources in lexical order, then the routed office.
  IF p_answer_status = 'SUCCESS' THEN
    FOR v_source_public_id IN
      SELECT sources.public_id
      FROM pg_catalog.unnest(p_used_source_ids) AS sources(public_id)
      ORDER BY sources.public_id
    LOOP
      SELECT kb.id INTO v_source_row_id
      FROM app_private.kb_documents AS kb
      WHERE kb.public_id = v_source_public_id
        AND kb.status = 'ACTIVE'
        AND kb.data_origin = 'OFFICIAL'
      FOR SHARE;

      IF NOT FOUND THEN
        RAISE EXCEPTION USING
          ERRCODE = 'P1010', MESSAGE = 'INVALID_INTERACTION';
      END IF;
    END LOOP;
  END IF;

  IF p_routed_office_public_id IS NOT NULL THEN
    SELECT offices.id INTO v_routed_office_id
    FROM app_private.offices AS offices
    WHERE offices.public_id = p_routed_office_public_id
      AND offices.data_origin = 'OFFICIAL'
    FOR SHARE;

    IF NOT FOUND THEN
      RAISE EXCEPTION USING
        ERRCODE = 'P1010', MESSAGE = 'INVALID_INTERACTION';
    END IF;
  END IF;

  INSERT INTO app_private.interaction_events AS events (
    intent, answer_status, fallback_reason, source_count, used_source_ids,
    response_time_ms, selected_region, routed_office_id, is_test, request_id
  ) VALUES (
    v_intent, v_answer_status, v_fallback_reason, v_source_count,
    v_used_source_ids, p_response_time_ms, p_selected_region,
    v_routed_office_id, p_is_test, p_request_id
  )
  ON CONFLICT (request_id) DO NOTHING
  RETURNING events.id INTO v_interaction_id;

  IF v_interaction_id IS NULL THEN
    SELECT events.* INTO v_existing
    FROM app_private.interaction_events AS events
    WHERE events.request_id = p_request_id
    FOR SHARE;

    IF NOT FOUND
       OR v_existing.intent IS DISTINCT FROM v_intent
       OR v_existing.answer_status IS DISTINCT FROM v_answer_status
       OR v_existing.fallback_reason IS DISTINCT FROM v_fallback_reason
       OR v_existing.source_count IS DISTINCT FROM v_source_count
       OR v_existing.used_source_ids IS DISTINCT FROM v_used_source_ids
       OR v_existing.response_time_ms IS DISTINCT FROM p_response_time_ms
       OR v_existing.selected_region IS DISTINCT FROM p_selected_region
       OR v_existing.routed_office_id IS DISTINCT FROM v_routed_office_id
       OR v_existing.is_test IS DISTINCT FROM p_is_test THEN
      RAISE EXCEPTION USING
        ERRCODE = 'P1010', MESSAGE = 'INVALID_INTERACTION';
    END IF;

    v_interaction_id := v_existing.id;
    SELECT failures.id INTO v_failed_question_id
    FROM app_private.failed_questions AS failures
    WHERE failures.interaction_event_id = v_interaction_id
    FOR SHARE;

    RETURN QUERY SELECT v_interaction_id, v_failed_question_id;
    RETURN;
  END IF;

  IF p_answer_status = 'FALLBACK'
     AND p_fallback_reason <> 'OUT_OF_SCOPE'
     AND p_masked_question IS NOT NULL THEN
    INSERT INTO app_private.failed_questions (
      interaction_event_id, masked_question, intent, fallback_reason,
      candidate_eligible
    ) VALUES (
      v_interaction_id, p_masked_question, v_intent, v_fallback_reason,
      p_fallback_reason = 'INSUFFICIENT_GROUNDING'
    )
    RETURNING id INTO v_failed_question_id;
  END IF;

  RETURN QUERY SELECT v_interaction_id, v_failed_question_id;
END;
$record_interaction$;

CREATE FUNCTION app_private.purge_expired_failed_question_text_at(
  p_cutoff timestamptz
)
RETURNS TABLE (purged_count integer, purged_ids uuid[])
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $purge_at$
BEGIN
  IF p_cutoff IS NULL THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'INVALID_RETENTION_CUTOFF';
  END IF;

  RETURN QUERY
  WITH purged AS (
    UPDATE app_private.failed_questions AS failures
    SET masked_question = NULL,
        text_purged_at = p_cutoff
    WHERE failures.masked_question IS NOT NULL
      AND failures.text_expires_at <= p_cutoff
    RETURNING failures.id
  )
  SELECT pg_catalog.count(*)::integer,
    COALESCE(
      pg_catalog.array_agg(purged.id ORDER BY purged.id),
      ARRAY[]::uuid[]
    )
  FROM purged;
END;
$purge_at$;

CREATE FUNCTION app_api.purge_expired_failed_question_text()
RETURNS TABLE (purged_count integer, purged_ids uuid[])
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $purge_current$
DECLARE
  v_cutoff timestamptz := pg_catalog.clock_timestamp();
BEGIN
  RETURN QUERY
  SELECT result.purged_count, result.purged_ids
  FROM app_private.purge_expired_failed_question_text_at(v_cutoff) AS result;
END;
$purge_current$;

ALTER FUNCTION app_api.record_interaction(
  uuid, text, text, text, text[], integer, text, text, boolean, text
) OWNER TO sejong_schema_owner;
ALTER FUNCTION app_private.purge_expired_failed_question_text_at(timestamptz)
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_api.purge_expired_failed_question_text()
  OWNER TO sejong_schema_owner;

REVOKE ALL ON FUNCTION app_api.record_interaction(
  uuid, text, text, text, text[], integer, text, text, boolean, text
) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION
  app_private.purge_expired_failed_question_text_at(timestamptz)
  FROM PUBLIC, anon, authenticated, sejong_backend;
REVOKE ALL ON FUNCTION app_api.purge_expired_failed_question_text()
  FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION app_api.record_interaction(
  uuid, text, text, text, text[], integer, text, text, boolean, text
) TO sejong_backend;
GRANT EXECUTE ON FUNCTION app_api.purge_expired_failed_question_text()
  TO sejong_backend;

COMMIT;
