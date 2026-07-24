BEGIN;

DROP TRIGGER IF EXISTS ctrg_kb_question_examples_require_active_question
  ON app_private.kb_question_examples;
DROP TRIGGER IF EXISTS ctrg_kb_documents_require_question
  ON app_private.kb_documents;

DROP TRIGGER IF EXISTS trg_kb_question_examples_lock_parents
  ON app_private.kb_question_examples;
DROP TRIGGER IF EXISTS trg_failed_questions_validate_candidate
  ON app_private.failed_questions;
DROP TRIGGER IF EXISTS trg_kb_candidates_validate_failure
  ON app_private.kb_candidates;
DROP TRIGGER IF EXISTS trg_interaction_events_validate_failure
  ON app_private.interaction_events;
DROP TRIGGER IF EXISTS trg_failed_questions_validate_event
  ON app_private.failed_questions;
DROP TRIGGER IF EXISTS trg_interaction_events_validate_sources
  ON app_private.interaction_events;
DROP TRIGGER IF EXISTS trg_kb_candidates_set_updated_at
  ON app_private.kb_candidates;
DROP TRIGGER IF EXISTS trg_failed_questions_set_updated_at
  ON app_private.failed_questions;
DROP TRIGGER IF EXISTS trg_kb_documents_set_updated_at
  ON app_private.kb_documents;

DROP FUNCTION IF EXISTS app_private.validate_active_kb_question();
DROP FUNCTION IF EXISTS app_private.lock_kb_question_parents();
DROP FUNCTION IF EXISTS app_private.validate_failed_question_candidate();
DROP FUNCTION IF EXISTS app_private.validate_kb_candidate_failure();
DROP FUNCTION IF EXISTS app_private.validate_interaction_event_failure();
DROP FUNCTION IF EXISTS app_private.validate_failed_question_event();
DROP FUNCTION IF EXISTS app_private.validate_interaction_event_sources();
DROP FUNCTION IF EXISTS app_private.set_updated_at();

ALTER TABLE app_private.audit_logs
  DROP CONSTRAINT IF EXISTS audit_logs_review_comment_trimmed_nonempty_chk,
  DROP CONSTRAINT IF EXISTS audit_logs_changed_fields_allowlist_chk,
  DROP CONSTRAINT IF EXISTS audit_logs_status_values_chk,
  DROP CONSTRAINT IF EXISTS audit_logs_target_type_chk,
  DROP CONSTRAINT IF EXISTS audit_logs_action_allowlist_chk,
  DROP CONSTRAINT IF EXISTS audit_logs_actor_trimmed_nonempty_chk;

ALTER TABLE app_private.kb_candidates
  DROP CONSTRAINT IF EXISTS kb_candidates_status_subset_chk,
  DROP CONSTRAINT IF EXISTS kb_candidates_approved_fields_chk,
  DROP CONSTRAINT IF EXISTS kb_candidates_reviewer_not_author_chk,
  DROP CONSTRAINT IF EXISTS kb_candidates_supported_category_chk,
  DROP CONSTRAINT IF EXISTS kb_candidates_text_arrays_chk,
  DROP CONSTRAINT IF EXISTS kb_candidates_optional_text_trimmed_nonempty_chk,
  DROP CONSTRAINT IF EXISTS kb_candidates_required_text_trimmed_nonempty_chk;

ALTER TABLE app_private.failed_questions
  DROP CONSTRAINT IF EXISTS failed_questions_status_subset_chk,
  DROP CONSTRAINT IF EXISTS failed_questions_text_lifecycle_chk,
  DROP CONSTRAINT IF EXISTS failed_questions_exact_expiry_chk,
  DROP CONSTRAINT IF EXISTS failed_questions_no_out_of_scope_chk,
  DROP CONSTRAINT IF EXISTS failed_questions_candidate_eligibility_chk,
  DROP CONSTRAINT IF EXISTS failed_questions_supported_intent_chk,
  DROP CONSTRAINT IF EXISTS failed_questions_masked_text_trimmed_nonempty_chk;

ALTER TABLE app_private.interaction_events
  DROP CONSTRAINT IF EXISTS interaction_events_selected_region_chk,
  DROP CONSTRAINT IF EXISTS interaction_events_success_has_sources_chk,
  DROP CONSTRAINT IF EXISTS interaction_events_source_count_chk,
  DROP CONSTRAINT IF EXISTS interaction_events_used_sources_unique_chk,
  DROP CONSTRAINT IF EXISTS interaction_events_used_sources_text_array_chk,
  DROP CONSTRAINT IF EXISTS interaction_events_status_reason_chk;

ALTER TABLE app_private.office_service_mappings
  DROP CONSTRAINT IF EXISTS office_service_mappings_department_trimmed_nonempty_chk,
  DROP CONSTRAINT IF EXISTS office_service_mappings_supported_intent_chk;

ALTER TABLE app_private.offices
  DROP CONSTRAINT IF EXISTS offices_supported_region_chk,
  DROP CONSTRAINT IF EXISTS offices_optional_text_trimmed_nonempty_chk,
  DROP CONSTRAINT IF EXISTS offices_required_text_trimmed_nonempty_chk,
  DROP CONSTRAINT IF EXISTS offices_public_id_trimmed_nonempty_chk;

ALTER TABLE app_private.kb_question_examples
  DROP CONSTRAINT IF EXISTS kb_question_examples_normalized_trimmed_nonempty_chk,
  DROP CONSTRAINT IF EXISTS kb_question_examples_question_trimmed_nonempty_chk;

ALTER TABLE app_private.kb_documents
  DROP CONSTRAINT IF EXISTS kb_documents_approver_not_author_chk,
  DROP CONSTRAINT IF EXISTS kb_documents_active_official_approval_chk,
  DROP CONSTRAINT IF EXISTS kb_documents_supported_category_chk,
  DROP CONSTRAINT IF EXISTS kb_documents_text_arrays_chk,
  DROP CONSTRAINT IF EXISTS kb_documents_optional_text_trimmed_nonempty_chk,
  DROP CONSTRAINT IF EXISTS kb_documents_required_text_trimmed_nonempty_chk,
  DROP CONSTRAINT IF EXISTS kb_documents_public_id_trimmed_nonempty_chk;

DROP FUNCTION IF EXISTS app_private.is_allowed_audit_changed_fields(jsonb);
DROP FUNCTION IF EXISTS app_private.is_unique_text_array(jsonb);
DROP FUNCTION IF EXISTS app_private.is_text_array(jsonb);
DROP FUNCTION IF EXISTS app_private.is_nonempty_text(text);

COMMIT;
