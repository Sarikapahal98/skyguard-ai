"""
Database connection setup.
Edit DATABASE_URL below (or set it via a .env file) to match your local Postgres.
Default assumes: user=postgres, password=postgres, db=skyguard, running on localhost.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load variables from local .env file
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/skyguard"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # tests each connection before using it, reconnects if dead
    pool_recycle=300,     # recycle connections every 5 minutes, before Neon kills them
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: gives each request its own DB session, closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
