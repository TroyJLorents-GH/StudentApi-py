from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
import urllib

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the .env file.")

# Create the SQLAlchemy engine
# Detect if the string is a plain ODBC string or SQLAlchemy-style
if DATABASE_URL.strip().startswith("Driver="):
    # It's a plain ODBC connection string, so encode it for SQLAlchemy
    params = urllib.parse.quote_plus(DATABASE_URL)
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}", echo=True, future=True)
else:
    # It's already in SQLAlchemy format
    engine = create_engine(DATABASE_URL, echo=True, future=True)

# SessionLocal is a factory for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
