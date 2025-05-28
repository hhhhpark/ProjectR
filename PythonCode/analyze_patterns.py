import pandas as pd
import os
import glob
from pattern_analyzer import StockPatternAnalyzer
from db_manager import DatabaseManager
import logging
import numpy as np
import json
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_csv_data(csv_path):
    """CSV 파일에서 데이터를 로드합니다."""
    try:
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        return df
    except Exception as e:
        logger.error(f"CSV 파일 로딩 실패 ({csv_path}): {str(e)}")
        return None

def extract_stock_info_from_filename(filename):
    """파일명에서 종목명과 종목코드를 추출합니다."""
    basename = os.path.basename(filename)
    name_without_ext = basename.replace('.csv', '')
    
    # 종목명_종목코드 형식에서 분리
    parts = name_without_ext.split('_')
    if len(parts) >= 2:
        stock_name = parts[0]
        stock_code = parts[1]
        return stock_name, stock_code
    else:
        # 기존 형식 (종목명_comprehensive_data) 처리
        stock_name = name_without_ext.replace('_comprehensive_data', '')
        return stock_name, None

def save_analysis_to_db(analysis_results):
    """분석 결과를 DB에 저장합니다."""
    try:
        def convert_numpy_types(obj):
            """numpy 타입을 Python 기본 타입으로 변환"""
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj
        
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        for result in analysis_results:
            # 패턴 데이터를 JSON 문자열로 변환 (numpy 타입 변환 포함)
            patterns_converted = convert_numpy_types(result['patterns'])
            patterns_json = json.dumps(patterns_converted, ensure_ascii=False)
            warnings_json = json.dumps(result['warnings'], ensure_ascii=False)
            
            # 최대 상승률 계산 (패턴에서 추출)
            max_rise_rate = float(result['patterns'].get('최대등락률', 0))
            
            # 조작 유형 결정
            manipulation_type = []
            if result['patterns'].get('급등일수', 0) > 5:
                manipulation_type.append('급등빈발')
            if result['patterns'].get('거래량폭등일수', 0) > 10:
                manipulation_type.append('거래량조작')
            if result['patterns'].get('상한가근처일수', 0) > 3:
                manipulation_type.append('상한가조작')
            
            manipulation_type_str = ', '.join(manipulation_type) if manipulation_type else '정상'
            
            # DB에 삽입
            cursor.execute('''
                INSERT OR REPLACE INTO manipulation_analysis 
                (stock_name, stock_code, category, manipulation_period, max_rise_rate, 
                 manipulation_type, risk_level, risk_score, description, 
                 analysis_patterns, warnings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result['stock_name'],
                result['stock_code'],
                '패턴분석',
                result['data_summary']['period'],
                max_rise_rate,
                manipulation_type_str,
                result['risk_level'],
                int(result['risk_score']),
                f"3년간 데이터 분석 결과 - {len(result['warnings'])}개 이상 패턴 감지",
                patterns_json,
                warnings_json
            ))
        
        conn.commit()
        conn.close()
        
        print(f"\n💾 분석 결과 {len(analysis_results)}건이 DB에 저장되었습니다.")
        
    except Exception as e:
        logger.error(f"DB 저장 실패: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """패턴 분석 메인 실행 함수"""
    # 명령행 인자로 종목코드가 전달된 경우 단일 종목 처리
    if len(sys.argv) > 1:
        stock_code = sys.argv[1]
        
        # 패턴 분석기 초기화
        analyzer = StockPatternAnalyzer()
        
        # Result 디렉토리에서 해당 종목의 CSV 파일 찾기
        csv_files = glob.glob(f"Result/*_{stock_code}.csv")
        
        if not csv_files:
            logger.error(f"종목코드 {stock_code}에 해당하는 CSV 파일을 찾을 수 없습니다.")
            return
        
        csv_file = csv_files[0]  # 첫 번째 파일 사용
        
        # 파일명에서 종목 정보 추출
        stock_name, _ = extract_stock_info_from_filename(csv_file)
        
        logger.info(f"단일 종목 패턴 분석 시작: {stock_name} ({stock_code})")
        
        # CSV 데이터 로드
        df = load_csv_data(csv_file)
        
        if df is not None:
            # 패턴 분석 수행
            analysis_result = analyzer.analyze_stock_data(df, stock_name, stock_code)
            
            if analysis_result:
                # 분석 결과 출력
                analyzer.print_analysis_result(analysis_result)
                
                # 분석 결과를 DB에 저장
                save_analysis_to_db([analysis_result])
                
                # 작전주 의심 종목인지 확인하고 anomalousList.db에 저장
                save_to_anomalous_db_if_suspicious(analysis_result)
                
                logger.info(f"단일 종목 패턴 분석 완료: {stock_name} ({stock_code})")
            else:
                logger.error(f"패턴 분석 실패: {stock_name} ({stock_code})")
        else:
            logger.error(f"데이터 로딩 실패: {stock_name} ({stock_code})")
        return
    
    # 기존 전체 종목 처리 로직
    print("=== 🎯 K-Stock Pattern Insight 패턴 분석 시스템 ===\n")
    print("📊 수집된 데이터의 패턴 분석을 시작합니다...\n")
    
    # 패턴 분석기 초기화
    analyzer = StockPatternAnalyzer()
    
    # Result 디렉토리에서 CSV 파일들 찾기
    csv_files = glob.glob("Result/*.csv")
    
    if not csv_files:
        print("❌ Result 디렉토리에 분석할 CSV 파일이 없습니다.")
        print("💡 먼저 stock_scrap.py를 실행하여 데이터를 수집하세요.")
        return
    
    print(f"📋 총 {len(csv_files)}개 CSV 파일 발견\n")
    
    analysis_results = []
    
    for csv_file in csv_files:
        # 파일명에서 종목 정보 추출
        stock_name, stock_code = extract_stock_info_from_filename(csv_file)
        
        print(f"📈 {stock_name} ({stock_code}) 패턴 분석 중...")
        
        # CSV 데이터 로드
        df = load_csv_data(csv_file)
        
        if df is not None:
            # 패턴 분석 수행
            analysis_result = analyzer.analyze_stock_data(df, stock_name, stock_code)
            
            if analysis_result:
                # 분석 결과 출력
                analyzer.print_analysis_result(analysis_result)
                analysis_results.append(analysis_result)
                print()  # 빈 줄 추가
            else:
                print(f"❌ {stock_name} 패턴 분석 실패\n")
        else:
            print(f"❌ {stock_name} 데이터 로딩 실패\n")
    
    # 종합 분석 결과 요약
    if analysis_results:
        summary = analyzer.generate_summary_report(analysis_results)
        
        # 분석 결과를 JSON 파일로 저장
        save_analysis_results(analysis_results, summary)
        
        # 분석 결과를 DB에 저장
        save_analysis_to_db(analysis_results)
    else:
        print("❌ 분석 가능한 데이터가 없습니다.")

def save_analysis_results(analysis_results, summary):
    """분석 결과를 파일로 저장합니다."""
    try:
        import json
        from datetime import datetime
        
        def convert_numpy_types(obj):
            """numpy 타입을 Python 기본 타입으로 변환"""
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj
        
        # 결과 데이터 준비
        results_data = {
            'analysis_date': datetime.now().isoformat(),
            'summary': convert_numpy_types(summary),
            'detailed_results': []
        }
        
        for result in analysis_results:
            # pandas 객체들을 직렬화 가능한 형태로 변환
            detailed_result = {
                'stock_name': result['stock_name'],
                'stock_code': result['stock_code'],
                'risk_level': result['risk_level'],
                'risk_score': int(result['risk_score']),
                'warnings': result['warnings'],
                'patterns': convert_numpy_types(result['patterns']),
                'data_summary': convert_numpy_types(result['data_summary'])
            }
            
            # 숫자 데이터 처리
            if 'recent_market_cap' in result:
                detailed_result['recent_market_cap'] = float(result['recent_market_cap'])
            if 'avg_trading_value' in result:
                detailed_result['avg_trading_value'] = float(result['avg_trading_value'])
            if 'avg_short_balance' in result:
                detailed_result['avg_short_balance'] = float(result['avg_short_balance'])
            
            results_data['detailed_results'].append(detailed_result)
        
        # JSON 파일로 저장
        output_file = f"Result/pattern_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 분석 결과가 {output_file}에 저장되었습니다.")
        
    except Exception as e:
        logger.error(f"분석 결과 저장 실패: {str(e)}")

def save_to_anomalous_db_if_suspicious(analysis_result):
    """작전주 의심 종목인 경우 anomalousList.db에 저장"""
    try:
        # 위험도가 MEDIUM 이상인 경우만 저장
        if 'MEDIUM' in analysis_result['risk_level'] or 'HIGH' in analysis_result['risk_level']:
            import sqlite3
            
            conn = sqlite3.connect("DB/anomalousList.db")
            cursor = conn.cursor()
            
            # 기존 데이터 삭제 (중복 방지)
            cursor.execute("DELETE FROM manipulation_stocks WHERE stock_code = ?", 
                          (analysis_result['stock_code'],))
            
            # 패턴에서 상세 정보 추출
            patterns = analysis_result['patterns']
            
            # 급등빈발 기간 정보 (실제 발생 날짜들 사용)
            급등빈발_일수 = patterns.get('급등일수', 0)
            급등_발생날짜 = patterns.get('급등_발생날짜', [])
            if 급등_발생날짜:
                if len(급등_발생날짜) <= 3:
                    급등빈발_기간 = ', '.join(급등_발생날짜)
                else:
                    급등빈발_기간 = f"{급등_발생날짜[0]}, {급등_발생날짜[1]}, ... {급등_발생날짜[-1]} (총 {급등빈발_일수}일)"
            else:
                급등빈발_기간 = f"{analysis_result['data_summary']['period']} 중 {급등빈발_일수}일"
            
            # 극심한급등 정보 (실제 발생 날짜 사용)
            극심한급등_최대등락률 = patterns.get('최대등락률', 0)
            최대등락률_발생날짜 = patterns.get('최대등락률_발생날짜', '')
            if 최대등락률_발생날짜:
                극심한급등_기간 = f"{최대등락률_발생날짜} ({극심한급등_최대등락률:.1f}%)"
            else:
                극심한급등_기간 = f"최대 {극심한급등_최대등락률:.1f}%"
            
            # 거래량급증 기간 정보 (실제 발생 날짜들 사용)
            거래량급증빈발_일수 = patterns.get('거래량폭등일수', 0)
            거래량급증_발생날짜 = patterns.get('거래량급증_발생날짜', [])
            if 거래량급증_발생날짜:
                if len(거래량급증_발생날짜) <= 3:
                    거래량급증빈발_기간 = ', '.join(거래량급증_발생날짜)
                else:
                    거래량급증빈발_기간 = f"{거래량급증_발생날짜[0]}, {거래량급증_발생날짜[1]}, ... {거래량급증_발생날짜[-1]} (총 {거래량급증빈발_일수}일)"
            else:
                거래량급증빈발_기간 = f"{analysis_result['data_summary']['period']} 중 {거래량급증빈발_일수}일"
            
            # 새 데이터 삽입
            cursor.execute('''
                INSERT INTO manipulation_stocks 
                (stock_name, stock_code, manipulation_type, 급등빈발_일수, 급등빈발_기간,
                 극심한급등_최대등락률, 극심한급등_기간, 거래량급증빈발_일수, 거래량급증빈발_기간,
                 위험도점수, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis_result['stock_name'],
                analysis_result['stock_code'],
                '작전주의심',
                급등빈발_일수,
                급등빈발_기간,
                극심한급등_최대등락률,
                극심한급등_기간,
                거래량급증빈발_일수,
                거래량급증빈발_기간,
                int(analysis_result['risk_score']),
                f"패턴 분석 결과 {analysis_result['risk_level']} 위험도 감지"
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"작전주 의심 종목으로 등록: {analysis_result['stock_name']} ({analysis_result['stock_code']})")
            
    except Exception as e:
        logger.error(f"anomalousList.db 저장 오류: {str(e)}")

if __name__ == "__main__":
    main() 