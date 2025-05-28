import sqlite3
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 컬럼명 매핑 (한글 → 영어)
COLUMN_MAPPING = {
    '주식명': 'stock_name',
    '주식코드': 'stock_code',
    '날짜': 'date',
    '시가': 'open_price',
    '고가': 'high_price',
    '저가': 'low_price',
    '종가': 'close_price',
    '거래량': 'volume',
    '등락률': 'change_rate',
    '시가총액': 'market_cap',
    '거래량_cap': 'volume_cap',
    '거래대금': 'trading_value',
    '상장주식수': 'shares_outstanding',
    'BPS': 'bps',
    'PER': 'per',
    'PBR': 'pbr',
    'EPS': 'eps',
    'DIV': 'div',
    'DPS': 'dps',
    '기관합계': 'institutional_total',
    '기타법인': 'other_corporate',
    '개인': 'individual',
    '외국인합계': 'foreign_total'
}

def update_collectcompletedata_columns():
    """collectCompleteData.db의 컬럼명을 한글에서 영어로 변경"""
    
    try:
        db_path = "DB/collectCompleteData.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 기존 데이터 백업
        cursor.execute("""
            SELECT 주식명, 주식코드, 날짜, 시가, 고가, 저가, 종가, 거래량, 등락률, 시가총액,
                   거래량_cap, 거래대금, 상장주식수, BPS, PER, PBR, EPS, DIV, DPS,
                   기관합계, 기타법인, 개인, 외국인합계
            FROM completed_stocks
        """)
        existing_data = cursor.fetchall()
        
        logger.info(f"기존 데이터 {len(existing_data)}개 백업 완료")
        
        # 기존 테이블 삭제
        cursor.execute("DROP TABLE IF EXISTS completed_stocks")
        
        # 새로운 테이블 생성 (영어 컬럼명)
        cursor.execute('''
            CREATE TABLE completed_stocks (
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
                volume_cap BIGINT,
                trading_value BIGINT,
                shares_outstanding BIGINT,
                bps REAL,
                per REAL,
                pbr REAL,
                eps REAL,
                div REAL,
                dps REAL,
                institutional_total BIGINT,
                other_corporate BIGINT,
                individual BIGINT,
                foreign_total BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_code, date)
            )
        ''')
        
        logger.info("✅ 새로운 테이블 구조 생성 완료 (영어 컬럼명)")
        
        # 기존 데이터 삽입
        insert_count = 0
        for row in existing_data:
            cursor.execute('''
                INSERT INTO completed_stocks 
                (stock_name, stock_code, date, open_price, high_price, low_price, close_price,
                 volume, change_rate, market_cap, volume_cap, trading_value, shares_outstanding,
                 bps, per, pbr, eps, div, dps, institutional_total, other_corporate, individual, foreign_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', row)
            insert_count += 1
            
            if insert_count % 1000 == 0:
                logger.info(f"진행률: {insert_count}/{len(existing_data)} ({insert_count/len(existing_data)*100:.1f}%)")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ {len(existing_data)}개 데이터 복원 완료")
        logger.info("✅ collectCompleteData.db 컬럼명 변경 완료")
        
    except Exception as e:
        logger.error(f"❌ 컬럼명 변경 실패: {str(e)}")

def verify_updated_table():
    """변경된 테이블 구조 확인"""
    try:
        db_path = "DB/collectCompleteData.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n" + "=" * 80)
        print("📊 업데이트된 collectCompleteData.db 확인")
        print("=" * 80)
        
        # 테이블 구조 확인
        cursor.execute("PRAGMA table_info(completed_stocks)")
        columns = cursor.fetchall()
        
        print("📋 테이블 구조:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        
        # 데이터 개수 확인
        cursor.execute("SELECT COUNT(*) FROM completed_stocks")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT stock_code) FROM completed_stocks")
        stock_count = cursor.fetchone()[0]
        
        print(f"\n📈 데이터 요약:")
        print(f"   총 데이터: {total_count:,}개")
        print(f"   종목 수: {stock_count}개")
        
        # 샘플 데이터 확인
        cursor.execute("""
            SELECT stock_name, stock_code, date, close_price, volume 
            FROM completed_stocks 
            ORDER BY date DESC 
            LIMIT 5
        """)
        samples = cursor.fetchall()
        
        print(f"\n📊 최근 데이터 샘플:")
        for row in samples:
            print(f"   {row[0]} ({row[1]}) - {row[2]} | 종가: {row[3]:,} | 거래량: {row[4]:,}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ 테이블 확인 실패: {str(e)}")

def main():
    """메인 실행 함수"""
    print("=== 📝 collectCompleteData.db 컬럼명 변경 시스템 ===\n")
    print("한글 컬럼명을 영어로 변경합니다...")
    print("주식명 → stock_name, 주식코드 → stock_code, 날짜 → date 등\n")
    
    # 1. 컬럼명 변경
    print("📋 1단계: 컬럼명 변경 (시간이 오래 걸릴 수 있습니다)")
    update_collectcompletedata_columns()
    print()
    
    # 2. 변경 결과 확인
    print("📊 2단계: 변경 결과 확인")
    verify_updated_table()
    
    print("\n🎯 collectCompleteData.db 컬럼명 변경 완료!")
    print("💡 TIP: 이제 API에서 영어 컬럼명을 사용할 수 있습니다.")

if __name__ == "__main__":
    main() 