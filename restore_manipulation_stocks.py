import sqlite3
import os

def restore_manipulation_stocks_db():
    """manipulation_stocks.db에 과거 작전주 데이터를 복원합니다."""
    
    db_path = "DB/manipulation_stocks.db"
    
    # DB 디렉토리가 없으면 생성
    os.makedirs("DB", exist_ok=True)
    
    # DB 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 기존 테이블 삭제 후 재생성
    cursor.execute("DROP TABLE IF EXISTS historical_manipulation_stocks")
    
    # 과거 작전주 테이블 생성
    cursor.execute('''
        CREATE TABLE historical_manipulation_stocks (
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
    
    # 과거 작전주 데이터 삽입
    historical_stocks = [
        ("라이트론", "069540", "바이오", "2021.03-2021.06", 1250.5, "급등급락", "코로나 치료제 관련 허위 정보 유포로 급등 후 급락"),
        ("셀트리온제약", "068760", "바이오", "2020.07-2020.09", 890.2, "급등급락", "코로나 치료제 기대감 조성 후 실망 매물 출회"),
        ("진원생명과학", "011000", "바이오", "2020.02-2020.04", 2100.8, "급등급락", "코로나 진단키트 관련 과대 포장으로 급등 후 폭락"),
        ("씨젠", "096530", "바이오", "2020.01-2020.03", 567.3, "급등급락", "코로나 진단키트 독점 공급 기대감으로 급등"),
        ("카카오게임즈", "293490", "게임", "2020.09-2020.11", 234.7, "급등급락", "상장 초기 과도한 기대감으로 급등 후 조정"),
        ("SK바이오팜", "326030", "바이오", "2020.07-2020.08", 189.4, "급등급락", "상장 초기 바이오 테마 부각으로 급등"),
        ("메디톡스", "086900", "바이오", "2019.05-2019.07", 445.6, "급등급락", "보톡스 관련 호재 부각 후 실적 부진으로 급락"),
        ("코오롱생명과학", "102940", "바이오", "2019.03-2019.05", 678.9, "급등급락", "무릎 연골 치료제 허가 기대감으로 급등"),
        ("와이지엔터테인먼트", "122870", "엔터", "2018.10-2018.12", 123.4, "급등급락", "아이돌 그룹 해외 진출 기대감으로 급등"),
        ("LG에너지솔루션", "373220", "배터리", "2022.01-2022.03", 89.7, "급등급락", "상장 초기 전기차 테마 부각으로 급등 후 조정"),
        ("SK하이닉스", "000660", "반도체", "2021.01-2021.03", 156.8, "급등급락", "메모리 반도체 슈퍼사이클 기대감으로 급등"),
        ("삼성전자", "005930", "반도체", "2020.07-2020.09", 78.9, "급등급락", "비메모리 반도체 성장 기대감으로 급등"),
        ("네이버", "035420", "IT", "2020.03-2020.05", 234.5, "급등급락", "언택트 테마 부각으로 급등 후 조정"),
        ("카카오", "035720", "IT", "2020.03-2020.06", 345.6, "급등급락", "디지털 뉴딜 테마로 급등 후 규제 우려로 급락"),
        ("NAVER", "035420", "IT", "2021.02-2021.04", 167.8, "급등급락", "메타버스 테마 부각으로 급등"),
        ("현대차", "005380", "자동차", "2020.12-2021.02", 145.3, "급등급락", "애플카 협력설로 급등 후 부인으로 급락"),
        ("LG화학", "051910", "화학", "2020.01-2020.03", 234.7, "급등급락", "배터리 분할 기대감으로 급등"),
        ("포스코", "005490", "철강", "2021.05-2021.07", 123.4, "급등급락", "철강 가격 상승으로 급등 후 조정"),
        ("한국전력", "015760", "전력", "2020.11-2021.01", 89.6, "급등급락", "그린뉴딜 테마로 급등 후 실적 부진으로 급락"),
        ("KB금융", "105560", "금융", "2020.11-2021.01", 67.8, "급등급락", "금리 인상 기대감으로 급등 후 조정")
    ]
    
    cursor.executemany('''
        INSERT INTO historical_manipulation_stocks 
        (stock_name, stock_code, category, manipulation_period, max_rise_rate, manipulation_type, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', historical_stocks)
    
    # 변경사항 저장
    conn.commit()
    
    # 데이터 확인
    cursor.execute("SELECT COUNT(*) FROM historical_manipulation_stocks")
    count = cursor.fetchone()[0]
    print(f"✅ historical_manipulation_stocks 테이블에 {count}개 데이터가 복원되었습니다.")
    
    # 샘플 데이터 출력
    cursor.execute("SELECT stock_name, stock_code, manipulation_type, max_rise_rate FROM historical_manipulation_stocks LIMIT 5")
    samples = cursor.fetchall()
    print("\n📊 복원된 데이터 샘플:")
    for sample in samples:
        print(f"  - {sample[0]} ({sample[1]}): {sample[2]}, 최대상승률 {sample[3]}%")
    
    conn.close()
    print(f"\n✅ manipulation_stocks.db 복원 완료!")

if __name__ == "__main__":
    restore_manipulation_stocks_db() 