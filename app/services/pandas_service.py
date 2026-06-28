from datetime import datetime
import pandas as pd
import io



def validate_excel_integrity(file_bytes: bytes) -> dict:
    try:
        # 바이너리 바이트 데이터를 판다스가 읽을 수 있도록 메모리 버퍼 스트림으로 변환
        excel_stream = io.BytesIO(file_bytes)
        df = pd.read_excel(excel_stream)

        # 기획서상 필수적으로 존재해야 하는 데이터 컬럼 정의
        required_columns = ["제휴사ID", "배분율", "적용시작일"]

        # 파일 내에 필수 컬럼이 하나라도 누락되었는지 검사
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            return {"status": "fail", "reason": f"필수 컬럼 누락: {', '.join(missing_cols)}"}

        # 배분율 컬럼에 빈 값(Null)이나 결측치가 존재하는지 검사
        if df["배분율"].isnull().any():
            return {"status": "fail", "reason": "배분율 컬럼에 누락된 값이 존재합니다."}

        # 모든 검증 조건을 통과한 경우 데이터 총 행수와 함께 성공 반환
        return {
            "status": "success",
            "total_rows": len(df)
        }

    except Exception as e:
        # 엑셀 파일 손상이나 확장자 불일치 등 파싱 자체 실패 시 예외 처리
        return {"status": "fail", "reason": f"엑셀 파일 해석 불가 및 손상: {str(e)}"}