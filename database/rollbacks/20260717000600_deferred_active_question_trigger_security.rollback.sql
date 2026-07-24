BEGIN;

ALTER FUNCTION app_private.validate_active_kb_question()
  SECURITY INVOKER;
ALTER FUNCTION app_private.validate_active_kb_question()
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_private.validate_active_kb_question()
  SET search_path = pg_catalog, pg_temp;
REVOKE ALL ON FUNCTION app_private.validate_active_kb_question()
  FROM PUBLIC, anon, authenticated, sejong_backend;

COMMIT;
