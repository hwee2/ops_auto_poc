from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.pandas_service import validate_excel_integrity
import httpx
from app.config import settings
from app.services.pandas_service import validate_excel_integrity
from app.database import SessionLocal
from app.services.db_service import insert_validated_excel_meta

router = APIRouter()


# 수신 데이터 모델 정의
class GmailWebhookPayload(BaseModel):
    email_id: str
    sender: str
    subject: str
    has_attachment: bool
    body_text: Optional[str] = None

# 엑셀 정합성을 검증 함수
def process_excel_file(payload: GmailWebhookPayload):

    try:
        # 내부 Gmail 서비스 API를 호출하여 메일에 첨부된 엑셀 파일 다운로드 경로 설정
        gmail_api_url = f"{settings.GMAIL_SERVICE_URL}/emails/{payload.email_id}/attachments"
        response = httpx.get(gmail_api_url, timeout=30.0)

        # API 호출 실패 시 다운로드 에러 로그를 남기고 프로세스 즉시 종료
        if response.status_code != 200:
            print(f"[다운로드 실패] Gmail API 호출 실패: {response.status_code}")
            return

        # 다운로드한 파일의 바이너리 바이트 데이터를 변수에 할당
        file_bytes = response.content
        # 판다스 서비스의 정합성 검증 함수를 실행하여 결과 딕셔너리 수신
        validation_result = validate_excel_integrity(file_bytes)


        if validation_result.get("status") == "success":
            print(f"[자동화 성공] 정합성 검증 성공: 후속 적재 프로세스를 진행합니다.")
            # TODO: 성공 시 DB 적재 또는 다음 파이프라인 호출
            with SessionLocal() as db:
                insert_validated_excel_meta(
                    db=db,
                    email_id=payload.email_id,
                    sender=payload.sender,
                    total_rows=validation_result.get("total_rows")
                )

        else:
            print(f"[자동화 실패] 정합성 검증 실패: {validation_result.get('reason')}")
            # TODO: 실패 시 담당자 알림 및 제휴사 반려 메일 발송

            # 발신자(제휴사)에게 전송할 자동 반려 알림 메일 페이로드 구성
            alert_payload = {
                "to_email": payload.sender,
                "subject": f"[데이터 오류 알림] 엑셀 데이터 정합성 검증 실패 사유 확인 요청",
                "body_text": f"아래 제휴사로부터 유입된 엑셀 파일의 정합성 검증이 실패했습니다. 데이터 확인 부탁드립니다.\n\n"
                                f"■ 발신 제휴사 계정: {payload.sender}\n"
                                f"■ 메일 제목: {payload.subject}\n"
                                f"■ 검증 실패 사유: {validation_result.get('reason')}\n\n"
                                f"해당 데이터를 확인해 주시기 바랍니다."
        }
            # Gmail 발송 API를 호출하여 제휴사 담당자에게 에러 리포트 메일 즉시 발송
            httpx.post(f"{settings.GMAIL_SERVICE_URL}/emails/send", json=alert_payload, timeout=10.0)

    except Exception as e:
        print(f"[백그라운드 에러] {str(e)}")


# Gmail 수신 엔드포인트 구현 (POST /api/v1/gmail/webhook)
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