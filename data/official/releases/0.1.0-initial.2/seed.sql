BEGIN;
SET LOCAL standard_conforming_strings = on;
SET LOCAL lock_timeout = '5s';
SELECT pg_catalog.pg_advisory_xact_lock(20260719001);

DO $data_seed_assert_principal$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_catalog.pg_auth_members AS memberships
    JOIN pg_catalog.pg_roles AS granted_role
      ON granted_role.oid = memberships.roleid
    JOIN pg_catalog.pg_roles AS member_role
      ON member_role.oid = memberships.member
    WHERE granted_role.rolname = 'sejong_schema_owner'
      AND member_role.rolname = 'postgres'
      AND memberships.admin_option
  )
  OR NOT EXISTS (
    SELECT 1
    FROM pg_catalog.pg_auth_members AS memberships
    JOIN pg_catalog.pg_roles AS granted_role
      ON granted_role.oid = memberships.roleid
    JOIN pg_catalog.pg_roles AS member_role
      ON member_role.oid = memberships.member
    WHERE granted_role.rolname = 'sejong_schema_owner'
      AND member_role.rolname = 'postgres'
      AND memberships.inherit_option
  )
  OR NOT EXISTS (
    SELECT 1
    FROM pg_catalog.pg_auth_members AS memberships
    JOIN pg_catalog.pg_roles AS granted_role
      ON granted_role.oid = memberships.roleid
    JOIN pg_catalog.pg_roles AS member_role
      ON member_role.oid = memberships.member
    WHERE granted_role.rolname = 'sejong_schema_owner'
      AND member_role.rolname = 'postgres'
      AND memberships.set_option
  ) THEN
    RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'DATA_SEED_MEMBERSHIP_INVALID';
  END IF;
END;
$data_seed_assert_principal$;

SET LOCAL ROLE sejong_schema_owner;

DO $data_seed_assert_role_switch$
BEGIN
  IF NOT (
    session_user = 'postgres'
    AND current_user = 'sejong_schema_owner'
    AND current_database() = 'postgres'
  ) THEN
    RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'DATA_SEED_ROLE_SWITCH_INVALID';
  END IF;
END;
$data_seed_assert_role_switch$;

LOCK TABLE app_private.kb_documents IN ACCESS EXCLUSIVE MODE;
LOCK TABLE app_private.kb_question_examples IN ACCESS EXCLUSIVE MODE;
LOCK TABLE app_private.offices IN ACCESS EXCLUSIVE MODE;
LOCK TABLE app_private.office_service_mappings IN ACCESS EXCLUSIVE MODE;
LOCK TABLE app_private.interaction_events IN ACCESS EXCLUSIVE MODE;
LOCK TABLE app_private.failed_questions IN ACCESS EXCLUSIVE MODE;
LOCK TABLE app_private.kb_candidates IN ACCESS EXCLUSIVE MODE;
LOCK TABLE app_private.audit_logs IN ACCESS EXCLUSIVE MODE;

DO $data_seed_empty_guard$
BEGIN
  IF EXISTS (SELECT 1 FROM app_private.kb_documents)
     OR EXISTS (SELECT 1 FROM app_private.kb_question_examples)
     OR EXISTS (SELECT 1 FROM app_private.offices)
     OR EXISTS (SELECT 1 FROM app_private.office_service_mappings)
     OR EXISTS (SELECT 1 FROM app_private.interaction_events)
     OR EXISTS (SELECT 1 FROM app_private.failed_questions)
     OR EXISTS (SELECT 1 FROM app_private.kb_candidates)
     OR EXISTS (SELECT 1 FROM app_private.audit_logs) THEN
    RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'DATA_SEED_DATABASE_NOT_EMPTY';
  END IF;
END;
$data_seed_empty_guard$;

INSERT INTO app_private.kb_documents (public_id, data_origin, category, service_name, answer_summary, procedure_steps, required_documents, processing_time, fee, department, source_title, source_url, last_verified_at, caution, status, created_by, approved_by, approved_at)
VALUES
    ('KB-CERT-01'::text, 'OFFICIAL'::app_private.data_origin, 'CERTIFICATE_ISSUANCE'::app_private.intent_code, '등본과 초본의 차이'::text, '등본은 한 세대의 모든 구성원에 대한 주민등록 사항을, 초본은 한 사람의 자세한 주민등록 사항을 표시합니다.'::text, '["제출처가 요구하는 문서 종류와 표시 항목을 확인합니다.","정부24의 주민등록표 등본(초본) 발급 안내에서 신청 경로를 확인합니다."]'::jsonb, '["제출처가 요구하는 문서 종류와 표시 항목 확인"]'::jsonb, NULL::text, NULL::text, '행정안전부 주민과'::text, '주민등록표 등본(초본) 발급'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000015&typeSn=01'::text, '2026-07-18'::date, '제출처별 요구 문서와 표시 항목은 다를 수 있습니다. 용도별 상세 표시 항목을 이 안내가 단정하지 않으므로 제출처와 공식 신청 화면을 확인합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-CERT-02'::text, 'OFFICIAL'::app_private.data_origin, 'CERTIFICATE_ISSUANCE'::app_private.intent_code, '주민등록등본 발급 방법'::text, '주민등록등본은 인터넷, 방문, 무인발급기로 신청할 수 있습니다. 공식 안내상 인터넷 발급은 무료이고, 발급 수수료와 서류는 신청 방법과 신청자 유형에 따라 확인해야 합니다.'::text, '["정부24에서 주민등록표 등본(초본) 발급 민원을 확인합니다.","인터넷·방문·무인발급기 중 가능한 방법을 선택합니다.","방문 또는 대리 신청이면 신청자 유형별 공식 제출서류를 확인합니다."]'::jsonb, '["본인 방문: 유효한 신분증","대리 신청 등 상황별: 정부24 제출서류 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '1통 400원, 이해관계인 교부 500원, 인터넷 발급 무료'::text, '읍·면·동/출장소(접수·처리); 행정안전부 주민과'::text, '주민등록표 등본(초본) 발급'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000015&typeSn=01'::text, '2026-07-18'::date, '무인발급기의 실제 운영시간·수수료·발급 가능 여부는 기기와 자치단체별로 다를 수 있습니다. 온라인 대리 신청은 불가하며, 개인별 발급 가능 여부는 공식 신청 화면 또는 처리기관에서 확인합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-CERT-03'::text, 'OFFICIAL'::app_private.data_origin, 'CERTIFICATE_ISSUANCE'::app_private.intent_code, '주민등록초본 발급 방법'::text, '주민등록초본은 인터넷, 방문, 무인발급기로 신청할 수 있습니다. 신청자 본인의 초본과 같은 세대 구성원의 초본이 기본 발급 범위에 포함되며, 신청 방법과 신청자 유형에 따라 조건이 달라집니다.'::text, '["정부24에서 주민등록표 등본(초본) 발급 민원을 확인합니다.","본인은 가능한 신청 방법을 선택합니다.","대리인 또는 정당한 권리가 있는 사람의 신청은 공식 안내의 신청 방법과 서류를 확인합니다."]'::jsonb, '["본인 방문: 유효한 신분증","대리·이해관계인 등 상황별: 정부24 제출서류 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '1통 400원, 이해관계인 교부 500원, 인터넷 발급 무료'::text, '읍·면·동/출장소(접수·처리); 행정안전부 주민과'::text, '주민등록표 등본(초본) 발급'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000015&typeSn=01'::text, '2026-07-18'::date, '온라인 대리 신청은 불가합니다. 초본의 상세 표시 항목, 외국인 신청 범위 및 개인별 적용은 이 안내가 단정하지 않으므로 제출처와 관할 처리기관의 공식 안내를 확인합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-CERT-04'::text, 'OFFICIAL'::app_private.data_origin, 'CERTIFICATE_ISSUANCE'::app_private.intent_code, '주민등록표 열람'::text, '주민등록표 열람은 인터넷 또는 방문으로 신청할 수 있는 민원이며, 증명서 발급과는 구분됩니다. 공식 안내상 인터넷 열람은 무료이고 방문 열람 수수료는 1건 1회 300원입니다.'::text, '["정부24에서 주민등록표 열람 민원을 확인합니다.","본인 또는 대리인 해당 여부에 맞는 신청 방법을 확인합니다.","온라인 또는 방문 경로를 선택합니다."]'::jsonb, '["본인·대리인·정당한 이해관계인 여부에 따른 공식 제출서류 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '1건 1회 300원, 인터넷 열람 무료'::text, '시·군·구 및 읍·면·동 출장소(접수·처리); 행정안전부 주민과'::text, '주민등록표 열람'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000014&typeSn=01'::text, '2026-07-18'::date, '열람은 증명서 발급과 다른 민원입니다. 온라인 대리 신청은 불가하며, 개인별 열람 가능 여부와 수령·확인 방법은 공식 신청 화면 또는 처리기관에서 확인합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-CERT-05'::text, 'OFFICIAL'::app_private.data_origin, 'CERTIFICATE_ISSUANCE'::app_private.intent_code, '무인민원발급기 이용 안내'::text, '정부24 무인민원발급안내에서 시도·시군구·읍면동과 발급 가능 민원 조건으로 설치 장소를 확인할 수 있습니다.'::text, '["정부24 무인민원발급안내에서 설치 장소를 검색합니다.","필요한 민원의 발급 가능 여부를 선택한 설치 장소에서 확인합니다.","이용 전 운영시간과 수수료를 다시 확인합니다."]'::jsonb, '["발급 민원별 본인확인 및 공식 안내 확인"]'::jsonb, NULL::text, NULL::text, '정부24(행정안전부)'::text, '무인민원발급안내'::text, 'https://plus.gov.kr/portal/custcntr/utztngd/unmncvlcptissugd/'::text, '2026-07-18'::date, '표준 안내의 운영시간·수수료를 모든 기기에 동일하게 적용하지 않습니다. 실제 발급 종류·발급 가능 시간·수수료는 설치 장소와 자치단체 운영 상황에 따라 다를 수 있습니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-MOVE-01'::text, 'OFFICIAL'::app_private.data_origin, 'MOVE_IN_RESIDENT_REGISTRATION'::app_private.intent_code, '전입신고 개요·신청방법'::text, '전입신고는 인터넷 또는 방문으로 신청할 수 있습니다. 본인 또는 대리인이 신청할 수 있으나 온라인 대리 신청은 불가하며, 공식 안내상 수수료는 없습니다.'::text, '["정부24 전입신고 안내에서 본인에게 맞는 신청 방법을 확인합니다.","인터넷 또는 관할 읍·면·동·출장소 방문 중 가능한 방법을 선택합니다.","상황별 제출서류와 접수 가능 여부를 확인합니다."]'::jsonb, '["상황별 공식 구비서류 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '수수료 없음'::text, '읍·면·동/출장소(접수·처리); 행정안전부 주민과'::text, '전입신고'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000016&typeSn=01'::text, '2026-07-18'::date, '세대 구성과 신고자 관계에 따라 예외와 추가 서류가 있을 수 있습니다. 실제 접수 가능 여부는 관할 읍·면·동의 공식 안내로 확인합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-MOVE-02'::text, 'OFFICIAL'::app_private.data_origin, 'MOVE_IN_RESIDENT_REGISTRATION'::app_private.intent_code, '방문 전입신고 준비물'::text, '방문 전입신고는 본인·대리 여부와 세대 관계에 따라 준비물이 달라집니다. 본인 신고에는 유효한 신분증과 행정정보 공동이용 사전동의서가 안내되며, 대리 신고에는 위임 관련 서류와 신분증을 확인해야 합니다.'::text, '["본인 신고인지 대리 신고인지 확인합니다.","정부24 전입신고 안내에서 해당 유형의 구비서류를 확인합니다.","관할 읍·면·동 또는 출장소 방문 전 추가 서류 필요 여부를 확인합니다."]'::jsonb, '["본인 신고: 유효한 신분증, 행정정보 공동이용 사전동의서","대리 신고: 위임한 사람과 위임받은 사람의 신분증, 위임장, 행정정보 공동이용 사전동의서","조건부 서류: 건축물대장·재외국민 관련서류·출입국사실증명·가족관계증명서 등 공식 안내 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '수수료 없음'::text, '읍·면·동/출장소(접수·처리); 행정안전부 주민과'::text, '전입신고'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000016&typeSn=01'::text, '2026-07-18'::date, '신분증만으로 항상 접수되는 것은 아닙니다. 가족관계·위임·국적 또는 체류 상태와 동의 여부에 따라 준비물이 달라지므로 관할 처리기관의 공식 안내를 확인합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-MOVE-03'::text, 'OFFICIAL'::app_private.data_origin, 'MOVE_IN_RESIDENT_REGISTRATION'::app_private.intent_code, '온라인 전입신고'::text, '전입신고는 인터넷으로 본인이 신청할 수 있으나 온라인 대리 신청은 불가합니다. 재외국민과 해외체류자 등은 공식 안내에서 방문 신청 경계를 확인해야 합니다.'::text, '["정부24 전입신고에서 본인 신청 가능 여부를 확인합니다.","온라인 신청이 가능한 경우 본인으로 신청합니다.","방문 신청 대상이면 새 거주지 관할 주민센터의 공식 안내를 확인합니다."]'::jsonb, '["온라인 신청 가능 여부와 조건별 공식 안내 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '수수료 없음'::text, '읍·면·동/출장소(접수·처리); 행정안전부 주민과'::text, '전입신고'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000016&typeSn=01'::text, '2026-07-18'::date, '특정 인증수단은 이 출처로 확정하지 않습니다. 재외국민은 재외국민 여부 확인을 위해, 해외체류자는 입국 사실 확인을 위해 방문 신청 대상이 될 수 있으므로 개인별 적용은 관할기관에서 확인합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-MOVE-04'::text, 'OFFICIAL'::app_private.data_origin, 'MOVE_IN_RESIDENT_REGISTRATION'::app_private.intent_code, '주민등록 관련 통보서비스'::text, '주민등록 관련 통보서비스는 전입신고, 세대주 변경, 주민등록증, 주민등록표, 자신의 주소변경사실에 관한 통보를 안내합니다. 인터넷 또는 방문으로 신청할 수 있으며 온라인 대리 신청은 불가합니다.'::text, '["필요한 통보 종류가 공식 통보 범위에 있는지 확인합니다.","정부24에서 인터넷 또는 방문 신청 방법을 확인합니다.","대리 또는 자격 확인이 필요한 경우 공식 제출서류를 확인합니다."]'::jsonb, '["방문 신청: 신청인 신분확인증","전입신고·세대주변경 통보 등 자격별: 공식 자격 확인 자료"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '수수료 없음'::text, '읍·면·동/출장소(접수·처리); 행정안전부 주민과'::text, '주민등록 관련 통보서비스 (전입신고, 세대주변경, 주민등록증, 주민등록표, 주소변경사실)'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13110000039&typeSn=01'::text, '2026-07-18'::date, '이 서비스는 전입신고 자체와 다릅니다. 통보 대상과 신청 자격은 유형별로 다를 수 있으며, 온라인 대리 신청은 불가합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-MOVE-05'::text, 'OFFICIAL'::app_private.data_origin, 'MOVE_IN_RESIDENT_REGISTRATION'::app_private.intent_code, '주민등록법상 신고 일반 원칙·주의사항'::text, '세대 전원 또는 일부가 거주지를 이동한 경우, 신고의무자는 새 거주지에 전입한 날부터 14일 이내에 전입신고하는 일반 원칙이 안내됩니다.'::text, '["전입한 날과 새 거주지 관할기관을 확인합니다.","정부24 전입신고 안내 또는 관할기관의 공식 경로를 확인합니다.","개인 사정이 있는 경우 관할기관에 적용 여부를 확인합니다."]'::jsonb, '["상황별 전입신고 공식 구비서류 확인"]'::jsonb, NULL::text, NULL::text, '관할 읍·면·동; 국가법령정보센터'::text, '주민등록법'::text, 'https://www.law.go.kr/LSW/lsInfoP.do?lsId=001655&urlMode=lsInfoP'::text, '2026-07-18'::date, '이 항목은 일반 원칙만 안내합니다. 위반 여부, 과태료 금액·부과 여부와 개인 사실관계의 법률 적용은 이 서비스가 판단하지 않으므로 관할기관 확인 또는 LEGAL_JUDGMENT 폴백이 필요합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-TAX-01'::text, 'OFFICIAL'::app_private.data_origin, 'LOCAL_TAX_GENERAL'::app_private.intent_code, '지방세 온라인 납부 공식 경로 안내'::text, '지방세의 온라인 조회·납부가 필요하면 위택스 공식 누리집에서 확인할 수 있습니다. 고지서에 전자납부번호가 있으면 위택스의 빠른납부 경로를 확인할 수 있습니다.'::text, '["위택스에 접속합니다.","개인 고지·납부 대상 확인이 필요하면 본인에게 맞는 공식 로그인·인증 경로를 이용합니다.","전자납부번호가 있으면 빠른납부 안내를 확인합니다."]'::jsonb, '[]'::jsonb, NULL::text, NULL::text, '위택스(온라인 경로); 개별 세목 문의는 관할 지방세 담당기관 확인'::text, '위택스'::text, 'https://www.wetax.go.kr/main.do'::text, '2026-07-18'::date, '개인별 납부대상·세액·체납·납부완료 여부는 이 서비스가 조회하지 않습니다. 본인 인증 후 공식 시스템 또는 관할기관에서 직접 확인해야 합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-TAX-02'::text, 'OFFICIAL'::app_private.data_origin, 'LOCAL_TAX_GENERAL'::app_private.intent_code, '자동차세 개인 고지 확인·납부의 공식 로그인 경로'::text, '개인 자동차세 고지·납부 대상은 위택스에서 본인 인증 후 확인하도록 안내합니다. 이 서비스는 자동차세 금액이나 납부 상태를 조회하지 않습니다.'::text, '["위택스에 접속합니다.","공식 로그인 화면에서 본인에게 맞는 인증 방법을 선택합니다.","로그인 후 본인 고지 내역과 이용 가능한 납부 경로를 직접 확인합니다."]'::jsonb, '[]'::jsonb, NULL::text, NULL::text, '위택스(개인 고지 확인·납부 경로); 세목별 개별 문의는 관할 지방세 담당기관 확인'::text, '위택스 로그인(자동차세 개인 고지 확인 경계)'::text, 'https://www.wetax.go.kr/login.do'::text, '2026-07-18'::date, '로그인 후 노출되는 고지·차량·세액은 개인별로 다릅니다. 납기, 연세액 납부 가능 여부·혜택, 감면, 체납 여부 및 개별 부과액은 이 로그인 출처 범위 밖이며, 최신 자동차세 전용 공식 출처와 본인 화면 확인 없이는 안내하지 않습니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-TAX-03'::text, 'OFFICIAL'::app_private.data_origin, 'LOCAL_TAX_GENERAL'::app_private.intent_code, '지방세 납세증명서 발급 안내'::text, '지방세 납세증명서는 인터넷·방문·FAX·우편·무인발급기로 신청할 수 있으며, 온라인 대리 신청은 불가합니다. 공식 안내상 수수료는 없고 처리기간은 즉시(근무시간 내 3시간)입니다.'::text, '["정부24의 해당 민원에서 본인 신청 경로를 확인합니다.","대리 신청 또는 방문이 필요하면 신청자 유형별 제출서류와 접수·처리기관을 공식 페이지에서 확인합니다.","가능한 신청 방법을 선택합니다."]'::jsonb, '["상황별 상이: 본인·대리인·법인·상속·법정대리인 여부에 따른 정부24 제출서류 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '수수료 없음'::text, '시·군·구, 읍·면·동, 출장소(접수·처리); 행정안전부 지방세정책과'::text, '정부24 지방세 납세증명서 발급'::text, 'https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13100000056&tp_seq=01'::text, '2026-07-18'::date, '이 증명은 발급일 현재 법령상 예외 금액을 제외한 다른 체납액이 없음을 증명하는 민원입니다. 이를 개인의 모든 체납이 전혀 없다는 단정으로 바꾸지 않으며, 실제 발급 가능 여부와 개인 결과는 본인 또는 관할 처리기관이 확인합니다. PM은 정확한 plus.gov.kr deep-link와 최신 표시 내용을 재확인해야 합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-TAX-04'::text, 'OFFICIAL'::app_private.data_origin, 'LOCAL_TAX_GENERAL'::app_private.intent_code, '지방세 세목별 과세증명서 발급 안내'::text, '지방세 세목별 과세증명서는 지방세 과세 및 납부실적을 증명하는 민원입니다. 인터넷·방문·FAX·우편·무인발급기로 신청할 수 있고, 온라인 대리 신청은 불가합니다.'::text, '["정부24에서 증명하려는 과세·납부실적의 민원을 확인합니다.","본인 신청은 온라인 또는 가능한 발급 방법을 선택합니다.","대리·방문·무인발급은 신청자 유형과 설치 장소의 안내를 확인합니다."]'::jsonb, '["상황별 상이: 본인·대리인·법인·상속·법정대리인 여부에 따른 정부24 제출서류 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '자치단체 조례로 결정, 전자민원(인터넷) 신청 시 무료'::text, '시·군·구, 읍·면·동, 출장소(접수·처리); 행정안전부 지방세정책과'::text, '정부24 지방세 세목별 과세증명서 발급'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000084&typeSn=05'::text, '2026-07-18'::date, '방문 수수료는 자치단체 조례에 따라 달라질 수 있습니다. 개인별 과세·납부실적을 이 서비스가 확인하거나 해석하지 않으며, 무인발급기의 서비스 제공 여부는 설치 장소별로 다릅니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-TAX-05'::text, 'OFFICIAL'::app_private.data_origin, 'LOCAL_TAX_GENERAL'::app_private.intent_code, '지방세 납부확인서 발급 안내'::text, '지방세 납부확인서는 지방세 과세내역에 대한 납부사실을 증명하는 민원입니다. 인터넷 또는 방문으로 신청할 수 있고, 온라인 대리 신청은 불가합니다. 공식 안내상 수수료는 없고 처리기간은 즉시(근무시간 내 3시간)입니다.'::text, '["정부24에서 지방세 납부확인서 민원을 확인합니다.","본인은 인터넷 또는 방문 중 가능한 방법을 선택합니다.","대리·방문 신청은 신청자 유형별 제출서류와 접수·처리 가능 기관을 확인합니다."]'::jsonb, '["상황별 상이: 본인·대리인·법인·상속·법정대리인 여부에 따른 정부24 제출서류 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '수수료 없음'::text, '시·군·구, 읍·면·동(접수·처리); 행정안전부 지방세정책과'::text, '정부24 지방세 납부확인서 발급'::text, 'https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13110000017&HighCtgCD=A09002&tp_seq=01'::text, '2026-07-18'::date, '이 민원은 납부사실 증명 경로를 안내하는 것이며, 이 서비스가 개인 납부내역을 조회·저장·확인해 주지 않습니다. 실제 접수·처리 가능 여부는 해당 기관에 확인합니다. PM은 정확한 plus.gov.kr deep-link와 최신 표시 내용을 재확인해야 합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-WASTE-01'::text, 'OFFICIAL'::app_private.data_origin, 'BULKY_WASTE'::app_private.intent_code, '대형폐기물 배출신청 절차'::text, '홈페이지 또는 지정판매소에서 품목에 맞는 납부 절차를 마친 뒤, 납부필증 또는 납부정보를 표시하여 배출하고 수거를 기다리는 안내입니다.'::text, '["홈페이지: 배출신청서를 작성하고 배출장소·품목을 선택합니다.","신청조회에서 수수료 결제를 완료한 뒤 납부필증 스티커 또는 납부정보를 표시해 배출합니다.","지정판매소 이용 시 납부필증 구매·결제 후 납부필증을 부착하고 장소·배출일자를 준수합니다."]'::jsonb, '[]'::jsonb, NULL::text, NULL::text, '세종특별자치시시설관리공단'::text, '배출신청안내'::text, 'https://www.sjwaste.kr/board?menuId=MENU00303&siteId=null'::text, '2026-07-18'::date, '수수료 결제까지 완료해야 홈페이지 신고가 완료됩니다. 당일 배출 즉시 당일 수거는 어렵고, 건물 내부 수거는 하지 않으므로 차량 진입이 가능한 곳까지 직접 배출해야 합니다. 실제 수거 시점과 판매소 가능 여부는 PM 승인 직전에 재확인합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-WASTE-02'::text, 'OFFICIAL'::app_private.data_origin, 'BULKY_WASTE'::app_private.intent_code, '대형폐기물 결제·스티커·변경·환불 안내'::text, '홈페이지 신청은 신용카드 또는 가상계좌 결제까지 마쳐야 완료됩니다. 스티커는 신청조회에서 출력하며, 변경은 기존 신청을 취소한 뒤 다시 신청하는 방식입니다.'::text, '["신청조회에서 수수료를 결제합니다.","필요하면 납부필증 스티커를 출력합니다.","변경 시 기존 신청을 취소한 뒤 다시 신청하고, 출력 여부에 맞는 환불 절차를 확인합니다."]'::jsonb, '[]'::jsonb, NULL::text, NULL::text, '세종특별자치시시설관리공단'::text, '배출신청안내'::text, 'https://www.sjwaste.kr/board?menuId=MENU00303&siteId=null'::text, '2026-07-18'::date, '출력 전 취소는 즉시 환불 처리로 안내되지만 실제 환불은 결제일에 따라 3~4일 이상 걸릴 수 있습니다. 스티커를 한 장이라도 출력하면 미사용 증빙 사진 첨부 후 실제 환불까지 2주 이상 걸릴 수 있으며, 부분 환불은 불가하고 전체 환불만 가능합니다. 이는 보장 처리기한이 아니므로 PM 승인 직전에 재확인합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-WASTE-04'::text, 'OFFICIAL'::app_private.data_origin, 'BULKY_WASTE'::app_private.intent_code, '매트리스 배출 수수료'::text, '공식 품목표의 매트리스 수수료는 1인용 매트 4,000원, 2인용 매트 6,000원, 3단 쇼파겸용 4,000원으로 표시됩니다.'::text, '["매트리스의 공식 품목·규격을 확인합니다.","해당 수수료로 공식 배출 절차를 진행합니다."]'::jsonb, '[]'::jsonb, NULL::text, '1인용 매트 4,000원; 2인용 매트 6,000원; 3단 쇼파겸용 4,000원'::text, '세종특별자치시시설관리공단'::text, '배출항목선택'::text, 'https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305'::text, '2026-07-18'::date, '프레임과 매트리스는 공식 품목표에서 별도 품목입니다. 품목표에 없는 물건은 유사 품목 수수료를 준용한다고만 안내되어 있으므로 정확한 적용은 공식 신청 화면 또는 시설관리공단에 확인합니다. 수수료는 PM 승인 직전에 재확인합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
    ('KB-WASTE-05'::text, 'OFFICIAL'::app_private.data_origin, 'BULKY_WASTE'::app_private.intent_code, '대형폐기물 배출요일·수거 문의'::text, '공식 안내는 지역 분류별 배출·수거 요일과 시설관리공단 문의 경로를 제공합니다. 동지역은 동별 수거요일이 달라질 수 있어 개별 일정을 다시 확인해야 합니다.'::text, '["주소의 지역 분류를 확인합니다.","공식 표의 배출요일에 맞춰 배출합니다.","당일 수거 여부나 동별 일정은 시설관리공단의 공식 문의 경로로 확인합니다."]'::jsonb, '[]'::jsonb, NULL::text, NULL::text, '세종특별자치시시설관리공단'::text, '배출신청안내'::text, 'https://www.sjwaste.kr/board?menuId=MENU00303&siteId=null'::text, '2026-07-18'::date, '동지역은 월·수 배출, 화·목 수거로 안내되나 동별 수거요일이 다를 수 있습니다. 읍면지역은 지역 분류에 따라 요일이 다르며, 당일 배출 즉시 당일 수거는 어렵습니다. 운영 사정과 실제 일정은 PM 승인 직전에 공식 안내로 재확인합니다.'::text, 'ACTIVE'::app_private.kb_status, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz);

INSERT INTO app_private.kb_question_examples (
  kb_document_id, question_example, normalized_text
)
SELECT kb.id, expected.question_example, expected.normalized_text
FROM (VALUES
    ('KB-CERT-01'::text, '등본과 초본은 무엇이 다른가요?'::text, NULL::text),
    ('KB-CERT-01'::text, '등본은 누구의 정보가 나오나요?'::text, NULL::text),
    ('KB-CERT-01'::text, '초본을 제출하라고 하는데 무엇을 확인해야 하나요?'::text, NULL::text),
    ('KB-CERT-02'::text, '등본 발급 수수료가 있나요?'::text, NULL::text),
    ('KB-CERT-02'::text, '등본을 온라인으로 받을 수 있나요?'::text, NULL::text),
    ('KB-CERT-02'::text, '주민등록등본은 어떻게 발급하나요?'::text, NULL::text),
    ('KB-CERT-03'::text, '주민등록초본은 어떻게 발급하나요?'::text, NULL::text),
    ('KB-CERT-03'::text, '초본 발급에 무엇이 필요한가요?'::text, NULL::text),
    ('KB-CERT-03'::text, '초본을 인터넷으로 발급받을 수 있나요?'::text, NULL::text),
    ('KB-CERT-04'::text, '열람과 등본 발급은 다른가요?'::text, NULL::text),
    ('KB-CERT-04'::text, '주민등록표 열람 수수료가 있나요?'::text, NULL::text),
    ('KB-CERT-04'::text, '주민등록표는 어떻게 열람하나요?'::text, NULL::text),
    ('KB-CERT-05'::text, '가까운 무인민원발급기는 어디서 찾나요?'::text, NULL::text),
    ('KB-CERT-05'::text, '무인발급기는 항상 이용할 수 있나요?'::text, NULL::text),
    ('KB-CERT-05'::text, '무인발급기에서 등본을 뽑을 수 있나요?'::text, NULL::text),
    ('KB-MOVE-01'::text, '이사했는데 전입신고는 어떻게 하나요?'::text, NULL::text),
    ('KB-MOVE-01'::text, '전입신고 수수료가 있나요?'::text, NULL::text),
    ('KB-MOVE-01'::text, '전입신고를 온라인으로 할 수 있나요?'::text, NULL::text),
    ('KB-MOVE-02'::text, '가족이 대신 전입신고할 수 있나요?'::text, NULL::text),
    ('KB-MOVE-02'::text, '대리인이 전입신고할 때 준비물이 있나요?'::text, NULL::text),
    ('KB-MOVE-02'::text, '전입신고를 방문해서 하려면 무엇이 필요한가요?'::text, NULL::text),
    ('KB-MOVE-03'::text, '대신 온라인 전입신고를 해줄 수 있나요?'::text, NULL::text),
    ('KB-MOVE-03'::text, '온라인 전입신고는 누가 할 수 있나요?'::text, NULL::text),
    ('KB-MOVE-03'::text, '해외에 있다가 돌아왔는데 온라인 전입신고가 되나요?'::text, NULL::text),
    ('KB-MOVE-04'::text, '전입신고 사실을 통보받을 수 있나요?'::text, NULL::text),
    ('KB-MOVE-04'::text, '주민등록 통보서비스는 온라인으로 신청할 수 있나요?'::text, NULL::text),
    ('KB-MOVE-04'::text, '주소 변경 통보서비스는 어떻게 신청하나요?'::text, NULL::text),
    ('KB-MOVE-05'::text, '이사 후 전입신고는 언제까지 해야 하나요?'::text, NULL::text),
    ('KB-MOVE-05'::text, '전입신고 기한을 놓치면 어떻게 되나요?'::text, NULL::text),
    ('KB-MOVE-05'::text, '전입신고 의무가 있는지 궁금해요.'::text, NULL::text),
    ('KB-TAX-01'::text, '전자납부번호로 납부할 수 있나요?'::text, NULL::text),
    ('KB-TAX-01'::text, '지방세 납부 내역을 확인하고 싶어요.'::text, NULL::text),
    ('KB-TAX-01'::text, '지방세를 온라인으로 어디에서 내나요?'::text, NULL::text),
    ('KB-TAX-02'::text, '자동차세 고지는 어디서 확인하나요?'::text, NULL::text),
    ('KB-TAX-02'::text, '자동차세 납부 상태를 확인하려면 어떻게 하나요?'::text, NULL::text),
    ('KB-TAX-02'::text, '자동차세를 온라인으로 내고 싶어요.'::text, NULL::text),
    ('KB-TAX-03'::text, '납세증명서 수수료가 있나요?'::text, NULL::text),
    ('KB-TAX-03'::text, '납세증명서를 온라인으로 신청할 수 있나요?'::text, NULL::text),
    ('KB-TAX-03'::text, '지방세 납세증명서는 어떻게 발급하나요?'::text, NULL::text),
    ('KB-TAX-04'::text, '세목별 과세증명서 수수료가 있나요?'::text, NULL::text),
    ('KB-TAX-04'::text, '세목별 과세증명서를 온라인으로 받을 수 있나요?'::text, NULL::text),
    ('KB-TAX-04'::text, '지방세 세목별 과세증명서는 어떻게 발급하나요?'::text, NULL::text),
    ('KB-TAX-05'::text, '납부확인서를 온라인으로 받을 수 있나요?'::text, NULL::text),
    ('KB-TAX-05'::text, '지방세 납부확인서 발급 수수료가 있나요?'::text, NULL::text),
    ('KB-TAX-05'::text, '지방세 납부확인서는 어떻게 발급하나요?'::text, NULL::text),
    ('KB-WASTE-01'::text, '대형폐기물 스티커는 어디서 받나요?'::text, NULL::text),
    ('KB-WASTE-01'::text, '대형폐기물은 어떻게 신청하나요?'::text, NULL::text),
    ('KB-WASTE-01'::text, '대형폐기물을 어디에 내놓아야 하나요?'::text, NULL::text),
    ('KB-WASTE-02'::text, '대형폐기물 스티커는 어떻게 출력하나요?'::text, NULL::text),
    ('KB-WASTE-02'::text, '대형폐기물 신청 후 결제는 어떻게 하나요?'::text, NULL::text),
    ('KB-WASTE-02'::text, '대형폐기물 신청을 취소하면 환불되나요?'::text, NULL::text),
    ('KB-WASTE-04'::text, '1인용 매트리스 수수료가 있나요?'::text, NULL::text),
    ('KB-WASTE-04'::text, '3단 쇼파겸용 매트리스 비용은 얼마인가요?'::text, NULL::text),
    ('KB-WASTE-04'::text, '매트리스는 버리는 데 얼마인가요?'::text, NULL::text),
    ('KB-WASTE-05'::text, '대형폐기물은 무슨 요일에 내놓나요?'::text, NULL::text),
    ('KB-WASTE-05'::text, '오늘 대형폐기물을 내면 수거되나요?'::text, NULL::text),
    ('KB-WASTE-05'::text, '우리 동의 대형폐기물 수거일을 알고 싶어요.'::text, NULL::text)
) AS expected(kb_public_id, question_example, normalized_text)
JOIN app_private.kb_documents AS kb
  ON kb.public_id = expected.kb_public_id
ORDER BY expected.kb_public_id, expected.question_example;

INSERT INTO app_private.offices (public_id, data_origin, region, office_name, address, phone, opening_hours, map_url, source_title, source_url, last_verified_at)
VALUES
    ('OFFICE-AREUM'::text, 'OFFICIAL'::app_private.data_origin, '아름동'::text, '아름동 행정복지센터'::text, '(30100) 세종특별자치시 보듬3로 114(아름동)'::text, '044-301-6300'::text, '평일 09:00~18:00'::text, 'https://place.map.kakao.com/26471721'::text, '아름동 행정복지센터 찾아오시는 길'::text, 'https://www.sejong.go.kr/areum/sub02_02.do?cmsNo=1461'::text, '2026-07-18'::date),
    ('OFFICE-DODAM'::text, 'OFFICIAL'::app_private.data_origin, '도담동'::text, '도담동 행정복지센터'::text, '(30098) 세종특별자치시 보람로 77(도담동)'::text, '044-301-6200'::text, '평일 09:00~18:00'::text, 'https://place.map.kakao.com/23346315'::text, '도담동 행정복지센터 찾아오시는 길'::text, 'https://www.sejong.go.kr/dodam/sub02_02.do?cmsNo=1458'::text, '2026-07-18'::date),
    ('OFFICE-JOCHIWON'::text, 'OFFICIAL'::app_private.data_origin, '조치원읍'::text, '북세종 통합 행정복지센터'::text, '(30024) 세종특별자치시 조치원읍 새내16길 17'::text, '044-301-5000'::text, '평일 09:00~18:00'::text, 'https://place.map.kakao.com/19342218'::text, '조치원읍 찾아오시는 길'::text, 'https://www.sejong.go.kr/jochiwon/sub02_02.do?cmsNo=1425'::text, '2026-07-18'::date);

INSERT INTO app_private.office_service_mappings (
  office_id, intent, department_label
)
SELECT office.id, expected.intent::app_private.intent_code, expected.department_label
FROM (VALUES
    ('OFFICE-AREUM'::text, 'BULKY_WASTE'::text, '안전도시과 환경경제'::text),
    ('OFFICE-AREUM'::text, 'CERTIFICATE_ISSUANCE'::text, '민원행정과 일반민원'::text),
    ('OFFICE-AREUM'::text, 'MOVE_IN_RESIDENT_REGISTRATION'::text, '민원행정과 일반민원'::text),
    ('OFFICE-DODAM'::text, 'CERTIFICATE_ISSUANCE'::text, '민원행정'::text),
    ('OFFICE-DODAM'::text, 'LOCAL_TAX_GENERAL'::text, '민원행정'::text),
    ('OFFICE-DODAM'::text, 'MOVE_IN_RESIDENT_REGISTRATION'::text, '민원행정'::text),
    ('OFFICE-JOCHIWON'::text, 'BULKY_WASTE'::text, '안전도시과 청소환경'::text),
    ('OFFICE-JOCHIWON'::text, 'CERTIFICATE_ISSUANCE'::text, '민원행정과 일반민원'::text),
    ('OFFICE-JOCHIWON'::text, 'LOCAL_TAX_GENERAL'::text, '민원행정과 세무부동산'::text),
    ('OFFICE-JOCHIWON'::text, 'MOVE_IN_RESIDENT_REGISTRATION'::text, '민원행정과 일반민원'::text)
) AS expected(office_public_id, intent, department_label)
JOIN app_private.offices AS office
  ON office.public_id = expected.office_public_id
ORDER BY expected.office_public_id, expected.intent;

DO $data_seed_projection_guard$
DECLARE
  v_mismatch boolean;
BEGIN
  WITH
    expected_kb_documents (public_id, data_origin, category, service_name, answer_summary, procedure_steps, required_documents, processing_time, fee, department, source_title, source_url, last_verified_at, caution, status, created_by, approved_by, approved_at) AS (
      VALUES
        ('KB-CERT-01'::text, 'OFFICIAL'::text, 'CERTIFICATE_ISSUANCE'::text, '등본과 초본의 차이'::text, '등본은 한 세대의 모든 구성원에 대한 주민등록 사항을, 초본은 한 사람의 자세한 주민등록 사항을 표시합니다.'::text, '["제출처가 요구하는 문서 종류와 표시 항목을 확인합니다.","정부24의 주민등록표 등본(초본) 발급 안내에서 신청 경로를 확인합니다."]'::jsonb, '["제출처가 요구하는 문서 종류와 표시 항목 확인"]'::jsonb, NULL::text, NULL::text, '행정안전부 주민과'::text, '주민등록표 등본(초본) 발급'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000015&typeSn=01'::text, '2026-07-18'::date, '제출처별 요구 문서와 표시 항목은 다를 수 있습니다. 용도별 상세 표시 항목을 이 안내가 단정하지 않으므로 제출처와 공식 신청 화면을 확인합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-CERT-02'::text, 'OFFICIAL'::text, 'CERTIFICATE_ISSUANCE'::text, '주민등록등본 발급 방법'::text, '주민등록등본은 인터넷, 방문, 무인발급기로 신청할 수 있습니다. 공식 안내상 인터넷 발급은 무료이고, 발급 수수료와 서류는 신청 방법과 신청자 유형에 따라 확인해야 합니다.'::text, '["정부24에서 주민등록표 등본(초본) 발급 민원을 확인합니다.","인터넷·방문·무인발급기 중 가능한 방법을 선택합니다.","방문 또는 대리 신청이면 신청자 유형별 공식 제출서류를 확인합니다."]'::jsonb, '["본인 방문: 유효한 신분증","대리 신청 등 상황별: 정부24 제출서류 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '1통 400원, 이해관계인 교부 500원, 인터넷 발급 무료'::text, '읍·면·동/출장소(접수·처리); 행정안전부 주민과'::text, '주민등록표 등본(초본) 발급'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000015&typeSn=01'::text, '2026-07-18'::date, '무인발급기의 실제 운영시간·수수료·발급 가능 여부는 기기와 자치단체별로 다를 수 있습니다. 온라인 대리 신청은 불가하며, 개인별 발급 가능 여부는 공식 신청 화면 또는 처리기관에서 확인합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-CERT-03'::text, 'OFFICIAL'::text, 'CERTIFICATE_ISSUANCE'::text, '주민등록초본 발급 방법'::text, '주민등록초본은 인터넷, 방문, 무인발급기로 신청할 수 있습니다. 신청자 본인의 초본과 같은 세대 구성원의 초본이 기본 발급 범위에 포함되며, 신청 방법과 신청자 유형에 따라 조건이 달라집니다.'::text, '["정부24에서 주민등록표 등본(초본) 발급 민원을 확인합니다.","본인은 가능한 신청 방법을 선택합니다.","대리인 또는 정당한 권리가 있는 사람의 신청은 공식 안내의 신청 방법과 서류를 확인합니다."]'::jsonb, '["본인 방문: 유효한 신분증","대리·이해관계인 등 상황별: 정부24 제출서류 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '1통 400원, 이해관계인 교부 500원, 인터넷 발급 무료'::text, '읍·면·동/출장소(접수·처리); 행정안전부 주민과'::text, '주민등록표 등본(초본) 발급'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000015&typeSn=01'::text, '2026-07-18'::date, '온라인 대리 신청은 불가합니다. 초본의 상세 표시 항목, 외국인 신청 범위 및 개인별 적용은 이 안내가 단정하지 않으므로 제출처와 관할 처리기관의 공식 안내를 확인합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-CERT-04'::text, 'OFFICIAL'::text, 'CERTIFICATE_ISSUANCE'::text, '주민등록표 열람'::text, '주민등록표 열람은 인터넷 또는 방문으로 신청할 수 있는 민원이며, 증명서 발급과는 구분됩니다. 공식 안내상 인터넷 열람은 무료이고 방문 열람 수수료는 1건 1회 300원입니다.'::text, '["정부24에서 주민등록표 열람 민원을 확인합니다.","본인 또는 대리인 해당 여부에 맞는 신청 방법을 확인합니다.","온라인 또는 방문 경로를 선택합니다."]'::jsonb, '["본인·대리인·정당한 이해관계인 여부에 따른 공식 제출서류 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '1건 1회 300원, 인터넷 열람 무료'::text, '시·군·구 및 읍·면·동 출장소(접수·처리); 행정안전부 주민과'::text, '주민등록표 열람'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000014&typeSn=01'::text, '2026-07-18'::date, '열람은 증명서 발급과 다른 민원입니다. 온라인 대리 신청은 불가하며, 개인별 열람 가능 여부와 수령·확인 방법은 공식 신청 화면 또는 처리기관에서 확인합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-CERT-05'::text, 'OFFICIAL'::text, 'CERTIFICATE_ISSUANCE'::text, '무인민원발급기 이용 안내'::text, '정부24 무인민원발급안내에서 시도·시군구·읍면동과 발급 가능 민원 조건으로 설치 장소를 확인할 수 있습니다.'::text, '["정부24 무인민원발급안내에서 설치 장소를 검색합니다.","필요한 민원의 발급 가능 여부를 선택한 설치 장소에서 확인합니다.","이용 전 운영시간과 수수료를 다시 확인합니다."]'::jsonb, '["발급 민원별 본인확인 및 공식 안내 확인"]'::jsonb, NULL::text, NULL::text, '정부24(행정안전부)'::text, '무인민원발급안내'::text, 'https://plus.gov.kr/portal/custcntr/utztngd/unmncvlcptissugd/'::text, '2026-07-18'::date, '표준 안내의 운영시간·수수료를 모든 기기에 동일하게 적용하지 않습니다. 실제 발급 종류·발급 가능 시간·수수료는 설치 장소와 자치단체 운영 상황에 따라 다를 수 있습니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-MOVE-01'::text, 'OFFICIAL'::text, 'MOVE_IN_RESIDENT_REGISTRATION'::text, '전입신고 개요·신청방법'::text, '전입신고는 인터넷 또는 방문으로 신청할 수 있습니다. 본인 또는 대리인이 신청할 수 있으나 온라인 대리 신청은 불가하며, 공식 안내상 수수료는 없습니다.'::text, '["정부24 전입신고 안내에서 본인에게 맞는 신청 방법을 확인합니다.","인터넷 또는 관할 읍·면·동·출장소 방문 중 가능한 방법을 선택합니다.","상황별 제출서류와 접수 가능 여부를 확인합니다."]'::jsonb, '["상황별 공식 구비서류 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '수수료 없음'::text, '읍·면·동/출장소(접수·처리); 행정안전부 주민과'::text, '전입신고'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000016&typeSn=01'::text, '2026-07-18'::date, '세대 구성과 신고자 관계에 따라 예외와 추가 서류가 있을 수 있습니다. 실제 접수 가능 여부는 관할 읍·면·동의 공식 안내로 확인합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-MOVE-02'::text, 'OFFICIAL'::text, 'MOVE_IN_RESIDENT_REGISTRATION'::text, '방문 전입신고 준비물'::text, '방문 전입신고는 본인·대리 여부와 세대 관계에 따라 준비물이 달라집니다. 본인 신고에는 유효한 신분증과 행정정보 공동이용 사전동의서가 안내되며, 대리 신고에는 위임 관련 서류와 신분증을 확인해야 합니다.'::text, '["본인 신고인지 대리 신고인지 확인합니다.","정부24 전입신고 안내에서 해당 유형의 구비서류를 확인합니다.","관할 읍·면·동 또는 출장소 방문 전 추가 서류 필요 여부를 확인합니다."]'::jsonb, '["본인 신고: 유효한 신분증, 행정정보 공동이용 사전동의서","대리 신고: 위임한 사람과 위임받은 사람의 신분증, 위임장, 행정정보 공동이용 사전동의서","조건부 서류: 건축물대장·재외국민 관련서류·출입국사실증명·가족관계증명서 등 공식 안내 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '수수료 없음'::text, '읍·면·동/출장소(접수·처리); 행정안전부 주민과'::text, '전입신고'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000016&typeSn=01'::text, '2026-07-18'::date, '신분증만으로 항상 접수되는 것은 아닙니다. 가족관계·위임·국적 또는 체류 상태와 동의 여부에 따라 준비물이 달라지므로 관할 처리기관의 공식 안내를 확인합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-MOVE-03'::text, 'OFFICIAL'::text, 'MOVE_IN_RESIDENT_REGISTRATION'::text, '온라인 전입신고'::text, '전입신고는 인터넷으로 본인이 신청할 수 있으나 온라인 대리 신청은 불가합니다. 재외국민과 해외체류자 등은 공식 안내에서 방문 신청 경계를 확인해야 합니다.'::text, '["정부24 전입신고에서 본인 신청 가능 여부를 확인합니다.","온라인 신청이 가능한 경우 본인으로 신청합니다.","방문 신청 대상이면 새 거주지 관할 주민센터의 공식 안내를 확인합니다."]'::jsonb, '["온라인 신청 가능 여부와 조건별 공식 안내 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '수수료 없음'::text, '읍·면·동/출장소(접수·처리); 행정안전부 주민과'::text, '전입신고'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000016&typeSn=01'::text, '2026-07-18'::date, '특정 인증수단은 이 출처로 확정하지 않습니다. 재외국민은 재외국민 여부 확인을 위해, 해외체류자는 입국 사실 확인을 위해 방문 신청 대상이 될 수 있으므로 개인별 적용은 관할기관에서 확인합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-MOVE-04'::text, 'OFFICIAL'::text, 'MOVE_IN_RESIDENT_REGISTRATION'::text, '주민등록 관련 통보서비스'::text, '주민등록 관련 통보서비스는 전입신고, 세대주 변경, 주민등록증, 주민등록표, 자신의 주소변경사실에 관한 통보를 안내합니다. 인터넷 또는 방문으로 신청할 수 있으며 온라인 대리 신청은 불가합니다.'::text, '["필요한 통보 종류가 공식 통보 범위에 있는지 확인합니다.","정부24에서 인터넷 또는 방문 신청 방법을 확인합니다.","대리 또는 자격 확인이 필요한 경우 공식 제출서류를 확인합니다."]'::jsonb, '["방문 신청: 신청인 신분확인증","전입신고·세대주변경 통보 등 자격별: 공식 자격 확인 자료"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '수수료 없음'::text, '읍·면·동/출장소(접수·처리); 행정안전부 주민과'::text, '주민등록 관련 통보서비스 (전입신고, 세대주변경, 주민등록증, 주민등록표, 주소변경사실)'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13110000039&typeSn=01'::text, '2026-07-18'::date, '이 서비스는 전입신고 자체와 다릅니다. 통보 대상과 신청 자격은 유형별로 다를 수 있으며, 온라인 대리 신청은 불가합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-MOVE-05'::text, 'OFFICIAL'::text, 'MOVE_IN_RESIDENT_REGISTRATION'::text, '주민등록법상 신고 일반 원칙·주의사항'::text, '세대 전원 또는 일부가 거주지를 이동한 경우, 신고의무자는 새 거주지에 전입한 날부터 14일 이내에 전입신고하는 일반 원칙이 안내됩니다.'::text, '["전입한 날과 새 거주지 관할기관을 확인합니다.","정부24 전입신고 안내 또는 관할기관의 공식 경로를 확인합니다.","개인 사정이 있는 경우 관할기관에 적용 여부를 확인합니다."]'::jsonb, '["상황별 전입신고 공식 구비서류 확인"]'::jsonb, NULL::text, NULL::text, '관할 읍·면·동; 국가법령정보센터'::text, '주민등록법'::text, 'https://www.law.go.kr/LSW/lsInfoP.do?lsId=001655&urlMode=lsInfoP'::text, '2026-07-18'::date, '이 항목은 일반 원칙만 안내합니다. 위반 여부, 과태료 금액·부과 여부와 개인 사실관계의 법률 적용은 이 서비스가 판단하지 않으므로 관할기관 확인 또는 LEGAL_JUDGMENT 폴백이 필요합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-TAX-01'::text, 'OFFICIAL'::text, 'LOCAL_TAX_GENERAL'::text, '지방세 온라인 납부 공식 경로 안내'::text, '지방세의 온라인 조회·납부가 필요하면 위택스 공식 누리집에서 확인할 수 있습니다. 고지서에 전자납부번호가 있으면 위택스의 빠른납부 경로를 확인할 수 있습니다.'::text, '["위택스에 접속합니다.","개인 고지·납부 대상 확인이 필요하면 본인에게 맞는 공식 로그인·인증 경로를 이용합니다.","전자납부번호가 있으면 빠른납부 안내를 확인합니다."]'::jsonb, '[]'::jsonb, NULL::text, NULL::text, '위택스(온라인 경로); 개별 세목 문의는 관할 지방세 담당기관 확인'::text, '위택스'::text, 'https://www.wetax.go.kr/main.do'::text, '2026-07-18'::date, '개인별 납부대상·세액·체납·납부완료 여부는 이 서비스가 조회하지 않습니다. 본인 인증 후 공식 시스템 또는 관할기관에서 직접 확인해야 합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-TAX-02'::text, 'OFFICIAL'::text, 'LOCAL_TAX_GENERAL'::text, '자동차세 개인 고지 확인·납부의 공식 로그인 경로'::text, '개인 자동차세 고지·납부 대상은 위택스에서 본인 인증 후 확인하도록 안내합니다. 이 서비스는 자동차세 금액이나 납부 상태를 조회하지 않습니다.'::text, '["위택스에 접속합니다.","공식 로그인 화면에서 본인에게 맞는 인증 방법을 선택합니다.","로그인 후 본인 고지 내역과 이용 가능한 납부 경로를 직접 확인합니다."]'::jsonb, '[]'::jsonb, NULL::text, NULL::text, '위택스(개인 고지 확인·납부 경로); 세목별 개별 문의는 관할 지방세 담당기관 확인'::text, '위택스 로그인(자동차세 개인 고지 확인 경계)'::text, 'https://www.wetax.go.kr/login.do'::text, '2026-07-18'::date, '로그인 후 노출되는 고지·차량·세액은 개인별로 다릅니다. 납기, 연세액 납부 가능 여부·혜택, 감면, 체납 여부 및 개별 부과액은 이 로그인 출처 범위 밖이며, 최신 자동차세 전용 공식 출처와 본인 화면 확인 없이는 안내하지 않습니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-TAX-03'::text, 'OFFICIAL'::text, 'LOCAL_TAX_GENERAL'::text, '지방세 납세증명서 발급 안내'::text, '지방세 납세증명서는 인터넷·방문·FAX·우편·무인발급기로 신청할 수 있으며, 온라인 대리 신청은 불가합니다. 공식 안내상 수수료는 없고 처리기간은 즉시(근무시간 내 3시간)입니다.'::text, '["정부24의 해당 민원에서 본인 신청 경로를 확인합니다.","대리 신청 또는 방문이 필요하면 신청자 유형별 제출서류와 접수·처리기관을 공식 페이지에서 확인합니다.","가능한 신청 방법을 선택합니다."]'::jsonb, '["상황별 상이: 본인·대리인·법인·상속·법정대리인 여부에 따른 정부24 제출서류 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '수수료 없음'::text, '시·군·구, 읍·면·동, 출장소(접수·처리); 행정안전부 지방세정책과'::text, '정부24 지방세 납세증명서 발급'::text, 'https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13100000056&tp_seq=01'::text, '2026-07-18'::date, '이 증명은 발급일 현재 법령상 예외 금액을 제외한 다른 체납액이 없음을 증명하는 민원입니다. 이를 개인의 모든 체납이 전혀 없다는 단정으로 바꾸지 않으며, 실제 발급 가능 여부와 개인 결과는 본인 또는 관할 처리기관이 확인합니다. PM은 정확한 plus.gov.kr deep-link와 최신 표시 내용을 재확인해야 합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-TAX-04'::text, 'OFFICIAL'::text, 'LOCAL_TAX_GENERAL'::text, '지방세 세목별 과세증명서 발급 안내'::text, '지방세 세목별 과세증명서는 지방세 과세 및 납부실적을 증명하는 민원입니다. 인터넷·방문·FAX·우편·무인발급기로 신청할 수 있고, 온라인 대리 신청은 불가합니다.'::text, '["정부24에서 증명하려는 과세·납부실적의 민원을 확인합니다.","본인 신청은 온라인 또는 가능한 발급 방법을 선택합니다.","대리·방문·무인발급은 신청자 유형과 설치 장소의 안내를 확인합니다."]'::jsonb, '["상황별 상이: 본인·대리인·법인·상속·법정대리인 여부에 따른 정부24 제출서류 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '자치단체 조례로 결정, 전자민원(인터넷) 신청 시 무료'::text, '시·군·구, 읍·면·동, 출장소(접수·처리); 행정안전부 지방세정책과'::text, '정부24 지방세 세목별 과세증명서 발급'::text, 'https://plus.gov.kr/search/searchdtl/?srvcId=13100000084&typeSn=05'::text, '2026-07-18'::date, '방문 수수료는 자치단체 조례에 따라 달라질 수 있습니다. 개인별 과세·납부실적을 이 서비스가 확인하거나 해석하지 않으며, 무인발급기의 서비스 제공 여부는 설치 장소별로 다릅니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-TAX-05'::text, 'OFFICIAL'::text, 'LOCAL_TAX_GENERAL'::text, '지방세 납부확인서 발급 안내'::text, '지방세 납부확인서는 지방세 과세내역에 대한 납부사실을 증명하는 민원입니다. 인터넷 또는 방문으로 신청할 수 있고, 온라인 대리 신청은 불가합니다. 공식 안내상 수수료는 없고 처리기간은 즉시(근무시간 내 3시간)입니다.'::text, '["정부24에서 지방세 납부확인서 민원을 확인합니다.","본인은 인터넷 또는 방문 중 가능한 방법을 선택합니다.","대리·방문 신청은 신청자 유형별 제출서류와 접수·처리 가능 기관을 확인합니다."]'::jsonb, '["상황별 상이: 본인·대리인·법인·상속·법정대리인 여부에 따른 정부24 제출서류 확인"]'::jsonb, '즉시(근무시간 내 3시간)'::text, '수수료 없음'::text, '시·군·구, 읍·면·동(접수·처리); 행정안전부 지방세정책과'::text, '정부24 지방세 납부확인서 발급'::text, 'https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13110000017&HighCtgCD=A09002&tp_seq=01'::text, '2026-07-18'::date, '이 민원은 납부사실 증명 경로를 안내하는 것이며, 이 서비스가 개인 납부내역을 조회·저장·확인해 주지 않습니다. 실제 접수·처리 가능 여부는 해당 기관에 확인합니다. PM은 정확한 plus.gov.kr deep-link와 최신 표시 내용을 재확인해야 합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-WASTE-01'::text, 'OFFICIAL'::text, 'BULKY_WASTE'::text, '대형폐기물 배출신청 절차'::text, '홈페이지 또는 지정판매소에서 품목에 맞는 납부 절차를 마친 뒤, 납부필증 또는 납부정보를 표시하여 배출하고 수거를 기다리는 안내입니다.'::text, '["홈페이지: 배출신청서를 작성하고 배출장소·품목을 선택합니다.","신청조회에서 수수료 결제를 완료한 뒤 납부필증 스티커 또는 납부정보를 표시해 배출합니다.","지정판매소 이용 시 납부필증 구매·결제 후 납부필증을 부착하고 장소·배출일자를 준수합니다."]'::jsonb, '[]'::jsonb, NULL::text, NULL::text, '세종특별자치시시설관리공단'::text, '배출신청안내'::text, 'https://www.sjwaste.kr/board?menuId=MENU00303&siteId=null'::text, '2026-07-18'::date, '수수료 결제까지 완료해야 홈페이지 신고가 완료됩니다. 당일 배출 즉시 당일 수거는 어렵고, 건물 내부 수거는 하지 않으므로 차량 진입이 가능한 곳까지 직접 배출해야 합니다. 실제 수거 시점과 판매소 가능 여부는 PM 승인 직전에 재확인합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-WASTE-02'::text, 'OFFICIAL'::text, 'BULKY_WASTE'::text, '대형폐기물 결제·스티커·변경·환불 안내'::text, '홈페이지 신청은 신용카드 또는 가상계좌 결제까지 마쳐야 완료됩니다. 스티커는 신청조회에서 출력하며, 변경은 기존 신청을 취소한 뒤 다시 신청하는 방식입니다.'::text, '["신청조회에서 수수료를 결제합니다.","필요하면 납부필증 스티커를 출력합니다.","변경 시 기존 신청을 취소한 뒤 다시 신청하고, 출력 여부에 맞는 환불 절차를 확인합니다."]'::jsonb, '[]'::jsonb, NULL::text, NULL::text, '세종특별자치시시설관리공단'::text, '배출신청안내'::text, 'https://www.sjwaste.kr/board?menuId=MENU00303&siteId=null'::text, '2026-07-18'::date, '출력 전 취소는 즉시 환불 처리로 안내되지만 실제 환불은 결제일에 따라 3~4일 이상 걸릴 수 있습니다. 스티커를 한 장이라도 출력하면 미사용 증빙 사진 첨부 후 실제 환불까지 2주 이상 걸릴 수 있으며, 부분 환불은 불가하고 전체 환불만 가능합니다. 이는 보장 처리기한이 아니므로 PM 승인 직전에 재확인합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-WASTE-04'::text, 'OFFICIAL'::text, 'BULKY_WASTE'::text, '매트리스 배출 수수료'::text, '공식 품목표의 매트리스 수수료는 1인용 매트 4,000원, 2인용 매트 6,000원, 3단 쇼파겸용 4,000원으로 표시됩니다.'::text, '["매트리스의 공식 품목·규격을 확인합니다.","해당 수수료로 공식 배출 절차를 진행합니다."]'::jsonb, '[]'::jsonb, NULL::text, '1인용 매트 4,000원; 2인용 매트 6,000원; 3단 쇼파겸용 4,000원'::text, '세종특별자치시시설관리공단'::text, '배출항목선택'::text, 'https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305'::text, '2026-07-18'::date, '프레임과 매트리스는 공식 품목표에서 별도 품목입니다. 품목표에 없는 물건은 유사 품목 수수료를 준용한다고만 안내되어 있으므로 정확한 적용은 공식 신청 화면 또는 시설관리공단에 확인합니다. 수수료는 PM 승인 직전에 재확인합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz),
        ('KB-WASTE-05'::text, 'OFFICIAL'::text, 'BULKY_WASTE'::text, '대형폐기물 배출요일·수거 문의'::text, '공식 안내는 지역 분류별 배출·수거 요일과 시설관리공단 문의 경로를 제공합니다. 동지역은 동별 수거요일이 달라질 수 있어 개별 일정을 다시 확인해야 합니다.'::text, '["주소의 지역 분류를 확인합니다.","공식 표의 배출요일에 맞춰 배출합니다.","당일 수거 여부나 동별 일정은 시설관리공단의 공식 문의 경로로 확인합니다."]'::jsonb, '[]'::jsonb, NULL::text, NULL::text, '세종특별자치시시설관리공단'::text, '배출신청안내'::text, 'https://www.sjwaste.kr/board?menuId=MENU00303&siteId=null'::text, '2026-07-18'::date, '동지역은 월·수 배출, 화·목 수거로 안내되나 동별 수거요일이 다를 수 있습니다. 읍면지역은 지역 분류에 따라 요일이 다르며, 당일 배출 즉시 당일 수거는 어렵습니다. 운영 사정과 실제 일정은 PM 승인 직전에 공식 안내로 재확인합니다.'::text, 'ACTIVE'::text, 'AI-DATA-BACKEND'::text, 'PM-LOCAL-001'::text, '2026-07-18T17:06:19Z'::timestamptz)
    ),
    expected_kb_question_examples (kb_public_id, question_example, normalized_text) AS (
      VALUES
        ('KB-CERT-01'::text, '등본과 초본은 무엇이 다른가요?'::text, NULL::text),
        ('KB-CERT-01'::text, '등본은 누구의 정보가 나오나요?'::text, NULL::text),
        ('KB-CERT-01'::text, '초본을 제출하라고 하는데 무엇을 확인해야 하나요?'::text, NULL::text),
        ('KB-CERT-02'::text, '등본 발급 수수료가 있나요?'::text, NULL::text),
        ('KB-CERT-02'::text, '등본을 온라인으로 받을 수 있나요?'::text, NULL::text),
        ('KB-CERT-02'::text, '주민등록등본은 어떻게 발급하나요?'::text, NULL::text),
        ('KB-CERT-03'::text, '주민등록초본은 어떻게 발급하나요?'::text, NULL::text),
        ('KB-CERT-03'::text, '초본 발급에 무엇이 필요한가요?'::text, NULL::text),
        ('KB-CERT-03'::text, '초본을 인터넷으로 발급받을 수 있나요?'::text, NULL::text),
        ('KB-CERT-04'::text, '열람과 등본 발급은 다른가요?'::text, NULL::text),
        ('KB-CERT-04'::text, '주민등록표 열람 수수료가 있나요?'::text, NULL::text),
        ('KB-CERT-04'::text, '주민등록표는 어떻게 열람하나요?'::text, NULL::text),
        ('KB-CERT-05'::text, '가까운 무인민원발급기는 어디서 찾나요?'::text, NULL::text),
        ('KB-CERT-05'::text, '무인발급기는 항상 이용할 수 있나요?'::text, NULL::text),
        ('KB-CERT-05'::text, '무인발급기에서 등본을 뽑을 수 있나요?'::text, NULL::text),
        ('KB-MOVE-01'::text, '이사했는데 전입신고는 어떻게 하나요?'::text, NULL::text),
        ('KB-MOVE-01'::text, '전입신고 수수료가 있나요?'::text, NULL::text),
        ('KB-MOVE-01'::text, '전입신고를 온라인으로 할 수 있나요?'::text, NULL::text),
        ('KB-MOVE-02'::text, '가족이 대신 전입신고할 수 있나요?'::text, NULL::text),
        ('KB-MOVE-02'::text, '대리인이 전입신고할 때 준비물이 있나요?'::text, NULL::text),
        ('KB-MOVE-02'::text, '전입신고를 방문해서 하려면 무엇이 필요한가요?'::text, NULL::text),
        ('KB-MOVE-03'::text, '대신 온라인 전입신고를 해줄 수 있나요?'::text, NULL::text),
        ('KB-MOVE-03'::text, '온라인 전입신고는 누가 할 수 있나요?'::text, NULL::text),
        ('KB-MOVE-03'::text, '해외에 있다가 돌아왔는데 온라인 전입신고가 되나요?'::text, NULL::text),
        ('KB-MOVE-04'::text, '전입신고 사실을 통보받을 수 있나요?'::text, NULL::text),
        ('KB-MOVE-04'::text, '주민등록 통보서비스는 온라인으로 신청할 수 있나요?'::text, NULL::text),
        ('KB-MOVE-04'::text, '주소 변경 통보서비스는 어떻게 신청하나요?'::text, NULL::text),
        ('KB-MOVE-05'::text, '이사 후 전입신고는 언제까지 해야 하나요?'::text, NULL::text),
        ('KB-MOVE-05'::text, '전입신고 기한을 놓치면 어떻게 되나요?'::text, NULL::text),
        ('KB-MOVE-05'::text, '전입신고 의무가 있는지 궁금해요.'::text, NULL::text),
        ('KB-TAX-01'::text, '전자납부번호로 납부할 수 있나요?'::text, NULL::text),
        ('KB-TAX-01'::text, '지방세 납부 내역을 확인하고 싶어요.'::text, NULL::text),
        ('KB-TAX-01'::text, '지방세를 온라인으로 어디에서 내나요?'::text, NULL::text),
        ('KB-TAX-02'::text, '자동차세 고지는 어디서 확인하나요?'::text, NULL::text),
        ('KB-TAX-02'::text, '자동차세 납부 상태를 확인하려면 어떻게 하나요?'::text, NULL::text),
        ('KB-TAX-02'::text, '자동차세를 온라인으로 내고 싶어요.'::text, NULL::text),
        ('KB-TAX-03'::text, '납세증명서 수수료가 있나요?'::text, NULL::text),
        ('KB-TAX-03'::text, '납세증명서를 온라인으로 신청할 수 있나요?'::text, NULL::text),
        ('KB-TAX-03'::text, '지방세 납세증명서는 어떻게 발급하나요?'::text, NULL::text),
        ('KB-TAX-04'::text, '세목별 과세증명서 수수료가 있나요?'::text, NULL::text),
        ('KB-TAX-04'::text, '세목별 과세증명서를 온라인으로 받을 수 있나요?'::text, NULL::text),
        ('KB-TAX-04'::text, '지방세 세목별 과세증명서는 어떻게 발급하나요?'::text, NULL::text),
        ('KB-TAX-05'::text, '납부확인서를 온라인으로 받을 수 있나요?'::text, NULL::text),
        ('KB-TAX-05'::text, '지방세 납부확인서 발급 수수료가 있나요?'::text, NULL::text),
        ('KB-TAX-05'::text, '지방세 납부확인서는 어떻게 발급하나요?'::text, NULL::text),
        ('KB-WASTE-01'::text, '대형폐기물 스티커는 어디서 받나요?'::text, NULL::text),
        ('KB-WASTE-01'::text, '대형폐기물은 어떻게 신청하나요?'::text, NULL::text),
        ('KB-WASTE-01'::text, '대형폐기물을 어디에 내놓아야 하나요?'::text, NULL::text),
        ('KB-WASTE-02'::text, '대형폐기물 스티커는 어떻게 출력하나요?'::text, NULL::text),
        ('KB-WASTE-02'::text, '대형폐기물 신청 후 결제는 어떻게 하나요?'::text, NULL::text),
        ('KB-WASTE-02'::text, '대형폐기물 신청을 취소하면 환불되나요?'::text, NULL::text),
        ('KB-WASTE-04'::text, '1인용 매트리스 수수료가 있나요?'::text, NULL::text),
        ('KB-WASTE-04'::text, '3단 쇼파겸용 매트리스 비용은 얼마인가요?'::text, NULL::text),
        ('KB-WASTE-04'::text, '매트리스는 버리는 데 얼마인가요?'::text, NULL::text),
        ('KB-WASTE-05'::text, '대형폐기물은 무슨 요일에 내놓나요?'::text, NULL::text),
        ('KB-WASTE-05'::text, '오늘 대형폐기물을 내면 수거되나요?'::text, NULL::text),
        ('KB-WASTE-05'::text, '우리 동의 대형폐기물 수거일을 알고 싶어요.'::text, NULL::text)
    ),
    expected_offices (public_id, data_origin, region, office_name, address, phone, opening_hours, map_url, source_title, source_url, last_verified_at) AS (
      VALUES
        ('OFFICE-AREUM'::text, 'OFFICIAL'::text, '아름동'::text, '아름동 행정복지센터'::text, '(30100) 세종특별자치시 보듬3로 114(아름동)'::text, '044-301-6300'::text, '평일 09:00~18:00'::text, 'https://place.map.kakao.com/26471721'::text, '아름동 행정복지센터 찾아오시는 길'::text, 'https://www.sejong.go.kr/areum/sub02_02.do?cmsNo=1461'::text, '2026-07-18'::date),
        ('OFFICE-DODAM'::text, 'OFFICIAL'::text, '도담동'::text, '도담동 행정복지센터'::text, '(30098) 세종특별자치시 보람로 77(도담동)'::text, '044-301-6200'::text, '평일 09:00~18:00'::text, 'https://place.map.kakao.com/23346315'::text, '도담동 행정복지센터 찾아오시는 길'::text, 'https://www.sejong.go.kr/dodam/sub02_02.do?cmsNo=1458'::text, '2026-07-18'::date),
        ('OFFICE-JOCHIWON'::text, 'OFFICIAL'::text, '조치원읍'::text, '북세종 통합 행정복지센터'::text, '(30024) 세종특별자치시 조치원읍 새내16길 17'::text, '044-301-5000'::text, '평일 09:00~18:00'::text, 'https://place.map.kakao.com/19342218'::text, '조치원읍 찾아오시는 길'::text, 'https://www.sejong.go.kr/jochiwon/sub02_02.do?cmsNo=1425'::text, '2026-07-18'::date)
    ),
    expected_office_service_mappings (office_public_id, intent, department_label) AS (
      VALUES
        ('OFFICE-AREUM'::text, 'BULKY_WASTE'::text, '안전도시과 환경경제'::text),
        ('OFFICE-AREUM'::text, 'CERTIFICATE_ISSUANCE'::text, '민원행정과 일반민원'::text),
        ('OFFICE-AREUM'::text, 'MOVE_IN_RESIDENT_REGISTRATION'::text, '민원행정과 일반민원'::text),
        ('OFFICE-DODAM'::text, 'CERTIFICATE_ISSUANCE'::text, '민원행정'::text),
        ('OFFICE-DODAM'::text, 'LOCAL_TAX_GENERAL'::text, '민원행정'::text),
        ('OFFICE-DODAM'::text, 'MOVE_IN_RESIDENT_REGISTRATION'::text, '민원행정'::text),
        ('OFFICE-JOCHIWON'::text, 'BULKY_WASTE'::text, '안전도시과 청소환경'::text),
        ('OFFICE-JOCHIWON'::text, 'CERTIFICATE_ISSUANCE'::text, '민원행정과 일반민원'::text),
        ('OFFICE-JOCHIWON'::text, 'LOCAL_TAX_GENERAL'::text, '민원행정과 세무부동산'::text),
        ('OFFICE-JOCHIWON'::text, 'MOVE_IN_RESIDENT_REGISTRATION'::text, '민원행정과 일반민원'::text)
    ),
    actual_kb_documents AS (
      SELECT
        kb.public_id,
        kb.data_origin::text AS data_origin,
        kb.category::text AS category,
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
        kb.status::text AS status,
        kb.created_by,
        kb.approved_by,
        kb.approved_at
      FROM app_private.kb_documents AS kb
    ),
    actual_kb_question_examples AS (
      SELECT
        kb.public_id AS kb_public_id,
        question.question_example,
        question.normalized_text
      FROM app_private.kb_question_examples AS question
      JOIN app_private.kb_documents AS kb ON kb.id = question.kb_document_id
    ),
    actual_offices AS (
      SELECT
        office.public_id,
        office.data_origin::text AS data_origin,
        office.region,
        office.office_name,
        office.address,
        office.phone,
        office.opening_hours,
        office.map_url,
        office.source_title,
        office.source_url,
        office.last_verified_at
      FROM app_private.offices AS office
    ),
    actual_office_service_mappings AS (
      SELECT
        office.public_id AS office_public_id,
        mapping.intent::text AS intent,
        mapping.department_label
      FROM app_private.office_service_mappings AS mapping
      JOIN app_private.offices AS office ON office.id = mapping.office_id
    )
  SELECT
    EXISTS (SELECT * FROM expected_kb_documents EXCEPT ALL SELECT * FROM actual_kb_documents)
    OR EXISTS (SELECT * FROM actual_kb_documents EXCEPT ALL SELECT * FROM expected_kb_documents)
    OR EXISTS (SELECT * FROM expected_kb_question_examples EXCEPT ALL SELECT * FROM actual_kb_question_examples)
    OR EXISTS (SELECT * FROM actual_kb_question_examples EXCEPT ALL SELECT * FROM expected_kb_question_examples)
    OR EXISTS (SELECT * FROM expected_offices EXCEPT ALL SELECT * FROM actual_offices)
    OR EXISTS (SELECT * FROM actual_offices EXCEPT ALL SELECT * FROM expected_offices)
    OR EXISTS (SELECT * FROM expected_office_service_mappings EXCEPT ALL SELECT * FROM actual_office_service_mappings)
    OR EXISTS (SELECT * FROM actual_office_service_mappings EXCEPT ALL SELECT * FROM expected_office_service_mappings)
  INTO v_mismatch;

  IF v_mismatch THEN
    RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'DATA_SEED_PROJECTION_MISMATCH';
  END IF;
END;
$data_seed_projection_guard$;

DO $data_seed_exclusion_guard$
BEGIN
  IF EXISTS (
       SELECT 1 FROM app_private.kb_documents
       WHERE public_id = 'KB-WASTE-03'
     )
     OR EXISTS (
       SELECT 1
       FROM app_private.office_service_mappings AS mapping
       JOIN app_private.offices AS office ON office.id = mapping.office_id
       WHERE (office.public_id, mapping.intent::text) IN (
         ('OFFICE-AREUM', 'LOCAL_TAX_GENERAL'),
         ('OFFICE-DODAM', 'BULKY_WASTE')
       )
     )
     OR EXISTS (
       SELECT 1 FROM app_private.kb_documents WHERE data_origin::text = 'MOCK'
     )
     OR EXISTS (
       SELECT 1 FROM app_private.offices WHERE data_origin::text = 'MOCK'
     ) THEN
    RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'DATA_SEED_EXCLUSION_FAILED';
  END IF;
END;
$data_seed_exclusion_guard$;

COMMIT;
