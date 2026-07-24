BEGIN;

CREATE FUNCTION app_api.list_failed_questions(
  p_reason text,
  p_status text
)
RETURNS TABLE (
  id uuid,
  masked_question text,
  intent text,
  fallback_reason text,
  candidate_eligible boolean,
  status text,
  created_at timestamptz,
  text_expires_at timestamptz,
  text_purged_at timestamptz
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $list_failed_questions$
BEGIN
  IF (p_reason IS NOT NULL AND p_reason NOT IN (
       'INSUFFICIENT_GROUNDING', 'PERSONAL_LOOKUP', 'LEGAL_JUDGMENT'
     ))
     OR (p_status IS NOT NULL AND p_status NOT IN ('NEW', 'REASON_CONFIRMED')) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'INVALID_ADMIN_READ_FILTER';
  END IF;

  RETURN QUERY
  SELECT
    failures.id,
    failures.masked_question,
    failures.intent::text,
    failures.fallback_reason::text,
    failures.candidate_eligible,
    failures.status::text,
    failures.created_at,
    failures.text_expires_at,
    failures.text_purged_at
  FROM app_private.failed_questions AS failures
  WHERE (p_reason IS NULL OR failures.fallback_reason::text = p_reason)
    AND (p_status IS NULL OR failures.status::text = p_status)
  ORDER BY failures.created_at DESC, failures.id;
END
$list_failed_questions$;

CREATE FUNCTION app_api.get_failed_question(
  p_failed_question_id uuid
)
RETURNS TABLE (
  id uuid,
  masked_question text,
  intent text,
  fallback_reason text,
  candidate_eligible boolean,
  status text,
  created_at timestamptz,
  text_expires_at timestamptz,
  text_purged_at timestamptz
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $get_failed_question$
BEGIN
  IF p_failed_question_id IS NULL THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'INVALID_ADMIN_READ_FILTER';
  END IF;

  RETURN QUERY
  SELECT
    failures.id,
    failures.masked_question,
    failures.intent::text,
    failures.fallback_reason::text,
    failures.candidate_eligible,
    failures.status::text,
    failures.created_at,
    failures.text_expires_at,
    failures.text_purged_at
  FROM app_private.failed_questions AS failures
  WHERE failures.id = p_failed_question_id;
END
$get_failed_question$;

CREATE FUNCTION app_api.list_kb_candidates()
RETURNS TABLE (
  id uuid,
  failed_question_id uuid,
  title text,
  representative_question text,
  data_origin text,
  category text,
  answer_summary text,
  procedure_steps jsonb,
  required_documents jsonb,
  processing_time text,
  fee text,
  department text,
  source_title text,
  source_url text,
  last_verified_at date,
  caution text,
  status text,
  created_by text,
  reviewed_by text,
  review_comment text,
  approved_at timestamptz,
  activated_kb_id uuid,
  created_at timestamptz,
  updated_at timestamptz
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $list_kb_candidates$
  SELECT
    candidates.id,
    candidates.failed_question_id,
    candidates.title,
    candidates.representative_question,
    candidates.data_origin::text,
    candidates.category::text,
    candidates.answer_summary,
    candidates.procedure_steps,
    candidates.required_documents,
    candidates.processing_time,
    candidates.fee,
    candidates.department,
    candidates.source_title,
    candidates.source_url,
    candidates.last_verified_at,
    candidates.caution,
    candidates.review_status::text,
    candidates.created_by,
    candidates.reviewed_by,
    candidates.review_comment,
    candidates.approved_at,
    candidates.activated_kb_id,
    candidates.created_at,
    candidates.updated_at
  FROM app_private.kb_candidates AS candidates
  ORDER BY candidates.created_at DESC, candidates.id
$list_kb_candidates$;

CREATE FUNCTION app_api.get_kb_candidate(
  p_candidate_id uuid
)
RETURNS TABLE (
  id uuid,
  failed_question_id uuid,
  title text,
  representative_question text,
  data_origin text,
  category text,
  answer_summary text,
  procedure_steps jsonb,
  required_documents jsonb,
  processing_time text,
  fee text,
  department text,
  source_title text,
  source_url text,
  last_verified_at date,
  caution text,
  status text,
  created_by text,
  reviewed_by text,
  review_comment text,
  approved_at timestamptz,
  activated_kb_id uuid,
  created_at timestamptz,
  updated_at timestamptz
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $get_kb_candidate$
BEGIN
  IF p_candidate_id IS NULL THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'INVALID_ADMIN_READ_FILTER';
  END IF;

  RETURN QUERY
  SELECT
    candidates.id,
    candidates.failed_question_id,
    candidates.title,
    candidates.representative_question,
    candidates.data_origin::text,
    candidates.category::text,
    candidates.answer_summary,
    candidates.procedure_steps,
    candidates.required_documents,
    candidates.processing_time,
    candidates.fee,
    candidates.department,
    candidates.source_title,
    candidates.source_url,
    candidates.last_verified_at,
    candidates.caution,
    candidates.review_status::text,
    candidates.created_by,
    candidates.reviewed_by,
    candidates.review_comment,
    candidates.approved_at,
    candidates.activated_kb_id,
    candidates.created_at,
    candidates.updated_at
  FROM app_private.kb_candidates AS candidates
  WHERE candidates.id = p_candidate_id;
END
$get_kb_candidate$;

ALTER FUNCTION app_api.list_failed_questions(text, text)
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_api.get_failed_question(uuid)
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_api.list_kb_candidates()
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_api.get_kb_candidate(uuid)
  OWNER TO sejong_schema_owner;

REVOKE ALL ON FUNCTION app_api.list_failed_questions(text, text)
  FROM PUBLIC, anon, authenticated, sejong_backend;
REVOKE ALL ON FUNCTION app_api.get_failed_question(uuid)
  FROM PUBLIC, anon, authenticated, sejong_backend;
REVOKE ALL ON FUNCTION app_api.list_kb_candidates()
  FROM PUBLIC, anon, authenticated, sejong_backend;
REVOKE ALL ON FUNCTION app_api.get_kb_candidate(uuid)
  FROM PUBLIC, anon, authenticated, sejong_backend;

GRANT EXECUTE ON FUNCTION app_api.list_failed_questions(text, text)
  TO sejong_backend;
GRANT EXECUTE ON FUNCTION app_api.get_failed_question(uuid)
  TO sejong_backend;
GRANT EXECUTE ON FUNCTION app_api.list_kb_candidates()
  TO sejong_backend;
GRANT EXECUTE ON FUNCTION app_api.get_kb_candidate(uuid)
  TO sejong_backend;

COMMIT;
