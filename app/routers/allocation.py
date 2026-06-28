from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.partner_model import PartnerMaster
from dateutil import parser
from datetime import datetime

router = APIRouter()


class AllocationAutoControlRequest(BaseModel):
    partner_name: str
    start_date: str
    end_date: str
    is_pause_request: bool


@router.put("/auto-control")
async def auto_control_partner_allocation(payload: AllocationAutoControlRequest, db: Session = Depends(get_db)):
    print(f"DEBUG: 서버가 받은 데이터 -> {payload.dict()}")

    partner = db.query(PartnerMaster).filter(PartnerMaster.partner_name == payload.partner_name).first()

    if not partner:
        raise HTTPException(status_code=404, detail="등록되지 않은 제휴사입니다.")

    try:
        now = datetime.now()
        start_dt = parser.parse(payload.start_date.strip() if "T" in payload.start_date else f"{datetime.now().strftime('%Y-%m-%d')}T{payload.start_date.strip()}")
        end_dt = parser.parse(payload.end_date.strip() if "T" in payload.end_date else f"{datetime.now().strftime('%Y-%m-%d')}T{payload.end_date.strip()}")
    except Exception:
        raise HTTPException(status_code=400, detail="날짜 형식이 잘못되었습니다.")

    # 1. 예약 정보 및 중지 요청 상태 DB 기록
    partner.is_reserved = payload.is_pause_request
    partner.start_date = start_dt
    partner.end_date = end_dt

    # 2. 제어 로직 적용
    if payload.is_pause_request and (start_dt <= now <= end_dt):
        partner.current_ratio = 0
    else:
        partner.current_ratio = partner.original_ratio

    db.commit()

    return {
        "status": "success",
        "partner_name": partner.partner_name,
        "is_reserved": partner.is_reserved,
        "current_ratio": partner.current_ratio,
        "start_date": partner.start_date,
        "end_date": partner.end_date
    }