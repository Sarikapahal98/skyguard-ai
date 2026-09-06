"""
Database connection setup.
Edit DATABASE_URL below (or set it via a .env file) to match your local Postgres.
Default assumes: user=postgres, password=postgres, db=skyguard, running on localhost.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:Karan%402006@localhost:5432/skyguard"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: gives each request its own DB session, closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
