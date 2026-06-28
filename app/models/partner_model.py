from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class PartnerMaster(Base):
    __tablename__ = "partner_master"

    id = Column(Integer, primary_key=True, index=True)
    partner_name = Column(String, unique=True, index=True, nullable=False)
    original_ratio = Column(Integer, nullable=False) # 원복 기준값
    current_ratio = Column(Integer, nullable=False) # 실시간 제어값


class PartnerExcelRecord(Base):
    __tablename__ = "partner_excel_records"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String, unique=True, index=True, nullable=False)
    sender_email = Column(String, nullable=False)
    row_count = Column(Integer, nullable=False)
    processed_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    # # 배분율 관련 컬럼
    # allocation_ratio = Column(Integer, nullable=False)
    # pause_start_time = Column(String, nullable=True)
    # pause_end_time = Column(String, nullable=True)
    # updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))