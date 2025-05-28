# K-Stock Pattern Insight 시스템

주식 데이터 수집 및 조작 의심 패턴 분석을 위한 모듈화된 시스템입니다.

## 📁 파일 구조

```
PythonCode/
├── stock_scrap.py          # 📊 데이터 수집 전용 모듈
├── pattern_analyzer.py     # 🎯 패턴 분석 전용 모듈
├── analyze_patterns.py     # 🔍 패턴 분석 실행 스크립트
└── README.md              # 📖 사용법 가이드
```

## 🚀 사용법

### 1단계: 데이터 수집

```bash
python stock_scrap.py
```

- **기능**: 주식 데이터 수집 및 CSV 파일 생성
- **수집 데이터**: 3년치 종합 주식 데이터 (OHLCV, 시가총액, 재무정보, 투자자별 거래량, 공매도 등)
- **출력**: `Result/종목명_종목코드.csv` 형식의 파일들

### 2단계: 패턴 분석

```bash
python analyze_patterns.py
```

- **기능**: 수집된 CSV 데이터의 조작 의심 패턴 분석
- **분석 항목**: 급등락, 거래량 이상, 상하한가, 회전율, 공매도 비중
- **출력**: 위험도 등급 (NORMAL → LOW → MEDIUM → HIGH) 및 상세 분석 결과

## 📊 모듈 설명

### StockDataCollector (stock_scrap.py)

**데이터 수집 전용 클래스**

주요 메서드:

- `get_stock_code()`: 종목명으로 종목코드 조회
- `collect_basic_data()`: 기본 주가 데이터 수집
- `collect_market_cap_data()`: 시가총액 데이터 수집
- `collect_fundamental_data()`: 재무정보 수집
- `collect_trading_volume_by_investor()`: 투자자별 거래량 수집
- `collect_shorting_data()`: 공매도 데이터 수집
- `collect_comprehensive_data()`: 종합 데이터 수집 및 병합
- `save_data_to_csv()`: CSV 파일 저장

### StockPatternAnalyzer (pattern_analyzer.py)

**패턴 분석 전용 클래스**

주요 메서드:

- `analyze_manipulation_patterns()`: 조작 의심 패턴 분석
- `detect_suspicious_patterns()`: 위험도 평가 및 경고 생성
- `analyze_stock_data()`: 종합 분석 수행
- `print_analysis_result()`: 분석 결과 출력
- `generate_summary_report()`: 종합 리포트 생성

## 🎯 분석 기준

### 위험도 등급

- **🔴 HIGH RISK** (8점 이상): 매우 위험한 패턴 감지
- **🟡 MEDIUM RISK** (5-7점): 주의 필요한 패턴 감지
- **🟢 LOW RISK** (2-4점): 경미한 이상 패턴 감지
- **✅ NORMAL** (0-1점): 정상 패턴

### 분석 항목

1. **급등락 패턴**: 15% 이상 급등/급락 빈도
2. **거래량 이상**: 평균 + 3σ 이상 거래량 급증
3. **상하한가**: 29.5% 이상/이하 등락률 빈도
4. **회전율**: 시가총액 대비 거래대금 비율
5. **공매도**: 공매도 잔고 및 비중 분석

## 📈 데이터 소스

- **pykrx**: 한국거래소 데이터 API
- **수집 기간**: 최근 3년
- **수집 종목**: DB 등록 종목 + 주요 대형주 (삼성전자, LG에너지솔루션, SK하이닉스)

## 📁 출력 파일

### CSV 데이터 파일

- **위치**: `Result/종목명_종목코드.csv`
- **형식**: 날짜별 시계열 데이터
- **컬럼**: 20개 지표 (주가, 거래량, 시가총액, 재무정보 등)

### 분석 결과 파일

- **위치**: `Result/pattern_analysis_results_YYYYMMDD_HHMMSS.json`
- **내용**: 종합 분석 결과 및 위험도 평가

## 🔧 의존성

```bash
pip install pykrx pandas numpy
```

## 💡 사용 팁

1. **데이터 수집 주기**: 주 1회 정도 실행 권장
2. **분석 결과 활용**: MEDIUM/HIGH RISK 종목은 추가 정밀 분석 필요
3. **API 제한**: pykrx API 호출 간격 조절로 안정성 확보
4. **데이터 품질**: 공매도 데이터는 일부 종목에서 누락 가능

## 🚨 주의사항

- 본 시스템은 **참고용**이며 투자 결정의 유일한 근거로 사용하지 마세요
- 패턴 분석 결과는 **의심 신호**일 뿐 확정적 판단이 아닙니다
- 실제 투자 시에는 **다양한 요소**를 종합적으로 고려하세요
