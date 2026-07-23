BEGIN;

REVOKE EXECUTE ON FUNCTION app_api.list_failed_questions(text, text)
  FROM sejong_backend;
REVOKE EXECUTE ON FUNCTION app_api.get_failed_question(uuid)
  FROM sejong_backend;
REVOKE EXECUTE ON FUNCTION app_api.list_kb_candidates()
  FROM sejong_backend;
REVOKE EXECUTE ON FUNCTION app_api.get_kb_candidate(uuid)
  FROM sejong_backend;

DROP FUNCTION app_api.get_kb_candidate(uuid);
DROP FUNCTION app_api.list_kb_candidates();
DROP FUNCTION app_api.get_failed_question(uuid);
DROP FUNCTION app_api.list_failed_questions(text, text);

COMMIT;
