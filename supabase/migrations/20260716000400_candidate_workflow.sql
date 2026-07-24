BEGIN;

-- Task 6 extends the metadata-only audit vocabulary. The helper remains an
-- immutable, fixed-search-path validator and gains only workflow field names.
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
              'status',
              'fallback_reason',
              'candidate_eligible',
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
  DROP CONSTRAINT kb_candidates_approved_fields_chk,
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
      AND pg_catalog.char_length(review_comment) <= 1000
    ))
  ),
  ADD CONSTRAINT kb_candidates_state_shape_chk CHECK (
    CASE review_status
      WHEN 'DRAFTED' THEN
        reviewed_by IS NULL
        AND review_comment IS NULL
        AND approved_at IS NULL
        AND activated_kb_id IS NULL
      WHEN 'PENDING_APPROVAL' THEN
        reviewed_by IS NULL
        AND review_comment IS NULL
        AND approved_at IS NULL
        AND activated_kb_id IS NULL
      WHEN 'APPROVED' THEN
        reviewed_by IS NOT NULL
        AND review_comment IS NOT NULL
        AND approved_at IS NOT NULL
        AND activated_kb_id IS NOT NULL
      WHEN 'REJECTED' THEN
        reviewed_by IS NOT NULL
        AND review_comment IS NOT NULL
        AND approved_at IS NULL
        AND activated_kb_id IS NULL
      ELSE false
    END
  );

ALTER TABLE app_private.audit_logs
  DROP CONSTRAINT audit_logs_action_allowlist_chk,
  DROP CONSTRAINT audit_logs_target_type_chk,
  DROP CONSTRAINT audit_logs_status_values_chk,
  DROP CONSTRAINT audit_logs_review_comment_trimmed_nonempty_chk,
  ADD CONSTRAINT audit_logs_action_allowlist_chk CHECK (
    action IN (
      'CANDIDATE_CREATED',
      'CANDIDATE_SUBMITTED',
      'CANDIDATE_APPROVED',
      'CANDIDATE_REJECTED',
      'FAILED_QUESTION_REASON_CONFIRMED'
    )
  ),
  ADD CONSTRAINT audit_logs_target_type_chk CHECK (
    target_type IN ('KB_CANDIDATE', 'FAILED_QUESTION')
  ),
  ADD CONSTRAINT audit_logs_status_values_chk CHECK (
    (old_status IS NULL OR old_status IN (
      'NEW', 'REASON_CONFIRMED', 'DRAFTED', 'PENDING_APPROVAL',
      'APPROVED', 'REJECTED'
    ))
    AND (new_status IS NULL OR new_status IN (
      'NEW', 'REASON_CONFIRMED', 'DRAFTED', 'PENDING_APPROVAL',
      'APPROVED', 'REJECTED'
    ))
  ),
  ADD CONSTRAINT audit_logs_review_comment_trimmed_nonempty_chk CHECK (
    review_comment IS NULL OR (
      review_comment = pg_catalog.btrim(review_comment)
      AND app_private.is_nonempty_text(review_comment)
      AND pg_catalog.char_length(review_comment) <= 1000
    )
  ),
  ADD CONSTRAINT audit_logs_action_shape_chk CHECK (
    CASE action
      WHEN 'CANDIDATE_CREATED' THEN
        actor_role = 'OPERATOR'
        AND target_type = 'KB_CANDIDATE'
        AND old_status IS NULL
        AND new_status = 'DRAFTED'
        AND changed_field_names = '["review_status"]'::jsonb
        AND review_comment IS NULL
      WHEN 'CANDIDATE_SUBMITTED' THEN
        actor_role = 'OPERATOR'
        AND target_type = 'KB_CANDIDATE'
        AND old_status = 'DRAFTED'
        AND new_status = 'PENDING_APPROVAL'
        AND changed_field_names = '["review_status"]'::jsonb
        AND review_comment IS NULL
      WHEN 'CANDIDATE_APPROVED' THEN
        actor_role = 'APPROVER'
        AND target_type = 'KB_CANDIDATE'
        AND old_status = 'PENDING_APPROVAL'
        AND new_status = 'APPROVED'
        AND changed_field_names =
          '["review_status","reviewed_by","review_comment","approved_at","activated_kb_id"]'::jsonb
        AND review_comment IS NOT NULL
      WHEN 'CANDIDATE_REJECTED' THEN
        actor_role = 'APPROVER'
        AND target_type = 'KB_CANDIDATE'
        AND old_status = 'PENDING_APPROVAL'
        AND new_status = 'REJECTED'
        AND changed_field_names =
          '["review_status","reviewed_by","review_comment"]'::jsonb
        AND review_comment IS NOT NULL
      WHEN 'FAILED_QUESTION_REASON_CONFIRMED' THEN
        actor_role = 'OPERATOR'
        AND target_type = 'FAILED_QUESTION'
        AND old_status = 'NEW'
        AND new_status = 'REASON_CONFIRMED'
        AND changed_field_names IN (
          '["status"]'::jsonb,
          '["status","fallback_reason"]'::jsonb,
          '["status","fallback_reason","candidate_eligible"]'::jsonb
        )
        AND review_comment IS NULL
      ELSE false
    END
  );

-- A NEW failure must match its immutable automated event. After confirmation,
-- only the operator-owned reason may differ; intent and parent shape still hold.
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

  IF TG_OP = 'UPDATE'
     AND OLD.status = 'REASON_CONFIRMED'
     AND NEW.status = 'NEW' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'FAILED_EVENT_MISMATCH';
  END IF;

  SELECT event.answer_status, event.intent, event.fallback_reason
  INTO v_answer_status, v_intent, v_fallback_reason
  FROM app_private.interaction_events AS event
  WHERE event.id = NEW.interaction_event_id
  FOR SHARE;

  IF NOT FOUND THEN
    RETURN NEW;
  END IF;

  IF v_answer_status <> 'FALLBACK'
     OR v_fallback_reason = 'OUT_OF_SCOPE'
     OR v_intent IS DISTINCT FROM NEW.intent
     OR (
       NEW.status = 'NEW'
       AND v_fallback_reason IS DISTINCT FROM NEW.fallback_reason
     ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'FAILED_EVENT_MISMATCH';
  END IF;

  RETURN NEW;
END
$function$;

-- Once a failure exists, event classification is immutable. A no-op update is
-- allowed even when the operator-confirmed failure reason differs.
CREATE OR REPLACE FUNCTION app_private.validate_interaction_event_failure()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_has_failure boolean;
BEGIN
  IF pg_catalog.current_setting('transaction_isolation')
     IS DISTINCT FROM 'read committed' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'LINEAGE_WRITE_REQUIRES_READ_COMMITTED';
  END IF;

  SELECT EXISTS (
    SELECT 1
    FROM app_private.failed_questions AS failure
    WHERE failure.interaction_event_id = OLD.id
  )
  INTO v_has_failure;

  IF v_has_failure
     AND (
       NEW.intent IS DISTINCT FROM OLD.intent
       OR NEW.answer_status IS DISTINCT FROM OLD.answer_status
       OR NEW.fallback_reason IS DISTINCT FROM OLD.fallback_reason
     ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'FAILED_EVENT_IMMUTABLE';
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
  v_status app_private.candidate_status;
BEGIN
  IF pg_catalog.current_setting('transaction_isolation')
     IS DISTINCT FROM 'read committed' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'LINEAGE_WRITE_REQUIRES_READ_COMMITTED';
  END IF;

  SELECT failure.candidate_eligible, failure.fallback_reason, failure.status
  INTO v_candidate_eligible, v_fallback_reason, v_status
  FROM app_private.failed_questions AS failure
  WHERE failure.id = NEW.failed_question_id
  FOR UPDATE;

  IF NOT FOUND THEN
    RETURN NEW;
  END IF;

  IF v_status <> 'REASON_CONFIRMED'
     OR NOT v_candidate_eligible
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
       NEW.status <> 'REASON_CONFIRMED'
       OR NOT NEW.candidate_eligible
       OR NEW.fallback_reason <> 'INSUFFICIENT_GROUNDING'
     ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'CANDIDATE_FAILURE_NOT_ELIGIBLE';
  END IF;

  RETURN NEW;
END
$function$;

DROP TRIGGER trg_failed_questions_validate_event
  ON app_private.failed_questions;
CREATE TRIGGER trg_failed_questions_validate_event
BEFORE INSERT OR UPDATE OF interaction_event_id, intent, fallback_reason, status
ON app_private.failed_questions
FOR EACH ROW EXECUTE FUNCTION app_private.validate_failed_question_event();

DROP TRIGGER trg_failed_questions_validate_candidate
  ON app_private.failed_questions;
CREATE TRIGGER trg_failed_questions_validate_candidate
BEFORE UPDATE OF candidate_eligible, fallback_reason
ON app_private.failed_questions
FOR EACH ROW EXECUTE FUNCTION app_private.validate_failed_question_candidate();

CREATE TRIGGER trg_failed_questions_validate_candidate_status
BEFORE UPDATE OF status ON app_private.failed_questions
FOR EACH ROW EXECUTE FUNCTION app_private.validate_failed_question_candidate();

CREATE FUNCTION app_api.confirm_failed_question_reason(
  p_failed_question_id uuid,
  p_actor_id text,
  p_actor_role text,
  p_confirmed_reason text
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $confirm_reason$
DECLARE
  v_failure app_private.failed_questions%ROWTYPE;
  v_event app_private.interaction_events%ROWTYPE;
  v_confirmed_reason app_private.fallback_reason;
  v_candidate_eligible boolean;
  v_changed_fields jsonb := '["status"]'::jsonb;
BEGIN
  IF p_actor_role IS DISTINCT FROM 'OPERATOR'
     OR p_actor_id IS NULL
     OR p_actor_id IS DISTINCT FROM pg_catalog.btrim(p_actor_id)
     OR pg_catalog.btrim(p_actor_id) = '' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1001', MESSAGE = 'FORBIDDEN_ACTOR';
  END IF;

  IF p_confirmed_reason IS NULL
     OR p_confirmed_reason NOT IN (
       'INSUFFICIENT_GROUNDING', 'PERSONAL_LOOKUP', 'LEGAL_JUDGMENT'
     ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'INVALID_FAILURE_REASON';
  END IF;

  IF pg_catalog.current_setting('transaction_isolation')
     IS DISTINCT FROM 'read committed' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'INVALID_FAILURE_REASON';
  END IF;

  SELECT failures.* INTO v_failure
  FROM app_private.failed_questions AS failures
  WHERE failures.id = p_failed_question_id
  FOR UPDATE;

  IF NOT FOUND OR v_failure.status <> 'NEW' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
  END IF;

  SELECT events.* INTO v_event
  FROM app_private.interaction_events AS events
  WHERE events.id = v_failure.interaction_event_id
  FOR SHARE;

  IF NOT FOUND
     OR v_event.answer_status <> 'FALLBACK'
     OR v_event.fallback_reason = 'OUT_OF_SCOPE'
     OR v_event.intent IS DISTINCT FROM v_failure.intent
     OR v_event.fallback_reason IS DISTINCT FROM v_failure.fallback_reason THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'INVALID_FAILURE_REASON';
  END IF;

  v_confirmed_reason := p_confirmed_reason::app_private.fallback_reason;
  v_candidate_eligible := p_confirmed_reason = 'INSUFFICIENT_GROUNDING';

  IF v_failure.fallback_reason IS DISTINCT FROM v_confirmed_reason THEN
    v_changed_fields := v_changed_fields || '["fallback_reason"]'::jsonb;
  END IF;
  IF v_failure.candidate_eligible IS DISTINCT FROM v_candidate_eligible THEN
    v_changed_fields := v_changed_fields || '["candidate_eligible"]'::jsonb;
  END IF;

  UPDATE app_private.failed_questions AS failures
  SET fallback_reason = v_confirmed_reason,
      candidate_eligible = v_candidate_eligible,
      status = 'REASON_CONFIRMED'
  WHERE failures.id = p_failed_question_id;

  INSERT INTO app_private.audit_logs (
    actor_id, actor_role, action, target_type, target_id,
    old_status, new_status, changed_field_names
  ) VALUES (
    p_actor_id, 'OPERATOR', 'FAILED_QUESTION_REASON_CONFIRMED',
    'FAILED_QUESTION', p_failed_question_id, 'NEW', 'REASON_CONFIRMED',
    v_changed_fields
  );
END
$confirm_reason$;

CREATE FUNCTION app_api.create_kb_candidate(
  p_failed_question_id uuid,
  p_actor_id text,
  p_actor_role text,
  p_title text,
  p_representative_question text,
  p_category text,
  p_answer_summary text,
  p_procedure_steps jsonb,
  p_required_documents jsonb,
  p_processing_time text,
  p_fee text,
  p_department text,
  p_source_title text,
  p_source_url text,
  p_last_verified_at date,
  p_caution text,
  p_data_origin text
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $create_candidate$
DECLARE
  v_failure app_private.failed_questions%ROWTYPE;
  v_candidate_id uuid;
BEGIN
  IF p_actor_role IS DISTINCT FROM 'OPERATOR'
     OR p_actor_id IS NULL
     OR p_actor_id IS DISTINCT FROM pg_catalog.btrim(p_actor_id)
     OR pg_catalog.btrim(p_actor_id) = '' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1001', MESSAGE = 'FORBIDDEN_ACTOR';
  END IF;

  IF p_title IS NULL OR p_title IS DISTINCT FROM pg_catalog.btrim(p_title)
     OR pg_catalog.btrim(p_title) = ''
     OR p_representative_question IS NULL
     OR p_representative_question IS DISTINCT FROM
       pg_catalog.btrim(p_representative_question)
     OR pg_catalog.btrim(p_representative_question) = ''
     OR p_category IS NULL
     OR p_category NOT IN (
       'MOVE_IN_RESIDENT_REGISTRATION', 'CERTIFICATE_ISSUANCE',
       'BULKY_WASTE', 'LOCAL_TAX_GENERAL'
     )
     OR p_answer_summary IS NULL
     OR p_answer_summary IS DISTINCT FROM pg_catalog.btrim(p_answer_summary)
     OR pg_catalog.btrim(p_answer_summary) = ''
     OR p_procedure_steps IS NULL
     OR NOT app_private.is_text_array(p_procedure_steps)
     OR p_required_documents IS NULL
     OR NOT app_private.is_text_array(p_required_documents)
     OR p_department IS NULL
     OR p_department IS DISTINCT FROM pg_catalog.btrim(p_department)
     OR pg_catalog.btrim(p_department) = ''
     OR p_source_title IS NULL
     OR p_source_title IS DISTINCT FROM pg_catalog.btrim(p_source_title)
     OR pg_catalog.btrim(p_source_title) = ''
     OR p_source_url IS NULL
     OR p_source_url IS DISTINCT FROM pg_catalog.btrim(p_source_url)
     OR pg_catalog.btrim(p_source_url) = ''
     OR p_last_verified_at IS NULL
     OR (p_processing_time IS NOT NULL AND (
       p_processing_time IS DISTINCT FROM pg_catalog.btrim(p_processing_time)
       OR pg_catalog.btrim(p_processing_time) = ''
     ))
     OR (p_fee IS NOT NULL AND (
       p_fee IS DISTINCT FROM pg_catalog.btrim(p_fee)
       OR pg_catalog.btrim(p_fee) = ''
     ))
     OR (p_caution IS NOT NULL AND (
       p_caution IS DISTINCT FROM pg_catalog.btrim(p_caution)
       OR pg_catalog.btrim(p_caution) = ''
     )) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1004', MESSAGE = 'INCOMPLETE_CANDIDATE';
  END IF;

  IF p_data_origin IS NULL OR p_data_origin NOT IN ('OFFICIAL', 'MOCK') THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1005', MESSAGE = 'DISALLOWED_ORIGIN';
  END IF;

  IF pg_catalog.current_setting('transaction_isolation')
     IS DISTINCT FROM 'read committed' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
  END IF;

  SELECT failures.* INTO v_failure
  FROM app_private.failed_questions AS failures
  WHERE failures.id = p_failed_question_id
  FOR UPDATE;

  IF NOT FOUND
     OR v_failure.status <> 'REASON_CONFIRMED'
     OR v_failure.fallback_reason <> 'INSUFFICIENT_GROUNDING'
     OR NOT v_failure.candidate_eligible
     OR EXISTS (
       SELECT 1 FROM app_private.kb_candidates AS candidates
       WHERE candidates.failed_question_id = p_failed_question_id
     ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
  END IF;

  INSERT INTO app_private.kb_candidates (
    failed_question_id, title, representative_question, data_origin, category,
    answer_summary, procedure_steps, required_documents, processing_time, fee,
    department, source_title, source_url, last_verified_at, caution,
    created_by, review_status
  ) VALUES (
    p_failed_question_id, p_title, p_representative_question,
    p_data_origin::app_private.data_origin,
    p_category::app_private.intent_code, p_answer_summary, p_procedure_steps,
    p_required_documents, p_processing_time, p_fee, p_department,
    p_source_title, p_source_url, p_last_verified_at, p_caution,
    p_actor_id, 'DRAFTED'
  )
  RETURNING id INTO v_candidate_id;

  INSERT INTO app_private.audit_logs (
    actor_id, actor_role, action, target_type, target_id,
    old_status, new_status, changed_field_names
  ) VALUES (
    p_actor_id, 'OPERATOR', 'CANDIDATE_CREATED', 'KB_CANDIDATE',
    v_candidate_id, NULL, 'DRAFTED', '["review_status"]'::jsonb
  );

  RETURN v_candidate_id;
END
$create_candidate$;

CREATE FUNCTION app_api.submit_kb_candidate(
  p_candidate_id uuid,
  p_actor_id text,
  p_actor_role text
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $submit_candidate$
DECLARE
  v_candidate app_private.kb_candidates%ROWTYPE;
BEGIN
  IF p_actor_role IS DISTINCT FROM 'OPERATOR'
     OR p_actor_id IS NULL
     OR p_actor_id IS DISTINCT FROM pg_catalog.btrim(p_actor_id)
     OR pg_catalog.btrim(p_actor_id) = '' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1001', MESSAGE = 'FORBIDDEN_ACTOR';
  END IF;

  IF pg_catalog.current_setting('transaction_isolation')
     IS DISTINCT FROM 'read committed' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
  END IF;

  SELECT candidates.* INTO v_candidate
  FROM app_private.kb_candidates AS candidates
  WHERE candidates.id = p_candidate_id
  FOR UPDATE;

  IF NOT FOUND OR v_candidate.review_status <> 'DRAFTED' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
  END IF;

  IF v_candidate.created_by IS DISTINCT FROM p_actor_id THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1001', MESSAGE = 'FORBIDDEN_ACTOR';
  END IF;

  IF NOT app_private.is_nonempty_text(v_candidate.title)
     OR NOT app_private.is_nonempty_text(v_candidate.representative_question)
     OR NOT app_private.is_nonempty_text(v_candidate.answer_summary)
     OR NOT app_private.is_text_array(v_candidate.procedure_steps)
     OR NOT app_private.is_text_array(v_candidate.required_documents)
     OR NOT app_private.is_nonempty_text(v_candidate.department)
     OR NOT app_private.is_nonempty_text(v_candidate.source_title)
     OR NOT app_private.is_nonempty_text(v_candidate.source_url)
     OR v_candidate.last_verified_at IS NULL THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1004', MESSAGE = 'INCOMPLETE_CANDIDATE';
  END IF;

  UPDATE app_private.kb_candidates AS candidates
  SET review_status = 'PENDING_APPROVAL'
  WHERE candidates.id = p_candidate_id;

  INSERT INTO app_private.audit_logs (
    actor_id, actor_role, action, target_type, target_id,
    old_status, new_status, changed_field_names
  ) VALUES (
    p_actor_id, 'OPERATOR', 'CANDIDATE_SUBMITTED', 'KB_CANDIDATE',
    p_candidate_id, 'DRAFTED', 'PENDING_APPROVAL',
    '["review_status"]'::jsonb
  );
END
$submit_candidate$;

CREATE FUNCTION app_api.approve_kb_candidate(
  p_candidate_id uuid,
  p_actor_id text,
  p_actor_role text,
  p_review_comment text
)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $approve_candidate$
DECLARE
  v_candidate app_private.kb_candidates%ROWTYPE;
  v_review_comment text;
  v_approved_at timestamptz;
  v_kb_id uuid;
  v_public_id text;
BEGIN
  IF p_actor_role IS DISTINCT FROM 'APPROVER'
     OR p_actor_id IS NULL
     OR p_actor_id IS DISTINCT FROM pg_catalog.btrim(p_actor_id)
     OR pg_catalog.btrim(p_actor_id) = '' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1001', MESSAGE = 'FORBIDDEN_ACTOR';
  END IF;

  v_review_comment := pg_catalog.btrim(p_review_comment);
  IF p_review_comment IS NULL
     OR v_review_comment = ''
     OR pg_catalog.char_length(v_review_comment) > 1000 THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1004', MESSAGE = 'INCOMPLETE_CANDIDATE';
  END IF;

  IF pg_catalog.current_setting('transaction_isolation')
     IS DISTINCT FROM 'read committed' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
  END IF;

  SELECT candidates.* INTO v_candidate
  FROM app_private.kb_candidates AS candidates
  WHERE candidates.id = p_candidate_id
  FOR UPDATE;

  IF NOT FOUND OR v_candidate.review_status <> 'PENDING_APPROVAL' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
  END IF;

  IF v_candidate.created_by = p_actor_id THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1002', MESSAGE = 'SELF_REVIEW_FORBIDDEN';
  END IF;

  IF NOT app_private.is_nonempty_text(v_candidate.title)
     OR NOT app_private.is_nonempty_text(v_candidate.representative_question)
     OR NOT app_private.is_nonempty_text(v_candidate.answer_summary)
     OR NOT app_private.is_text_array(v_candidate.procedure_steps)
     OR NOT app_private.is_text_array(v_candidate.required_documents)
     OR NOT app_private.is_nonempty_text(v_candidate.department)
     OR NOT app_private.is_nonempty_text(v_candidate.source_title)
     OR NOT app_private.is_nonempty_text(v_candidate.source_url)
     OR v_candidate.last_verified_at IS NULL THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1004', MESSAGE = 'INCOMPLETE_CANDIDATE';
  END IF;

  IF v_candidate.data_origin <> 'OFFICIAL' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1005', MESSAGE = 'DISALLOWED_ORIGIN';
  END IF;

  v_approved_at := pg_catalog.clock_timestamp();
  v_public_id := 'KB-' || pg_catalog.upper(
    pg_catalog.replace(v_candidate.id::text, '-', '')
  );

  BEGIN
    INSERT INTO app_private.kb_documents (
      public_id, data_origin, category, service_name, answer_summary,
      procedure_steps, required_documents, processing_time, fee, department,
      source_title, source_url, last_verified_at, caution, status,
      created_by, approved_by, approved_at
    ) VALUES (
      v_public_id, 'OFFICIAL', v_candidate.category, v_candidate.title,
      v_candidate.answer_summary, v_candidate.procedure_steps,
      v_candidate.required_documents, v_candidate.processing_time,
      v_candidate.fee, v_candidate.department, v_candidate.source_title,
      v_candidate.source_url, v_candidate.last_verified_at, v_candidate.caution,
      'ACTIVE', v_candidate.created_by, p_actor_id, v_approved_at
    )
    RETURNING id INTO v_kb_id;
  EXCEPTION
    WHEN unique_violation THEN
      RAISE EXCEPTION USING
        ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
  END;

  INSERT INTO app_private.kb_question_examples (
    kb_document_id, question_example
  ) VALUES (
    v_kb_id, v_candidate.representative_question
  );

  UPDATE app_private.kb_candidates AS candidates
  SET review_status = 'APPROVED',
      reviewed_by = p_actor_id,
      review_comment = v_review_comment,
      approved_at = v_approved_at,
      activated_kb_id = v_kb_id
  WHERE candidates.id = p_candidate_id;

  INSERT INTO app_private.audit_logs (
    actor_id, actor_role, action, target_type, target_id,
    old_status, new_status, changed_field_names, review_comment
  ) VALUES (
    p_actor_id, 'APPROVER', 'CANDIDATE_APPROVED', 'KB_CANDIDATE',
    p_candidate_id, 'PENDING_APPROVAL', 'APPROVED',
    '["review_status","reviewed_by","review_comment","approved_at","activated_kb_id"]'::jsonb,
    v_review_comment
  );

  RETURN v_public_id;
END
$approve_candidate$;

CREATE FUNCTION app_api.reject_kb_candidate(
  p_candidate_id uuid,
  p_actor_id text,
  p_actor_role text,
  p_review_comment text
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $reject_candidate$
DECLARE
  v_candidate app_private.kb_candidates%ROWTYPE;
  v_review_comment text;
BEGIN
  IF p_actor_role IS DISTINCT FROM 'APPROVER'
     OR p_actor_id IS NULL
     OR p_actor_id IS DISTINCT FROM pg_catalog.btrim(p_actor_id)
     OR pg_catalog.btrim(p_actor_id) = '' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1001', MESSAGE = 'FORBIDDEN_ACTOR';
  END IF;

  v_review_comment := pg_catalog.btrim(p_review_comment);
  IF p_review_comment IS NULL
     OR v_review_comment = ''
     OR pg_catalog.char_length(v_review_comment) > 1000 THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1004', MESSAGE = 'INCOMPLETE_CANDIDATE';
  END IF;

  IF pg_catalog.current_setting('transaction_isolation')
     IS DISTINCT FROM 'read committed' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
  END IF;

  SELECT candidates.* INTO v_candidate
  FROM app_private.kb_candidates AS candidates
  WHERE candidates.id = p_candidate_id
  FOR UPDATE;

  IF NOT FOUND OR v_candidate.review_status <> 'PENDING_APPROVAL' THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
  END IF;

  IF v_candidate.created_by = p_actor_id THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1002', MESSAGE = 'SELF_REVIEW_FORBIDDEN';
  END IF;

  UPDATE app_private.kb_candidates AS candidates
  SET review_status = 'REJECTED',
      reviewed_by = p_actor_id,
      review_comment = v_review_comment
  WHERE candidates.id = p_candidate_id;

  INSERT INTO app_private.audit_logs (
    actor_id, actor_role, action, target_type, target_id,
    old_status, new_status, changed_field_names, review_comment
  ) VALUES (
    p_actor_id, 'APPROVER', 'CANDIDATE_REJECTED', 'KB_CANDIDATE',
    p_candidate_id, 'PENDING_APPROVAL', 'REJECTED',
    '["review_status","reviewed_by","review_comment"]'::jsonb,
    v_review_comment
  );
END
$reject_candidate$;

ALTER FUNCTION app_api.confirm_failed_question_reason(uuid, text, text, text)
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_api.create_kb_candidate(
  uuid, text, text, text, text, text, text, jsonb, jsonb,
  text, text, text, text, text, date, text, text
) OWNER TO sejong_schema_owner;
ALTER FUNCTION app_api.submit_kb_candidate(uuid, text, text)
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_api.approve_kb_candidate(uuid, text, text, text)
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_api.reject_kb_candidate(uuid, text, text, text)
  OWNER TO sejong_schema_owner;

REVOKE ALL ON FUNCTION app_api.confirm_failed_question_reason(
  uuid, text, text, text
) FROM PUBLIC, anon, authenticated, sejong_backend;
REVOKE ALL ON FUNCTION app_api.create_kb_candidate(
  uuid, text, text, text, text, text, text, jsonb, jsonb,
  text, text, text, text, text, date, text, text
) FROM PUBLIC, anon, authenticated, sejong_backend;
REVOKE ALL ON FUNCTION app_api.submit_kb_candidate(uuid, text, text)
  FROM PUBLIC, anon, authenticated, sejong_backend;
REVOKE ALL ON FUNCTION app_api.approve_kb_candidate(uuid, text, text, text)
  FROM PUBLIC, anon, authenticated, sejong_backend;
REVOKE ALL ON FUNCTION app_api.reject_kb_candidate(uuid, text, text, text)
  FROM PUBLIC, anon, authenticated, sejong_backend;

GRANT EXECUTE ON FUNCTION app_api.confirm_failed_question_reason(
  uuid, text, text, text
) TO sejong_backend;
GRANT EXECUTE ON FUNCTION app_api.create_kb_candidate(
  uuid, text, text, text, text, text, text, jsonb, jsonb,
  text, text, text, text, text, date, text, text
) TO sejong_backend;
GRANT EXECUTE ON FUNCTION app_api.submit_kb_candidate(uuid, text, text)
  TO sejong_backend;
GRANT EXECUTE ON FUNCTION app_api.approve_kb_candidate(
  uuid, text, text, text
) TO sejong_backend;
GRANT EXECUTE ON FUNCTION app_api.reject_kb_candidate(
  uuid, text, text, text
) TO sejong_backend;

COMMIT;
