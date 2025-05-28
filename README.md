# Stock Pattern Viewer

주식 패턴을 분석하고 시각화하는 웹 애플리케이션입니다.

## 기술 스택

- Frontend: Vue 3
- Backend: FastAPI
- Database: SQLite
- Data Source: yfinance

## 프로젝트 구조

```
.
├── WebAPI/          # FastAPI 백엔드
├── DB/              # SQLite 데이터베이스 파일
└── stock-pattern-viewer/  # Vue.js 프론트엔드
```

## 설치 및 실행 방법

### 백엔드 설정

1. Python 패키지 설치:
```bash
pip install fastapi uvicorn yfinance
```

2. FastAPI 서버 실행:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 프론트엔드 설정

1. Node.js 18 이상 설치

2. 의존성 설치:
```bash
cd stock-pattern-viewer
npm install
```

3. 개발 서버 실행:
```bash
npm run dev
```

## API 엔드포인트

- `/api/collect-stocks`: 수집된 주식 목록
- `/api/anomalous-stocks`: 이상 패턴 주식 목록
- `/api/suspect-stocks`: 의심 주식 목록
- `/api/collect-stock-data/{stock_code}`: 특정 주식의 상세 데이터 