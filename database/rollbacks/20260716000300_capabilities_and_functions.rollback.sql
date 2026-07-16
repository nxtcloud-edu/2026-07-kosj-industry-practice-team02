BEGIN;

DO $require_read_interface_compensation$
BEGIN
  IF pg_catalog.to_regprocedure('app_api.list_active_kb(text)') IS NOT NULL
     OR pg_catalog.to_regprocedure('app_api.list_offices(text,text)') IS NOT NULL
     OR pg_catalog.to_regclass(
       'app_private.idx_kb_active_official_category'
     ) IS NOT NULL
     OR pg_catalog.to_regclass('app_private.idx_events_occurred') IS NOT NULL
     OR pg_catalog.to_regclass('app_private.idx_failures_status') IS NOT NULL
     OR pg_catalog.to_regclass('app_private.idx_failure_text_expiry') IS NOT NULL
     OR pg_catalog.to_regclass('app_private.idx_candidates_status') IS NOT NULL THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'READ_INTERFACE_COMPENSATION_REQUIRED';
  END IF;
END;
$require_read_interface_compensation$;

REVOKE EXECUTE ON FUNCTION app_api.record_interaction(
  uuid, text, text, text, text[], integer, text, text, boolean, text
) FROM sejong_backend;
REVOKE EXECUTE ON FUNCTION app_api.purge_expired_failed_question_text()
  FROM sejong_backend;
REVOKE USAGE ON SCHEMA app_api FROM sejong_backend;

-- Task 6 extends the same forward migration. Keep its compensation identities
-- here from the start so this file remains the complete 00300 inverse.
DROP FUNCTION IF EXISTS app_api.reject_kb_candidate(uuid, text, text, text);
DROP FUNCTION IF EXISTS app_api.approve_kb_candidate(uuid, text, text);
DROP FUNCTION IF EXISTS app_api.submit_kb_candidate(uuid, text, text);
DROP FUNCTION IF EXISTS app_api.create_kb_candidate(
  uuid, text, text, text, text, text, text, jsonb, jsonb,
  text, text, text, text, text, date, text, text
);

DROP FUNCTION IF EXISTS app_api.purge_expired_failed_question_text();
DROP FUNCTION IF EXISTS app_api.record_interaction(
  uuid, text, text, text, text[], integer, text, text, boolean, text
);
DROP FUNCTION IF EXISTS
  app_private.purge_expired_failed_question_text_at(timestamptz);

DROP POLICY IF EXISTS audit_logs_owner_all ON app_private.audit_logs;
DROP POLICY IF EXISTS kb_candidates_owner_all ON app_private.kb_candidates;
DROP POLICY IF EXISTS failed_questions_owner_all ON app_private.failed_questions;
DROP POLICY IF EXISTS interaction_events_owner_all
  ON app_private.interaction_events;
DROP POLICY IF EXISTS office_service_mappings_owner_all
  ON app_private.office_service_mappings;
DROP POLICY IF EXISTS offices_owner_all ON app_private.offices;
DROP POLICY IF EXISTS kb_question_examples_owner_all
  ON app_private.kb_question_examples;
DROP POLICY IF EXISTS kb_documents_owner_all ON app_private.kb_documents;

ALTER TABLE app_private.audit_logs NO FORCE ROW LEVEL SECURITY;
ALTER TABLE app_private.kb_candidates NO FORCE ROW LEVEL SECURITY;
ALTER TABLE app_private.failed_questions NO FORCE ROW LEVEL SECURITY;
ALTER TABLE app_private.interaction_events NO FORCE ROW LEVEL SECURITY;
ALTER TABLE app_private.office_service_mappings NO FORCE ROW LEVEL SECURITY;
ALTER TABLE app_private.offices NO FORCE ROW LEVEL SECURITY;
ALTER TABLE app_private.kb_question_examples NO FORCE ROW LEVEL SECURITY;
ALTER TABLE app_private.kb_documents NO FORCE ROW LEVEL SECURITY;

REASSIGN OWNED BY sejong_schema_owner TO postgres;

DO $revoke_database_create$
BEGIN
  EXECUTE pg_catalog.format(
    'REVOKE CREATE ON DATABASE %I FROM sejong_schema_owner',
    pg_catalog.current_database()
  );
END;
$revoke_database_create$;

-- Forward grants deliberately prevent the migration runner from SET ROLE to
-- backend. Compensation temporarily enables SET (never INHERIT) solely so
-- DROP OWNED can revoke role-scoped privileges before the role is removed.
DO $grant_backend_cleanup$
BEGIN
  EXECUTE pg_catalog.format(
    'GRANT sejong_backend TO %I WITH SET TRUE',
    CURRENT_USER
  );
  EXECUTE pg_catalog.format(
    'GRANT sejong_backend TO %I WITH INHERIT FALSE',
    CURRENT_USER
  );
END;
$grant_backend_cleanup$;

SET LOCAL ROLE sejong_backend;
DROP OWNED BY sejong_backend;
RESET ROLE;

SET LOCAL ROLE sejong_schema_owner;
DROP OWNED BY sejong_schema_owner;
RESET ROLE;

DROP ROLE IF EXISTS sejong_backend;
DROP ROLE IF EXISTS sejong_schema_owner;

COMMIT;
