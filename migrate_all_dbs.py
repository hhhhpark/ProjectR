from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Date, Text, Boolean
from sqlalchemy.orm import Session
import os
from datetime import datetime

# PostgreSQL 연결 정보
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_SERVER = "localhost"
POSTGRES_PORT = "5432"
POSTGRES_DB = "stock_pattern_db"

POSTGRES_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
postgres_engine = create_engine(POSTGRES_URL)

# SQLite DB 파일 목록
sqlite_dbs = [
    "DB/collectCompleteData.db",
    "DB/manipulation_stocks.db",
    "DB/collectList.db",
    "DB/anomalousList.db",
    "DB/suspect_stocks.db",
    "DB/named_abnormal_stocks.db"
]

def convert_datetime(value):
    if isinstance(value, str):
        try:
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                return None
    return value

def create_tables(engine):
    metadata = MetaData()
    
    # 테이블 정의
    Table('completed_stocks', metadata,
        Column('id', Integer, primary_key=True),
        Column('stock_name', String),  # NULL 허용
        Column('stock_code', String),  # NULL 허용
        Column('date', Date),
        Column('open_price', Float),
        Column('high_price', Float),
        Column('low_price', Float),
        Column('close_price', Float),
        Column('volume', Integer),
        Column('change_rate', Float),
        Column('market_cap', Float),
        Column('trading_value', Float),
        Column('listed_shares', Integer),
        Column('bps', Float),
        Column('per', Float),
        Column('pbr', Float),
        Column('eps', Float),
        Column('div', Float),
        Column('dps', Float),
        Column('institution_total', Float),
        Column('other_corporation', Float),
        Column('individual', Float),
        Column('foreign_total', Float),
        Column('short_balance', Float),
        Column('short_ratio', Float),
        Column('created_at', DateTime),
        Column('updated_at', DateTime)
    )

    Table('manipulation_stocks', metadata,
        Column('id', Integer, primary_key=True),
        Column('stock_name', String),  # NULL 허용
        Column('stock_code', String),  # NULL 허용
        Column('category', String),
        Column('manipulation_period', String),
        Column('max_rise_rate', Float),
        Column('manipulation_type', String),
        Column('description', Text),
        Column('급등빈발_일수', Integer),
        Column('급등빈발_기간', String),
        Column('극심한급등_최대등락률', Float),
        Column('극심한급등_기간', String),
        Column('거래량급증빈발_일수', Integer),
        Column('거래량급증빈발_기간', String),
        Column('상한가근처_일수', Integer),
        Column('상한가근처_기간', String),
        Column('평균회전율', Float),
        Column('위험도점수', Integer),
        Column('created_at', DateTime),
        Column('updated_at', DateTime)
    )

    Table('collection_stocks', metadata,
        Column('id', Integer, primary_key=True),
        Column('stock_name', String),  # NULL 허용
        Column('stock_code', String),  # NULL 허용
        Column('created_at', DateTime),
        Column('updated_at', DateTime)
    )

    Table('suspect_stocks', metadata,
        Column('id', Integer, primary_key=True),
        Column('stock_name', String),  # NULL 허용
        Column('stock_code', String),  # NULL 허용
        Column('suspected_period', String),
        Column('theme_reason', Text),
        Column('main_issue', Text),
        Column('active_duration', String),
        Column('buy_side_pattern', Text),
        Column('price_3y_ago', Float),
        Column('price_peak', Float),
        Column('price_current', Float)
    )

    Table('stock_daily_data', metadata,
        Column('id', Integer, primary_key=True),
        Column('stock_code', String),  # NULL 허용
        Column('date', Date),
        Column('open_price', Float),
        Column('high_price', Float),
        Column('low_price', Float),
        Column('close_price', Float),
        Column('volume', Integer),
        Column('change_rate', Float),
        Column('market_cap', Float),
        Column('trading_value', Float),
        Column('created_at', DateTime)
    )

    Table('manipulation_analysis', metadata,
        Column('id', Integer, primary_key=True),
        Column('stock_name', String),  # NULL 허용
        Column('stock_code', String),  # NULL 허용
        Column('category', String),
        Column('manipulation_period', String),
        Column('max_rise_rate', Float),
        Column('manipulation_type', String),
        Column('risk_level', String),
        Column('risk_score', Integer),
        Column('description', Text),
        Column('analysis_patterns', Text),
        Column('warnings', Text),
        Column('created_at', DateTime),
        Column('updated_at', DateTime)
    )

    metadata.create_all(engine)

def migrate_db(sqlite_path, postgres_engine):
    print(f"\n🔄 Migrating {sqlite_path} to PostgreSQL...")
    
    # SQLite 연결
    sqlite_url = f"sqlite:///./{sqlite_path}"
    sqlite_engine = create_engine(sqlite_url)
    sqlite_metadata = MetaData()
    sqlite_metadata.reflect(bind=sqlite_engine)
    
    # PostgreSQL 연결
    postgres_metadata = MetaData()
    postgres_metadata.reflect(bind=postgres_engine)
    
    # 각 테이블 마이그레이션
    for table_name in sqlite_metadata.tables:
        print(f"  ⏳ Migrating table: {table_name}")
        try:
            # SQLite 테이블에서 데이터 읽기
            sqlite_table = Table(table_name, sqlite_metadata, autoload_with=sqlite_engine)
            with sqlite_engine.connect() as sqlite_conn:
                result = sqlite_conn.execute(sqlite_table.select())
                columns = [col.name for col in sqlite_table.columns]
                data = []
                for row in result:
                    row_dict = {}
                    for idx, column in enumerate(columns):
                        value = row[idx]
                        if isinstance(value, str) and ('date' in column.lower() or 'created_at' in column.lower() or 'updated_at' in column.lower()):
                            value = convert_datetime(value)
                        row_dict[column] = value
                    data.append(row_dict)
            
            if not data:
                print(f"  ✅ Successfully migrated 0 rows from {table_name}")
                continue
            
            # PostgreSQL에 데이터 삽입
            postgres_table = Table(table_name, postgres_metadata, autoload_with=postgres_engine)
            with postgres_engine.connect() as postgres_conn:
                postgres_conn.execute(postgres_table.delete())
                if data:
                    postgres_conn.execute(postgres_table.insert(), data)
                postgres_conn.commit()
            
            print(f"  ✅ Successfully migrated {len(data)} rows from {table_name}")
            
        except Exception as e:
            print(f"  ❌ Error migrating {table_name}: {str(e)}")
            try:
                # 테이블 재생성 시도
                create_tables(postgres_engine)
                with postgres_engine.connect() as postgres_conn:
                    postgres_table = Table(table_name, postgres_metadata, autoload_with=postgres_engine)
                    postgres_conn.execute(postgres_table.delete())
                    if data:
                        postgres_conn.execute(postgres_table.insert(), data)
                    postgres_conn.commit()
                print(f"  ✅ Successfully migrated {len(data)} rows from {table_name} after recreation")
            except Exception as e2:
                print(f"  ❌ Error setting up table {table_name}: {str(e2)}")

def main():
    # PostgreSQL 테이블 생성
    create_tables(postgres_engine)
    
    # 각 DB 마이그레이션
    for sqlite_db in sqlite_dbs:
        if os.path.exists(sqlite_db):
            migrate_db(sqlite_db, postgres_engine)
        else:
            print(f"\n⚠️ Warning: {sqlite_db} not found, skipping...")
    
    print("\n✨ Migration process completed!")

if __name__ == "__main__":
    main() 