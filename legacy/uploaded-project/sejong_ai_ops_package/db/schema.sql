-- PostgreSQL schema draft for Sejong AI Civil Service Platform

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name_ko VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE civil_services (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES categories(id),
    service_code VARCHAR(80) UNIQUE NOT NULL,
    service_name VARCHAR(150) NOT NULL,
    summary TEXT,
    default_department VARCHAR(150),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE kb_documents (
    id SERIAL PRIMARY KEY,
    kb_id VARCHAR(50) UNIQUE NOT NULL,
    service_code VARCHAR(80),
    title VARCHAR(250) NOT NULL,
    content TEXT NOT NULL,
    source_title VARCHAR(250),
    source_url TEXT,
    last_updated DATE,
    confidence_level VARCHAR(20) DEFAULT 'normal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE kb_chunks (
    id SERIAL PRIMARY KEY,
    kb_document_id INTEGER REFERENCES kb_documents(id),
    chunk_text TEXT NOT NULL,
    keywords TEXT,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE offices (
    id SERIAL PRIMARY KEY,
    office_code VARCHAR(50) UNIQUE NOT NULL,
    office_name VARCHAR(200) NOT NULL,
    office_type VARCHAR(50),
    area_name VARCHAR(100),
    address TEXT,
    phone VARCHAR(50),
    opening_hours VARCHAR(200),
    lat NUMERIC(10, 7),
    lng NUMERIC(10, 7),
    services TEXT
);

CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_area VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,
    question_masked TEXT,
    answer_text TEXT,
    intent VARCHAR(80),
    answer_status VARCHAR(30),
    fallback_reason VARCHAR(80),
    source_count INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    pii_detected BOOLEAN DEFAULT FALSE,
    office_routed VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE failed_questions (
    id SERIAL PRIMARY KEY,
    question_masked TEXT NOT NULL,
    estimated_intent VARCHAR(80),
    failure_reason VARCHAR(80),
    recommended_action TEXT,
    related_count INTEGER DEFAULT 1,
    priority_score NUMERIC(5,2) DEFAULT 0,
    status VARCHAR(30) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE kb_recommendations (
    id SERIAL PRIMARY KEY,
    title VARCHAR(250) NOT NULL,
    estimated_intent VARCHAR(80),
    reason TEXT,
    related_questions_count INTEGER DEFAULT 0,
    failure_rate NUMERIC(5,2),
    growth_rate NUMERIC(5,2),
    priority_score NUMERIC(5,2),
    recommended_action TEXT,
    status VARCHAR(30) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mock_status_cases (
    id SERIAL PRIMARY KEY,
    receipt_no VARCHAR(50) UNIQUE NOT NULL,
    service_name VARCHAR(150),
    status VARCHAR(50),
    department VARCHAR(150),
    next_step TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE evaluation_cases (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    expected_intent VARCHAR(80),
    expected_behavior VARCHAR(80),
    expected_keywords TEXT,
    case_type VARCHAR(50)
);

CREATE TABLE evaluation_results (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(80),
    evaluation_case_id INTEGER REFERENCES evaluation_cases(id),
    actual_intent VARCHAR(80),
    answer_status VARCHAR(50),
    is_correct BOOLEAN,
    has_source BOOLEAN,
    response_time_ms INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
