BEGIN;

CREATE INDEX idx_kb_active_official_category
  ON app_private.kb_documents (category)
  WHERE status = 'ACTIVE' AND data_origin = 'OFFICIAL';

CREATE INDEX idx_events_occurred
  ON app_private.interaction_events (occurred_at DESC);

CREATE INDEX idx_failures_status
  ON app_private.failed_questions (status, fallback_reason);

CREATE INDEX idx_failure_text_expiry
  ON app_private.failed_questions (text_expires_at)
  WHERE masked_question IS NOT NULL;

CREATE INDEX idx_candidates_status
  ON app_private.kb_candidates (review_status);

CREATE FUNCTION app_api.list_active_kb(p_intent text)
RETURNS TABLE (
  public_id text,
  category text,
  service_name text,
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
  question_examples jsonb
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog
AS $list_active_kb$
BEGIN
  IF p_intent IS NULL
     OR p_intent NOT IN (
       'MOVE_IN_RESIDENT_REGISTRATION',
       'CERTIFICATE_ISSUANCE',
       'BULKY_WASTE',
       'LOCAL_TAX_GENERAL'
     ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'INVALID_READ_FILTER';
  END IF;

  RETURN QUERY
  SELECT
    kb.public_id,
    kb.category::text,
    kb.service_name,
    kb.answer_summary,
    kb.procedure_steps,
    kb.required_documents,
    kb.processing_time,
    kb.fee,
    kb.department,
    kb.source_title,
    kb.source_url,
    kb.last_verified_at,
    kb.caution,
    COALESCE(
      (
        SELECT pg_catalog.jsonb_agg(
          questions.question_example
          ORDER BY questions.question_example COLLATE pg_catalog."C"
        )
        FROM app_private.kb_question_examples AS questions
        WHERE questions.kb_document_id = kb.id
      ),
      '[]'::jsonb
    )
  FROM app_private.kb_documents AS kb
  WHERE kb.category = p_intent::app_private.intent_code
    AND kb.status = 'ACTIVE'
    AND kb.data_origin = 'OFFICIAL'
  ORDER BY kb.public_id COLLATE pg_catalog."C" ASC;
END;
$list_active_kb$;

CREATE FUNCTION app_api.list_offices(p_region text, p_intent text)
RETURNS TABLE (
  public_id text,
  region text,
  office_name text,
  address text,
  phone text,
  opening_hours text,
  map_url text,
  department_label text,
  source_title text,
  source_url text,
  last_verified_at date
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog
AS $list_offices$
BEGIN
  IF p_region IS NULL
     OR p_region NOT IN ('아름동', '도담동', '조치원읍')
     OR p_intent IS NULL
     OR p_intent NOT IN (
       'MOVE_IN_RESIDENT_REGISTRATION',
       'CERTIFICATE_ISSUANCE',
       'BULKY_WASTE',
       'LOCAL_TAX_GENERAL'
     ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P1010', MESSAGE = 'INVALID_READ_FILTER';
  END IF;

  RETURN QUERY
  SELECT
    offices.public_id,
    offices.region,
    offices.office_name,
    offices.address,
    offices.phone,
    offices.opening_hours,
    offices.map_url,
    mappings.department_label,
    offices.source_title,
    offices.source_url,
    offices.last_verified_at
  FROM app_private.office_service_mappings AS mappings
  JOIN app_private.offices AS offices
    ON offices.id = mappings.office_id
  WHERE offices.region = p_region
    AND mappings.intent = p_intent::app_private.intent_code
    AND offices.data_origin = 'OFFICIAL'
  ORDER BY offices.public_id COLLATE pg_catalog."C" ASC;
END;
$list_offices$;

ALTER FUNCTION app_api.list_active_kb(text)
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_api.list_offices(text, text)
  OWNER TO sejong_schema_owner;

REVOKE ALL ON FUNCTION app_api.list_active_kb(text)
  FROM PUBLIC, anon, authenticated, sejong_backend;
REVOKE ALL ON FUNCTION app_api.list_offices(text, text)
  FROM PUBLIC, anon, authenticated, sejong_backend;

GRANT EXECUTE ON FUNCTION app_api.list_active_kb(text)
  TO sejong_backend;
GRANT EXECUTE ON FUNCTION app_api.list_offices(text, text)
  TO sejong_backend;

COMMIT;
