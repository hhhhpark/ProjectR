from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
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
from database import get_db, engine, Base
from sqlalchemy import text

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

# 요청 모델 정의
class AddStockRequest(BaseModel):
    stock_code: str
    stock_name: str = ""

@app.get("/")
async def read_root():
    if os.path.exists("stock-pattern-viewer/dist/index.html"):
        return FileResponse("stock-pattern-viewer/dist/index.html")
    else:
        return {"message": "K-Stock Pattern API is running", "version": "1.0.0"}

@app.get("/api/stocks", response_model=List[Dict[str, Any]])
async def get_manipulation_stocks(db: Session = Depends(get_db)):
    """등록된 작전주 목록을 반환합니다."""
    try:
        query = text("""
        SELECT m.*, p.risk_level, p.risk_score 
        FROM manipulation_stocks m 
        LEFT JOIN pattern_analysis p ON m.stock_code = p.stock_code
        """)
        result = db.execute(query)
        return [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/{stock_code}/data")
async def get_stock_data(stock_code: str, days: int = 365, db: Session = Depends(get_db)):
    """특정 종목의 일별 데이터를 반환합니다."""
    try:
        # 날짜 범위 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = text("""
        SELECT * FROM stock_daily_data 
        WHERE stock_code = :stock_code AND date >= :start_date 
        ORDER BY date ASC
        """)
        
        result = db.execute(
            query, 
            {"stock_code": stock_code, "start_date": start_date.strftime('%Y-%m-%d')}
        )
        
        rows = [dict(row._mapping) for row in result]
        if not rows:
            raise HTTPException(status_code=404, detail="Stock data not found")
        
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/{stock_code}/pattern")
async def get_stock_pattern(stock_code: str, db: Session = Depends(get_db)):
    """특정 종목의 패턴 분석 결과를 반환합니다."""
    try:
        query = text("""
        SELECT * FROM pattern_analysis 
        WHERE stock_code = :stock_code 
        ORDER BY analysis_date DESC 
        LIMIT 1
        """)
        
        result = db.execute(query, {"stock_code": stock_code}).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Pattern analysis not found")
        
        pattern_data = dict(result._mapping)
        
        # JSON 문자열을 파싱
        if pattern_data.get('warnings'):
            pattern_data['warnings'] = json.loads(pattern_data['warnings'])
        if pattern_data.get('patterns'):
            pattern_data['patterns'] = json.loads(pattern_data['patterns'])
        
        return pattern_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/summary")
async def get_dashboard_summary(db: Session = Depends(get_db)):
    try:
        # 작전주 통계 정보 가져오기
        total_query = text("SELECT COUNT(*) FROM manipulation_stocks")
        high_risk_query = text("SELECT COUNT(*) FROM manipulation_stocks WHERE 위험도점수 >= 7")
        
        total_anomalous = db.execute(total_query).scalar()
        high_risk = db.execute(high_risk_query).scalar()
        
        return {
            "total_stocks": total_anomalous,
            "high_risk_stocks": high_risk,
            "latest_analysis_date": "2024-01-15"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/anomalous-stocks")
async def get_anomalous_stocks(db: Session = Depends(get_db)):
    """작전주 의심 종목 목록 가져오기"""
    try:
        # 기본 정보 가져오기
        base_query = text("""
            SELECT stock_name, stock_code, manipulation_type, 급등빈발_일수, 
                   급등빈발_기간, 극심한급등_최대등락률, 극심한급등_기간,
                   거래량급증빈발_일수, 거래량급증빈발_기간, 위험도점수, description
            FROM manipulation_stocks
            ORDER BY 위험도점수 DESC
        """)
        
        results = db.execute(base_query)
        
        stocks = []
        for row in results:
            stock_data = dict(row._mapping)
            stock_code = stock_data['stock_code']
            
            # 상세 패턴 정보 조회
            pattern_query = text("""
                SELECT analysis_patterns
                FROM manipulation_analysis
                WHERE stock_code = :stock_code
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            pattern_result = db.execute(pattern_query, {"stock_code": stock_code}).first()
            
            if pattern_result and pattern_result.analysis_patterns:
                stock_data['patterns'] = json.loads(pattern_result.analysis_patterns)
            else:
                stock_data['patterns'] = []
            
            stocks.append(stock_data)
        
        return stocks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock-detail/{stock_code}")
async def get_stock_detail(stock_code: str, db: Session = Depends(get_db)):
    """특정 종목의 상세 정보를 반환합니다."""
    try:
        # 기본 정보 조회
        base_query = text("""
            SELECT * FROM manipulation_stocks 
            WHERE stock_code = :stock_code
        """)
        
        stock = db.execute(base_query, {"stock_code": stock_code}).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        stock_data = dict(stock._mapping)
        
        # 패턴 분석 정보 조회
        pattern_query = text("""
            SELECT * FROM pattern_analysis 
            WHERE stock_code = :stock_code 
            ORDER BY analysis_date DESC 
            LIMIT 1
        """)
        
        pattern = db.execute(pattern_query, {"stock_code": stock_code}).first()
        if pattern:
            pattern_data = dict(pattern._mapping)
            if pattern_data.get('warnings'):
                pattern_data['warnings'] = json.loads(pattern_data['warnings'])
            if pattern_data.get('patterns'):
                pattern_data['patterns'] = json.loads(pattern_data['patterns'])
            stock_data.update(pattern_data)
        
        return stock_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks")
async def get_stocks(db: Session = Depends(get_db)):
    """모든 종목 목록을 반환합니다."""
    try:
        query = text("SELECT * FROM collection_stocks")
        result = db.execute(query)
        return [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/{stock_code}/chart")
async def get_stock_chart_data(stock_code: str, days: int = 90, db: Session = Depends(get_db)):
    """특정 종목의 차트 데이터를 반환합니다."""
    try:
        # 날짜 범위 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = text("""
            SELECT date, open_price, high_price, low_price, close_price, volume, 
                   change_rate, market_cap, trading_value
            FROM stock_daily_data 
            WHERE stock_code = :stock_code AND date >= :start_date 
            ORDER BY date ASC
        """)
        
        result = db.execute(
            query, 
            {"stock_code": stock_code, "start_date": start_date.strftime('%Y-%m-%d')}
        )
        
        rows = [dict(row._mapping) for row in result]
        if not rows:
            raise HTTPException(status_code=404, detail="Chart data not found")
        
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/collect-stocks")
async def get_collect_stocks(db: Session = Depends(get_db)):
    """수집 대상 종목 목록을 반환합니다."""
    try:
        query = text("SELECT * FROM collection_stocks ORDER BY stock_name")
        result = db.execute(query)
        return [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/collect-stock-data/{stock_code}")
async def get_collect_stock_data(stock_code: str, limit: int = 100, db: Session = Depends(get_db)):
    """특정 종목의 수집된 데이터를 반환합니다."""
    try:
        # 먼저 completed_stocks에서 조회
        query = text("""
            SELECT * FROM completed_stocks 
            WHERE stock_code = :stock_code 
            ORDER BY date DESC 
            LIMIT :limit
        """)
        
        result = db.execute(query, {"stock_code": stock_code, "limit": limit})
        rows = [dict(row._mapping) for row in result]
        
        # completed_stocks에 데이터가 없으면 stock_daily_data에서 조회
        if not rows:
            query = text("""
                SELECT 
                    date,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume,
                    change_rate,
                    market_cap,
                    trading_value,
                    stock_code
                FROM stock_daily_data 
                WHERE stock_code = :stock_code 
                ORDER BY date DESC 
                LIMIT :limit
            """)
            
            result = db.execute(query, {"stock_code": stock_code, "limit": limit})
            rows = [dict(row._mapping) for row in result]
        
        if not rows:
            print(f"API 에러 - 종목코드: {stock_code}, 오류: 데이터 없음")
            return {"data": [], "message": f"종목코드 {stock_code}에 대한 데이터가 없습니다."}
        
        return {"data": rows}
    except Exception as e:
        print(f"API 에러 - 종목코드: {stock_code}, 오류: {str(e)}")
        return {"data": [], "error": str(e)}

@app.get("/api/collect-stock-chart/{stock_code}")
async def get_collect_stock_chart(stock_code: str, days: int = 90, db: Session = Depends(get_db)):
    """특정 종목의 수집된 차트 데이터를 반환합니다."""
    try:
        # 날짜 범위 계산
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = text("""
            SELECT date, open_price, high_price, low_price, close_price, volume, 
                   change_rate, market_cap, trading_value, institution_total, 
                   other_corporation, individual, foreign_total
            FROM completed_stocks 
            WHERE stock_code = :stock_code AND date >= :start_date 
            ORDER BY date ASC
        """)
        
        result = db.execute(
            query, 
            {"stock_code": stock_code, "start_date": start_date.strftime('%Y-%m-%d')}
        )
        
        rows = [dict(row._mapping) for row in result]
        if not rows:
            raise HTTPException(status_code=404, detail="Chart data not found")
        
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/suspect-stocks")
async def get_suspect_stocks(db: Session = Depends(get_db)):
    """의심 종목 목록을 반환합니다."""
    try:
        query = text("SELECT * FROM suspect_stocks ORDER BY stock_name")
        result = db.execute(query)
        return [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/historical-manipulation-stocks")
async def get_historical_manipulation_stocks(db: Session = Depends(get_db)):
    """과거 작전주 목록을 반환합니다."""
    try:
        query = text("""
            SELECT * FROM historical_manipulation_stocks 
            ORDER BY manipulation_period DESC
        """)
        result = db.execute(query)
        return [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock-surge-dates/{stock_code}")
async def get_stock_surge_dates(stock_code: str, db: Session = Depends(get_db)):
    """특정 종목의 급등 발생일들을 반환합니다."""
    try:
        # stock_daily_data에서 해당 종목의 모든 데이터 조회
        query = text("""
            SELECT date, change_rate, close_price, volume
            FROM stock_daily_data 
            WHERE stock_code = :stock_code 
            ORDER BY date ASC
        """)
        
        result = db.execute(query, {"stock_code": stock_code})
        rows = [dict(row._mapping) for row in result]
        
        if not rows:
            return {"surge_dates": [], "message": f"종목코드 {stock_code}에 대한 데이터가 없습니다."}
        
        # 급등일 기준: 일일 상승률이 5% 이상인 날
        surge_threshold = 5.0
        surge_dates = []
        
        for row in rows:
            if row['change_rate'] and float(row['change_rate']) >= surge_threshold:
                surge_dates.append({
                    'date': row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date']),
                    'change_rate': float(row['change_rate']),
                    'close_price': float(row['close_price']) if row['close_price'] else 0,
                    'volume': int(row['volume']) if row['volume'] else 0
                })
        
        return {
            "surge_dates": surge_dates,
            "total_surge_days": len(surge_dates),
            "threshold": surge_threshold
        }
        
    except Exception as e:
        print(f"급등일 조회 에러 - 종목코드: {stock_code}, 오류: {str(e)}")
        return {"surge_dates": [], "error": str(e)}

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
async def add_stock(request: AddStockRequest, db: Session = Depends(get_db)):
    """새로운 종목을 추가합니다."""
    try:
        # 주식 코드 형식 검증
        if not re.match(r'^\d{6}$', request.stock_code):
            raise HTTPException(status_code=400, detail="Invalid stock code format")
        
        # 이미 존재하는지 확인
        check_query = text("""
            SELECT 1 FROM collection_stocks 
            WHERE stock_code = :stock_code
        """)
        exists = db.execute(check_query, {"stock_code": request.stock_code}).first()
        
        if exists:
            raise HTTPException(status_code=400, detail="Stock already exists")
        
        # 주식명이 제공되지 않은 경우 API에서 조회
        stock_name = request.stock_name
        if not stock_name:
            stock_name = get_korean_stock_name(request.stock_code)
        
        # 새 종목 추가
        insert_query = text("""
            INSERT INTO collection_stocks (stock_name, stock_code, created_at, updated_at)
            VALUES (:stock_name, :stock_code, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """)
        
        db.execute(
            insert_query,
            {"stock_name": stock_name, "stock_code": request.stock_code}
        )
        db.commit()
        
        return {"message": "Stock added successfully", "stock_code": request.stock_code, "stock_name": stock_name}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/manipulation-criteria/{stock_code}")
async def get_manipulation_criteria(stock_code: str, db: Session = Depends(get_db)):
    """특정 종목의 작전주 판단 기준을 반환합니다."""
    try:
        # 기본 정보 조회
        base_query = text("""
            SELECT * FROM manipulation_stocks 
            WHERE stock_code = :stock_code
        """)
        
        stock = db.execute(base_query, {"stock_code": stock_code}).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        stock_data = dict(stock._mapping)
        
        # 패턴 분석 정보 조회
        pattern_query = text("""
            SELECT * FROM pattern_analysis 
            WHERE stock_code = :stock_code 
            ORDER BY analysis_date DESC 
            LIMIT 1
        """)
        
        pattern = db.execute(pattern_query, {"stock_code": stock_code}).first()
        if pattern:
            pattern_data = dict(pattern._mapping)
            if pattern_data.get('warnings'):
                pattern_data['warnings'] = json.loads(pattern_data['warnings'])
            if pattern_data.get('patterns'):
                pattern_data['patterns'] = json.loads(pattern_data['patterns'])
            stock_data.update(pattern_data)
        
        return {
            "criteria": {
                "급등빈발": {
                    "일수": stock_data.get("급등빈발_일수", 0),
                    "기간": stock_data.get("급등빈발_기간", ""),
                    "발생날짜": stock_data.get("patterns", {}).get("급등_발생날짜", [])
                },
                "극심한급등": {
                    "최대등락률": stock_data.get("극심한급등_최대등락률", 0),
                    "기간": stock_data.get("극심한급등_기간", ""),
                    "발생날짜": stock_data.get("patterns", {}).get("최대등락률_발생날짜", "")
                },
                "거래량급증빈발": {
                    "일수": stock_data.get("거래량급증빈발_일수", 0),
                    "기간": stock_data.get("거래량급증빈발_기간", ""),
                    "발생날짜": stock_data.get("patterns", {}).get("거래량급증_발생날짜", [])
                }
            },
            "위험도": {
                "점수": stock_data.get("위험도점수", 0),
                "등급": stock_data.get("risk_level", ""),
                "경고": stock_data.get("warnings", [])
            },
            "description": stock_data.get("description", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock-name/{stock_code}")
async def get_stock_name(stock_code: str, db: Session = Depends(get_db)):
    """주식 코드로 종목명을 조회합니다."""
    try:
        query = text("""
            SELECT stock_name FROM collection_stocks 
            WHERE stock_code = :stock_code
        """)
        result = db.execute(query, {"stock_code": stock_code}).first()
        
        if result:
            return {"stock_name": result.stock_name}
        else:
            # API에서 종목명 조회 시도
            stock_name = get_korean_stock_name(stock_code)
            if stock_name:
                return {"stock_name": stock_name}
            else:
                raise HTTPException(status_code=404, detail="Stock not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import os
    import uvicorn
    
    # Render에서 제공하는 PORT 환경변수 사용, 없으면 8000 사용
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}")
    
    # uvicorn main:app --host 0.0.0.0 --port $PORT 형태로 실행
    uvicorn.run("main:app", host="0.0.0.0", port=port) 
