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

REVOKE EXECUTE ON FUNCTION app_api.confirm_failed_question_reason(
  uuid, text, text, text
) FROM sejong_backend;
REVOKE EXECUTE ON FUNCTION app_api.create_kb_candidate(
  uuid, text, text, text, text, text, text, jsonb, jsonb,
  text, text, text, text, text, date, text, text
) FROM sejong_backend;
REVOKE EXECUTE ON FUNCTION app_api.submit_kb_candidate(uuid, text, text)
  FROM sejong_backend;
REVOKE EXECUTE ON FUNCTION app_api.approve_kb_candidate(
  uuid, text, text, text
) FROM sejong_backend;
REVOKE EXECUTE ON FUNCTION app_api.reject_kb_candidate(
  uuid, text, text, text
) FROM sejong_backend;

DROP FUNCTION app_api.reject_kb_candidate(uuid, text, text, text);
DROP FUNCTION app_api.approve_kb_candidate(uuid, text, text, text);
DROP FUNCTION app_api.submit_kb_candidate(uuid, text, text);
DROP FUNCTION app_api.create_kb_candidate(
  uuid, text, text, text, text, text, text, jsonb, jsonb,
  text, text, text, text, text, date, text, text
);
DROP FUNCTION app_api.confirm_failed_question_reason(uuid, text, text, text);

DROP TRIGGER trg_failed_questions_validate_candidate_status
  ON app_private.failed_questions;
DROP TRIGGER trg_failed_questions_validate_candidate
  ON app_private.failed_questions;
DROP TRIGGER trg_failed_questions_validate_event
  ON app_private.failed_questions;

CREATE OR REPLACE FUNCTION app_private.validate_failed_question_event()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_answer_status app_private.answer_status;
  v_intent app_private.intent_code;
  v_fallback_reason app_private.fallback_reason;
BEGIN
  IF pg_catalog.current_setting('transaction_isolation')
     IS DISTINCT FROM 'read committed' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'LINEAGE_WRITE_REQUIRES_READ_COMMITTED';
  END IF;

  SELECT event.answer_status, event.intent, event.fallback_reason
  INTO v_answer_status, v_intent, v_fallback_reason
  FROM app_private.interaction_events AS event
  WHERE event.id = NEW.interaction_event_id
  FOR UPDATE;

  IF NOT FOUND THEN
    RETURN NEW;
  END IF;

  IF v_answer_status <> 'FALLBACK'
     OR v_fallback_reason = 'OUT_OF_SCOPE'
     OR v_intent IS DISTINCT FROM NEW.intent
     OR v_fallback_reason IS DISTINCT FROM NEW.fallback_reason THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'FAILED_EVENT_MISMATCH';
  END IF;

  RETURN NEW;
END
$function$;

CREATE OR REPLACE FUNCTION app_private.validate_interaction_event_failure()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_failure_intent app_private.intent_code;
  v_failure_reason app_private.fallback_reason;
BEGIN
  IF pg_catalog.current_setting('transaction_isolation')
     IS DISTINCT FROM 'read committed' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'LINEAGE_WRITE_REQUIRES_READ_COMMITTED';
  END IF;

  SELECT failure.intent, failure.fallback_reason
  INTO v_failure_intent, v_failure_reason
  FROM app_private.failed_questions AS failure
  WHERE failure.interaction_event_id = OLD.id;

  IF NOT FOUND THEN
    RETURN NEW;
  END IF;

  IF NEW.answer_status <> 'FALLBACK'
     OR NEW.fallback_reason = 'OUT_OF_SCOPE'
     OR NEW.intent IS DISTINCT FROM v_failure_intent
     OR NEW.fallback_reason IS DISTINCT FROM v_failure_reason THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'FAILED_EVENT_MISMATCH';
  END IF;

  RETURN NEW;
END
$function$;

CREATE OR REPLACE FUNCTION app_private.validate_kb_candidate_failure()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_candidate_eligible boolean;
  v_fallback_reason app_private.fallback_reason;
BEGIN
  IF pg_catalog.current_setting('transaction_isolation')
     IS DISTINCT FROM 'read committed' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'LINEAGE_WRITE_REQUIRES_READ_COMMITTED';
  END IF;

  SELECT failure.candidate_eligible, failure.fallback_reason
  INTO v_candidate_eligible, v_fallback_reason
  FROM app_private.failed_questions AS failure
  WHERE failure.id = NEW.failed_question_id
  FOR UPDATE;

  IF NOT FOUND THEN
    RETURN NEW;
  END IF;

  IF NOT v_candidate_eligible
     OR v_fallback_reason <> 'INSUFFICIENT_GROUNDING' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'CANDIDATE_FAILURE_NOT_ELIGIBLE';
  END IF;

  RETURN NEW;
END
$function$;

CREATE OR REPLACE FUNCTION app_private.validate_failed_question_candidate()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_has_candidate boolean;
BEGIN
  IF pg_catalog.current_setting('transaction_isolation')
     IS DISTINCT FROM 'read committed' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'LINEAGE_WRITE_REQUIRES_READ_COMMITTED';
  END IF;

  SELECT EXISTS (
    SELECT 1
    FROM app_private.kb_candidates AS candidate
    WHERE candidate.failed_question_id = OLD.id
  )
  INTO v_has_candidate;

  IF v_has_candidate
     AND (
       NOT NEW.candidate_eligible
       OR NEW.fallback_reason <> 'INSUFFICIENT_GROUNDING'
     ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'CANDIDATE_FAILURE_NOT_ELIGIBLE';
  END IF;

  RETURN NEW;
END
$function$;

CREATE TRIGGER trg_failed_questions_validate_event
BEFORE INSERT OR UPDATE OF interaction_event_id, intent, fallback_reason
ON app_private.failed_questions
FOR EACH ROW EXECUTE FUNCTION app_private.validate_failed_question_event();

CREATE TRIGGER trg_failed_questions_validate_candidate
BEFORE UPDATE OF candidate_eligible, fallback_reason
ON app_private.failed_questions
FOR EACH ROW EXECUTE FUNCTION app_private.validate_failed_question_candidate();

ALTER TABLE app_private.audit_logs
  DROP CONSTRAINT audit_logs_action_shape_chk,
  DROP CONSTRAINT audit_logs_review_comment_trimmed_nonempty_chk,
  DROP CONSTRAINT audit_logs_status_values_chk,
  DROP CONSTRAINT audit_logs_target_type_chk,
  DROP CONSTRAINT audit_logs_action_allowlist_chk,
  ADD CONSTRAINT audit_logs_action_allowlist_chk CHECK (
    action IN (
      'CANDIDATE_CREATED',
      'CANDIDATE_SUBMITTED',
      'CANDIDATE_APPROVED',
      'CANDIDATE_REJECTED'
    )
  ),
  ADD CONSTRAINT audit_logs_target_type_chk CHECK (
    target_type = 'KB_CANDIDATE'
  ),
  ADD CONSTRAINT audit_logs_status_values_chk CHECK (
    (old_status IS NULL OR old_status IN (
      'DRAFTED', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED'
    ))
    AND (new_status IS NULL OR new_status IN (
      'DRAFTED', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED'
    ))
  ),
  ADD CONSTRAINT audit_logs_review_comment_trimmed_nonempty_chk CHECK (
    review_comment IS NULL OR (
      review_comment = pg_catalog.btrim(review_comment)
      AND app_private.is_nonempty_text(review_comment)
    )
  );

CREATE OR REPLACE FUNCTION app_private.is_allowed_audit_changed_fields(
  p_value jsonb
)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
STRICT
SET search_path = pg_catalog
AS $function$
  SELECT CASE
    WHEN pg_catalog.jsonb_typeof(p_value) <> 'array' THEN false
    WHEN pg_catalog.jsonb_array_length(p_value) = 0 THEN false
    ELSE
      NOT EXISTS (
        SELECT 1
        FROM pg_catalog.jsonb_array_elements(p_value) AS item(value)
        WHERE CASE
          WHEN pg_catalog.jsonb_typeof(item.value) = 'string' THEN
            pg_catalog.btrim(item.value #>> '{}') = ''
            OR item.value #>> '{}' NOT IN (
              'review_status',
              'reviewed_by',
              'review_comment',
              'approved_at',
              'activated_kb_id'
            )
          ELSE true
        END
      )
      AND (
        SELECT pg_catalog.count(*) = pg_catalog.count(
          DISTINCT CASE
            WHEN pg_catalog.jsonb_typeof(item.value) = 'string'
              THEN item.value #>> '{}'
            ELSE NULL
          END
        )
        FROM pg_catalog.jsonb_array_elements(p_value) AS item(value)
      )
  END
$function$;

ALTER TABLE app_private.kb_candidates
  DROP CONSTRAINT kb_candidates_state_shape_chk,
  DROP CONSTRAINT kb_candidates_optional_text_trimmed_nonempty_chk,
  ADD CONSTRAINT kb_candidates_optional_text_trimmed_nonempty_chk CHECK (
    (processing_time IS NULL OR (
      processing_time = pg_catalog.btrim(processing_time)
      AND app_private.is_nonempty_text(processing_time)
    ))
    AND (fee IS NULL OR (
      fee = pg_catalog.btrim(fee)
      AND app_private.is_nonempty_text(fee)
    ))
    AND (caution IS NULL OR (
      caution = pg_catalog.btrim(caution)
      AND app_private.is_nonempty_text(caution)
    ))
    AND (reviewed_by IS NULL OR (
      reviewed_by = pg_catalog.btrim(reviewed_by)
      AND app_private.is_nonempty_text(reviewed_by)
    ))
    AND (review_comment IS NULL OR (
      review_comment = pg_catalog.btrim(review_comment)
      AND app_private.is_nonempty_text(review_comment)
    ))
  ),
  ADD CONSTRAINT kb_candidates_approved_fields_chk CHECK (
    review_status <> 'APPROVED'
    OR (
      reviewed_by IS NOT NULL
      AND approved_at IS NOT NULL
      AND activated_kb_id IS NOT NULL
    )
  );

COMMIT;
