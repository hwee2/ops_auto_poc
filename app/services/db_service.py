from sqlalchemy.orm import Session
from app.models.partner_model import PartnerExcelRecord
from datetime import datetime


def insert_validated_excel_meta(db: Session, email_id: str, sender: str, total_rows: int) -> PartnerExcelRecord:
    try:
        # 데이터베이스 테이블 구조에 맞게 제휴사 엑셀 메타데이터 객체 생성
        db_record = PartnerExcelRecord(
            email_id=email_id,
            sender_email=sender,
            row_count=total_rows,
            processed_at=datetime.utcnow()
        )

        db.add(db_record)
        db.commit()
        db.refresh(db_record)

        return db_record

    except Exception as e:
        db.rollback()
        print(f"[DB 데이터 적재 실패] 사유: {str(e)}")
        raise e