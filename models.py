from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, Boolean
from sqlalchemy.sql import func
from database import Base

class CompletedStock(Base):
    __tablename__ = "completed_stocks"

    id = Column(Integer, primary_key=True, index=True)
    stock_name = Column(String)
    stock_code = Column(String)
    date = Column(Date)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    change_rate = Column(Float)
    market_cap = Column(Float)
    trading_value = Column(Float)
    listed_shares = Column(Integer)
    bps = Column(Float)
    per = Column(Float)
    pbr = Column(Float)
    eps = Column(Float)
    div = Column(Float)
    dps = Column(Float)
    institution_total = Column(Float)
    other_corporation = Column(Float)
    individual = Column(Float)
    foreign_total = Column(Float)
    short_balance = Column(Float)
    short_ratio = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ManipulationStock(Base):
    __tablename__ = "manipulation_stocks"

    id = Column(Integer, primary_key=True, index=True)
    stock_name = Column(String)
    stock_code = Column(String)
    category = Column(String)
    manipulation_period = Column(String)
    max_rise_rate = Column(Float)
    manipulation_type = Column(String)
    description = Column(Text)
    급등빈발_일수 = Column(Integer)
    급등빈발_기간 = Column(String)
    극심한급등_최대등락률 = Column(Float)
    극심한급등_기간 = Column(String)
    거래량급증빈발_일수 = Column(Integer)
    거래량급증빈발_기간 = Column(String)
    상한가근처_일수 = Column(Integer)
    상한가근처_기간 = Column(String)
    평균회전율 = Column(Float)
    위험도점수 = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class CollectionStock(Base):
    __tablename__ = "collection_stocks"

    id = Column(Integer, primary_key=True, index=True)
    stock_name = Column(String)
    stock_code = Column(String, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class SuspectStock(Base):
    __tablename__ = "suspect_stocks"

    id = Column(Integer, primary_key=True, index=True)
    stock_name = Column(String)
    stock_code = Column(String)
    suspected_period = Column(String)
    theme_reason = Column(Text)
    main_issue = Column(Text)
    active_duration = Column(String)
    buy_side_pattern = Column(Text)
    price_3y_ago = Column(Float)
    price_peak = Column(Float)
    price_current = Column(Float)

class StockDailyData(Base):
    __tablename__ = "stock_daily_data"

    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String)
    date = Column(Date)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    change_rate = Column(Float)
    market_cap = Column(Float)
    trading_value = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

class ManipulationAnalysis(Base):
    __tablename__ = "manipulation_analysis"

    id = Column(Integer, primary_key=True, index=True)
    stock_name = Column(String)
    stock_code = Column(String)
    category = Column(String)
    manipulation_period = Column(String)
    max_rise_rate = Column(Float)
    manipulation_type = Column(String)
    risk_level = Column(String)
    risk_score = Column(Integer)
    description = Column(Text)
    analysis_patterns = Column(Text)
    warnings = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class HistoricalManipulationStock(Base):
    __tablename__ = "historical_manipulation_stocks"

    id = Column(Integer, primary_key=True, index=True)
    stock_name = Column(String)
    stock_code = Column(String)
    category = Column(String)
    manipulation_period = Column(String)
    max_rise_rate = Column(Float)
    manipulation_type = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now()) 