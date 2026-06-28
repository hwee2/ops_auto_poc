from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pandas_service import validate_excel_integrity

router = APIRouter(prefix="/excel", tags=["Excel"])


@router.post("/upload")
async def upload_partner_excel(file: UploadFile = File(...)) -> dict:
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="올바른 파일 형식이 아닙니다.")

    try:
        file_bytes = await file.read()
        validation_result = validate_excel_integrity(file_bytes)
        return validation_result

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 처리 중 오류 발생: {str(e)}")