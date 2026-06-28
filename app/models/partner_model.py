from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class PartnerExcelRecord(Base):
    __tablename__ = "partner_excel_records"

    id = Column(Integer, primary_key=True, index=True)

    email_id = Column(String, unique=True, index=True, nullable=False)

    sender_email = Column(String, nullable=False)

    row_count = Column(Integer, nullable=False)

    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)