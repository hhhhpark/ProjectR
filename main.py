from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3
import pandas as pd
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
import os
from pydantic import BaseModel
import subprocess
import yfinance as yf
from pykrx import stock
import re
from fastapi import FastAPI
from database import Base, engine


app = FastAPI(title="K-Stock Pattern API", description="주가 패턴 분석 API")


# PostgreSQL에 테이블 생성
Base.metadata.create_all(bind=engine)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://localhost:5175", 
        "http://localhost:5176",
        "http://localhost:5177"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vue.js 정적 파일 서빙 (dist 폴더가 있을 때만)
if os.path.exists("stock-pattern-viewer/dist"):
    app.mount("/assets", StaticFiles(directory="stock-pattern-viewer/dist/assets"), name="assets")
    app.mount("/Result", StaticFiles(directory="Result"), name="result")

# DB 경로 설정
DB_PATH = "/Users/juyeon/Desktop/projectR/DB/manipulation_stocks.db"

# 요청 모델 정의
class AddStockRequest(BaseModel):
    stock_code: str
    stock_name: str = ""

def get_db_connection():
    """데이터베이스 연결을 반환합니다."""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database not found")
    return sqlite3.connect(DB_PATH)

@app.get("/")
async def read_root():
    if os.path.exists("stock-pattern-viewer/dist/index.html"):
        return FileResponse("stock-pattern-viewer/dist/index.html")
    else:
        return {"message": "K-Stock Pattern API is running", "version": "1.0.0"}

@app.get("/api/stocks", response_model=List[Dict[str, Any]])
async def get_manipulation_stocks():
    """등록된 작전주 목록을 반환합니다."""
    try:
        conn = get_db_connection()
        query = """
        SELECT m.*, p.risk_level, p.risk_score 
        FROM manipulation_stocks m 
        LEFT JOIN pattern_analysis p ON m.stock_code = p.stock_code
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/{stock_code}/data")
async def get_stock_data(stock_code: str, days: int = 365):
    """특정 종목의 일별 데이터를 반환합니다."""
    try:
        conn = get_db_connection()
        
        # 날짜 범위 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = """
        SELECT * FROM stock_daily_data 
        WHERE stock_code = ? AND date >= ? 
        ORDER BY date ASC
        """
        
        df = pd.read_sql_query(
            query, 
            conn, 
            params=[stock_code, start_date.strftime('%Y-%m-%d')]
        )
        conn.close()
        
        if df.empty:
            raise HTTPException(status_code=404, detail="Stock data not found")
        
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/{stock_code}/pattern")
async def get_stock_pattern(stock_code: str):
    """특정 종목의 패턴 분석 결과를 반환합니다."""
    try:
        conn = get_db_connection()
        
        query = """
        SELECT * FROM pattern_analysis 
        WHERE stock_code = ? 
        ORDER BY analysis_date DESC 
        LIMIT 1
        """
        
        cursor = conn.cursor()
        cursor.execute(query, [stock_code])
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Pattern analysis not found")
        
        # 컬럼명과 함께 딕셔너리로 변환
        columns = [description[0] for description in cursor.description]
        pattern_data = dict(zip(columns, result))
        
        # JSON 문자열을 파싱
        if pattern_data.get('warnings'):
            pattern_data['warnings'] = json.loads(pattern_data['warnings'])
        if pattern_data.get('patterns'):
            pattern_data['patterns'] = json.loads(pattern_data['patterns'])
        
        conn.close()
        return pattern_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    try:
        # anomalousList.db에서 요약 정보 가져오기
        conn = sqlite3.connect("DB/anomalousList.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM manipulation_stocks")
        total_anomalous = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM manipulation_stocks WHERE 위험도점수 >= 7")
        high_risk = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_stocks": total_anomalous,
            "high_risk_stocks": high_risk,
            "latest_analysis_date": "2024-01-15"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/anomalous-stocks")
async def get_anomalous_stocks():
    """anomalousList.db에서 작전주 의심 종목 목록 가져오기"""
    try:
        # anomalousList.db에서 기본 정보 가져오기
        conn1 = sqlite3.connect("DB/anomalousList.db")
        cursor1 = conn1.cursor()
        
        cursor1.execute('''
            SELECT stock_name, stock_code, manipulation_type, 급등빈발_일수, 
                   급등빈발_기간, 극심한급등_최대등락률, 극심한급등_기간,
                   거래량급증빈발_일수, 거래량급증빈발_기간, 위험도점수, description
            FROM manipulation_stocks
            ORDER BY 위험도점수 DESC
        ''')
        
        results1 = cursor1.fetchall()
        conn1.close()
        
        # manipulation_stocks.db에서 상세 패턴 정보 가져오기
        conn2 = sqlite3.connect("DB/manipulation_stocks.db")
        cursor2 = conn2.cursor()
        
        stocks = []
        for row in results1:
            stock_code = row[1]
            
            # 상세 패턴 정보 조회
            cursor2.execute('''
                SELECT analysis_patterns
                FROM manipulation_analysis
                WHERE stock_code = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (stock_code,))
            
            pattern_result = cursor2.fetchone()
            pattern_data = {}
            
            if pattern_result and pattern_result[0]:
                try:
                    import json
                    pattern_data = json.loads(pattern_result[0])
                except:
                    pattern_data = {}
            
            stock_info = {
                "stock_name": row[0],
                "stock_code": row[1],
                "manipulation_type": row[2],
                "급등빈발_일수": row[3],
                "급등빈발_기간": row[4],
                "극심한급등_최대등락률": row[5],
                "극심한급등_기간": row[6],
                "거래량급증빈발_일수": row[7],
                "거래량급증빈발_기간": row[8],
                "위험도점수": row[9],
                "description": row[10]
            }
            
            # 상세 패턴 날짜 정보 추가
            if pattern_data:
                stock_info.update({
                    "급등_발생날짜": pattern_data.get('급등_발생날짜', []),
                    "최대등락률_발생날짜": pattern_data.get('최대등락률_발생날짜', ''),
                    "거래량급증_발생날짜": pattern_data.get('거래량급증_발생날짜', [])
                })
            
            stocks.append(stock_info)
        
        conn2.close()
        return stocks
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock-detail/{stock_code}")
async def get_stock_detail(stock_code: str):
    """collectCompleteData.db에서 특정 종목의 상세 데이터 가져오기"""
    try:
        conn = sqlite3.connect("DB/collectCompleteData.db")
        cursor = conn.cursor()
        
        # 최근 30일 데이터 가져오기
        cursor.execute('''
            SELECT date, open_price, high_price, low_price, close_price, volume, change_rate, market_cap,
                   volume_cap, trading_value, bps, per, pbr, eps
            FROM completed_stocks 
            WHERE stock_code = ?
            ORDER BY date DESC
            LIMIT 30
        ''', (stock_code,))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            raise HTTPException(status_code=404, detail="종목 데이터를 찾을 수 없습니다.")
        
        stock_data = []
        for row in results:
            stock_data.append({
                "date": row[0],
                "open_price": row[1],
                "high_price": row[2],
                "low_price": row[3],
                "close_price": row[4],
                "volume": row[5],
                "change_rate": row[6],
                "market_cap": row[7],
                "volume_cap": row[8],
                "trading_value": row[9],
                "bps": row[10],
                "per": row[11],
                "pbr": row[12],
                "eps": row[13]
            })
        
        return {
            "stock_code": stock_code,
            "data": stock_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks")
async def get_stocks():
    """기존 API - 호환성 유지"""
    try:
        return await get_anomalous_stocks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/{stock_code}/chart")
async def get_stock_chart_data(stock_code: str, days: int = 90):
    """차트용 주가 데이터를 반환합니다."""
    try:
        conn = get_db_connection()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = """
        SELECT date, open_price, high_price, low_price, close_price, volume, change_rate
        FROM stock_daily_data 
        WHERE stock_code = ? AND date >= ? 
        ORDER BY date ASC
        """
        
        df = pd.read_sql_query(
            query, 
            conn, 
            params=[stock_code, start_date.strftime('%Y-%m-%d')]
        )
        conn.close()
        
        if df.empty:
            raise HTTPException(status_code=404, detail="Chart data not found")
        
        # 차트 데이터 형식으로 변환
        chart_data = {
            "labels": df['date'].tolist(),
            "datasets": [
                {
                    "label": "종가",
                    "data": df['close_price'].tolist(),
                    "borderColor": "rgb(59, 130, 246)",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "tension": 0.1
                },
                {
                    "label": "거래량",
                    "data": df['volume'].tolist(),
                    "type": "bar",
                    "yAxisID": "y1",
                    "backgroundColor": "rgba(34, 197, 94, 0.3)",
                    "borderColor": "rgb(34, 197, 94)"
                }
            ]
        }
        
        return {"data": chart_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/collect-stocks")
async def get_collect_stocks():
    """collectList.db에서 전체 수집 종목 목록 가져오기"""
    try:
        conn = sqlite3.connect("DB/collectList.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT stock_name, stock_code
            FROM collection_stocks
            ORDER BY ROWID DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        stocks = []
        for row in results:
            stocks.append({
                "stock_name": row[0],
                "stock_code": row[1]
            })
        
        return stocks
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/collect-stock-data/{stock_code}")
async def get_collect_stock_data(stock_code: str, limit: int = 100):
    """collectCompleteData.db에서 특정 종목의 전체 데이터 가져오기"""
    try:
        conn = sqlite3.connect("DB/collectCompleteData.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, open_price, high_price, low_price, close_price, volume, change_rate, market_cap,
                   volume_cap, trading_value, shares_outstanding, bps, per, pbr, eps, div, dps,
                   institutional_total, other_corporate, individual, foreign_total
            FROM completed_stocks 
            WHERE stock_code = ?
            ORDER BY date DESC
            LIMIT ?
        ''', (stock_code, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            raise HTTPException(status_code=404, detail="종목 데이터를 찾을 수 없습니다.")
        
        stock_data = []
        for row in results:
            stock_data.append({
                "date": row[0],
                "open_price": row[1],
                "high_price": row[2],
                "low_price": row[3],
                "close_price": row[4],
                "volume": row[5],
                "change_rate": row[6],
                "market_cap": row[7],
                "volume_cap": row[8],
                "trading_value": row[9],
                "shares_outstanding": row[10],
                "bps": row[11],
                "per": row[12],
                "pbr": row[13],
                "eps": row[14],
                "div": row[15],
                "dps": row[16],
                "institutional_total": row[17],
                "other_corporate": row[18],
                "individual": row[19],
                "foreign_total": row[20]
            })
        
        return {
            "stock_code": stock_code,
            "data": stock_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/collect-stock-chart/{stock_code}")
async def get_collect_stock_chart(stock_code: str, days: int = 90):
    """collectCompleteData.db에서 차트용 데이터 가져오기"""
    try:
        conn = sqlite3.connect("DB/collectCompleteData.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, open_price, high_price, low_price, close_price, volume
            FROM completed_stocks 
            WHERE stock_code = ?
            ORDER BY date DESC
            LIMIT ?
        ''', (stock_code, days))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            raise HTTPException(status_code=404, detail="차트 데이터를 찾을 수 없습니다.")
        
        # 날짜 순으로 정렬 (차트용)
        results.reverse()
        
        chart_data = {
            "labels": [row[0] for row in results],
            "datasets": [
                {
                    "label": "종가",
                    "data": [float(row[4]) if row[4] else 0 for row in results],
                    "borderColor": "rgb(59, 130, 246)",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "tension": 0.1,
                    "yAxisID": "y"
                },
                {
                    "label": "거래량",
                    "data": [float(row[5]) if row[5] else 0 for row in results],
                    "type": "bar",
                    "yAxisID": "y1",
                    "backgroundColor": "rgba(34, 197, 94, 0.3)",
                    "borderColor": "rgb(34, 197, 94)"
                }
            ],
            "candlestick": [
                {
                    "x": row[0],
                    "o": float(row[1]) if row[1] else 0,
                    "h": float(row[2]) if row[2] else 0,
                    "l": float(row[3]) if row[3] else 0,
                    "c": float(row[4]) if row[4] else 0
                } for row in results
            ]
        }
        
        return chart_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/suspect-stocks")
async def get_suspect_stocks():
    """suspect_stocks.db에서 과거 작전주 목록 가져오기"""
    try:
        conn = sqlite3.connect("DB/suspect_stocks.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, stock_name, suspected_period, theme_reason, main_issue,
                   active_duration, buy_side_pattern, price_3y_ago, price_peak, price_current, stock_code
            FROM suspect_stocks
            ORDER BY price_peak DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        stocks = []
        for row in results:
            # 수익률 계산
            price_3y_ago = row[7] if row[7] else 0
            price_peak = row[8] if row[8] else 0
            price_current = row[9] if row[9] else 0
            
            peak_return = ((price_peak - price_3y_ago) / price_3y_ago * 100) if price_3y_ago > 0 else 0
            current_return = ((price_current - price_3y_ago) / price_3y_ago * 100) if price_3y_ago > 0 else 0
            
            stocks.append({
                "id": row[0],
                "stock_name": row[1],
                "stock_code": row[10] if row[10] else "-",
                "suspected_period": row[2],
                "theme_reason": row[3],
                "main_issue": row[4],
                "active_duration": row[5],
                "buy_side_pattern": row[6],
                "price_3y_ago": price_3y_ago,
                "price_peak": price_peak,
                "price_current": price_current,
                "peak_return": round(peak_return, 1),
                "current_return": round(current_return, 1)
            })
        
        return stocks
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/historical-manipulation-stocks")
async def get_historical_manipulation_stocks():
    """manipulation_stocks.db에서 과거 작전주 목록 가져오기"""
    try:
        conn = sqlite3.connect("DB/manipulation_stocks.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT stock_name, stock_code, category, manipulation_period, 
                   max_rise_rate, manipulation_type, description, created_at
            FROM historical_manipulation_stocks
            ORDER BY max_rise_rate DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        stocks = []
        for row in results:
            stocks.append({
                "stock_name": row[0],
                "stock_code": row[1] if row[1] else "-",
                "category": row[2],
                "manipulation_period": row[3],
                "max_rise_rate": row[4],
                "manipulation_type": row[5],
                "description": row[6],
                "created_at": row[7]
            })
        
        return stocks
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def validate_korean_stock_name(stock_name: str) -> bool:
    """한국 주식 종목명인지 검증합니다."""
    if not stock_name:
        return False
    
    # 영문만으로 구성된 종목명 필터링 (Co., Ltd, Inc 등 포함)
    english_only_pattern = r'^[A-Za-z\s\.,&\-()]+$'
    if re.match(english_only_pattern, stock_name):
        return False
    
    # 한글이 포함된 종목명만 허용
    korean_pattern = r'[가-힣]'
    return bool(re.search(korean_pattern, stock_name))

def get_korean_stock_name(stock_code: str) -> str:
    """pykrx를 사용하여 정확한 한국 종목명을 조회합니다."""
    try:
        # pykrx로 종목명 조회
        stock_name = stock.get_market_ticker_name(stock_code)
        print(f"pykrx 조회 결과 - 종목코드: {stock_code}, 종목명: {stock_name}")
        
        if stock_name and validate_korean_stock_name(stock_name):
            return stock_name
        else:
            print(f"종목명 검증 실패 - 종목코드: {stock_code}, 종목명: {stock_name}")
            return None
            
    except Exception as e:
        print(f"pykrx 종목명 조회 실패 - 종목코드: {stock_code}, 오류: {e}")
        return None

@app.post("/api/add-stock")
async def add_stock(request: AddStockRequest):
    """새로운 종목을 추가하고 데이터를 수집/분석합니다."""
    try:
        stock_code = request.stock_code.strip()
        stock_name = request.stock_name.strip()
        
        # 종목코드 유효성 검사
        if not stock_code or len(stock_code) != 6 or not stock_code.isdigit():
            raise HTTPException(status_code=400, detail="올바른 6자리 종목코드를 입력해주세요.")
        
        # 이미 존재하는 종목인지 확인
        conn = sqlite3.connect("DB/collectList.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM collection_stocks WHERE stock_code = ?", (stock_code,))
        exists = cursor.fetchone()[0] > 0
        conn.close()
        
        if exists:
            raise HTTPException(status_code=400, detail="이미 등록된 종목입니다.")
        
        # pykrx로 정확한 한국 종목명 조회
        korean_stock_name = get_korean_stock_name(stock_code)
        
        if not korean_stock_name:
            raise HTTPException(
                status_code=400, 
                detail=f"종목코드 {stock_code}에 해당하는 한국 주식을 찾을 수 없습니다. 올바른 종목코드인지 확인해주세요."
            )
        
        # 사용자가 입력한 종목명이 있으면 검증
        if stock_name:
            if not validate_korean_stock_name(stock_name):
                # 사용자 입력 종목명이 유효하지 않으면 pykrx에서 조회한 종목명 사용
                stock_name = korean_stock_name
                print(f"입력된 종목명이 유효하지 않아 조회된 종목명으로 대체: {korean_stock_name}")
        else:
            stock_name = korean_stock_name
        
        # 1. collectList.db에 종목 추가
        conn = sqlite3.connect("DB/collectList.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO collection_stocks (stock_name, stock_code) 
            VALUES (?, ?)
        """, (stock_name, stock_code))
        conn.commit()
        conn.close()
        
        # 2. 데이터 수집 스크립트 실행 (백그라운드)
        data_collection_success = False
        try:
            # PythonCode/stock_scrap.py 실행하여 3년치 데이터 수집
            result = subprocess.run([
                "python", "PythonCode/stock_scrap.py", stock_code
            ], capture_output=True, text=True, timeout=180)  # 3분 타임아웃
            
            if result.returncode == 0:
                data_collection_success = True
                print(f"데이터 수집 성공: {stock_name} ({stock_code})")
            else:
                print(f"데이터 수집 오류: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("데이터 수집 시간 초과")
        except Exception as e:
            print(f"데이터 수집 실패: {e}")
        
        # 3. 패턴 분석 실행 (데이터 수집이 성공한 경우에만)
        pattern_analysis_success = False
        if data_collection_success:
            try:
                result = subprocess.run([
                    "python", "PythonCode/analyze_patterns.py", stock_code
                ], capture_output=True, text=True, timeout=120)  # 2분 타임아웃
                
                if result.returncode == 0:
                    pattern_analysis_success = True
                    print(f"패턴 분석 성공: {stock_name} ({stock_code})")
                else:
                    print(f"패턴 분석 오류: {result.stderr}")
            except subprocess.TimeoutExpired:
                print("패턴 분석 시간 초과")
            except Exception as e:
                print(f"패턴 분석 실패: {e}")
        
        # 결과 메시지 생성
        message = f"{stock_name} ({stock_code}) 종목이 성공적으로 추가되었습니다."
        if not data_collection_success:
            message += " (데이터 수집 실패)"
        elif not pattern_analysis_success:
            message += " (패턴 분석 실패)"
        
        return {
            "success": True,
            "message": message,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "data_collection_success": data_collection_success,
            "pattern_analysis_success": pattern_analysis_success
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"종목 추가 중 오류가 발생했습니다: {str(e)}")

@app.get("/api/manipulation-criteria/{stock_code}")
async def get_manipulation_criteria(stock_code: str):
    """특정 종목의 작전주 분류 기준 상세 정보 제공"""
    try:
        # anomalousList.db에서 기본 정보 가져오기
        conn1 = sqlite3.connect("DB/anomalousList.db")
        cursor1 = conn1.cursor()
        
        cursor1.execute('''
            SELECT stock_name, stock_code, manipulation_type, 급등빈발_일수, 
                   급등빈발_기간, 극심한급등_최대등락률, 극심한급등_기간,
                   거래량급증빈발_일수, 거래량급증빈발_기간, 위험도점수, description
            FROM manipulation_stocks
            WHERE stock_code = ?
        ''', (stock_code,))
        
        result = cursor1.fetchone()
        conn1.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")
        
        # manipulation_stocks.db에서 상세 패턴 정보 가져오기
        conn2 = sqlite3.connect("DB/manipulation_stocks.db")
        cursor2 = conn2.cursor()
        
        cursor2.execute('''
            SELECT analysis_patterns, warnings, risk_level, risk_score
            FROM manipulation_analysis
            WHERE stock_code = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (stock_code,))
        
        pattern_result = cursor2.fetchone()
        conn2.close()
        
        # 분류 기준 생성
        criteria = []
        
        # 급등빈발 기준
        if result[3] > 0:  # 급등빈발_일수
            status = 'danger' if result[3] >= 5 else 'warning' if result[3] >= 3 else 'normal'
            criteria.append({
                "category": "급등빈발 패턴",
                "condition": f"{result[3]}일간 급등 발생",
                "threshold": "3일 이상 주의, 5일 이상 고위험",
                "status": status,
                "description": "단기간 내 반복적인 급등은 인위적 조작 가능성을 시사합니다. 정상적인 시장에서는 연속적인 급등이 드물기 때문입니다."
            })
        
        # 극심한급등 기준
        if result[5] > 0:  # 극심한급등_최대등락률
            status = 'danger' if result[5] >= 30 else 'warning' if result[5] >= 20 else 'normal'
            criteria.append({
                "category": "극심한급등 패턴",
                "condition": f"최대 {result[5]}% 급등",
                "threshold": "20% 이상 주의, 30% 이상 고위험",
                "status": status,
                "description": "비정상적으로 높은 등락률은 주가 조작의 전형적인 신호입니다. 특히 하루 만에 20% 이상 오르는 것은 매우 이례적입니다."
            })
        
        # 거래량급증 기준
        if result[7] > 0:  # 거래량급증빈발_일수
            status = 'danger' if result[7] >= 10 else 'warning' if result[7] >= 5 else 'normal'
            criteria.append({
                "category": "거래량급증 패턴",
                "condition": f"{result[7]}일간 거래량 급증",
                "threshold": "5일 이상 주의, 10일 이상 고위험",
                "status": status,
                "description": "평소보다 급격히 증가한 거래량은 작전 세력의 개입을 의미할 수 있습니다. 특히 주가 상승과 함께 나타나면 더욱 의심스럽습니다."
            })
        
        # 위험도 점수 기준
        risk_score = result[9]  # 위험도점수
        status = 'danger' if risk_score >= 7 else 'warning' if risk_score >= 5 else 'normal'
        criteria.append({
            "category": "종합 위험도",
            "condition": f"위험도 점수: {risk_score}점",
            "threshold": "5점 이상 주의, 7점 이상 고위험",
            "status": status,
            "description": "여러 패턴을 종합한 위험도 평가 결과입니다. 급등빈발, 극심한급등, 거래량급증 등을 종합적으로 고려합니다."
        })
        
        # 추가 경고사항
        if pattern_result and pattern_result[1]:  # warnings
            try:
                warnings = json.loads(pattern_result[1])
                if warnings:
                    criteria.append({
                        "category": "추가 경고사항",
                        "condition": f"{len(warnings)}개 경고 발견",
                        "threshold": "1개 이상 주의",
                        "status": "warning",
                        "description": f"시스템이 감지한 추가 위험 요소: {', '.join(warnings[:3])}{'...' if len(warnings) > 3 else ''}"
                    })
            except:
                pass
        
        danger_count = len([c for c in criteria if c['status'] == 'danger'])
        warning_count = len([c for c in criteria if c['status'] == 'warning'])
        
        return {
            "stock_name": result[0],
            "stock_code": result[1],
            "manipulation_type": result[2],
            "criteria": criteria,
            "summary": f"총 {danger_count}개 고위험, {warning_count}개 주의 요소 발견",
            "overall_risk": "고위험" if danger_count > 0 else "주의" if warning_count > 0 else "정상",
            "recommendation": "투자 시 각별한 주의가 필요합니다." if danger_count > 0 else "신중한 투자 검토가 필요합니다." if warning_count > 0 else "상대적으로 안전한 종목입니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock-name/{stock_code}")
async def get_stock_name(stock_code: str):
    """종목코드로 종목명 조회"""
    try:
        print(f"종목명 조회 요청 - 종목코드: {stock_code}")
        stock_name = get_korean_stock_name(stock_code)
        print(f"종목명 조회 결과 - 종목코드: {stock_code}, 종목명: {stock_name}")
        
        if stock_name:
            return {"stock_code": stock_code, "stock_name": stock_name}
        else:
            print(f"종목을 찾을 수 없음 - 종목코드: {stock_code}")
            raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")
    except HTTPException:
        raise
    except Exception as e:
        print(f"종목명 조회 중 예외 발생 - 종목코드: {stock_code}, 오류: {e}")
        raise HTTPException(status_code=500, detail=f"종목명 조회 중 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
