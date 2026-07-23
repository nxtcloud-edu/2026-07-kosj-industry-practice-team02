BEGIN;

REVOKE EXECUTE ON FUNCTION app_api.purge_expired_chat_idempotency()
  FROM sejong_backend;
REVOKE EXECUTE ON FUNCTION app_api.abandon_chat_idempotency(uuid, text, uuid)
  FROM sejong_backend;
REVOKE EXECUTE ON FUNCTION app_api.complete_chat_idempotency(uuid, text, uuid, jsonb)
  FROM sejong_backend;
REVOKE EXECUTE ON FUNCTION app_api.claim_chat_idempotency(uuid, text, uuid)
  FROM sejong_backend;

DROP FUNCTION app_api.purge_expired_chat_idempotency();
DROP FUNCTION app_api.abandon_chat_idempotency(uuid, text, uuid);
DROP FUNCTION app_api.complete_chat_idempotency(uuid, text, uuid, jsonb);
DROP FUNCTION app_api.claim_chat_idempotency(uuid, text, uuid);

DROP TRIGGER trg_chat_idempotency_set_updated_at
  ON app_private.chat_idempotency;
DROP POLICY chat_idempotency_owner_all
  ON app_private.chat_idempotency;
DROP TABLE app_private.chat_idempotency;
DROP FUNCTION app_private.idempotency_response_is_safe(jsonb);

COMMIT;
