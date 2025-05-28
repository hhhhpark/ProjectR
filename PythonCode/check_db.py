import sqlite3
import pandas as pd

def check_database():
    """데이터베이스 테이블과 데이터를 확인합니다."""
    
    db_path = "DB/manipulation_stocks.db"
    conn = sqlite3.connect(db_path)
    
    print("=== 📊 K-Stock Pattern Insight DB 현황 ===\n")
    
    # 1. 수집 종목 테이블 확인
    print("📈 1. 수집 종목 테이블 (collection_stocks)")
    print("-" * 50)
    try:
        df = pd.read_sql_query("SELECT * FROM collection_stocks", conn)
        print(f"총 {len(df)}개 종목")
        print(df[['stock_name', 'stock_code']].to_string(index=False))
        print()
    except Exception as e:
        print(f"오류: {e}\n")
    
    # 2. 등록 완료 테이블 확인 (요약)
    print("📊 2. 등록 완료 테이블 (completed_stocks) - 요약")
    print("-" * 50)
    try:
        # 종목별 데이터 건수
        df = pd.read_sql_query("""
            SELECT stock_name, stock_code, COUNT(*) as data_count, 
                   MIN(date) as start_date, MAX(date) as end_date
            FROM completed_stocks 
            GROUP BY stock_code 
            ORDER BY stock_name
        """, conn)
        print(df.to_string(index=False))
        print(f"\n총 데이터: {pd.read_sql_query('SELECT COUNT(*) as total FROM completed_stocks', conn)['total'][0]:,}건")
        print()
    except Exception as e:
        print(f"오류: {e}\n")
    
    # 3. 작전주 분석 테이블 확인
    print("🎯 3. 작전주 분석 테이블 (manipulation_analysis)")
    print("-" * 50)
    try:
        df = pd.read_sql_query("""
            SELECT stock_name, stock_code, risk_level, risk_score, 
                   manipulation_type, max_rise_rate
            FROM manipulation_analysis 
            ORDER BY risk_score DESC
        """, conn)
        print(df.to_string(index=False))
        print()
    except Exception as e:
        print(f"오류: {e}\n")
    
    # 4. 위험도별 통계
    print("📈 4. 위험도별 통계")
    print("-" * 50)
    try:
        df = pd.read_sql_query("""
            SELECT risk_level, COUNT(*) as count
            FROM manipulation_analysis 
            GROUP BY risk_level
            ORDER BY 
                CASE risk_level 
                    WHEN '🔴 HIGH RISK' THEN 1
                    WHEN '🟡 MEDIUM RISK' THEN 2
                    WHEN '🟢 LOW RISK' THEN 3
                    WHEN '✅ NORMAL' THEN 4
                END
        """, conn)
        print(df.to_string(index=False))
        print()
    except Exception as e:
        print(f"오류: {e}\n")
    
    conn.close()

if __name__ == "__main__":
    check_database() 