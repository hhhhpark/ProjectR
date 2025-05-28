import sqlite3
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_collectlist_columns():
    """collectList.db의 컬럼명을 한글에서 영어로 변경"""
    
    try:
        db_path = "DB/collectList.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 기존 데이터 백업
        cursor.execute("SELECT 주식명, 주식코드 FROM collection_stocks")
        existing_data = cursor.fetchall()
        
        logger.info(f"기존 데이터 {len(existing_data)}개 백업 완료")
        
        # 기존 테이블 삭제
        cursor.execute("DROP TABLE IF EXISTS collection_stocks")
        
        # 새로운 테이블 생성 (영어 컬럼명)
        cursor.execute('''
            CREATE TABLE collection_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_name TEXT NOT NULL,
                stock_code TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        logger.info("✅ 새로운 테이블 구조 생성 완료 (영어 컬럼명)")
        
        # 기존 데이터 삽입
        for row in existing_data:
            cursor.execute('''
                INSERT INTO collection_stocks (stock_name, stock_code)
                VALUES (?, ?)
            ''', (row[0], row[1]))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ {len(existing_data)}개 데이터 복원 완료")
        logger.info("✅ collectList.db 컬럼명 변경 완료: 주식명 → stock_name, 주식코드 → stock_code")
        
    except Exception as e:
        logger.error(f"❌ 컬럼명 변경 실패: {str(e)}")

def verify_updated_table():
    """변경된 테이블 구조 확인"""
    try:
        db_path = "DB/collectList.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n" + "=" * 60)
        print("📊 업데이트된 collectList.db 확인")
        print("=" * 60)
        
        # 테이블 구조 확인
        cursor.execute("PRAGMA table_info(collection_stocks)")
        columns = cursor.fetchall()
        
        print("📋 테이블 구조:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        
        # 데이터 확인
        cursor.execute("SELECT stock_name, stock_code FROM collection_stocks ORDER BY stock_name")
        results = cursor.fetchall()
        
        print(f"\n📈 데이터 내용 ({len(results)}개 종목):")
        for row in results:
            print(f"   {row[0]} ({row[1]})")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ 테이블 확인 실패: {str(e)}")

def main():
    """메인 실행 함수"""
    print("=== 📝 collectList.db 컬럼명 변경 시스템 ===\n")
    print("한글 컬럼명을 영어로 변경합니다...")
    print("주식명 → stock_name")
    print("주식코드 → stock_code\n")
    
    # 1. 컬럼명 변경
    print("📋 1단계: 컬럼명 변경")
    update_collectlist_columns()
    print()
    
    # 2. 변경 결과 확인
    print("📊 2단계: 변경 결과 확인")
    verify_updated_table()
    
    print("\n🎯 collectList.db 컬럼명 변경 완료!")
    print("💡 TIP: 이제 API에서 영어 컬럼명을 사용할 수 있습니다.")

if __name__ == "__main__":
    main() 