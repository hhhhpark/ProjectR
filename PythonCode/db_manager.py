import sqlite3
import pandas as pd
import os
import glob
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, db_path="DB/manipulation_stocks.db"):
        self.db_path = db_path
        self.ensure_db_directory()
    
    def ensure_db_directory(self):
        """DB 디렉토리가 없으면 생성"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        return sqlite3.connect(self.db_path)
    
    def create_collection_stocks_table(self):
        """1. 수집 종목 테이블 생성"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS collection_stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_name TEXT NOT NULL,
                    stock_code TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ 수집 종목 테이블 생성 완료")
            
        except Exception as e:
            logger.error(f"❌ 수집 종목 테이블 생성 실패: {str(e)}")
    
    def create_completed_stocks_table(self):
        """2. 등록 완료 테이블 생성"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS completed_stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_name TEXT NOT NULL,
                    stock_code TEXT NOT NULL,
                    date DATE NOT NULL,
                    open_price INTEGER,
                    high_price INTEGER,
                    low_price INTEGER,
                    close_price INTEGER,
                    volume BIGINT,
                    change_rate REAL,
                    market_cap BIGINT,
                    trading_volume_cap BIGINT,
                    trading_value BIGINT,
                    listed_shares BIGINT,
                    bps REAL,
                    per REAL,
                    pbr REAL,
                    eps REAL,
                    div REAL,
                    dps REAL,
                    institution_total BIGINT,
                    other_corporation BIGINT,
                    individual BIGINT,
                    foreign_total BIGINT,
                    short_balance BIGINT,
                    short_ratio REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stock_code, date)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ 등록 완료 테이블 생성 완료")
            
        except Exception as e:
            logger.error(f"❌ 등록 완료 테이블 생성 실패: {str(e)}")
    
    def create_manipulation_stocks_table(self):
        """3. 작전주 테이블 생성"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS manipulation_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_name TEXT NOT NULL,
                    stock_code TEXT NOT NULL,
                    category TEXT,
                    manipulation_period TEXT,
                    max_rise_rate REAL,
                    manipulation_type TEXT,
                    risk_level TEXT,
                    risk_score INTEGER,
                    description TEXT,
                    analysis_patterns TEXT,
                    warnings TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ 작전주 테이블 생성 완료")
            
        except Exception as e:
            logger.error(f"❌ 작전주 테이블 생성 실패: {str(e)}")
    
    def insert_collection_stocks_from_csv(self):
        """CSV 파일들에서 종목 정보를 추출하여 수집 종목 테이블에 삽입"""
        try:
            csv_files = glob.glob("Result/*.csv")
            
            if not csv_files:
                logger.warning("Result 폴더에 CSV 파일이 없습니다.")
                return
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            for csv_file in csv_files:
                # 파일명에서 종목명과 종목코드 추출
                basename = os.path.basename(csv_file)
                name_without_ext = basename.replace('.csv', '')
                parts = name_without_ext.split('_')
                
                if len(parts) >= 2:
                    stock_name = parts[0]
                    stock_code = parts[1]
                    
                    # 중복 체크 후 삽입
                    cursor.execute('''
                        INSERT OR IGNORE INTO collection_stocks (stock_name, stock_code)
                        VALUES (?, ?)
                    ''', (stock_name, stock_code))
                    
                    logger.info(f"📈 {stock_name} ({stock_code}) 수집 종목 테이블에 추가")
            
            conn.commit()
            conn.close()
            logger.info("✅ 수집 종목 테이블 업데이트 완료")
            
        except Exception as e:
            logger.error(f"❌ 수집 종목 테이블 업데이트 실패: {str(e)}")
    
    def insert_completed_stocks_from_csv(self):
        """CSV 파일들의 데이터를 등록 완료 테이블에 삽입"""
        try:
            csv_files = glob.glob("Result/*.csv")
            
            if not csv_files:
                logger.warning("Result 폴더에 CSV 파일이 없습니다.")
                return
            
            conn = self.get_connection()
            
            for csv_file in csv_files:
                # 파일명에서 종목 정보 추출
                basename = os.path.basename(csv_file)
                name_without_ext = basename.replace('.csv', '')
                parts = name_without_ext.split('_')
                
                if len(parts) >= 2:
                    stock_name = parts[0]
                    stock_code = parts[1]
                    
                    logger.info(f"📊 {stock_name} ({stock_code}) 데이터 처리 중...")
                    
                    # CSV 파일 읽기
                    df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
                    
                    # 데이터 전처리 및 컬럼 매핑
                    processed_data = []
                    
                    for date, row in df.iterrows():
                        # 날짜 형식 변환
                        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
                        
                        # 데이터 매핑 (None 값 처리)
                        data_row = {
                            'stock_name': stock_name,
                            'stock_code': stock_code,
                            'date': date_str,
                            'open_price': self.safe_int(row.get('시가')),
                            'high_price': self.safe_int(row.get('고가')),
                            'low_price': self.safe_int(row.get('저가')),
                            'close_price': self.safe_int(row.get('종가')),
                            'volume': self.safe_int(row.get('거래량')),
                            'change_rate': self.safe_float(row.get('등락률')),
                            'market_cap': self.safe_int(row.get('시가총액')),
                            'trading_volume_cap': self.safe_int(row.get('거래량_cap')),
                            'trading_value': self.safe_int(row.get('거래대금')),
                            'listed_shares': self.safe_int(row.get('상장주식수')),
                            'bps': self.safe_float(row.get('BPS')),
                            'per': self.safe_float(row.get('PER')),
                            'pbr': self.safe_float(row.get('PBR')),
                            'eps': self.safe_float(row.get('EPS')),
                            'div': self.safe_float(row.get('DIV')),
                            'dps': self.safe_float(row.get('DPS')),
                            'institution_total': self.safe_int(row.get('기관합계')),
                            'other_corporation': self.safe_int(row.get('기타법인')),
                            'individual': self.safe_int(row.get('개인')),
                            'foreign_total': self.safe_int(row.get('외국인합계')),
                            'short_balance': self.safe_int(row.get('공매도잔고')),
                            'short_ratio': self.safe_float(row.get('비중'))
                        }
                        
                        processed_data.append(data_row)
                    
                    # 배치 삽입
                    if processed_data:
                        df_to_insert = pd.DataFrame(processed_data)
                        df_to_insert.to_sql('completed_stocks', conn, if_exists='append', index=False, method='multi')
                        logger.info(f"✅ {stock_name} 데이터 {len(processed_data)}건 삽입 완료")
                    
            conn.close()
            logger.info("✅ 등록 완료 테이블 업데이트 완료")
            
        except Exception as e:
            logger.error(f"❌ 등록 완료 테이블 업데이트 실패: {str(e)}")
    
    def safe_int(self, value):
        """안전한 정수 변환"""
        try:
            if pd.isna(value) or value == '' or value is None:
                return None
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def safe_float(self, value):
        """안전한 실수 변환"""
        try:
            if pd.isna(value) or value == '' or value is None:
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def check_existing_data(self, stock_code):
        """특정 종목의 기존 데이터 확인"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*), MAX(date) as latest_date
                FROM completed_stocks
                WHERE stock_code = ?
            ''', (stock_code,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0], result[1]
            
        except Exception as e:
            logger.error(f"기존 데이터 확인 실패: {str(e)}")
            return 0, None
    
    def get_table_info(self, table_name):
        """테이블 정보 조회"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            logger.error(f"테이블 정보 조회 실패: {str(e)}")
            return 0
    
    def print_summary(self):
        """데이터베이스 요약 정보 출력"""
        print("=" * 60)
        print("📊 데이터베이스 요약 정보")
        print("=" * 60)
        
        collection_count = self.get_table_info('collection_stocks')
        completed_count = self.get_table_info('completed_stocks')
        manipulation_count = self.get_table_info('manipulation_analysis')
        
        print(f"📈 수집 종목 테이블: {collection_count:,}개 종목")
        print(f"📊 등록 완료 테이블: {completed_count:,}건 데이터")
        print(f"🎯 작전주 분석 테이블: {manipulation_count:,}건 분석")
        
        # 최근 데이터 확인
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT stock_name, stock_code, MAX(date) as latest_date
                FROM completed_stocks
                GROUP BY stock_code
                ORDER BY latest_date DESC
                LIMIT 5
            ''')
            
            recent_data = cursor.fetchall()
            
            if recent_data:
                print(f"\n📅 최근 업데이트된 종목 (상위 5개):")
                for stock_name, stock_code, latest_date in recent_data:
                    print(f"   {stock_name} ({stock_code}): {latest_date}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"최근 데이터 조회 실패: {str(e)}")

def main():
    """메인 실행 함수"""
    print("=== 📊 K-Stock Pattern Insight DB 관리 시스템 ===\n")
    print("🗄️ 데이터베이스 테이블 생성 및 데이터 업데이트를 시작합니다...\n")
    
    db_manager = DatabaseManager()
    
    # 1. 테이블 생성
    print("📋 1단계: 테이블 생성")
    db_manager.create_collection_stocks_table()
    db_manager.create_completed_stocks_table()
    db_manager.create_manipulation_stocks_table()
    print()
    
    # 2. 수집 종목 테이블 업데이트
    print("📈 2단계: 수집 종목 테이블 업데이트")
    db_manager.insert_collection_stocks_from_csv()
    print()
    
    # 3. 등록 완료 테이블 업데이트
    print("📊 3단계: 등록 완료 테이블 업데이트")
    db_manager.insert_completed_stocks_from_csv()
    print()
    
    # 4. 요약 정보 출력
    db_manager.print_summary()
    
    print(f"\n🎯 데이터베이스 업데이트 완료!")
    print("💡 TIP: 이제 패턴 분석 결과를 manipulation_analysis 테이블에 저장할 수 있습니다.")

if __name__ == "__main__":
    main() 