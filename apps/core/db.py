from collections.abc import Generator
from sqlalchemy import create_engine,text
from sqlalchemy.orm import Session,sessionmaker
from apps.core.config import get_settings
engine=create_engine(get_settings().database_url,pool_pre_ping=True,future=True);SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False,expire_on_commit=False)
def get_db()->Generator[Session,None,None]:
    db=SessionLocal()
    try:yield db
    finally:db.close()
def check_database():
    try:
        with engine.connect() as c:c.execute(text("SELECT 1"))
        return True
    except Exception:return False
