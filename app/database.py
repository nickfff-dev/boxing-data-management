from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLite file lives next to this package 45 change path as needed
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, '..', 'fighterdata.db')}"

engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},  # required for SQLite + FastAPI
            echo=False,  # set True to see all SQL in stdout (useful for debugging)
                    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency 45 yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
