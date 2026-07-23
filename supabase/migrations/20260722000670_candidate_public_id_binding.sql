BEGIN;

CREATE FUNCTION app_api.approve_kb_candidate_with_public_id(
  p_candidate_id uuid,
  p_actor_id text,
  p_actor_role text,
  p_review_comment text,
  p_public_id text
)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $approve_candidate_with_public_id$
DECLARE
  v_candidate app_private.kb_candidates%ROWTYPE;
  v_generated_public_id text;
  v_updated_count integer;
BEGIN
  BEGIN
    IF p_public_id IS DISTINCT FROM 'KB-WASTE-03' THEN
      RAISE EXCEPTION USING
        ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
    END IF;

    SELECT candidates.* INTO v_candidate
    FROM app_private.kb_candidates AS candidates
    WHERE candidates.id = p_candidate_id
    FOR UPDATE;

    IF NOT FOUND
       OR v_candidate.review_status <> 'PENDING_APPROVAL'
       OR v_candidate.title IS DISTINCT FROM '침대 프레임 배출 수수료'
       OR v_candidate.representative_question IS DISTINCT FROM
         '침대 2인용 프레임 수수료가 얼마예요?'
       OR v_candidate.data_origin <> 'OFFICIAL'
       OR v_candidate.category <> 'BULKY_WASTE'
       OR v_candidate.answer_summary IS DISTINCT FROM
         '공식 품목표의 침대 프레임 수수료는 1인용침대 8,000원, 2인용침대 10,000원으로 표시됩니다.'
       OR v_candidate.procedure_steps IS DISTINCT FROM
         '["공식 품목표에서 침대 프레임의 1인용침대 또는 2인용침대 항목을 확인합니다.","해당 수수료로 공식 배출 절차를 진행합니다."]'::jsonb
       OR v_candidate.required_documents IS DISTINCT FROM '[]'::jsonb
       OR v_candidate.processing_time IS NOT NULL
       OR v_candidate.fee IS DISTINCT FROM
         '1인용침대 8,000원; 2인용침대 10,000원'
       OR v_candidate.department IS DISTINCT FROM '세종특별자치시시설관리공단'
       OR v_candidate.source_title IS DISTINCT FROM '배출항목선택'
       OR v_candidate.source_url IS DISTINCT FROM
         'https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305'
       OR v_candidate.last_verified_at IS DISTINCT FROM DATE '2026-07-18'
       OR v_candidate.caution IS DISTINCT FROM
         '공식 품목표의 1인용침대·2인용침대 항목을 그대로 따릅니다. 매트리스 포함 가격이나 실제 규격을 단정하지 않습니다.' THEN
      RAISE EXCEPTION USING
        ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
    END IF;

    v_generated_public_id := app_api.approve_kb_candidate(
      p_candidate_id, p_actor_id, p_actor_role, p_review_comment
    );

    UPDATE app_private.kb_documents AS documents
    SET public_id = p_public_id
    FROM app_private.kb_candidates AS candidates
    WHERE candidates.id = p_candidate_id
      AND documents.id = candidates.activated_kb_id
      AND documents.public_id = v_generated_public_id;

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    IF v_updated_count <> 1 THEN
      RAISE EXCEPTION USING
        ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
    END IF;

    RETURN p_public_id;
  EXCEPTION
    WHEN OTHERS THEN
      RAISE EXCEPTION USING
        ERRCODE = 'P1003', MESSAGE = 'INVALID_WORKFLOW_STATE';
  END;
END
$approve_candidate_with_public_id$;

ALTER FUNCTION app_api.approve_kb_candidate_with_public_id(uuid, text, text, text, text)
  OWNER TO sejong_schema_owner;

REVOKE ALL ON FUNCTION app_api.approve_kb_candidate_with_public_id(uuid, text, text, text, text)
  FROM PUBLIC, anon, authenticated, sejong_backend;
GRANT EXECUTE ON FUNCTION app_api.approve_kb_candidate_with_public_id(uuid, text, text, text, text)
  TO sejong_backend;

COMMIT;
