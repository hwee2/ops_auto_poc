from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# SQLite 및 스레드 호환성을 위한 커넥션 인자 설정 가드 유지
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

# 백그라운드 태스크 및 라우터에서 공용으로 사용할 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# FastAPI 엔드포인트 동기식 의존성 주입 함수 유지
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()