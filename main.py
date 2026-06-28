import sqlite3
from fastapi import FastAPI
from app.config import settings
from app.routers import gmail, allocation
from app.upload import excel_upload
from app.database import engine
from app.models import partner_model
from fastapi.responses import JSONResponse

# 데이터베이스 테이블 자동 생성
partner_model.Base.metadata.create_all(bind=engine)

# fastapi 어플리케이션 인스턴스 생성
app = FastAPI(
    title="제휴사 운영 자동화 시스템 PoC",
    description="Gmail API 연동, Dify AI 텍스트 파싱, Pandas 정합성 검증을 통합한 백엔드 서버",
    version="1.0.0"
)

DB_PATH = "test.db"
# 기능별 라우터 등록
# 메일 처리 경로
app.include_router(gmail.router, prefix="/api/v1/gmail", tags=["Gmail 연동"])
# 배분율 변경 API 호출 경로
app.include_router(allocation.router, prefix="/api/v1/allocation", tags=["배분율 관리"])
app.include_router(excel_upload.router, prefix="/api/v1/excel", tags=["Excel 검증"])

# 시스템 상태 체크 엔드포인트
@app.get("/", tags=["시스템 상태"])
def read_root():
    return {
        "status": "healthy",
        "message": "운영 자동화 시스템 서버가 정상 구동 중입니다.",
        "database_connected": settings.DATABASE_URL.startswith("sqlite")
    }


@app.get("/api/v1/allocation/auto-control")
async def get_db_status():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM partner_master")
        rows = cursor.fetchall()

        all_data = [dict(row) for row in rows]

        conn.close()
        return JSONResponse(content={"current_db_status": all_data})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# 서버 내부 로그 확인
@app.put("/api/v1/allocation/auto-control")
async def auto_control(data: dict):
    print(f"DEBUG: 수신된 데이터 -> {data}") # <--- 추가
    # 데이터 변경 로직...
    return {"status": "success", "received": data}