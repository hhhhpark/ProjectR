from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import AnomalousStock, StockPattern  # 필요한 모델들 import

# 1) SQLite DB 연결
sqlite_engine = create_engine("sqlite:///./manipulation_stocks.db")
sqlite_session = Session(bind=sqlite_engine)

# 2) PostgreSQL DB 연결
import os
from database import SessionLocal  # PostgreSQL 세션

postgres_session = SessionLocal()

try:
    # 3) 데이터 이관
    print("🔄 이상 거래 종목 데이터 이관 중...")
    anomalous_stocks = sqlite_session.query(AnomalousStock).all()
    for stock in anomalous_stocks:
        new_stock = AnomalousStock(
            stock_code=stock.stock_code,
            stock_name=stock.stock_name,
            manipulation_type=stock.manipulation_type,
            급등빈발_일수=stock.급등빈발_일수,
            극심한급등_최대등락률=stock.극심한급등_최대등락률,
            거래량급증빈발_일수=stock.거래량급증빈발_일수,
            위험도점수=stock.위험도점수,
            created_at=stock.created_at
        )
        postgres_session.add(new_stock)
    
    print("🔄 주식 패턴 데이터 이관 중...")
    stock_patterns = sqlite_session.query(StockPattern).all()
    for pattern in stock_patterns:
        new_pattern = StockPattern(
            stock_code=pattern.stock_code,
            date=pattern.date,
            open_price=pattern.open_price,
            high_price=pattern.high_price,
            low_price=pattern.low_price,
            close_price=pattern.close_price,
            volume=pattern.volume,
            pattern_type=pattern.pattern_type,
            created_at=pattern.created_at
        )
        postgres_session.add(new_pattern)

    postgres_session.commit()
    print("✅ 데이터 이관 완료!")

except Exception as e:
    print(f"❌ 데이터 이관 중 오류 발생: {str(e)}")
    postgres_session.rollback()

finally:
    # 4) 세션 종료
    sqlite_session.close()
    postgres_session.close() 