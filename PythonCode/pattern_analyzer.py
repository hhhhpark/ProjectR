import pandas as pd
import numpy as np
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StockPatternAnalyzer:
    """주식 패턴 분석 및 조작 의심 패턴 탐지 클래스"""
    
    def __init__(self):
        pass
    
    def analyze_manipulation_patterns(self, df, stock_name):
        """작전주/세력주 의심 패턴을 분석합니다."""
        patterns = {}
        
        if df is None or len(df) == 0:
            return patterns
        
        # 1. 급등락 패턴 분석
        if '등락률' in df.columns:
            extreme_up = df[df['등락률'] > 15]  # 15% 이상 급등
            extreme_down = df[df['등락률'] < -15]  # 15% 이상 급락
            patterns['급등일수'] = len(extreme_up)
            patterns['급락일수'] = len(extreme_down)
            patterns['최대등락률'] = df['등락률'].max()
            patterns['최소등락률'] = df['등락률'].min()
            
            # 급등 발생 날짜 정보 추가
            if len(extreme_up) > 0:
                급등_날짜들 = extreme_up.index.strftime('%Y-%m-%d').tolist()
                patterns['급등_발생날짜'] = 급등_날짜들
                patterns['급등_기간'] = f"{급등_날짜들[0]} ~ {급등_날짜들[-1]} 중 {len(extreme_up)}일" if len(급등_날짜들) > 1 else f"{급등_날짜들[0]} (1일)"
            else:
                patterns['급등_기간'] = "해당없음"
            
            # 최대 등락률 발생 날짜 정보 추가
            max_rate_date = df[df['등락률'] == patterns['최대등락률']].index[0]
            patterns['최대등락률_발생날짜'] = max_rate_date.strftime('%Y-%m-%d')
            patterns['극심한급등_기간'] = f"{patterns['최대등락률_발생날짜']} (최대 {patterns['최대등락률']:.1f}%)"
        
        # 2. 거래량 이상 패턴
        if '거래량' in df.columns:
            volume_mean = df['거래량'].mean()
            volume_std = df['거래량'].std()
            volume_spike = df[df['거래량'] > volume_mean + 3*volume_std]
            patterns['거래량폭등일수'] = len(volume_spike)
            patterns['평균거래량'] = volume_mean
            patterns['최대거래량'] = df['거래량'].max()
            
            # 거래량 급증 발생 날짜 정보 추가
            if len(volume_spike) > 0:
                거래량급증_날짜들 = volume_spike.index.strftime('%Y-%m-%d').tolist()
                patterns['거래량급증_발생날짜'] = 거래량급증_날짜들
                patterns['거래량급증_기간'] = f"{거래량급증_날짜들[0]} ~ {거래량급증_날짜들[-1]} 중 {len(volume_spike)}일" if len(거래량급증_날짜들) > 1 else f"{거래량급증_날짜들[0]} (1일)"
            else:
                patterns['거래량급증_기간'] = "해당없음"
        
        # 3. 가격 조작 의심 패턴 (연속 상한가/하한가)
        if '등락률' in df.columns:
            upper_limit = df[df['등락률'] >= 29.5]  # 상한가 근처
            lower_limit = df[df['등락률'] <= -29.5]  # 하한가 근처
            patterns['상한가근처일수'] = len(upper_limit)
            patterns['하한가근처일수'] = len(lower_limit)
        
        # 4. 공매도 비중 분석
        if '비중' in df.columns:
            avg_short_ratio = df['비중'].mean()
            patterns['평균공매도비중'] = avg_short_ratio
            patterns['최대공매도비중'] = df['비중'].max()
        
        # 5. 시가총액 대비 거래대금 비율 (회전율)
        if '거래대금' in df.columns and '시가총액' in df.columns:
            turnover_ratio = (df['거래대금'] / df['시가총액'] * 100).mean()
            patterns['평균회전율'] = turnover_ratio
        
        return patterns

    def detect_suspicious_patterns(self, patterns, stock_name):
        """의심스러운 패턴을 탐지하고 경고를 생성합니다."""
        warnings = []
        risk_score = 0
        
        # 급등락 패턴 검사
        if patterns.get('급등일수', 0) > 5:
            warnings.append(f"⚠️ 급등 빈발: {patterns['급등일수']}일")
            risk_score += 2
        
        if patterns.get('최대등락률', 0) > 25:
            warnings.append(f"⚠️ 극심한 급등: {patterns['최대등락률']:.1f}%")
            risk_score += 3
        
        # 거래량 이상 패턴
        if patterns.get('거래량폭등일수', 0) > 10:
            warnings.append(f"⚠️ 거래량 급증 빈발: {patterns['거래량폭등일수']}일")
            risk_score += 2
        
        # 상하한가 패턴
        if patterns.get('상한가근처일수', 0) > 3:
            warnings.append(f"⚠️ 상한가 빈발: {patterns['상한가근처일수']}일")
            risk_score += 3
        
        # 회전율 이상
        if patterns.get('평균회전율', 0) > 50:
            warnings.append(f"⚠️ 높은 회전율: {patterns['평균회전율']:.1f}%")
            risk_score += 2
        
        # 공매도 비중 이상
        if patterns.get('최대공매도비중', 0) > 10:
            warnings.append(f"⚠️ 높은 공매도 비중: {patterns['최대공매도비중']:.1f}%")
            risk_score += 1
        
        # 위험도 등급 결정
        if risk_score >= 8:
            risk_level = "🔴 HIGH RISK"
        elif risk_score >= 5:
            risk_level = "🟡 MEDIUM RISK"
        elif risk_score >= 2:
            risk_level = "🟢 LOW RISK"
        else:
            risk_level = "✅ NORMAL"
        
        return warnings, risk_level, risk_score
    
    def analyze_stock_data(self, df, stock_name, stock_code):
        """주식 데이터를 종합적으로 분석합니다."""
        if df is None or len(df) == 0:
            logger.error(f"{stock_name} 데이터가 없습니다.")
            return None
        
        # 패턴 분석
        patterns = self.analyze_manipulation_patterns(df, stock_name)
        warnings, risk_level, risk_score = self.detect_suspicious_patterns(patterns, stock_name)
        
        # 분석 결과 구성
        analysis_result = {
            'stock_name': stock_name,
            'stock_code': stock_code,
            'risk_level': risk_level,
            'risk_score': risk_score,
            'warnings': warnings,
            'patterns': patterns,
            'data_summary': {
                'data_size': df.shape,
                'period': f"{df.index.min().strftime('%Y-%m-%d')} ~ {df.index.max().strftime('%Y-%m-%d')}",
                'indicators_count': len(df.columns)
            }
        }
        
        # 주요 지표 추가
        if '시가총액' in df.columns:
            analysis_result['recent_market_cap'] = df['시가총액'].iloc[-1]
        
        if '거래대금' in df.columns:
            analysis_result['avg_trading_value'] = df['거래대금'].mean()
        
        if '공매도잔고' in df.columns and df['공매도잔고'].notna().any():
            analysis_result['avg_short_balance'] = df['공매도잔고'].mean()
        
        return analysis_result
    
    def print_analysis_result(self, analysis_result):
        """분석 결과를 출력합니다."""
        if not analysis_result:
            return
        
        stock_name = analysis_result['stock_name']
        stock_code = analysis_result['stock_code']
        
        print(f"✅ {stock_name} 데이터 분석 완료")
        print(f"   - 종목코드: {stock_code}")
        print(f"   - 데이터 크기: {analysis_result['data_summary']['data_size']}")
        print(f"   - 수집 기간: {analysis_result['data_summary']['period']}")
        print(f"   - 수집된 지표: {analysis_result['data_summary']['indicators_count']}개")
        
        # 패턴 분석 결과 출력
        print(f"   📊 패턴 분석 결과:")
        print(f"      위험도: {analysis_result['risk_level']} (점수: {analysis_result['risk_score']})")
        
        if analysis_result['warnings']:
            print(f"      감지된 이상 패턴:")
            for warning in analysis_result['warnings']:
                print(f"         {warning}")
        else:
            print(f"      ✅ 특별한 이상 패턴이 감지되지 않았습니다.")
        
        # 주요 지표 요약
        if 'recent_market_cap' in analysis_result:
            print(f"   💰 최근 시가총액: {analysis_result['recent_market_cap']:,.0f} 원")
        
        if 'avg_trading_value' in analysis_result:
            print(f"   💵 평균 거래대금: {analysis_result['avg_trading_value']:,.0f} 원")
        
        if analysis_result['patterns'].get('평균회전율'):
            print(f"   🔄 평균 회전율: {analysis_result['patterns']['평균회전율']:.2f}%")
        
        if 'avg_short_balance' in analysis_result:
            print(f"   📉 평균 공매도 잔고: {analysis_result['avg_short_balance']:,.0f} 주")
            if analysis_result['patterns'].get('평균공매도비중'):
                print(f"   📊 평균 공매도 비중: {analysis_result['patterns']['평균공매도비중']:.2f}%")
    
    def generate_summary_report(self, analysis_results):
        """종합 분석 결과 요약 리포트를 생성합니다."""
        print("=" * 60)
        print("📋 종합 분석 결과 요약")
        print("=" * 60)
        
        # 위험도별 분류
        high_risk = [r for r in analysis_results if '🔴' in r['risk_level']]
        medium_risk = [r for r in analysis_results if '🟡' in r['risk_level']]
        low_risk = [r for r in analysis_results if '🟢' in r['risk_level']]
        normal = [r for r in analysis_results if '✅' in r['risk_level']]
        
        if high_risk:
            high_risk_names = [f"{r['stock_name']}({r['stock_code']})" for r in high_risk]
            print(f"🚨 HIGH RISK 종목: {high_risk_names}")
        if medium_risk:
            medium_risk_names = [f"{r['stock_name']}({r['stock_code']})" for r in medium_risk]
            print(f"⚠️  MEDIUM RISK 종목: {medium_risk_names}")
        if low_risk:
            low_risk_names = [f"{r['stock_name']}({r['stock_code']})" for r in low_risk]
            print(f"🟢 LOW RISK 종목: {low_risk_names}")
        if normal:
            normal_names = [f"{r['stock_name']}({r['stock_code']})" for r in normal]
            print(f"✅ NORMAL 종목: {normal_names}")
        
        print(f"\n🎯 총 {len(analysis_results)}개 종목 분석 완료!")
        print("📁 생성된 CSV 파일들을 확인하여 상세한 데이터를 분석하세요.")
        print("\n💡 TIP: HIGH/MEDIUM RISK 종목은 추가적인 정밀 분석을 권장합니다.")
        
        return {
            'high_risk': high_risk,
            'medium_risk': medium_risk,
            'low_risk': low_risk,
            'normal': normal,
            'total_count': len(analysis_results)
        } 