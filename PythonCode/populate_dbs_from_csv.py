import sqlite3
import pandas as pd
import os
import glob
import logging
import json
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DBPopulator:
    """CSV 데이터를 각 DB에 삽입하는 클래스"""
    
    def __init__(self):
        self.db_paths = {
            'collectList': 'DB/collectList.db',
            'collectCompleteData': 'DB/collectCompleteData.db',
            'anomalousList': 'DB/anomalousList.db'
        }
    
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
    
    def extract_stock_info_from_filename(self, filename):
        """파일명에서 종목명과 종목코드를 추출"""
        basename = os.path.basename(filename)
        name_without_ext = basename.replace('.csv', '')
        parts = name_without_ext.split('_')
        
        if len(parts) >= 2:
            stock_name = parts[0]
            stock_code = parts[1]
            return stock_name, stock_code
        return None, None
    
    def populate_collect_list(self):
        """1. collectList.db에 종목 정보 삽입"""
        try:
            csv_files = glob.glob("Result/*.csv")
            if not csv_files:
                logger.warning("Result 폴더에 CSV 파일이 없습니다.")
                return
            
            conn = sqlite3.connect(self.db_paths['collectList'])
            cursor = conn.cursor()
            
            # 기존 데이터 확인
            cursor.execute("SELECT COUNT(*) FROM collection_stocks")
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                logger.info(f"collectList.db에 이미 {existing_count}개 종목이 있습니다.")
                conn.close()
                return
            
            for csv_file in csv_files:
                stock_name, stock_code = self.extract_stock_info_from_filename(csv_file)
                if stock_name and stock_code:
                    cursor.execute('''
                        INSERT OR IGNORE INTO collection_stocks (주식명, 주식코드)
                        VALUES (?, ?)
                    ''', (stock_name, stock_code))
                    logger.info(f"📈 {stock_name} ({stock_code}) 추가")
            
            conn.commit()
            conn.close()
            logger.info("✅ collectList.db 데이터 삽입 완료")
            
        except Exception as e:
            logger.error(f"❌ collectList.db 데이터 삽입 실패: {str(e)}")
    
    def populate_collect_complete_data(self):
        """2. collectCompleteData.db에 상세 주식 데이터 삽입"""
        try:
            csv_files = glob.glob("Result/*.csv")
            if not csv_files:
                logger.warning("Result 폴더에 CSV 파일이 없습니다.")
                return
            
            conn = sqlite3.connect(self.db_paths['collectCompleteData'])
            
            total_inserted = 0
            
            for csv_file in csv_files:
                stock_name, stock_code = self.extract_stock_info_from_filename(csv_file)
                if not stock_name or not stock_code:
                    continue
                
                logger.info(f"📊 {stock_name} ({stock_code}) 데이터 처리 중...")
                
                # CSV 파일 읽기
                df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
                
                # 데이터 전처리
                processed_data = []
                
                for date, row in df.iterrows():
                    date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
                    
                    data_row = {
                        '주식명': stock_name,
                        '주식코드': stock_code,
                        '날짜': date_str,
                        '시가': self.safe_int(row.get('시가')),
                        '고가': self.safe_int(row.get('고가')),
                        '저가': self.safe_int(row.get('저가')),
                        '종가': self.safe_int(row.get('종가')),
                        '거래량': self.safe_int(row.get('거래량')),
                        '등락률': self.safe_float(row.get('등락률')),
                        '시가총액': self.safe_int(row.get('시가총액')),
                        '거래량_cap': self.safe_int(row.get('거래량_cap')),
                        '거래대금': self.safe_int(row.get('거래대금')),
                        '상장주식수': self.safe_int(row.get('상장주식수')),
                        'BPS': self.safe_float(row.get('BPS')),
                        'PER': self.safe_float(row.get('PER')),
                        'PBR': self.safe_float(row.get('PBR')),
                        'EPS': self.safe_float(row.get('EPS')),
                        'DIV': self.safe_float(row.get('DIV')),
                        'DPS': self.safe_float(row.get('DPS')),
                        '기관합계': self.safe_int(row.get('기관합계')),
                        '기타법인': self.safe_int(row.get('기타법인')),
                        '개인': self.safe_int(row.get('개인')),
                        '외국인합계': self.safe_int(row.get('외국인합계'))
                    }
                    processed_data.append(data_row)
                
                # 배치 삽입
                if processed_data:
                    df_to_insert = pd.DataFrame(processed_data)
                    df_to_insert.to_sql('completed_stocks', conn, if_exists='append', index=False, method='multi')
                    total_inserted += len(processed_data)
                    logger.info(f"✅ {stock_name} 데이터 {len(processed_data)}건 삽입")
            
            conn.close()
            logger.info(f"✅ collectCompleteData.db 총 {total_inserted:,}건 데이터 삽입 완료")
            
        except Exception as e:
            logger.error(f"❌ collectCompleteData.db 데이터 삽입 실패: {str(e)}")
    
    def populate_anomalous_list(self):
        """3. anomalousList.db에 패턴 분석 결과 삽입"""
        try:
            # 패턴 분석 결과 JSON 파일 찾기
            json_files = glob.glob("Result/pattern_analysis_results_*.json")
            
            if not json_files:
                logger.warning("패턴 분석 결과 JSON 파일이 없습니다.")
                return
            
            # 가장 최근 파일 선택
            latest_json = max(json_files, key=os.path.getctime)
            logger.info(f"패턴 분석 결과 파일 사용: {latest_json}")
            
            with open(latest_json, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            conn = sqlite3.connect(self.db_paths['anomalousList'])
            cursor = conn.cursor()
            
            inserted_count = 0
            
            for result in analysis_data.get('detailed_results', []):
                # MEDIUM RISK 이상만 작전주 테이블에 삽입
                risk_level = result.get('risk_level', '')
                if '🟡 MEDIUM RISK' in risk_level or '🔴 HIGH RISK' in risk_level:
                    
                    # 조작 유형 결정
                    patterns = result.get('patterns', {})
                    manipulation_types = []
                    
                    if patterns.get('급등일수', 0) > 5:
                        manipulation_types.append('급등빈발')
                    if patterns.get('거래량폭등일수', 0) > 10:
                        manipulation_types.append('거래량조작')
                    if patterns.get('상한가근처일수', 0) > 3:
                        manipulation_types.append('상한가조작')
                    
                    manipulation_type = ', '.join(manipulation_types) if manipulation_types else '기타'
                    
                    # 설명 생성
                    warnings = result.get('warnings', [])
                    description = f"패턴 분석 결과: {len(warnings)}개 이상 패턴 감지. " + "; ".join(warnings[:3])
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO manipulation_stocks 
                        (stock_name, stock_code, category, manipulation_period, 
                         max_rise_rate, manipulation_type, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        result['stock_name'],
                        result['stock_code'],
                        '패턴분석',
                        '3년간',
                        patterns.get('최대등락률', 0),
                        manipulation_type,
                        description
                    ))
                    
                    inserted_count += 1
                    logger.info(f"🚨 {result['stock_name']} ({result['stock_code']}) - {risk_level}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ anomalousList.db에 {inserted_count}개 의심 종목 삽입 완료")
            
        except Exception as e:
            logger.error(f"❌ anomalousList.db 데이터 삽입 실패: {str(e)}")
    
    def check_all_dbs(self):
        """모든 DB의 데이터 상태 확인"""
        print("\n" + "=" * 60)
        print("📊 모든 DB 데이터 상태 확인")
        print("=" * 60)
        
        db_info = [
            ('collectList.db', 'collection_stocks', '수집 종목'),
            ('collectCompleteData.db', 'completed_stocks', '등록 완료 데이터'),
            ('anomalousList.db', 'manipulation_stocks', '작전주 의심 종목')
        ]
        
        for db_file, table_name, description in db_info:
            db_path = f"DB/{db_file}"
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                
                print(f"✅ {db_file}")
                print(f"   - 설명: {description}")
                print(f"   - 데이터: {count:,}건")
                
                # 샘플 데이터 표시
                if count > 0:
                    if table_name == 'collection_stocks':
                        cursor.execute("SELECT 주식명, 주식코드 FROM collection_stocks LIMIT 3")
                        samples = cursor.fetchall()
                        print(f"   - 샘플: {samples}")
                    elif table_name == 'completed_stocks':
                        cursor.execute("SELECT 주식명, 주식코드, COUNT(*) as cnt FROM completed_stocks GROUP BY 주식코드 LIMIT 3")
                        samples = cursor.fetchall()
                        print(f"   - 샘플: {samples}")
                    elif table_name == 'manipulation_stocks':
                        cursor.execute("SELECT stock_name, stock_code, manipulation_type FROM manipulation_stocks LIMIT 3")
                        samples = cursor.fetchall()
                        print(f"   - 샘플: {samples}")
                
                conn.close()
                
            except Exception as e:
                print(f"❌ {db_file} - 오류: {str(e)}")
            
            print()

def main():
    """메인 실행 함수"""
    print("=== 📊 K-Stock Pattern Insight DB 데이터 삽입 시스템 ===\n")
    print("📁 Result 폴더의 CSV 파일들을 각 DB에 맞게 데이터를 삽입합니다...\n")
    
    populator = DBPopulator()
    
    # 1. collectList.db 데이터 삽입
    print("📋 1단계: collectList.db 종목 정보 삽입")
    populator.populate_collect_list()
    print()
    
    # 2. collectCompleteData.db 데이터 삽입
    print("📊 2단계: collectCompleteData.db 상세 데이터 삽입")
    populator.populate_collect_complete_data()
    print()
    
    # 3. anomalousList.db 데이터 삽입
    print("🚨 3단계: anomalousList.db 의심 종목 삽입")
    populator.populate_anomalous_list()
    print()
    
    # 4. 모든 DB 상태 확인
    populator.check_all_dbs()
    
    print("🎯 모든 DB 데이터 삽입 완료!")
    print("💡 TIP: 이제 각 DB에서 필요한 데이터를 조회할 수 있습니다.")

if __name__ == "__main__":
    main() 