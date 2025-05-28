import sqlite3
import json
import logging
import glob
import os

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_anomalous_db_structure():
    """anomalousList.db 테이블 구조를 업데이트하고 상세 데이터를 삽입"""
    
    try:
        db_path = "DB/anomalousList.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 기존 테이블 삭제하고 새로 생성
        cursor.execute("DROP TABLE IF EXISTS manipulation_stocks")
        
        # 새로운 테이블 구조 생성
        cursor.execute('''
            CREATE TABLE manipulation_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_name TEXT NOT NULL,
                stock_code TEXT NOT NULL,
                category TEXT,
                manipulation_period TEXT,
                max_rise_rate REAL,
                manipulation_type TEXT,
                description TEXT,
                급등빈발_일수 INTEGER,
                급등빈발_기간 TEXT,
                극심한급등_최대등락률 REAL,
                극심한급등_기간 TEXT,
                거래량급증빈발_일수 INTEGER,
                거래량급증빈발_기간 TEXT,
                상한가근처_일수 INTEGER,
                상한가근처_기간 TEXT,
                평균회전율 REAL,
                위험도점수 INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        logger.info("✅ anomalousList.db 테이블 구조 업데이트 완료")
        
        # 패턴 분석 결과 JSON 파일 찾기
        json_files = glob.glob("Result/pattern_analysis_results_*.json")
        
        if not json_files:
            logger.warning("패턴 분석 결과 JSON 파일이 없습니다.")
            conn.close()
            return
        
        # 가장 최근 파일 선택
        latest_json = max(json_files, key=os.path.getctime)
        logger.info(f"패턴 분석 결과 파일 사용: {latest_json}")
        
        with open(latest_json, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        inserted_count = 0
        
        for result in analysis_data.get('detailed_results', []):
            # MEDIUM RISK 이상만 처리
            risk_level = result.get('risk_level', '')
            if '🟡 MEDIUM RISK' in risk_level or '🔴 HIGH RISK' in risk_level:
                
                patterns = result.get('patterns', {})
                warnings = result.get('warnings', [])
                
                # 조작 유형 결정
                manipulation_types = []
                if patterns.get('급등일수', 0) > 5:
                    manipulation_types.append('급등빈발')
                if patterns.get('거래량폭등일수', 0) > 10:
                    manipulation_types.append('거래량조작')
                if patterns.get('상한가근처일수', 0) > 3:
                    manipulation_types.append('상한가조작')
                
                manipulation_type = ', '.join(manipulation_types) if manipulation_types else '기타'
                
                # 기간 정보 (3년간 분석)
                period_info = result.get('data_summary', {}).get('period', '2022-05-26 ~ 2025-05-23')
                
                # 급등빈발 기간 계산 (전체 기간에서 급등일수 비율)
                급등일수 = patterns.get('급등일수', 0)
                급등빈발_기간 = f"{period_info} 중 {급등일수}일" if 급등일수 > 0 else None
                
                # 극심한 급등 기간 (최대 등락률 발생 시점)
                최대등락률 = patterns.get('최대등락률', 0)
                극심한급등_기간 = f"{period_info} 중 최대 {최대등락률:.1f}%" if 최대등락률 > 25 else None
                
                # 거래량 급증 기간
                거래량폭등일수 = patterns.get('거래량폭등일수', 0)
                거래량급증빈발_기간 = f"{period_info} 중 {거래량폭등일수}일" if 거래량폭등일수 > 0 else None
                
                # 상한가 근처 기간
                상한가근처일수 = patterns.get('상한가근처일수', 0)
                상한가근처_기간 = f"{period_info} 중 {상한가근처일수}일" if 상한가근처일수 > 0 else None
                
                # 설명 생성
                description = f"패턴 분석 결과: {len(warnings)}개 이상 패턴 감지. " + "; ".join(warnings[:3])
                
                # 데이터 삽입
                cursor.execute('''
                    INSERT INTO manipulation_stocks 
                    (stock_name, stock_code, category, manipulation_period, max_rise_rate, 
                     manipulation_type, description, 급등빈발_일수, 급등빈발_기간, 
                     극심한급등_최대등락률, 극심한급등_기간, 거래량급증빈발_일수, 거래량급증빈발_기간,
                     상한가근처_일수, 상한가근처_기간, 평균회전율, 위험도점수)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result['stock_name'],
                    result['stock_code'],
                    '패턴분석',
                    '3년간',
                    patterns.get('최대등락률', 0),
                    manipulation_type,
                    description,
                    급등일수,
                    급등빈발_기간,
                    최대등락률,
                    극심한급등_기간,
                    거래량폭등일수,
                    거래량급증빈발_기간,
                    상한가근처일수,
                    상한가근처_기간,
                    patterns.get('평균회전율', 0),
                    result.get('risk_score', 0)
                ))
                
                inserted_count += 1
                logger.info(f"🚨 {result['stock_name']} ({result['stock_code']}) 상세 데이터 삽입")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ anomalousList.db에 {inserted_count}개 종목 상세 데이터 삽입 완료")
        
    except Exception as e:
        logger.error(f"❌ anomalousList.db 업데이트 실패: {str(e)}")

def check_updated_db():
    """업데이트된 DB 구조와 데이터 확인"""
    try:
        db_path = "DB/anomalousList.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n" + "=" * 80)
        print("📊 업데이트된 anomalousList.db 확인")
        print("=" * 80)
        
        # 테이블 구조 확인
        cursor.execute("PRAGMA table_info(manipulation_stocks)")
        columns = cursor.fetchall()
        
        print("📋 테이블 구조:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        
        print(f"\n📈 데이터 내용:")
        cursor.execute('''
            SELECT stock_name, stock_code, 급등빈발_일수, 급등빈발_기간, 
                   극심한급등_최대등락률, 극심한급등_기간, 거래량급증빈발_일수, 거래량급증빈발_기간,
                   위험도점수
            FROM manipulation_stocks
        ''')
        
        results = cursor.fetchall()
        
        for row in results:
            print(f"\n🚨 {row[0]} ({row[1]})")
            print(f"   급등빈발: {row[2]}일 - {row[3]}")
            print(f"   극심한급등: {row[4]:.1f}% - {row[5]}")
            print(f"   거래량급증: {row[6]}일 - {row[7]}")
            print(f"   위험도점수: {row[8]}점")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ DB 확인 실패: {str(e)}")

def main():
    """메인 실행 함수"""
    print("=== 🚨 anomalousList.db 상세 패턴 업데이트 시스템 ===\n")
    print("📊 상세 패턴 컬럼을 추가하고 데이터를 업데이트합니다...\n")
    
    # 1. DB 구조 업데이트 및 데이터 삽입
    print("📋 1단계: 테이블 구조 업데이트 및 상세 데이터 삽입")
    update_anomalous_db_structure()
    print()
    
    # 2. 업데이트된 DB 확인
    print("📊 2단계: 업데이트된 DB 확인")
    check_updated_db()
    
    print("\n🎯 anomalousList.db 상세 패턴 업데이트 완료!")
    print("💡 TIP: 이제 각 종목의 상세한 패턴 정보를 확인할 수 있습니다.")

if __name__ == "__main__":
    main() 