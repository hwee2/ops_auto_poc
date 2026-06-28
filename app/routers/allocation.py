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
    # 1. Dify 인입 데이터 로그 출력 (시작시간 필드 포함 필수 기록)
    print(
        f"[Dify Webhook 인입] 제휴사: {payload.partner_name} | 시작시간: {payload.start_time} | 종료시간: {payload.end_time} | 중지요청: {payload.is_pause_request}")

    # 2. 등록된 제휴사 검증
    partner = db.query(PartnerMaster).filter(PartnerMaster.partner_name == payload.partner_name).first()

    if not partner:
        raise HTTPException(status_code=404, detail="등록되지 않은 제휴사입니다.")

    # 3. 시작시간 및 종료시간 날짜 파싱 및 형식 보완
    try:
        now = datetime.now()
        raw_start_time = payload.start_time.strip()
        raw_end_time = payload.end_time.strip()

        # Dify LLM이 날짜 없이 단순 시간("14:00")만 반환했을 경우 오늘 날짜와 결합하는 방어 처리
        today_str = now.strftime("%Y-%m-%d")
        if "T" not in raw_start_time and len(raw_start_time) <= 8:
            raw_start_time = f"{today_str}T{raw_start_time}"
        if "T" not in raw_end_time and len(raw_end_time) <= 8:
            raw_end_time = f"{today_str}T{raw_end_time}"

        start_dt = parser.parse(raw_start_time)
        end_dt = parser.parse(raw_end_time)
    except Exception:
        print(f"[오류 알림 발송] 시간 파싱 실패 - 입력값: start={payload.start_time}, end={payload.end_time}")
        raise HTTPException(status_code=400, detail="날짜 형식이 잘못되었습니다.")

    # 4. 예약된 제어 시간 범위 비즈니스 로직 처리
    # 중지 요청(true)이고, 현재 시간이 제휴사가 지정한 [시작시간]과 [종료시간] 사이에 위치할 때만 배분율 0 처리
    if payload.is_pause_request and (start_dt <= now <= end_dt):
        partner.current_ratio = 0
    else:
        # 지정된 예약 시간이 아니거나, 중지 요청이 해제된 경우 원래 배분율로 복구
        partner.current_ratio = partner.original_ratio

    # 5. DB 최종 반영 및 적재
    db.commit()

    return {
        "status": "success",
        "partner_name": partner.partner_name,
        "current_ratio": partner.current_ratio,
        "original_ratio": partner.original_ratio,
        "applied_start_time": start_dt.isoformat(),
        "applied_end_time": end_dt.isoformat()
    }