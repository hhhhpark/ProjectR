import sqlite3
import os

def create_suspect_stocks_db():
    """새로운 suspect_stocks.db 파일을 생성합니다."""
    
    # DB 디렉토리가 없으면 생성
    os.makedirs("DB", exist_ok=True)
    
    db_path = "DB/suspect_stocks.db"
    
    # 기존 파일이 있으면 삭제
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️ 기존 {db_path} 파일을 삭제했습니다.")
    
    # 새로운 DB 파일 생성
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # suspect_stocks 테이블 생성
    cursor.execute('''
        CREATE TABLE suspect_stocks (
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
        print("✅ suspect_stocks.db 파일이 성공적으로 생성되었습니다.")
        
        # 테이블 구조 확인
        cursor.execute("PRAGMA table_info(suspect_stocks)")
        columns = cursor.fetchall()
        
        print("\n📋 테이블 구조:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
        # 파일 크기 확인
        file_size = os.path.getsize(db_path)
        print(f"\n📁 파일 크기: {file_size} bytes")
        
    else:
        print("❌ 테이블 생성에 실패했습니다.")
    
    conn.close()
    print(f"\n✅ 작업 완료! DB 파일 위치: {db_path}")

if __name__ == "__main__":
    create_suspect_stocks_db() 