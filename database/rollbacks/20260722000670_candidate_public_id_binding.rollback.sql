BEGIN;

REVOKE ALL ON FUNCTION app_api.approve_kb_candidate_with_public_id(uuid, text, text, text, text)
  FROM PUBLIC, anon, authenticated, sejong_backend;
DROP FUNCTION app_api.approve_kb_candidate_with_public_id(uuid, text, text, text, text);

COMMIT;
