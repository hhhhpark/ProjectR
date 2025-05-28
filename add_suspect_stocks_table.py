import sqlite3
import os

def add_suspect_stocks_table():
    """manipulation_stocks.db에 suspect_stocks 테이블을 추가합니다."""
    
    db_path = "DB/manipulation_stocks.db"
    
    if not os.path.exists(db_path):
        print(f"❌ {db_path} 파일이 존재하지 않습니다.")
        return
    
    # DB 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # suspect_stocks 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suspect_stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_name TEXT,
            suspected_period TEXT,
            theme_reason TEXT,
            main_issue TEXT,
            active_duration TEXT,
            buy_side_pattern TEXT,
            price_3y_ago INTEGER,
            price_peak INTEGER,
            price_current INTEGER
        )
    ''')
    
    # 변경사항 저장
    conn.commit()
    
    # 테이블 생성 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='suspect_stocks'")
    result = cursor.fetchone()
    
    if result:
        print("✅ suspect_stocks 테이블이 성공적으로 생성되었습니다.")
        
        # 테이블 구조 확인
        cursor.execute("PRAGMA table_info(suspect_stocks)")
        columns = cursor.fetchall()
        
        print("\n📋 테이블 구조:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    else:
        print("❌ 테이블 생성에 실패했습니다.")
    
    # 현재 DB의 모든 테이블 목록 출력
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"\n📊 manipulation_stocks.db의 전체 테이블 목록:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  - {table[0]}: {count}개 레코드")
    
    conn.close()
    print(f"\n✅ 작업 완료!")

if __name__ == "__main__":
    add_suspect_stocks_table() 