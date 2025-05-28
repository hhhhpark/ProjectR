- 스크립트 구성(데이터 수집 관런)
  1. [DB] 수집 종목 테이블 생성 (컬럼: 주식명, 주식코드 / sample : 100개)
  2. [DB] 등록 완료 테이블 생성 (컬럼: 주식명, 주식코드, 날짜, 시가, 고가 저가 종가 거래량 등락률 시가총액 거래량\_cap 거래대금 상장주식수 BPS PER PBR EPS DIV DPS 기관합계 기타법인 개인 외국인합계)
  3. [DB] 작전주 테이블 생성(컬럼: id stock_name stock_code category manipulation_period max_rise_rate manipulation_type description created_at updated_at)
  4. [Python Script] 수집 종목 테이블 에 있는 종목이 등록 완료 테이블에 있을 경우, 어제 데이터만 가져와서 업데이트 하고, 등록 완료 테이블에 없을 경우 3년치 데이터를 가져와서 등록 완료 테이블에 업데이트 해줘. 스크립트 수집 항목들은 DB 등록완료 테이블 컬럼을 참고해서 가져와줘
  5. [Python Script] 등록완료 테이블에 등록된 주식 중, 작전주 의심 정황이 있으면 작전주 테이블에 업데이트해줘.
