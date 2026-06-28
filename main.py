from fastapi import FastAPI
from app.config import settings
from app.routers import gmail, allocation
from app.upload import excel_upload
from app.database import engine
from app.models import partner_model

# 데이터베이스 테이블 자동 생성
partner_model.Base.metadata.create_all(bind=engine)

# fastapi 어플리케이션 인스턴스 생성
app = FastAPI(
    title="제휴사 운영 자동화 시스템 PoC",
    description="Gmail API 연동, Dify AI 텍스트 파싱, Pandas 정합성 검증을 통합한 백엔드 서버",
    version="1.0.0"
)

# 기능별 라우터 등록
# 메일 처리 경로
app.include_router(gmail.router, prefix="/api/v1/gmail", tags=["Gmail 연동"])
# 배분율 변경 API 호출 경로
app.include_router(allocation.router, prefix="/api/v1/allocation", tags=["배분율 관리"])
app.include_router(excel_upload.router, prefix="/api/v1/excel", tags=["Excel 검증"])

# 3. 시스템 상태 체크 엔드포인트
@app.get("/", tags=["시스템 상태"])
def read_root():
    return {
        "status": "healthy",
        "message": "운영 자동화 시스템 서버가 정상 구동 중입니다.",
        "database_connected": settings.DATABASE_URL.startswith("sqlite")
    }