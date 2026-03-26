# VOC Classifier

VOC(Voice of Customer)를 BERTopic 기반 AI로 자동 분류하고 분석하는 시스템입니다.

## 기능

- 📊 VOC 수집 및 관리
- 🤖 BERTopic 기반 자동 분류 (AI 추천 카테고리)
- 📈 분석 및 시각화 대시보드
- 📉 카테고리별 트렌드 분석
- 🎯 분류 신뢰도 통계

## 기술 스택

| 구분 | 기술 |
|------|------|
| 백엔드 | FastAPI, SQLAlchemy |
| 프론트엔드 | Streamlit |
| ML 모델 | BERTopic, sentence-transformers |
| 데이터베이스 | PostgreSQL |

## 설치 가이드

### 1. 저장소 클론

```bash
git clone https://github.com/prodigyduck/voc-classifier.git
cd voc-classifier
```

### 2. 가상환경 생성 및 활성화

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 데이터베이스 설정

PostgreSQL 데이터베이스가 이미 실행 중이라고 가정합니다.

`config.yaml` 파일을 프로젝트 루트에 생성하고 DB 연결 정보를 입력하세요:

```yaml
# Database Configuration
database:
  host: localhost
  port: 5432
  name: your_database_name
  schema: voc_classifier
  user: your_username
  password: your_password

# BERTopic Configuration
bertopic:
  language: korean
  model_name: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
  min_topic_size: 10
  nr_topics: null
  calculate_probabilities: true

# Application Configuration
app:
  name: VOC Classifier
  version: 1.0.0
  debug: true

# AI Classification Settings
classification:
  auto_classify: true
  confidence_threshold: 0.6
  suggest_new_categories: true
```

### 5. 테이블 생성

```bash
python sql/create_tables.py
```

### 6. 샘플 데이터 생성 (선택사항)

```bash
python sql/insert_sample_data.py
```

## 실행 방법

### 백엔드 실행

```bash
# 가상환경 활성화 후
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

- API 서버: http://localhost:8000
- API 문서: http://localhost:8000/docs

### 프론트엔드 실행

```bash
# 가상환경 활성화 후
streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501
```

- 대시보드: http://localhost:8501

## 사용법

### 1. 모델 학습

대시보드의 **"분류 모델"** 메뉴에서 **"모델 학습"** 버튼을 클릭합니다.

또는 API 호출:
```bash
curl -X POST http://localhost:8000/api/v1/classification/train
```

### 2. VOC 분류

**"분류 실행"** 버튼을 클릭하면 미분류 VOC를 AI가 자동 분류합니다.

또는 API 호출:
```bash
curl -X POST "http://localhost:8000/api/v1/classification/classify-batch?limit=100"
```

### 3. 대시보드 확인

- 총 VOC 건수
- AI 분류 완료 건수
- 카테고리별 분포
- AI 추천 카테고리별 분포
- 월별 트렌드
- AI 분류 결과 트렌드
- 분류 신뢰도 분포

## AI 분류 방식

```
VOC 텍스트 → BERTopic 토픽 분류 → 키워드 추출 → 카테고리 매핑
```

| 단계 | 설명 |
|------|------|
| 임베딩 | sentence-transformers로 문서 벡터화 |
| 클러스터링 | BERTopic으로 유사 문서 그룹화 |
| 토픽 생성 | 각 그룹의 대표 키워드 추출 |
| 카테고리 매핑 | 키워드 기반 카테고리 추천 |

### 카테고리 매핑 규칙

| 키워드 | 카테고리 |
|--------|----------|
| 느림, 지연, 속도, 로딩 | 성능 |
| 화면, 버튼, 메뉴, 인터페이스 | UI/UX |
| 에러, 오류, 실패, 버그 | 버그 |
| 데이터, 저장, 검색 | 데이터 |
| 로그인, 권한, 인증, 보안 | 보안 |
| 기능, 추가, 요청 | 기능 요청 |

## 프로젝트 구조

```
voc-classifier/
├── backend/
│   ├── api/                 # API 라우터
│   │   ├── analytics.py     # 분석 API
│   │   ├── classification.py # 분류 API
│   │   ├── voc.py           # VOC 관리 API
│   │   └── categories.py    # 카테고리 API
│   ├── database/            # DB 연결 설정
│   │   └── db.py
│   ├── ml/                  # ML 분류 모델
│   │   └── classifier.py    # BERTopic 분류기
│   └── models/              # 데이터 모델
│       ├── models.py        # SQLAlchemy 모델
│       └── schemas.py       # Pydantic 스키마
├── frontend/
│   ├── app.py               # Streamlit 대시보드
│   └── i18n.py              # 다국어 지원
├── sql/
│   ├── schema.sql           # DB 스키마
│   ├── create_tables.py     # 테이블 생성 스크립트
│   └── insert_sample_data.py # 샘플 데이터 생성
├── models/                  # 학습된 모델 저장 (자동 생성)
├── config.yaml              # 설정 파일 (직접 생성 필요)
├── requirements.txt         # Python 의존성
└── README.md
```

## API 엔드포인트

### 분석
- `GET /api/v1/analytics/overview` - 대시보드 분석 데이터

### 분류
- `POST /api/v1/classification/train` - 모델 학습
- `POST /api/v1/classification/classify-batch` - 일괄 분류
- `GET /api/v1/classification/topics` - 토픽 정보 조회

### VOC 관리
- `GET /api/v1/vocs` - VOC 목록 조회
- `POST /api/v1/vocs` - VOC 생성

### 카테고리
- `GET /api/v1/categories` - 카테고리 목록 조회

## 라이선스

MIT License
