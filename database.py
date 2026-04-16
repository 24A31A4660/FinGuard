"""
Database Models & Engine — Financial Intelligence Platform
==========================================================
Persistent SQLAlchemy models for user accounts, transactions,
spending analytics, budgets, savings goals, and security audit.
"""

import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config import settings

Base = declarative_base()

# ─── Existing Models (preserved) ────────────────────────────────────────────

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(String, primary_key=True)
    avg_login_time = Column(Float, default=12.0)
    avg_transaction_amount = Column(Float, default=5000.0)
    usual_device = Column(String, default="unknown")
    usual_location = Column(String, default="unknown")
    last_transaction_time = Column(DateTime, nullable=True)
    trusted_devices = Column(Text, default="[]")
    transaction_timestamps = Column(Text, default="[]")
    daily_total = Column(Float, default=0.0)
    daily_limit = Column(Float, default=10000.0)
    transaction_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "avg_login_time": self.avg_login_time,
            "avg_transaction_amount": self.avg_transaction_amount,
            "usual_device": self.usual_device,
            "usual_location": self.usual_location,
            "last_transaction_time": self.last_transaction_time.timestamp() if self.last_transaction_time else 0,
            "trusted_devices": json.loads(self.trusted_devices) if self.trusted_devices else [],
            "daily_total": self.daily_total,
            "daily_limit": self.daily_limit,
            "transaction_count": self.transaction_count,
            "transaction_timestamps": json.loads(self.transaction_timestamps) if self.transaction_timestamps else [],
        }


class OTPStore(Base):
    __tablename__ = "otp_store"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    otp_code = Column(String)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class TransactionAudit(Base):
    __tablename__ = "transaction_audit"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    amount = Column(Float)
    risk_score = Column(Float)
    prediction = Column(String)
    action = Column(String)
    reason = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


# ─── User & Transaction Models ────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    monthly_income = Column(Float, default=0.0)
    google_id = Column(String, unique=True, index=True, nullable=True)
    profile_image = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True)
    date = Column(String, nullable=False) # YYYY-MM-DD
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Database Setup ─────────────────────────────────────────────────────────

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
