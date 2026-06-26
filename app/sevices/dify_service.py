import httpx
from app.config import settings

DIFY_API_URL = "https://api.dify.ai/v1/completion-messages"


async def parse_email_with_dify(body_text: str) -> dict:
    """
    Gmail 본문 텍스트를 Dify API로 전송하여 제휴사 정보 및 중지 시간/여부를 파싱합니다.
    """
    if not settings.DIFY_API_KEY:
        print("[경고] DIFY_API_KEY가 설정되지 않아 모크 데이터를 반환합니다.")
        return {
            "partner_name": "테스트생명보험",
            "start_time": "14:00",
            "end_time": "17:00",
            "is_pause_request": True
        }

    headers = {
        "Authorization": f"Bearer {settings.DIFY_API_KEY}",
        "Content-Type": "application/json"
    }

    # Dify Chat/Completion Prompt 연동 규격 파라미터
    payload = {
        "inputs": {
            "email_body": body_text
        },
        "response_mode": "blocking",
        "user": "automation-backend-server"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(DIFY_API_URL, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            result = response.json()

            # Dify LLM이 출력한 JSON 텍스트 파싱 처리
            answer_text = result.get("answer", "{}")
            import json
            parsed_data = json.loads(answer_text)

            return {
                "partner_name": parsed_data.get("partner_name"),
                "start_time": parsed_data.get("start_time"),
                "end_time": parsed_data.get("end_time"),
                "is_pause_request": bool(parsed_data.get("is_pause_request", False))
            }

        except httpx.HTTPStatusError as e:
            print(f"[Dify API 오류] 상태 코드: {e.response.status_code} | 내용: {e.response.text}")
            raise e
        except Exception as e:
            print(f"[Dify 서비스 내부 오류] {str(e)}")
            raise e