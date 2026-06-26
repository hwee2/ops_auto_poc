import os
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드
load_dotenv()

class Settings:
    # Dify 설정 정보
    DIFY_API_KEY: str = os.getenv("DIFY_API_KEY")
    DIFY_API_URL: str = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1")

    # SQLite DB 경로
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# 시스템 전역에서 사용할 설정 객체 생성
settings = Settings()