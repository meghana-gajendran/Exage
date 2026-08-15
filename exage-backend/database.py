from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///./exage.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from models import Session, Message, AgentTrace  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Migration: add session_context_json column if it doesn't exist.
    # create_all() only creates tables from scratch — it doesn't alter
    # existing tables. This handles databases created before this column
    # was added, so existing users don't hit OperationalError on startup.
    with engine.connect() as conn:
        try:
            conn.execute(text(
                "ALTER TABLE sessions ADD COLUMN session_context_json TEXT DEFAULT '{}'"
            ))
            conn.commit()
        except Exception:
            # Column already exists — safe to ignore
            pass
