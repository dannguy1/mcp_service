from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variable or use default
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://netmonitor_user:netmonitor_password@192.168.10.14:5432/netmonitor_db')

# Create engine
engine = create_engine(DATABASE_URL)

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

@contextmanager
def get_db_connection():
    """Get a database connection with automatic cleanup"""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def init_db():
    """Initialize the database"""
    # Import models here to ensure they are registered with SQLAlchemy
    from app.models import LogEntry, AnomalyRecord, AnomalyPattern
    
    # Create all tables
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()
    Base.metadata.create_all(engine) 