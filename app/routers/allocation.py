from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# 데이터 모델 정의
class AllocationAutoControlRequest(BaseModel):
    partner_name: str          # 메일 본문에서 추출한 제휴사 명칭 (ex. OO생명보험)
    start_time: Optional[str] = None  # 중지 시작 시간 (HH:MM) (ex. "14:00")
    end_time: Optional[str] = None    # 중지 종료 시간 (HH:MM) (ex. "17:00")
    is_pause_request: bool     # 중지 요청 여부: 본문에 '중지', '멈춤' 등이 있으면 True

# 배분율 제어 엔드포인트 구현
@router.put("/auto-control", summary="기획서 규격 기반 배분율 자동 제어")
def auto_control_partner_allocation(payload: AllocationAutoControlRequest):
    """
    is_pause_request에 따라 제휴사의 배분율을 0%로 설정하거나 원복합니다.
    """
    try:
        print(f"[배분율 제어 신호 수신] 제휴사: {payload.partner_name}")

        # 기획서 규격 반영: is_pause_request가 True인 경우 배분율 0% 고정
        if payload.is_pause_request:
            print(f"-> [정정 확인] 유입 중지 요청 여부(is_pause_request): {payload.is_pause_request}")
            print(f"-> [규칙 실행] '{payload.partner_name}'의 배분율을 '0%'로 설정합니다.")
            print(f"-> [시간 제어] 유입 중지 시간대: {payload.start_time} ~ {payload.end_time}")

            return {
                "status": "success",
                "partner_name": payload.partner_name,
                "current_allocation": 0,
                "is_pause_request": payload.is_pause_request,
                "control_window": {
                    "start": payload.start_time,
                    "end": payload.end_time
                },
                "message": f"{payload.partner_name}의 요청이 확인되어 해당 시간 동안 배분율이 0%로 설정되었습니다."
            }
        else:
            # 중지 요청이 False인 경우 (정상 복구 혹은 대기 상태)
            print(f"-> [규칙 실행] 중지 요청 없음. {payload.partner_name}은 정상 배분율 상태를 유지하거나 복구됩니다.")
            return {
                "status": "success",
                "partner_name": payload.partner_name,
                "is_pause_request": payload.is_pause_request,
                "message": "정상 상태를 유지합니다."
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"배분율 제어 시스템 내부 오류: {str(e)}")