-- Final-scope logical draft v0.2.0. Convert to versioned migrations after tool selection.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE intent_code AS ENUM (
  'MOVE_IN_RESIDENT_REGISTRATION', 'CERTIFICATE_ISSUANCE',
  'BULKY_WASTE', 'LOCAL_TAX_GENERAL', 'OUT_OF_SCOPE', 'UNKNOWN'
);
CREATE TYPE answer_status AS ENUM ('SUCCESS', 'FOLLOWUP', 'FALLBACK', 'SYSTEM_ERROR');
CREATE TYPE fallback_reason AS ENUM ('INSUFFICIENT_GROUNDING', 'PERSONAL_LOOKUP', 'LEGAL_JUDGMENT', 'OUT_OF_SCOPE');
CREATE TYPE kb_status AS ENUM ('DRAFT', 'PENDING', 'ACTIVE', 'REJECTED', 'RETIRED');
CREATE TYPE candidate_status AS ENUM ('NEW', 'REASON_CONFIRMED', 'DRAFTED', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED');
CREATE TYPE admin_role AS ENUM ('OPERATOR', 'APPROVER');

CREATE TABLE kb_documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  public_id text UNIQUE NOT NULL,
  category intent_code NOT NULL CHECK (category NOT IN ('OUT_OF_SCOPE', 'UNKNOWN')),
  service_name text NOT NULL,
  answer_summary text NOT NULL,
  procedure_steps jsonb NOT NULL DEFAULT '[]'::jsonb,
  required_documents jsonb NOT NULL DEFAULT '[]'::jsonb,
  processing_time text,
  fee text,
  department text NOT NULL,
  source_title text NOT NULL,
  source_url text NOT NULL,
  last_verified_at date NOT NULL,
  caution text,
  status kb_status NOT NULL DEFAULT 'DRAFT',
  created_by text NOT NULL,
  approved_by text,
  approved_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK ((status <> 'ACTIVE') OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)),
  CHECK (approved_by IS NULL OR approved_by <> created_by)
);

CREATE TABLE kb_question_examples (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kb_document_id uuid NOT NULL REFERENCES kb_documents(id) ON DELETE CASCADE,
  question_example text NOT NULL,
  normalized_text text,
  UNIQUE (kb_document_id, question_example)
);

CREATE TABLE offices (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  public_id text UNIQUE NOT NULL,
  region text NOT NULL CHECK (region IN ('아름동', '도담동', '조치원읍')),
  office_name text NOT NULL,
  address text NOT NULL,
  phone text NOT NULL,
  opening_hours text,
  map_url text,
  source_title text NOT NULL,
  source_url text NOT NULL,
  last_verified_at date NOT NULL,
  is_official boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE office_service_mappings (
  office_id uuid NOT NULL REFERENCES offices(id) ON DELETE CASCADE,
  intent intent_code NOT NULL CHECK (intent NOT IN ('OUT_OF_SCOPE', 'UNKNOWN')),
  department_label text,
  PRIMARY KEY (office_id, intent)
);

-- Contains no user question or answer text.
CREATE TABLE interaction_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  occurred_at timestamptz NOT NULL DEFAULT now(),
  intent intent_code NOT NULL,
  answer_status answer_status NOT NULL,
  fallback_reason fallback_reason,
  source_count integer NOT NULL DEFAULT 0 CHECK (source_count >= 0),
  used_source_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  response_time_ms integer NOT NULL CHECK (response_time_ms >= 0),
  selected_region text,
  routed_office_id uuid REFERENCES offices(id),
  is_test boolean NOT NULL DEFAULT false,
  request_id uuid NOT NULL UNIQUE,
  CHECK ((answer_status = 'FALLBACK') = (fallback_reason IS NOT NULL))
);

CREATE TABLE failed_questions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  interaction_event_id uuid NOT NULL UNIQUE REFERENCES interaction_events(id) ON DELETE RESTRICT,
  masked_question text,
  intent intent_code NOT NULL CHECK (intent NOT IN ('OUT_OF_SCOPE', 'UNKNOWN')),
  fallback_reason fallback_reason NOT NULL,
  candidate_eligible boolean NOT NULL,
  status candidate_status NOT NULL DEFAULT 'NEW',
  created_at timestamptz NOT NULL DEFAULT now(),
  text_expires_at timestamptz NOT NULL DEFAULT (now() + interval '30 days'),
  text_purged_at timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (candidate_eligible = (fallback_reason = 'INSUFFICIENT_GROUNDING')),
  CHECK (fallback_reason <> 'OUT_OF_SCOPE'),
  CHECK (text_expires_at = created_at + interval '30 days'),
  CHECK (
    (masked_question IS NOT NULL AND text_purged_at IS NULL)
    OR
    (masked_question IS NULL AND text_purged_at IS NOT NULL AND text_purged_at >= text_expires_at)
  )
);

CREATE TABLE kb_candidates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  failed_question_id uuid NOT NULL UNIQUE REFERENCES failed_questions(id) ON DELETE RESTRICT,
  title text NOT NULL,
  representative_question text NOT NULL,
  category intent_code NOT NULL CHECK (category NOT IN ('OUT_OF_SCOPE', 'UNKNOWN')),
  answer_summary text NOT NULL,
  procedure_steps jsonb NOT NULL DEFAULT '[]'::jsonb,
  required_documents jsonb NOT NULL DEFAULT '[]'::jsonb,
  processing_time text,
  fee text,
  department text NOT NULL,
  source_title text NOT NULL,
  source_url text NOT NULL,
  last_verified_at date NOT NULL,
  caution text,
  created_by text NOT NULL,
  review_status candidate_status NOT NULL DEFAULT 'DRAFTED',
  reviewed_by text,
  review_comment text,
  approved_at timestamptz,
  activated_kb_id uuid UNIQUE REFERENCES kb_documents(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (reviewed_by IS NULL OR reviewed_by <> created_by),
  CHECK ((review_status <> 'APPROVED') OR (reviewed_by IS NOT NULL AND approved_at IS NOT NULL AND activated_kb_id IS NOT NULL))
);

-- Minimal audit metadata only; do not store question/answer snapshots.
CREATE TABLE audit_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id text NOT NULL,
  actor_role admin_role NOT NULL,
  action text NOT NULL,
  target_type text NOT NULL,
  target_id uuid NOT NULL,
  old_status text,
  new_status text,
  changed_field_names jsonb NOT NULL DEFAULT '[]'::jsonb,
  review_comment text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_kb_active_category ON kb_documents (category) WHERE status = 'ACTIVE';
CREATE INDEX idx_events_occurred ON interaction_events (occurred_at DESC);
CREATE INDEX idx_failures_status ON failed_questions (status, fallback_reason);
CREATE INDEX idx_failure_text_expiry ON failed_questions (text_expires_at) WHERE masked_question IS NOT NULL;
CREATE INDEX idx_candidates_status ON kb_candidates (review_status);
