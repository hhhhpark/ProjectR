import sqlite3
import os
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_collection_stocks_db():
    """1. 수집 종목 테이블 DB 생성"""
    try:
        os.makedirs("DB", exist_ok=True)
        db_path = "DB/collectList.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collection_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                주식명 TEXT NOT NULL,
                주식코드 TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 샘플 데이터 삽입
        sample_stocks = [
            ("삼성전자", "005930"),
            ("LG에너지솔루션", "373220"),
            ("SK하이닉스", "000660"),
            ("셀트리온제약", "068760"),
            ("진원생명과학", "011000"),
            ("씨젠", "096530"),
            ("카카오게임즈", "293490"),
            ("SK바이오팜", "326030"),
            ("메디톡스", "086900"),
            ("와이지엔터테인먼트", "122870"),
            ("코오롱생명과학", "102940")
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO collection_stocks (주식명, 주식코드)
            VALUES (?, ?)
        ''', sample_stocks)
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ 수집 종목 테이블 DB 생성 완료: {db_path}")
        logger.info(f"   - {len(sample_stocks)}개 종목 데이터 삽입")
        
    except Exception as e:
        logger.error(f"❌ 수집 종목 테이블 DB 생성 실패: {str(e)}")

def create_completed_stocks_db():
    """2. 등록 완료 테이블 DB 생성"""
    try:
        os.makedirs("DB", exist_ok=True)
        db_path = "DB/collectCompleteData.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS completed_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                주식명 TEXT NOT NULL,
                주식코드 TEXT NOT NULL,
                날짜 DATE NOT NULL,
                시가 INTEGER,
                고가 INTEGER,
                저가 INTEGER,
                종가 INTEGER,
                거래량 BIGINT,
                등락률 REAL,
                시가총액 BIGINT,
                거래량_cap BIGINT,
                거래대금 BIGINT,
                상장주식수 BIGINT,
                BPS REAL,
                PER REAL,
                PBR REAL,
                EPS REAL,
                DIV REAL,
                DPS REAL,
                기관합계 BIGINT,
                기타법인 BIGINT,
                개인 BIGINT,
                외국인합계 BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(주식코드, 날짜)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ 등록 완료 테이블 DB 생성 완료: {db_path}")
        
    except Exception as e:
        logger.error(f"❌ 등록 완료 테이블 DB 생성 실패: {str(e)}")

def create_manipulation_stocks_db():
    """3. 작전주 테이블 DB 생성"""
    try:
        os.makedirs("DB", exist_ok=True)
        db_path = "DB/anomalousList.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS manipulation_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_name TEXT NOT NULL,
                stock_code TEXT NOT NULL,
                category TEXT,
                manipulation_period TEXT,
                max_rise_rate REAL,
                manipulation_type TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ 작전주 테이블 DB 생성 완료: {db_path}")
        
    except Exception as e:
        logger.error(f"❌ 작전주 테이블 DB 생성 실패: {str(e)}")

def check_created_dbs():
    """생성된 DB 파일들을 확인합니다."""
    print("\n" + "=" * 60)
    print("📊 생성된 DB 파일 확인")
    print("=" * 60)
    
    db_files = [
        ("DB/collectList.db", "collection_stocks"),
        ("DB/collectCompleteData.db", "completed_stocks"),
        ("DB/anomalousList.db", "manipulation_stocks")
    ]
    
    for db_path, table_name in db_files:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 테이블 존재 확인
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                table_exists = cursor.fetchone()
                
                if table_exists:
                    # 데이터 건수 확인
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    
                    print(f"✅ {os.path.basename(db_path)}")
                    print(f"   - 테이블: {table_name}")
                    print(f"   - 데이터: {count:,}건")
                    print(f"   - 경로: {db_path}")
                else:
                    print(f"❌ {os.path.basename(db_path)} - 테이블 없음")
                
                conn.close()
                
            except Exception as e:
                print(f"❌ {os.path.basename(db_path)} - 오류: {str(e)}")
        else:
            print(f"❌ {os.path.basename(db_path)} - 파일 없음")
        
        print()

def main():
    """메인 실행 함수"""
    print("=== 📊 K-Stock Pattern Insight 개별 DB 생성 시스템 ===\n")
    print("🗄️ PRD 문서에 따라 3개의 개별 DB 파일을 생성합니다...\n")
    
    # 1. 수집 종목 테이블 DB 생성
    print("📋 1단계: 수집 종목 테이블 DB 생성")
    create_collection_stocks_db()
    
    # 2. 등록 완료 테이블 DB 생성
    print("\n📊 2단계: 등록 완료 테이블 DB 생성")
    create_completed_stocks_db()
    
    # 3. 작전주 테이블 DB 생성
    print("\n🎯 3단계: 작전주 테이블 DB 생성")
    create_manipulation_stocks_db()
    
    # 4. 생성된 DB 확인
    check_created_dbs()
    
    print("🎯 개별 DB 파일 생성 완료!")
    print("💡 TIP: 이제 각 DB 파일을 독립적으로 관리할 수 있습니다.")

if __name__ == "__main__":
    main() 