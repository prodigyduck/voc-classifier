-- VOC Classifier DB Schema
-- 별도 스키마 생성 (todo app과 테이블 겹침 방지)
CREATE SCHEMA IF NOT EXISTS voc_classifier;

-- 카테고리 테이블 (고정 카테고리 + AI가 생성한 동적 카테고리)
CREATE TABLE voc_classifier.categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    is_ai_generated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- VOC 테이블
CREATE TABLE voc_classifier.vocs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category_id INTEGER REFERENCES voc_classifier.categories(id),
    ai_suggested_category_id INTEGER REFERENCES voc_classifier.categories(id),  -- AI가 제안한 카테고리
    confidence_score DECIMAL(5,4),  -- 분류 신뢰도 (0.0 ~ 1.0)
    status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, ANALYZED, RESOLVED, REJECTED
    priority VARCHAR(20) DEFAULT 'MEDIUM',  -- LOW, MEDIUM, HIGH, CRITICAL
    submitted_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    ui_related BOOLEAN DEFAULT FALSE,  -- UI 개선으로 해결 가능한지 여부
    ui_improvement_action TEXT  -- UI 개선 활동 내용
);

-- UI 개선 활동 테이블
CREATE TABLE voc_classifier.ui_improvements (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    related_categories INTEGER[],  -- 관련 카테고리 ID 배열
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'IN_PROGRESS'  -- PLANNED, IN_PROGRESS, COMPLETED
);

-- UI 개선 전후 VOC 수 추적 테이블
CREATE TABLE voc_classifier.voc_tracking (
    id SERIAL PRIMARY KEY,
    ui_improvement_id INTEGER REFERENCES voc_classifier.ui_improvements(id),
    category_id INTEGER REFERENCES voc_classifier.categories(id),
    voc_count_before INTEGER NOT NULL,
    voc_count_after INTEGER,
    reduction_rate DECIMAL(5,4),  -- 감소율 (0.0 ~ 1.0)
    tracking_date DATE NOT NULL DEFAULT CURRENT_DATE
);

-- 토픽 모델링 결과 테이블 (BERTopic 결과 저장)
CREATE TABLE voc_classifier.topic_results (
    id SERIAL PRIMARY KEY,
    voc_id INTEGER REFERENCES voc_classifier.vocs(id),
    topic_id INTEGER,
    topic_name TEXT,
    probability DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_vocs_category ON voc_classifier.vocs(category_id);
CREATE INDEX idx_vocs_status ON voc_classifier.vocs(status);
CREATE INDEX idx_vocs_created_at ON voc_classifier.vocs(created_at);
CREATE INDEX idx_voc_tracking_improvement ON voc_classifier.voc_tracking(ui_improvement_id);
CREATE INDEX idx_topic_results_voc ON voc_classifier.topic_results(voc_id);

-- 초기 고정 카테고리 데이터
INSERT INTO voc_classifier.categories (name, description, is_ai_generated) VALUES
('버그', '시스템 오류 및 버그 보고', FALSE),
('UI/UX', '사용자 인터페이스 및 경험 관련', FALSE),
('기능 요청', '새로운 기능 추가 요청', FALSE),
('성능', '시스템 성능 및 속도 관련', FALSE),
('데이터', '데이터 처리 및 저장 관련', FALSE),
('보안', '보안 및 권한 관련', FALSE),
('기타', '그 외 기타 문의', FALSE);
