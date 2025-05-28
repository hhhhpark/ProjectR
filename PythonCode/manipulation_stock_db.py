import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import logging
from stock_scrap import StockDataCollector
import json
import os
import numpy as np

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ManipulationStockDB:
    def __init__(self, db_path="manipulation_stocks.db"):
        self.db_path = db_path
        self.collector = StockDataCollector()
        self.init_database()
        
    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 작전주 마스터 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS manipulation_stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_name TEXT NOT NULL,
                    stock_code TEXT,
                    category TEXT,
                    manipulation_period TEXT,
                    max_rise_rate REAL,
                    manipulation_type TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 작전주 일별 데이터 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_daily_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open_price REAL,
                    high_price REAL,
                    low_price REAL,
                    close_price REAL,
                    volume INTEGER,
                    change_rate REAL,
                    market_cap REAL,
                    trading_value REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stock_code, date)
                )
            ''')
            
            # 패턴 분석 결과 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pattern_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    analysis_date TEXT NOT NULL,
                    risk_score INTEGER,
                    risk_level TEXT,
                    warnings TEXT,
                    patterns TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("데이터베이스 초기화 완료")
            
        except Exception as e:
            logger.error(f"데이터베이스 초기화 오류: {str(e)}")

    def get_known_manipulation_stocks(self):
        """알려진 작전주/세력주 리스트를 반환합니다."""
        known_stocks = [
            {
                "stock_name": "넥스트사이언스",
                "category": "바이오",
                "manipulation_period": "2020-2021",
                "max_rise_rate": 2000.0,
                "manipulation_type": "급등형",
                "description": "코로나19 치료제 관련 급등 후 급락"
            },
            {
                "stock_name": "에이치엘비",
                "category": "바이오",
                "manipulation_period": "2020-2021",
                "max_rise_rate": 1500.0,
                "manipulation_type": "급등형",
                "description": "코로나19 백신 관련 테마주 급등락"
            },
            {
                "stock_name": "셀트리온제약",
                "category": "바이오",
                "manipulation_period": "2020",
                "max_rise_rate": 800.0,
                "manipulation_type": "테마형",
                "description": "코로나19 치료제 기대감 급등"
            },
            {
                "stock_name": "진원생명과학",
                "category": "바이오",
                "manipulation_period": "2020",
                "max_rise_rate": 1200.0,
                "manipulation_type": "급등형",
                "description": "코로나19 진단키트 관련 급등락"
            },
            {
                "stock_name": "씨젠",
                "category": "바이오",
                "manipulation_period": "2020",
                "max_rise_rate": 600.0,
                "manipulation_type": "테마형",
                "description": "코로나19 진단키트 실제 수혜주"
            },
            {
                "stock_name": "카카오게임즈",
                "category": "게임",
                "manipulation_period": "2020-2021",
                "max_rise_rate": 400.0,
                "manipulation_type": "공모주형",
                "description": "게임 테마 및 공모주 열풍"
            },
            {
                "stock_name": "빅히트",
                "category": "엔터테인먼트",
                "manipulation_period": "2020",
                "max_rise_rate": 300.0,
                "manipulation_type": "공모주형",
                "description": "BTS 관련 공모주 열풍"
            },
            {
                "stock_name": "SK바이오팜",
                "category": "바이오",
                "manipulation_period": "2020",
                "max_rise_rate": 500.0,
                "manipulation_type": "공모주형",
                "description": "신약개발 기대감 공모주"
            },
            {
                "stock_name": "메디톡스",
                "category": "바이오",
                "manipulation_period": "2019-2020",
                "max_rise_rate": 1000.0,
                "manipulation_type": "급등형",
                "description": "보톡스 관련 급등 후 급락"
            },
            {
                "stock_name": "코오롱생명과학",
                "category": "바이오",
                "manipulation_period": "2019",
                "max_rise_rate": 800.0,
                "manipulation_type": "테마형",
                "description": "인보사 관련 급등락"
            },
            {
                "stock_name": "셀리버리",
                "category": "바이오",
                "manipulation_period": "2021",
                "max_rise_rate": 600.0,
                "manipulation_type": "급등형",
                "description": "CAR-T 세포치료제 테마"
            },
            {
                "stock_name": "와이지엔터테인먼트",
                "category": "엔터테인먼트",
                "manipulation_period": "2020-2021",
                "max_rise_rate": 400.0,
                "manipulation_type": "테마형",
                "description": "K-POP 열풍 관련"
            }
        ]
        return known_stocks

    def register_manipulation_stocks(self):
        """알려진 작전주들을 DB에 등록합니다."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stocks = self.get_known_manipulation_stocks()
            registered_count = 0
            
            for stock_info in stocks:
                # 종목코드 조회
                stock_code = self.collector.get_stock_code(stock_info["stock_name"])
                
                # 중복 체크
                cursor.execute(
                    "SELECT COUNT(*) FROM manipulation_stocks WHERE stock_name = ?",
                    (stock_info["stock_name"],)
                )
                
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                        INSERT INTO manipulation_stocks 
                        (stock_name, stock_code, category, manipulation_period, 
                         max_rise_rate, manipulation_type, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        stock_info["stock_name"],
                        stock_code,
                        stock_info["category"],
                        stock_info["manipulation_period"],
                        stock_info["max_rise_rate"],
                        stock_info["manipulation_type"],
                        stock_info["description"]
                    ))
                    registered_count += 1
                    logger.info(f"등록: {stock_info['stock_name']} ({stock_code})")
                else:
                    logger.info(f"이미 등록된 종목: {stock_info['stock_name']}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"작전주 DB 등록 완료: {registered_count}개 종목")
            return registered_count
            
        except Exception as e:
            logger.error(f"작전주 등록 오류: {str(e)}")
            return 0

    def collect_manipulation_stock_data(self, years=3):
        """등록된 작전주들의 과거 데이터를 수집합니다."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 등록된 작전주 목록 조회
            cursor.execute("SELECT stock_name, stock_code FROM manipulation_stocks WHERE stock_code IS NOT NULL")
            stocks = cursor.fetchall()
            
            collected_stocks = []
            
            for stock_name, stock_code in stocks:
                logger.info(f"📊 {stock_name} 데이터 수집 중...")
                
                # 종합 데이터 수집
                df = self.collector.collect_comprehensive_data(stock_name, years=years)
                
                if df is not None:
                    # 패턴 분석
                    patterns = self.collector.analyze_manipulation_patterns(df, stock_name)
                    warnings, risk_level, risk_score = self.collector.detect_suspicious_patterns(patterns, stock_name)
                    
                    # 일별 데이터 저장
                    self.save_daily_data_to_db(stock_code, df)
                    
                    # 패턴 분석 결과 저장
                    self.save_pattern_analysis(stock_code, patterns, warnings, risk_level, risk_score)
                    
                    collected_stocks.append({
                        'stock_name': stock_name,
                        'stock_code': stock_code,
                        'data_count': len(df),
                        'risk_level': risk_level,
                        'risk_score': risk_score
                    })
                    
                    logger.info(f"✅ {stock_name} 수집 완료 - 위험도: {risk_level}")
                else:
                    logger.warning(f"❌ {stock_name} 데이터 수집 실패")
            
            conn.close()
            return collected_stocks
            
        except Exception as e:
            logger.error(f"작전주 데이터 수집 오류: {str(e)}")
            return []

    def save_daily_data_to_db(self, stock_code, df):
        """일별 데이터를 DB에 저장합니다."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for date, row in df.iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO stock_daily_data 
                    (stock_code, date, open_price, high_price, low_price, close_price, 
                     volume, change_rate, market_cap, trading_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stock_code,
                    date.strftime('%Y-%m-%d'),
                    row.get('시가'),
                    row.get('고가'),
                    row.get('저가'),
                    row.get('종가'),
                    row.get('거래량'),
                    row.get('등락률'),
                    row.get('시가총액'),
                    row.get('거래대금')
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"일별 데이터 저장 오류: {str(e)}")

    def convert_numpy_types(self, obj):
        """numpy 타입을 JSON 직렬화 가능한 타입으로 변환합니다."""
        if isinstance(obj, dict):
            return {key: self.convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

    def save_pattern_analysis(self, stock_code, patterns, warnings, risk_level, risk_score):
        """패턴 분석 결과를 DB에 저장합니다."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            # numpy 타입 변환
            clean_patterns = self.convert_numpy_types(patterns)
            clean_warnings = self.convert_numpy_types(warnings)
            
            cursor.execute('''
                INSERT OR REPLACE INTO pattern_analysis 
                (stock_code, analysis_date, risk_score, risk_level, warnings, patterns)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                stock_code,
                today,
                risk_score,
                risk_level,
                json.dumps(clean_warnings, ensure_ascii=False),
                json.dumps(clean_patterns, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"패턴 분석 저장 오류: {str(e)}")

    def get_manipulation_stocks_summary(self):
        """작전주 DB 요약 정보를 반환합니다."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 등록된 작전주 개수
            total_stocks = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM manipulation_stocks", conn
            ).iloc[0]['count']
            
            # 카테고리별 통계
            category_stats = pd.read_sql_query(
                "SELECT category, COUNT(*) as count FROM manipulation_stocks GROUP BY category", conn
            )
            
            # 최근 패턴 분석 결과
            risk_stats = pd.read_sql_query(
                """SELECT risk_level, COUNT(*) as count 
                   FROM pattern_analysis 
                   WHERE analysis_date = (SELECT MAX(analysis_date) FROM pattern_analysis)
                   GROUP BY risk_level""", conn
            )
            
            conn.close()
            
            return {
                'total_stocks': total_stocks,
                'category_stats': category_stats,
                'risk_stats': risk_stats
            }
            
        except Exception as e:
            logger.error(f"요약 정보 조회 오류: {str(e)}")
            return None

def main():
    print("=== 🗄️ K-Stock 작전주 DB 생성 시스템 ===\n")
    
    # DB 인스턴스 생성
    db = ManipulationStockDB()
    
    # 1. 작전주 등록
    print("📝 작전주 리스트 등록 중...")
    registered_count = db.register_manipulation_stocks()
    print(f"✅ {registered_count}개 작전주 등록 완료\n")
    
    # 2. 작전주 데이터 수집
    print("📊 작전주 데이터 수집 중...")
    collected_stocks = db.collect_manipulation_stock_data(years=2)
    print(f"✅ {len(collected_stocks)}개 종목 데이터 수집 완료\n")
    
    # 3. 수집 결과 요약
    print("=" * 60)
    print("📋 작전주 DB 구축 결과")
    print("=" * 60)
    
    summary = db.get_manipulation_stocks_summary()
    if summary:
        print(f"📊 총 등록 종목: {summary['total_stocks']}개")
        print(f"📊 데이터 수집 완료: {len(collected_stocks)}개")
        
        print(f"\n📈 카테고리별 분포:")
        for _, row in summary['category_stats'].iterrows():
            print(f"   - {row['category']}: {row['count']}개")
        
        print(f"\n⚠️ 위험도 분포:")
        for _, row in summary['risk_stats'].iterrows():
            print(f"   - {row['risk_level']}: {row['count']}개")
    
    # 4. 고위험 종목 하이라이트
    high_risk_stocks = [stock for stock in collected_stocks if '🔴' in stock['risk_level']]
    medium_risk_stocks = [stock for stock in collected_stocks if '🟡' in stock['risk_level']]
    
    if high_risk_stocks:
        print(f"\n🚨 HIGH RISK 작전주:")
        for stock in high_risk_stocks:
            print(f"   - {stock['stock_name']} (점수: {stock['risk_score']})")
    
    if medium_risk_stocks:
        print(f"\n⚠️ MEDIUM RISK 작전주:")
        for stock in medium_risk_stocks:
            print(f"   - {stock['stock_name']} (점수: {stock['risk_score']})")
    
    print(f"\n💾 데이터베이스 파일: manipulation_stocks.db")
    print(f"🎯 작전주 DB 구축이 완료되었습니다!")

if __name__ == "__main__":
    main() 