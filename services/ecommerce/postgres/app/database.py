import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/benchmark_db"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=25,  # Increase active connections from 5 to 25
    max_overflow=50,  # Allow up to 50 additional bursting connections
    pool_timeout=30,  # Keep the 30-second timeout
    pool_pre_ping=True,  # Safely recycles dead connections
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
