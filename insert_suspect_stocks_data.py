import sqlite3
import os

def insert_suspect_stocks_data():
    """suspect_stocks.db에 데이터를 삽입합니다."""
    
    db_path = "DB/suspect_stocks.db"
    
    if not os.path.exists(db_path):
        print(f"❌ {db_path} 파일이 존재하지 않습니다.")
        return
    
    # 삽입할 데이터
    data = [
        ("에디슨EV", "2021년", "쌍용차 인수 기대감", "쌍용차 인수 추진 발표 후 주가 급등. 이후 인수 무산 및 상장폐지 위기.", "약 3개월", "개인 투자자 중심 매수", 1000, 13000, 0),
        ("삼천리자전거", "2021년", "자전거 수요 증가 기대감", "코로나19로 인한 자전거 수요 증가 기대감으로 주가 상승.", "약 2개월", "기관 투자자 매수 증가", 5000, 20000, 10000),
        ("쌍방울", "2022년", "쌍용차 인수 기대감", "쌍용차 인수 의향서 제출 발표 후 주가 급등. 이후 인수 무산.", "약 1개월", "개인 투자자 중심 매수", 1500, 4500, 1200),
        ("루보", "2020년", "M&A 기대감", "인수합병 루머 확산으로 주가 급등. 이후 주가 급락.", "약 2개월", "외국인 투자자 매수 증가", 2000, 16000, 3000),
        ("리타워텍", "2020년", "녹색성장 테마주", "정부의 녹색성장 정책 수혜 기대감으로 주가 상승.", "약 1.5개월", "기관 투자자 매수 증가", 3000, 12000, 4000),
        ("헬리아텍", "2020년", "바이오 테마주", "신약 개발 관련 루머 확산으로 주가 급등. 이후 주가 급락.", "약 2개월", "개인 투자자 중심 매수", 4000, 28000, 5000),
        ("지이엔에프", "2020년", "M&A 기대감", "인수합병 루머 확산으로 주가 급등. 이후 주가 급락.", "약 1.5개월", "외국인 투자자 매수 증가", 3500, 17000, 4500),
        ("에이치엘비", "2021년", "신약 개발 기대감", "리보세라닙의 임상 결과 발표 후 주가 급등.", "약 3개월", "기관 투자자 매수 증가", 20000, 120000, 60000),
        ("씨티씨바이오", "2021년", "바이오 테마주", "신약 개발 관련 소식으로 주가 급등. 이후 주가 급락.", "약 2개월", "개인 투자자 중심 매수", 6000, 24000, 7000),
        ("넥스트사이언스", "2021년", "바이오 사업 진출 발표", "자회사인 바이오기업 인수 발표 후 주가 급등. 이후 주가 급락.", "약 2.5개월", "외국인 투자자 매수 증가", 5000, 25000, 6000),
    ]
    
    # DB 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 기존 데이터 삭제 (새로 시작)
    cursor.execute("DELETE FROM suspect_stocks")
    print("🗑️ 기존 데이터를 삭제했습니다.")
    
    # 데이터 삽입
    cursor.executemany('''
        INSERT INTO suspect_stocks (
            stock_name, suspected_period, theme_reason, main_issue, 
            active_duration, buy_side_pattern, price_3y_ago, price_peak, price_current
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    
    # 변경사항 저장
    conn.commit()
    
    # 삽입된 데이터 확인
    cursor.execute("SELECT COUNT(*) FROM suspect_stocks")
    count = cursor.fetchone()[0]
    
    print(f"✅ {count}개의 데이터가 성공적으로 삽입되었습니다.")
    
    # 삽입된 데이터 미리보기
    cursor.execute("SELECT id, stock_name, suspected_period, theme_reason FROM suspect_stocks LIMIT 5")
    preview_data = cursor.fetchall()
    
    print("\n📋 삽입된 데이터 미리보기:")
    for row in preview_data:
        print(f"  {row[0]}. {row[1]} ({row[2]}) - {row[3]}")
    
    if count > 5:
        print(f"  ... 외 {count - 5}개 더")
    
    # 통계 정보
    cursor.execute("SELECT suspected_period, COUNT(*) FROM suspect_stocks GROUP BY suspected_period")
    period_stats = cursor.fetchall()
    
    print("\n📊 연도별 통계:")
    for period, cnt in period_stats:
        print(f"  - {period}: {cnt}개")
    
    conn.close()
    print(f"\n✅ 작업 완료!")

if __name__ == "__main__":
    insert_suspect_stocks_data() 