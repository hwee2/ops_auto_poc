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
    has_attachment: bool = None
    body_text: Optional[str] = None


# 백그라운드에서 첨부파일 확장자를 판별하고 엑셀일 경우에만 Pandas 검증을 수행하는 함수
def process_excel_file(payload: GmailWebhookPayload):
    try:
        file_name = payload.file_name.lower() if payload.file_name else ""
        if not (file_name.endswith(".xlsx") or file_name.endswith(".xls")):
            validation_result = {"status": "fail", "reason": f"엑셀 규격(.xlsx, .xls)이 아닌 올바르지 않은 파일 형식입니다."}
        else:
            gmail_api_url = f"{settings.GMAIL_SERVICE_URL}/emails/{payload.email_id}/attachments"
            response = httpx.get(gmail_api_url, timeout=30.0)

            if response.status_code != 200:
                print(f"[다운로드 실패] Gmail API 호출 실패: {response.status_code}")
                return

            file_bytes = response.content
            validation_result = validate_excel_integrity(file_bytes)

        if validation_result.get("status") == "success":
            print(f"[자동화 성공] 체결실적 검증 성공: 후속 적재 프로세스를 진행합니다.")
            with SessionLocal() as db:
                insert_validated_excel_meta(
                    db=db,
                    email_id=payload.email_id,
                    sender=payload.sender,
                    total_rows=validation_result.get("total_rows")
                )
        else:
            print(f"[자동화 실패] 정합성 검증 실패. 사유: {validation_result.get('reason')}")

            alert_payload = {
                "to_email": payload.sender,
                "subject": f"[데이터 오류 알림] 엑셀 데이터 정합성 검증 실패 사유 확인 요청",
                "body_text": f"아래 제휴사로부터 유입된 엑셀 파일의 정합성 검증이 실패했습니다. 데이터 확인 부탁드립니다.\n\n"
                             f"■ 발신 제휴사 계정: {payload.sender}\n"
                             f"■ 메일 제목: {payload.subject}\n"
                             f"■ 검증 실패 사유: {validation_result.get('reason')}\n\n"
                             f"해당 데이터를 확인해 주시기 바랍니다."
            }
            httpx.post(f"{settings.GMAIL_SERVICE_URL}/emails/send", json=alert_payload, timeout=10.0)

    except Exception as e:
        print(f"[백그라운드 에러] {str(e)}")


# 백그라운드에서 Dify AI를 연동해 텍스트 메일을 파싱하고 결과를 처리하는 함수
def process_dify_parsing(payload: GmailWebhookPayload):
    try:
        import httpx
        from app.config import settings

        dify_api_url = f"{settings.DIFY_SERVICE_URL}/chat-messages"
        headers = {"Authorization": f"Bearer {settings.DIFY_API_KEY}"}
        dify_payload = {
            "inputs": {},
            "query": payload.body_text,
            "response_mode": "blocking",
            "user": payload.sender
        }

        response = httpx.post(dify_api_url, json=dify_payload, headers=headers, timeout=30.0)

        if response.status_code == 200:
            dify_result = response.json()
            parsed_answer = dify_result.get("answer", "")
            print(f"[Dify 파싱 성공] 추출 데이터: {parsed_answer}")
        else:
            print(f"[Dify 파싱 실패] 상태 코드: {response.status_code}")

            alert_payload = {
                "to_email": settings.ADMIN_EMAIL,
                "subject": f"[Dify AI 파싱 실패 알림] 제휴사 배분율 변경 텍스트 파싱 오류 발생",
                "body_text": f"아래 제휴사로부터 유입된 메일의 AI 파싱이 실패했습니다. 확인 부탁드립니다.\n\n"
                             f"■ 발신 제휴사 계정: {payload.sender}\n"
                             f"■ 메일 제목: {payload.subject}\n"
                             f"■ 메일 본문: {payload.body_text}\n\n"
                             f"Dify 인프라 상태를 점검하거나 내부 시스템에서 수동으로 배분율을 조정해 주시기 바랍니다."
            }
            httpx.post(f"{settings.GMAIL_SERVICE_URL}/emails/send", json=alert_payload, timeout=10.0)

    except Exception as e:
        print(f"[Dify 백그라운드 에러] {str(e)}")


@router.post("/webhook", summary="Gmail 수신 신호 처리 및 분기")
def receive_gmail_notification(payload: GmailWebhookPayload, background_tasks: BackgroundTasks):
    try:
        print(f"[수신 통계] 발신자: {payload.sender} | 제목: {payload.subject}")

        if payload.has_attachment:
            print("-> [YES 경로] 엑셀 첨부파일 확인: 파일 확장자 검증 단계로 진입합니다.")
            background_tasks.add_task(process_excel_file, payload)
            return {
                "status": "success",
                "route": "YES (Excel/Pandas)",
                "message": "첨부파일 확장자 필터링 및 검증 프로세스가 시작되었습니다."
            }
        else:
            print("-> [NO 경로] 텍스트 메일 확인: AI 파싱 단계로 진입합니다.")
            background_tasks.add_task(process_dify_parsing, payload)
            return {
                "status": "success",
                "route": "NO (Text/Dify)",
                "message": "AI 파싱 및 배분율 변경 프로세스가 시작되었습니다."
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gmail 라우터 내부 처리 오류: {str(e)}")