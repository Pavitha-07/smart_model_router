# app/database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smart_router.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class RequestLog(Base):
    """Logs every request to track costs and model usage"""
    __tablename__ = "request_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Request info
    prompt = Column(Text, nullable=False)
    prompt_tokens = Column(Integer)
    
    # Classification
    difficulty = Column(String(50), index=True)
    confidence = Column(Float)
    
    # Routing decision
    selected_model = Column(String(100), index=True)
    
    # Response info
    response = Column(Text)
    response_tokens = Column(Integer)
    latency_ms = Column(Float)
    
    # Cost tracking
    cost_usd = Column(Float)
    cost_saved_usd = Column(Float)
    
    # Metadata
    user_id = Column(String(100), index=True, nullable=True)
    status = Column(String(20))

class ModelStats(Base):
    """Aggregate statistics per model"""
    __tablename__ = "model_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), unique=True, index=True)
    total_requests = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    avg_latency_ms = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)

def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
if __name__ == "__main__":
    init_db()