BEGIN;

CREATE FUNCTION app_private.is_nonempty_text(p_value text)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
STRICT
SET search_path = pg_catalog
AS $function$
  SELECT pg_catalog.btrim(p_value) <> ''
$function$;

CREATE FUNCTION app_private.is_text_array(p_value jsonb)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
STRICT
SET search_path = pg_catalog
AS $function$
  SELECT CASE
    WHEN pg_catalog.jsonb_typeof(p_value) <> 'array' THEN false
    ELSE NOT EXISTS (
      SELECT 1
      FROM pg_catalog.jsonb_array_elements(p_value) AS item(value)
      WHERE CASE
        WHEN pg_catalog.jsonb_typeof(item.value) = 'string'
          THEN pg_catalog.btrim(item.value #>> '{}') = ''
        ELSE true
      END
    )
  END
$function$;

CREATE FUNCTION app_private.is_unique_text_array(p_value jsonb)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
STRICT
SET search_path = pg_catalog
AS $function$
  SELECT CASE
    WHEN pg_catalog.jsonb_typeof(p_value) <> 'array' THEN false
    ELSE (
      SELECT
        pg_catalog.count(*) = pg_catalog.count(
          CASE
            WHEN pg_catalog.jsonb_typeof(item.value) = 'string'
              THEN item.value #>> '{}'
            ELSE NULL
          END
        )
        AND pg_catalog.count(*) = pg_catalog.count(
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

CREATE FUNCTION app_private.is_allowed_audit_changed_fields(p_value jsonb)
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

ALTER TABLE app_private.kb_documents
  ADD CONSTRAINT kb_documents_public_id_trimmed_nonempty_chk CHECK (
    public_id = pg_catalog.btrim(public_id)
    AND app_private.is_nonempty_text(public_id)
  ),
  ADD CONSTRAINT kb_documents_required_text_trimmed_nonempty_chk CHECK (
    service_name = pg_catalog.btrim(service_name)
    AND app_private.is_nonempty_text(service_name)
    AND answer_summary = pg_catalog.btrim(answer_summary)
    AND app_private.is_nonempty_text(answer_summary)
    AND department = pg_catalog.btrim(department)
    AND app_private.is_nonempty_text(department)
    AND source_title = pg_catalog.btrim(source_title)
    AND app_private.is_nonempty_text(source_title)
    AND source_url = pg_catalog.btrim(source_url)
    AND app_private.is_nonempty_text(source_url)
    AND created_by = pg_catalog.btrim(created_by)
    AND app_private.is_nonempty_text(created_by)
  ),
  ADD CONSTRAINT kb_documents_optional_text_trimmed_nonempty_chk CHECK (
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
  ),
  ADD CONSTRAINT kb_documents_text_arrays_chk CHECK (
    app_private.is_text_array(procedure_steps)
    AND app_private.is_text_array(required_documents)
  ),
  ADD CONSTRAINT kb_documents_supported_category_chk CHECK (
    category IN (
      'MOVE_IN_RESIDENT_REGISTRATION',
      'CERTIFICATE_ISSUANCE',
      'BULKY_WASTE',
      'LOCAL_TAX_GENERAL'
    )
  ),
  ADD CONSTRAINT kb_documents_active_official_approval_chk CHECK (
    status <> 'ACTIVE'
    OR (
      data_origin = 'OFFICIAL'
      AND approved_by IS NOT NULL
      AND approved_by = pg_catalog.btrim(approved_by)
      AND app_private.is_nonempty_text(approved_by)
      AND approved_at IS NOT NULL
    )
  ),
  ADD CONSTRAINT kb_documents_approver_not_author_chk CHECK (
    approved_by IS NULL OR approved_by <> created_by
  );

ALTER TABLE app_private.kb_question_examples
  ADD CONSTRAINT kb_question_examples_question_trimmed_nonempty_chk CHECK (
    question_example = pg_catalog.btrim(question_example)
    AND app_private.is_nonempty_text(question_example)
  ),
  ADD CONSTRAINT kb_question_examples_normalized_trimmed_nonempty_chk CHECK (
    normalized_text IS NULL OR (
      normalized_text = pg_catalog.btrim(normalized_text)
      AND app_private.is_nonempty_text(normalized_text)
    )
  );

ALTER TABLE app_private.offices
  ADD CONSTRAINT offices_public_id_trimmed_nonempty_chk CHECK (
    public_id = pg_catalog.btrim(public_id)
    AND app_private.is_nonempty_text(public_id)
  ),
  ADD CONSTRAINT offices_required_text_trimmed_nonempty_chk CHECK (
    office_name = pg_catalog.btrim(office_name)
    AND app_private.is_nonempty_text(office_name)
    AND address = pg_catalog.btrim(address)
    AND app_private.is_nonempty_text(address)
    AND phone = pg_catalog.btrim(phone)
    AND app_private.is_nonempty_text(phone)
    AND source_title = pg_catalog.btrim(source_title)
    AND app_private.is_nonempty_text(source_title)
    AND source_url = pg_catalog.btrim(source_url)
    AND app_private.is_nonempty_text(source_url)
  ),
  ADD CONSTRAINT offices_optional_text_trimmed_nonempty_chk CHECK (
    (opening_hours IS NULL OR (
      opening_hours = pg_catalog.btrim(opening_hours)
      AND app_private.is_nonempty_text(opening_hours)
    ))
    AND (map_url IS NULL OR (
      map_url = pg_catalog.btrim(map_url)
      AND app_private.is_nonempty_text(map_url)
    ))
  ),
  ADD CONSTRAINT offices_supported_region_chk CHECK (
    region IN ('아름동', '도담동', '조치원읍')
  );

ALTER TABLE app_private.office_service_mappings
  ADD CONSTRAINT office_service_mappings_supported_intent_chk CHECK (
    intent IN (
      'MOVE_IN_RESIDENT_REGISTRATION',
      'CERTIFICATE_ISSUANCE',
      'BULKY_WASTE',
      'LOCAL_TAX_GENERAL'
    )
  ),
  ADD CONSTRAINT office_service_mappings_department_trimmed_nonempty_chk CHECK (
    department_label IS NULL OR (
      department_label = pg_catalog.btrim(department_label)
      AND app_private.is_nonempty_text(department_label)
    )
  );

ALTER TABLE app_private.interaction_events
  ADD CONSTRAINT interaction_events_status_reason_chk CHECK (
    (answer_status = 'FALLBACK') = (fallback_reason IS NOT NULL)
  ),
  ADD CONSTRAINT interaction_events_used_sources_text_array_chk CHECK (
    app_private.is_text_array(used_source_ids)
  ),
  ADD CONSTRAINT interaction_events_used_sources_unique_chk CHECK (
    app_private.is_unique_text_array(used_source_ids)
  ),
  ADD CONSTRAINT interaction_events_source_count_chk CHECK (
    CASE
      WHEN pg_catalog.jsonb_typeof(used_source_ids) = 'array'
        THEN source_count = pg_catalog.jsonb_array_length(used_source_ids)
      ELSE false
    END
  ),
  ADD CONSTRAINT interaction_events_success_has_sources_chk CHECK (
    answer_status <> 'SUCCESS' OR source_count > 0
  ),
  ADD CONSTRAINT interaction_events_selected_region_chk CHECK (
    selected_region IS NULL
    OR selected_region IN ('아름동', '도담동', '조치원읍')
  );

ALTER TABLE app_private.failed_questions
  ADD CONSTRAINT failed_questions_masked_text_trimmed_nonempty_chk CHECK (
    masked_question IS NULL OR (
      masked_question = pg_catalog.btrim(masked_question)
      AND app_private.is_nonempty_text(masked_question)
    )
  ),
  ADD CONSTRAINT failed_questions_supported_intent_chk CHECK (
    intent IN (
      'MOVE_IN_RESIDENT_REGISTRATION',
      'CERTIFICATE_ISSUANCE',
      'BULKY_WASTE',
      'LOCAL_TAX_GENERAL'
    )
  ),
  ADD CONSTRAINT failed_questions_candidate_eligibility_chk CHECK (
    candidate_eligible = (fallback_reason = 'INSUFFICIENT_GROUNDING')
  ),
  ADD CONSTRAINT failed_questions_no_out_of_scope_chk CHECK (
    fallback_reason <> 'OUT_OF_SCOPE'
  ),
  ADD CONSTRAINT failed_questions_exact_expiry_chk CHECK (
    text_expires_at = created_at + interval '30 days'
  ),
  ADD CONSTRAINT failed_questions_text_lifecycle_chk CHECK (
    (masked_question IS NOT NULL AND text_purged_at IS NULL)
    OR (
      masked_question IS NULL
      AND text_purged_at IS NOT NULL
      AND text_purged_at >= text_expires_at
    )
  ),
  ADD CONSTRAINT failed_questions_status_subset_chk CHECK (
    status IN ('NEW', 'REASON_CONFIRMED')
  );

ALTER TABLE app_private.kb_candidates
  ADD CONSTRAINT kb_candidates_required_text_trimmed_nonempty_chk CHECK (
    title = pg_catalog.btrim(title)
    AND app_private.is_nonempty_text(title)
    AND representative_question = pg_catalog.btrim(representative_question)
    AND app_private.is_nonempty_text(representative_question)
    AND answer_summary = pg_catalog.btrim(answer_summary)
    AND app_private.is_nonempty_text(answer_summary)
    AND department = pg_catalog.btrim(department)
    AND app_private.is_nonempty_text(department)
    AND source_title = pg_catalog.btrim(source_title)
    AND app_private.is_nonempty_text(source_title)
    AND source_url = pg_catalog.btrim(source_url)
    AND app_private.is_nonempty_text(source_url)
    AND created_by = pg_catalog.btrim(created_by)
    AND app_private.is_nonempty_text(created_by)
  ),
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
  ADD CONSTRAINT kb_candidates_text_arrays_chk CHECK (
    app_private.is_text_array(procedure_steps)
    AND app_private.is_text_array(required_documents)
  ),
  ADD CONSTRAINT kb_candidates_supported_category_chk CHECK (
    category IN (
      'MOVE_IN_RESIDENT_REGISTRATION',
      'CERTIFICATE_ISSUANCE',
      'BULKY_WASTE',
      'LOCAL_TAX_GENERAL'
    )
  ),
  ADD CONSTRAINT kb_candidates_reviewer_not_author_chk CHECK (
    reviewed_by IS NULL OR reviewed_by <> created_by
  ),
  ADD CONSTRAINT kb_candidates_approved_fields_chk CHECK (
    review_status <> 'APPROVED'
    OR (
      reviewed_by IS NOT NULL
      AND approved_at IS NOT NULL
      AND activated_kb_id IS NOT NULL
    )
  ),
  ADD CONSTRAINT kb_candidates_status_subset_chk CHECK (
    review_status IN ('DRAFTED', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED')
  );

ALTER TABLE app_private.audit_logs
  ADD CONSTRAINT audit_logs_actor_trimmed_nonempty_chk CHECK (
    actor_id = pg_catalog.btrim(actor_id)
    AND app_private.is_nonempty_text(actor_id)
  ),
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
  ADD CONSTRAINT audit_logs_changed_fields_allowlist_chk CHECK (
    app_private.is_allowed_audit_changed_fields(changed_field_names)
  ),
  ADD CONSTRAINT audit_logs_review_comment_trimmed_nonempty_chk CHECK (
    review_comment IS NULL OR (
      review_comment = pg_catalog.btrim(review_comment)
      AND app_private.is_nonempty_text(review_comment)
    )
  );

CREATE FUNCTION app_private.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  NEW.updated_at := pg_catalog.clock_timestamp();
  RETURN NEW;
END
$function$;

CREATE FUNCTION app_private.validate_interaction_event_sources()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_invalid_source boolean;
BEGIN
  IF NEW.answer_status <> 'SUCCESS' THEN
    RETURN NEW;
  END IF;

  IF pg_catalog.jsonb_typeof(NEW.used_source_ids) <> 'array' THEN
    RETURN NEW;
  END IF;

  IF NOT app_private.is_text_array(NEW.used_source_ids) THEN
    RETURN NEW;
  END IF;

  IF NOT app_private.is_unique_text_array(NEW.used_source_ids) THEN
    RETURN NEW;
  END IF;

  SELECT EXISTS (
    SELECT 1
    FROM pg_catalog.jsonb_array_elements_text(NEW.used_source_ids)
      AS source(public_id)
    LEFT JOIN app_private.kb_documents AS kb
      ON kb.public_id = source.public_id
      AND kb.status = 'ACTIVE'
      AND kb.data_origin = 'OFFICIAL'
    WHERE kb.id IS NULL
  )
  INTO v_invalid_source;

  IF v_invalid_source THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'EVENT_SOURCE_NOT_ACTIVE_OFFICIAL';
  END IF;

  RETURN NEW;
END
$function$;

CREATE FUNCTION app_private.validate_failed_question_event()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_answer_status app_private.answer_status;
  v_intent app_private.intent_code;
  v_fallback_reason app_private.fallback_reason;
BEGIN
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

CREATE FUNCTION app_private.validate_interaction_event_failure()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_failure_intent app_private.intent_code;
  v_failure_reason app_private.fallback_reason;
BEGIN
  SELECT failure.intent, failure.fallback_reason
  INTO v_failure_intent, v_failure_reason
  FROM app_private.failed_questions AS failure
  WHERE failure.interaction_event_id = OLD.id
  FOR UPDATE;

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

CREATE FUNCTION app_private.validate_kb_candidate_failure()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_candidate_eligible boolean;
  v_fallback_reason app_private.fallback_reason;
BEGIN
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

CREATE FUNCTION app_private.validate_failed_question_candidate()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_has_candidate boolean;
BEGIN
  SELECT EXISTS (
    SELECT 1
    FROM app_private.kb_candidates AS candidate
    WHERE candidate.failed_question_id = OLD.id
    FOR UPDATE
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

CREATE FUNCTION app_private.lock_kb_question_parents()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_old_parent uuid;
  v_new_parent uuid;
  v_parent_id uuid;
BEGIN
  IF TG_OP = 'INSERT' THEN
    v_new_parent := NEW.kb_document_id;
  ELSIF TG_OP = 'DELETE' THEN
    v_old_parent := OLD.kb_document_id;
  ELSE
    v_old_parent := OLD.kb_document_id;
    v_new_parent := NEW.kb_document_id;
  END IF;

  FOR v_parent_id IN
    SELECT parent.parent_id
    FROM pg_catalog.unnest(ARRAY[v_old_parent, v_new_parent])
      AS parent(parent_id)
    WHERE parent.parent_id IS NOT NULL
    GROUP BY parent.parent_id
    ORDER BY parent.parent_id
  LOOP
    PERFORM 1
    FROM app_private.kb_documents AS kb
    WHERE kb.id = v_parent_id
    FOR UPDATE;
  END LOOP;

  IF TG_OP = 'DELETE' THEN
    RETURN OLD;
  END IF;
  RETURN NEW;
END
$function$;

CREATE FUNCTION app_private.validate_active_kb_question()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_old_parent uuid;
  v_new_parent uuid;
  v_parent_id uuid;
  v_status app_private.kb_status;
  v_parent_exists boolean;
BEGIN
  IF TG_TABLE_NAME = 'kb_documents' THEN
    IF TG_OP = 'INSERT' THEN
      v_new_parent := NEW.id;
    ELSE
      v_old_parent := OLD.id;
      v_new_parent := NEW.id;
    END IF;
  ELSIF TG_OP = 'INSERT' THEN
    v_new_parent := NEW.kb_document_id;
  ELSIF TG_OP = 'DELETE' THEN
    v_old_parent := OLD.kb_document_id;
  ELSE
    v_old_parent := OLD.kb_document_id;
    v_new_parent := NEW.kb_document_id;
  END IF;

  FOR v_parent_id IN
    SELECT parent.parent_id
    FROM pg_catalog.unnest(ARRAY[v_old_parent, v_new_parent])
      AS parent(parent_id)
    WHERE parent.parent_id IS NOT NULL
    GROUP BY parent.parent_id
    ORDER BY parent.parent_id
  LOOP
    SELECT kb.status
    INTO v_status
    FROM app_private.kb_documents AS kb
    WHERE kb.id = v_parent_id
    FOR UPDATE;

    v_parent_exists := FOUND;
    IF v_parent_exists AND v_status = 'ACTIVE' THEN
      IF NOT EXISTS (
        SELECT 1
        FROM app_private.kb_question_examples AS question
        WHERE question.kb_document_id = v_parent_id
      ) THEN
        RAISE EXCEPTION USING
          ERRCODE = 'P0001',
          MESSAGE = 'KB_ACTIVE_QUESTION_REQUIRED';
      END IF;
    END IF;
  END LOOP;

  RETURN NULL;
END
$function$;

CREATE TRIGGER trg_kb_documents_set_updated_at
BEFORE UPDATE ON app_private.kb_documents
FOR EACH ROW EXECUTE FUNCTION app_private.set_updated_at();

CREATE TRIGGER trg_failed_questions_set_updated_at
BEFORE UPDATE ON app_private.failed_questions
FOR EACH ROW EXECUTE FUNCTION app_private.set_updated_at();

CREATE TRIGGER trg_kb_candidates_set_updated_at
BEFORE UPDATE ON app_private.kb_candidates
FOR EACH ROW EXECUTE FUNCTION app_private.set_updated_at();

CREATE TRIGGER trg_interaction_events_validate_sources
BEFORE INSERT OR UPDATE ON app_private.interaction_events
FOR EACH ROW EXECUTE FUNCTION app_private.validate_interaction_event_sources();

CREATE TRIGGER trg_failed_questions_validate_event
BEFORE INSERT OR UPDATE ON app_private.failed_questions
FOR EACH ROW EXECUTE FUNCTION app_private.validate_failed_question_event();

CREATE TRIGGER trg_interaction_events_validate_failure
BEFORE UPDATE ON app_private.interaction_events
FOR EACH ROW EXECUTE FUNCTION app_private.validate_interaction_event_failure();

CREATE TRIGGER trg_kb_candidates_validate_failure
BEFORE INSERT OR UPDATE ON app_private.kb_candidates
FOR EACH ROW EXECUTE FUNCTION app_private.validate_kb_candidate_failure();

CREATE TRIGGER trg_failed_questions_validate_candidate
BEFORE UPDATE ON app_private.failed_questions
FOR EACH ROW EXECUTE FUNCTION app_private.validate_failed_question_candidate();

CREATE TRIGGER trg_kb_question_examples_lock_parents
BEFORE INSERT OR UPDATE OR DELETE ON app_private.kb_question_examples
FOR EACH ROW EXECUTE FUNCTION app_private.lock_kb_question_parents();

CREATE CONSTRAINT TRIGGER ctrg_kb_documents_require_question
AFTER INSERT OR UPDATE ON app_private.kb_documents
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION app_private.validate_active_kb_question();

CREATE CONSTRAINT TRIGGER ctrg_kb_question_examples_require_active_question
AFTER INSERT OR UPDATE OR DELETE ON app_private.kb_question_examples
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION app_private.validate_active_kb_question();

COMMIT;
