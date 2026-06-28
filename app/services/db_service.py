from sqlalchemy.orm import Session
from sqlalchemy import text


def insert_validated_excel_meta(db: Session, email_id: str, sender: str, total_rows: int):
    try:
        # 체결실적 메타데이터를 마스터 규격에 맞게 적재하는 네이티브 쿼리
        query = text("""
                     INSERT INTO partner_excel_records (email_id, sender_email, total_rows, registered_at)
                     VALUES (:email_id, :sender_email, :total_rows, NOW())
                     """)

        db.execute(query, {
            "email_id": email_id,
            "sender_email": sender,
            "total_rows": total_rows
        })
        db.commit()
        print(f"[DB 적재 완료] 발신자: {sender} | 총 실적 행 수: {total_rows}")

    except Exception as e:
        db.rollback()
        print(f"[DB 적재 에러] 데이터 롤백 처리 완료. 사유: {str(e)}")
        raise e