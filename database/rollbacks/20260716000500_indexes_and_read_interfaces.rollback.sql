BEGIN;

REVOKE EXECUTE ON FUNCTION app_api.list_active_kb(text)
  FROM sejong_backend;
REVOKE EXECUTE ON FUNCTION app_api.list_offices(text, text)
  FROM sejong_backend;

REVOKE EXECUTE ON FUNCTION app_api.list_active_kb(text)
  FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION app_api.list_offices(text, text)
  FROM PUBLIC, anon, authenticated;

DROP FUNCTION app_api.list_active_kb(text);
DROP FUNCTION app_api.list_offices(text, text);

DROP INDEX app_private.idx_kb_active_official_category;
DROP INDEX app_private.idx_events_occurred;
DROP INDEX app_private.idx_failures_status;
DROP INDEX app_private.idx_failure_text_expiry;
DROP INDEX app_private.idx_candidates_status;

COMMIT;
