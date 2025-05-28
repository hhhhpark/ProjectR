import sys
sys.path.append('PythonCode')
from pattern_analyzer import StockPatternAnalyzer
import pandas as pd
import glob

# 진원생명과학 CSV 파일 로드
csv_files = glob.glob('Result/*011000*.csv')
if csv_files:
    print(f"CSV 파일: {csv_files[0]}")
    df = pd.read_csv(csv_files[0], index_col=0, parse_dates=True)
    
    # 패턴 분석 실행
    analyzer = StockPatternAnalyzer()
    patterns = analyzer.analyze_manipulation_patterns(df, '진원생명과학')
    
    print("\n=== 패턴 분석 결과 ===")
    for key, value in patterns.items():
        print(f"{key}: {value}")
    
    print("\n=== 기간 관련 정보만 ===")
    for key, value in patterns.items():
        if '기간' in key or '날짜' in key:
            print(f"{key}: {value}")
    
    # 급등 발생 날짜 직접 확인
    if '등락률' in df.columns:
        extreme_up = df[df['등락률'] > 15]
        print(f"\n=== 급등(15% 이상) 발생 상세 ===")
        print(f"총 {len(extreme_up)}회 발생")
        if len(extreme_up) > 0:
            print("발생 날짜들:")
            for date, rate in extreme_up['등락률'].items():
                print(f"  {date.strftime('%Y-%m-%d')}: {rate:.1f}%")
else:
    print("CSV 파일을 찾을 수 없습니다.") 