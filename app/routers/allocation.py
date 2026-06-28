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
    start_time: str
    end_time: str
    is_pause_request: bool


@router.put("/auto-control")
def auto_control_partner_allocation(payload: AllocationAutoControlRequest, db: Session = Depends(get_db)):
    partner = db.query(PartnerMaster).filter(PartnerMaster.partner_name == payload.partner_name).first()

    if not partner:
        raise HTTPException(status_code=404, detail="등록되지 않은 제휴사입니다.")

    try:
        end_dt = parser.parse(payload.end_time)
        now = datetime.now()
    except Exception:
        raise HTTPException(status_code=400, detail="날짜 형식이 잘못되었습니다.")

    if payload.is_pause_request and now < end_dt:
        partner.current_ratio = 0
    else:
        # DB에 저장된 원래 배분율(original_ratio)로 복구
        partner.current_ratio = partner.original_ratio

    db.commit()
    return {
        "status": "success",
        "partner_name": partner.partner_name,
        "current_ratio": partner.current_ratio,
        "original_ratio": partner.original_ratio
    }