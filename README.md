# VOC Classifier

제조시스템 UI에서 발생하는 VOC(Voice of Customer)를 BERTopic을 사용하여 자동 분류하고 분석하는 시스템입니다. UI 개선 활동으로 인한 VOC 감소율을 추적하여 시스템 개선을 지원합니다.

## 기능

- 📊 VOC 수집 및 관리
- 🤖 BERTopic 기반 자동 분류
- 📈 분석 및 시각화 대시보드
- 🔧 UI 개선 활동 추적
- 📉 VOC 감소율 분석
- 💻 CLI 툴 지원

## 기술 스택

- **백엔드**: FastAPI, SQLAlchemy, PostgreSQL
- **프론트엔드**: Streamlit
- **ML 모델**: BERTopic (sentence-transformers)
- **데이터베이스**: PostgreSQL (별도 스키마: voc_classifier)

## 설치

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 데이터베이스 설정

PostgreSQL 데이터베이스가 실행 중이어야 합니다. 기존 `config.yaml`에서 연결 정보를 확인하세요:

```yaml
database:
  host: localhost
  port: 5432
  name: todoapp
  schema: voc_classifier
  user: todoapp
  password: password
```

### 3. 테이블 생성

```bash
python3 sql/create_tables.py
```

### 4. 샘플 데이터 생성 (선택사항)

```bash
python3 sql/insert_sample_data.py
```

## 사용법

### 백엔드 실행

```bash
python3 backend/main.py
```

백엔드는 `http://localhost:8000`에서 실행됩니다.
API 문서: `http://localhost:8000/docs`

### 프론트엔드 실행

```bash
streamlit run frontend/app.py
```

프론트엔드는 `http://localhost:8501`에서 실행됩니다.

### CLI 사용법

```bash
# VOC 생성
python3 voc_cli.py create --title "화면 로딩이 느립니다" --content "대시보드 로딩이 너무 느려서 개선이 필요합니다." --priority HIGH --submitted-by "김관리" --ui-related

# VOC 목록 조회
python3 voc_cli.py list --status PENDING --limit 10

# 분류 모델 학습
python3 voc_cli.py train

# VOC 분류 (단일)
python3 voc_cli.py classify --voc-id 1

# VOC 일괄 분류
python3 voc_cli.py classify --batch --limit 100

# 분석 데이터 조회
python3 voc_cli.py analytics
```

## API 엔드포인트

### VOC 관리
- `GET /api/v1/vocs` - VOC 목록 조회
- `POST /api/v1/vocs` - VOC 생성
- `GET /api/v1/vocs/{voc_id}` - VOC 상세 조회
- `PUT /api/v1/vocs/{voc_id}` - VOC 수정
- `DELETE /api/v1/vocs/{voc_id}` - VOC 삭제
- `POST /api/v1/vocs/{voc_id}/resolve` - VOC 해결 처리

### 카테고리 관리
- `GET /api/v1/categories` - 카테고리 목록 조회
- `POST /api/v1/categories` - 카테고리 생성
- `GET /api/v1/categories/{category_id}` - 카테고리 상세 조회
- `DELETE /api/v1/categories/{category_id}` - 카테고리 삭제

### 분류
- `POST /api/v1/classification/train` - 모델 학습
- `POST /api/v1/classification/classify/{voc_id}` - 단일 VOC 분류
- `POST /api/v1/classification/classify-batch` - 일괄 분류
- `GET /api/v1/classification/topics` - 토픽 정보 조회

### 분석
- `GET /api/v1/analytics/overview` - 분석 개요 조회

### UI 개선 추적
- `GET /api/v1/ui-improvements` - UI 개선 활동 목록 조회
- `POST /api/v1/ui-improvements` - UI 개선 활동 생성
- `POST /api/v1/ui-improvements/{improvement_id}/track` - 감소율 추적
- `PUT /api/v1/ui-improvements/{improvement_id}/complete` - UI 개선 완료 처리

## 프로젝트 구조

```
vocClaasifier/
├── backend/
│   ├── api/              # API 라우터
│   ├── database/         # DB 연결 설정
│   ├── ml/             # ML 분류 모델
│   └── models/         # 데이터 모델
├── frontend/
│   └── app.py         # Streamlit 앱
├── sql/              # SQL 스크립트
│   ├── schema.sql
│   ├── create_tables.py
│   └── insert_sample_data.py
├── config.yaml       # 설정 파일
├── requirements.txt   # 의존성
├── voc_cli.py       # CLI 툴
└── README.md
```

## 카테고리

- **버그**: 시스템 오류 및 버그 보고
- **UI/UX**: 사용자 인터페이스 및 경험 관련
- **기능 요청**: 새로운 기능 추가 요청
- **성능**: 시스템 성능 및 속도 관련
- **데이터**: 데이터 처리 및 저장 관련
- **보안**: 보안 및 권한 관련
- **기타**: 그 외 기타 문의

## 개발 계획

- [x] 프로젝트 구조 설계
- [x] DB 스키마 설계 및 생성
- [x] 백엔드 API 구현
- [x] BERTopic 분류 모델 통합
- [x] Streamlit 프론트엔드 구현
- [x] CLI 툴 개발
- [ ] UI 개선 활동별 감소율 시각화 고도화
- [ ] 실시간 VOC 모니터링 대시보드
- [ ] 알림 시스템 통합
- [ ] 다국어 지원 확장

## 라이선스

MIT License

## 기여

이 프로젝트에 기여하고 싶으시다면 Pull Request를 제출해주세요.
