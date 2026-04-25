import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

_data_dir = os.getenv("DATA_DIR", ".")
DATABASE_URL = f"sqlite:///{_data_dir}/stocks.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite with FastAPI
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
