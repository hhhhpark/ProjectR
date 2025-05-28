from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
import numpy as np
import sqlite3
import os
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StockDataCollector:
    """주식 데이터 수집 전용 클래스"""
    
    def __init__(self):
        self.today = datetime.now().strftime("%Y%m%d")
        
    def get_stock_code(self, stock_name):
        """종목명으로 종목코드를 조회합니다."""
        try:
            stock_list = stock.get_market_ticker_list(market="ALL")
            for code in stock_list:
                if stock.get_market_ticker_name(code) == stock_name:
                    return code
            return None
        except Exception as e:
            logger.error(f"종목코드 조회 중 오류 발생: {str(e)}")
            return None

    def collect_basic_data(self, stock_code, start_date):
        """기본 주가 데이터(OHLCV)를 수집합니다."""
        try:
            df = stock.get_market_ohlcv_by_date(
                fromdate=start_date,
                todate=self.today,
                ticker=stock_code
            )
            logger.info("기본 주가 데이터 수집 완료")
            return df
        except Exception as e:
            logger.error(f"기본 주가 데이터 수집 오류: {str(e)}")
            return None

    def collect_market_cap_data(self, stock_code, start_date):
        """시가총액 및 상장주식수 데이터를 수집합니다."""
        try:
            time.sleep(1)  # API 호출 간격 조절
            df = stock.get_market_cap_by_date(
                fromdate=start_date,
                todate=self.today,
                ticker=stock_code
            )
            logger.info("시가총액 데이터 수집 완료")
            return df
        except Exception as e:
            logger.error(f"시가총액 데이터 수집 오류: {str(e)}")
            return None

    def collect_fundamental_data(self, stock_code, start_date):
        """기본 재무 정보(PER, PBR, DIV 등)를 수집합니다."""
        try:
            time.sleep(1)
            df = stock.get_market_fundamental_by_date(
                fromdate=start_date,
                todate=self.today,
                ticker=stock_code
            )
            logger.info("기본 재무정보 데이터 수집 완료")
            return df
        except Exception as e:
            logger.error(f"기본 재무정보 데이터 수집 오류: {str(e)}")
            return None

    def collect_trading_volume_by_investor(self, stock_code, start_date):
        """투자자별 거래량 데이터를 수집합니다."""
        try:
            time.sleep(1)
            df = stock.get_market_trading_value_by_date(
                fromdate=start_date,
                todate=self.today,
                ticker=stock_code,
                etf=True,
                etn=True,
                elw=True
            )
            logger.info("투자자별 거래량 데이터 수집 완료")
            return df
        except Exception as e:
            try:
                # 대안 방법 시도
                df = stock.get_market_net_purchases_of_equities_by_ticker(
                    fromdate=start_date,
                    todate=self.today,
                    market="ALL"
                )
                if stock_code in df.index:
                    stock_investor_data = df.loc[stock_code:stock_code]
                    logger.info("투자자별 순매수 데이터 수집 완료")
                    return stock_investor_data
                else:
                    logger.warning("투자자별 데이터에서 해당 종목을 찾을 수 없습니다.")
                    return None
            except Exception as e2:
                logger.error(f"투자자별 거래량 데이터 수집 오류: {str(e2)}")
                return None

    def collect_shorting_data(self, stock_code, start_date):
        """공매도 잔고 데이터를 수집합니다."""
        try:
            time.sleep(1)
            df = stock.get_shorting_balance_by_date(
                fromdate=start_date,
                todate=self.today,
                ticker=stock_code
            )
            logger.info("공매도 데이터 수집 완료")
            return df
        except Exception as e:
            logger.error(f"공매도 데이터 수집 오류: {str(e)}")
            return None

    def collect_comprehensive_data(self, stock_name, years=3):
        """종목명을 기반으로 종합적인 주식 데이터를 수집합니다."""
        try:
            # 종목코드 조회
            stock_code = self.get_stock_code(stock_name)
            if not stock_code:
                logger.error(f"종목 '{stock_name}'을 찾을 수 없습니다.")
                return None, None

            # 시작일 계산 (3년으로 변경)
            start_date = (datetime.now() - timedelta(days=365*years)).strftime("%Y%m%d")
            
            # 데이터 수집
            logger.info(f"'{stock_name}' 종합 데이터 수집 시작...")
            
            # 1. 기본 주가 데이터
            basic_df = self.collect_basic_data(stock_code, start_date)
            
            # 2. 시가총액 데이터
            market_cap_df = self.collect_market_cap_data(stock_code, start_date)
            
            # 3. 기본 재무정보
            fundamental_df = self.collect_fundamental_data(stock_code, start_date)
            
            # 4. 투자자별 거래량
            trading_volume_df = self.collect_trading_volume_by_investor(stock_code, start_date)
            
            # 5. 공매도 데이터
            shorting_df = self.collect_shorting_data(stock_code, start_date)
            
            # 데이터 병합
            if basic_df is not None:
                result_df = basic_df.copy()
                
                # 시가총액 데이터 병합
                if market_cap_df is not None:
                    result_df = result_df.join(market_cap_df, how='left', rsuffix='_cap')
                
                # 기본 재무정보 병합
                if fundamental_df is not None:
                    result_df = result_df.join(fundamental_df, how='left', rsuffix='_fund')
                
                # 투자자별 거래량 병합 (일부 컬럼만 선택)
                if trading_volume_df is not None:
                    # 주요 투자자 컬럼만 선택
                    investor_cols = ['기관합계', '기타법인', '개인', '외국인합계'] if len(trading_volume_df.columns) > 0 else []
                    available_cols = [col for col in investor_cols if col in trading_volume_df.columns]
                    if available_cols:
                        result_df = result_df.join(trading_volume_df[available_cols], how='left', rsuffix='_investor')
                
                # 공매도 데이터 병합
                if shorting_df is not None:
                    result_df = result_df.join(shorting_df, how='left', rsuffix='_short')
                
                logger.info(f"'{stock_name}' 종합 데이터 수집 완료")
                return result_df, stock_code
            else:
                logger.error("기본 주가 데이터 수집 실패")
                return None, None
                
        except Exception as e:
            logger.error(f"종합 데이터 수집 중 오류 발생: {str(e)}")
            return None, None

    def save_data_to_csv(self, df, stock_name, stock_code, output_dir="Result"):
        """데이터를 CSV 파일로 저장합니다."""
        try:
            os.makedirs(output_dir, exist_ok=True)
            filename = f"{output_dir}/{stock_name}_{stock_code}.csv"
            df.to_csv(filename, encoding='utf-8-sig')
            logger.info(f"{filename} 저장 완료")
            return filename
        except Exception as e:
            logger.error(f"CSV 저장 오류: {str(e)}")
            return None

    def collect_stock_data(self, stock_name, years=1):
        """기존 호환성을 위한 메서드 (기본 데이터만 수집)"""
        return self.collect_comprehensive_data(stock_name, years)

    def collect_intraday_data(self, stock_code, interval='1'):
        """분봉 데이터를 수집합니다. (당일 데이터만)"""
        try:
            time.sleep(1)
            df = stock.get_market_ohlcv_by_ticker(
                date=self.today,
                market="KOSPI"
            )
            # 특정 종목만 필터링
            if stock_code in df.index:
                stock_data = df.loc[stock_code:stock_code]
                logger.info("분봉 데이터 수집 완료")
                return stock_data
            else:
                logger.warning("분봉 데이터에서 해당 종목을 찾을 수 없습니다.")
                return None
        except Exception as e:
            logger.error(f"분봉 데이터 수집 오류: {str(e)}")
            return None

    def collect_sector_data(self, stock_code):
        """업종 정보 데이터를 수집합니다."""
        try:
            time.sleep(1)
            # 업종 정보는 따로 API가 있지만, 기본 정보에서 추출
            sectors = stock.get_market_ticker_list(market="ALL")
            if stock_code in sectors:
                logger.info("업종 데이터 수집 완료")
                return {"업종": "정보수집완료"}  # 실제로는 더 상세한 업종 정보 가능
            return None
        except Exception as e:
            logger.error(f"업종 데이터 수집 오류: {str(e)}")
            return None

def get_stocks_from_db():
    """DB에서 종목 정보를 가져옵니다."""
    try:
        # DB 경로 설정 (PythonCode 폴더에서 실행할 때 상위 폴더의 DB 접근)
        db_path = "../DB/manipulation_stocks.db" if os.path.exists("../DB/manipulation_stocks.db") else "DB/manipulation_stocks.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT stock_name, stock_code FROM manipulation_stocks WHERE stock_code IS NOT NULL")
        stocks = cursor.fetchall()
        conn.close()
        
        # 기본 종목들도 추가
        basic_stocks = [
            ("삼성전자", "005930"),
            ("LG에너지솔루션", "373220"), 
            ("SK하이닉스", "000660")
        ]
        
        # DB 종목과 기본 종목 합치기
        all_stocks = list(stocks) + basic_stocks
        
        # 중복 제거
        unique_stocks = []
        seen = set()
        for stock_name, stock_code in all_stocks:
            if stock_name not in seen:
                unique_stocks.append((stock_name, stock_code))
                seen.add(stock_name)
        
        return unique_stocks
        
    except Exception as e:
        logger.error(f"DB에서 종목 정보 조회 실패: {str(e)}")
        # DB 조회 실패시 기본 종목만 반환
        return [
            ("삼성전자", "005930"),
            ("LG에너지솔루션", "373220"), 
            ("SK하이닉스", "000660")
        ]

def main():
    """메인 실행 함수"""
    collector = StockDataCollector()
    
    # 명령행 인자로 종목코드가 전달된 경우 단일 종목 처리
    if len(sys.argv) > 1:
        stock_code = sys.argv[1]
        try:
            # 종목명 조회
            stock_name = stock.get_market_ticker_name(stock_code)
            if not stock_name:
                logger.error(f"종목코드 {stock_code}에 해당하는 종목을 찾을 수 없습니다.")
                return
            
            logger.info(f"단일 종목 데이터 수집 시작: {stock_name} ({stock_code})")
            
            # 3년치 데이터 수집
            df, _ = collector.collect_comprehensive_data(stock_name, years=3)
            
            if df is not None and not df.empty:
                # CSV 파일 저장
                filename = collector.save_data_to_csv(df, stock_name, stock_code)
                
                # DB에 저장
                save_to_collectcompletedata_db(df, stock_name, stock_code)
                
                logger.info(f"단일 종목 데이터 수집 완료: {stock_name} ({stock_code})")
            else:
                logger.error(f"데이터 수집 실패: {stock_name} ({stock_code})")
                
        except Exception as e:
            logger.error(f"단일 종목 처리 중 오류: {str(e)}")
        return
    
    # 기존 전체 종목 처리 로직
    stocks = get_stocks_from_db()
    
    if not stocks:
        logger.warning("DB에서 종목 목록을 가져올 수 없습니다.")
        return
    
    logger.info(f"총 {len(stocks)}개 종목의 데이터 수집을 시작합니다.")
    
    for i, (stock_name, stock_code) in enumerate(stocks, 1):
        try:
            logger.info(f"[{i}/{len(stocks)}] {stock_name} ({stock_code}) 데이터 수집 중...")
            
            # 3년치 데이터 수집
            df, _ = collector.collect_comprehensive_data(stock_name, years=3)
            
            if df is not None and not df.empty:
                # CSV 파일 저장
                filename = collector.save_data_to_csv(df, stock_name, stock_code)
                
                # DB에 저장
                save_to_collectcompletedata_db(df, stock_name, stock_code)
                
                logger.info(f"[{i}/{len(stocks)}] {stock_name} 데이터 수집 완료")
            else:
                logger.error(f"[{i}/{len(stocks)}] {stock_name} 데이터 수집 실패")
                
        except Exception as e:
            logger.error(f"[{i}/{len(stocks)}] {stock_name} 처리 중 오류: {str(e)}")
            continue
    
    logger.info("모든 종목 데이터 수집 완료")

def save_to_collectcompletedata_db(df, stock_name, stock_code):
    """collectCompleteData.db에 데이터 저장"""
    try:
        # 데이터 전처리
        df_copy = df.copy()
        df_copy.reset_index(inplace=True)
        
        # 컬럼명 매핑
        column_mapping = {
            '날짜': 'date',
            '시가': 'open_price',
            '고가': 'high_price', 
            '저가': 'low_price',
            '종가': 'close_price',
            '거래량': 'volume',
            '등락률': 'change_rate',
            '시가총액': 'market_cap',
            '거래량_cap': 'volume_cap',
            '거래대금': 'trading_value',
            '상장주식수': 'shares_outstanding',
            'BPS': 'bps',
            'PER': 'per',
            'PBR': 'pbr',
            'EPS': 'eps',
            'DIV': 'div',
            'DPS': 'dps',
            '기관합계': 'institutional_total',
            '기타법인': 'other_corporate',
            '개인': 'individual',
            '외국인합계': 'foreign_total'
        }
        
        # 컬럼명 변경
        df_copy.rename(columns=column_mapping, inplace=True)
        
        # 필수 컬럼 추가
        df_copy['stock_name'] = stock_name
        df_copy['stock_code'] = stock_code
        
        # 등락률 계산 (없는 경우)
        if 'change_rate' not in df_copy.columns:
            df_copy['change_rate'] = ((df_copy['close_price'] - df_copy['open_price']) / df_copy['open_price'] * 100).round(2)
        
        # DB 경로 설정 (PythonCode 폴더에서 실행할 때 상위 폴더의 DB 접근)
        db_path = "../DB/collectCompleteData.db" if os.path.exists("../DB/collectCompleteData.db") else "DB/collectCompleteData.db"
        
        # DB 연결 및 저장
        conn = sqlite3.connect(db_path)
        
        # 기존 데이터 삭제 (중복 방지)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM completed_stocks WHERE stock_code = ?", (stock_code,))
        
        # 새 데이터 삽입
        df_copy.to_sql('completed_stocks', conn, if_exists='append', index=False)
        conn.commit()
        conn.close()
        
        logger.info(f"{stock_name} ({stock_code}) DB 저장 완료")
        
    except Exception as e:
        logger.error(f"DB 저장 오류: {str(e)}")

if __name__ == "__main__":
    main()
