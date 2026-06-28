from datetime import datetime
import pandas as pd
from io import BytesIO
from fastapi import HTTPException


def validate_excel_integrity(file_bytes: bytes) -> dict:
    try:
        df = pd.read_excel(BytesIO(file_bytes))

        required_columns = ["partner_name", "contract_date", "contract_count"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"[검증 실패] 필수 컬럼 누락: {missing_columns}")
            return {"status": "fail", "reason": f"필수 컬럼 누락: {missing_columns}"}

        # 판다스가 날짜 형식을 자동으로 파싱하고 MM-DD는 현재 연도와 알아서 결합함
        df["contract_date"] = pd.to_datetime(df["contract_date"], errors="coerce").dt.strftime("%Y-%m-%d")

        if df["contract_date"].isnull().any():
            print(f"[검증 실패] 유효하지 않은 날짜 형식 포함")
            return {
                "status": "fail",
                "reason": "contract_date 필드에 처리할 수 없는 날짜 형식이 포함되어 있습니다."
            }

        # contract_count 검증
        df["contract_count"] = pd.to_numeric(df["contract_count"], errors="coerce")

        if (df["contract_count"] < 0).any() or df["contract_count"].isnull().any():
            print(f"[검증 실패] contract_count 규칙 위반 발견")
            return {
                "status": "fail",
                "reason": "contract_count 필드에 음수 또는 허용되지 않는 문자(공백 포함)가 존재합니다."
            }

        total_rows = len(df)
        print(f"[검증 성공] 총 {total_rows}건 검증 통과")
        return {
            "status": "success",
            "reason": "모든 규격 데이터 정합성 검증 및 정규화 통과",
            "total_rows": total_rows
        }

    except Exception as e:
        print(f"[Pandas 서비스 내부 오류] {str(e)}")
        raise HTTPException(status_code=500, detail=f"엑셀 정합성 검증 중 오류 발생: {str(e)}")