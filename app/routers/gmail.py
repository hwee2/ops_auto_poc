from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


# 1. 수신 데이터 규격 정의 (Pydantic 모델)
class GmailWebhookPayload(BaseModel):
    email_id: str
    sender: str
    subject: str
    has_attachment: bool
    body_text: Optional[str] = None


# 2. Gmail 수신 엔드포인트 구현 (POST /api/v1/gmail/webhook)
@router.post("/webhook", summary="Gmail 수신 신호 처리 및 분기")
def receive_gmail_notification(payload: GmailWebhookPayload, background_tasks: BackgroundTasks):
    """
    Gmail API 연동 신호를 수신하여 첨부파일 유무에 따라 후속 비즈니스 로직(Dify 또는 Pandas)으로 분기합니다.
    """
    try:
        print(f"[수신 통계] 발신자: {payload.sender} | 제목: {payload.subject}")

        # 기획서 3.0 단계: 첨부파일 유무 분기 처리
        if payload.has_attachment:
            print("-> [YES 경로] 엑셀 첨부파일 확인: Pandas 정합성 검증 단계로 진입합니다.")
            # TODO: background_tasks.add_task(pandas_service_process, payload)
            return {
                "status": "success",
                "route": "YES (Excel/Pandas)",
                "message": "엑셀 정합성 검증 프로세스가 시작되었습니다."
            }
        else:
            print("-> [NO 경로] 텍스트 메일 확인: AI 파싱 단계로 진입합니다.")
            # TODO: background_tasks.add_task(dify_service_process, payload)
            return {
                "status": "success",
                "route": "NO (Text/Dify)",
                "message": "AI 파싱 및 배분율 변경 프로세스가 시작되었습니다."
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gmail 라우터 내부 처리 오류: {str(e)}")