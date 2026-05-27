from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from pathlib import Path

Base = declarative_base()

class Series(Base):
    __tablename__ = 'series'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    site = Column(String, nullable=False)
    last_chapter = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Watchlist(Base):
    __tablename__ = 'watchlist'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    site = Column(String, default="any")
    added_at = Column(DateTime, default=datetime.utcnow)

class Wishlist(Base):
    __tablename__ = 'wishlist'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    site = Column(String, default="any")
    note = Column(String, default="")
    added_at = Column(DateTime, default=datetime.utcnow)

class ChapterHistory(Base):
    __tablename__ = 'chapter_history'
    id = Column(Integer, primary_key=True)
    series_title = Column(String, nullable=False)
    site = Column(String, nullable=False)
    chapter = Column(Float, nullable=False)
    read_at = Column(DateTime, default=datetime.utcnow)

class SiteStatus(Base):
    __tablename__ = 'site_status'
    id = Column(Integer, primary_key=True)
    site_name = Column(String, unique=True, nullable=False)
    status = Column(String, default="ACTIVE")
    last_checked = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HealingHistory(Base):
    __tablename__ = 'healing_history'
    id = Column(Integer, primary_key=True)
    site_name = Column(String, nullable=False)
    old_url = Column(String, nullable=False)
    new_url = Column(String, nullable=False)
    healed_at = Column(DateTime, default=datetime.utcnow)

class SystemConfig(Base):
    __tablename__ = 'system_config'
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)

class DigestQueue(Base):
    __tablename__ = 'digest_queue'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    site = Column(String, nullable=False)
    chapter = Column(Float, nullable=False)
    url = Column(String, nullable=False)
    is_new = Column(Boolean, default=False)
    added_at = Column(DateTime, default=datetime.utcnow)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'oracle.db'

engine = create_engine(f'sqlite:///{DB_PATH}')
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))
