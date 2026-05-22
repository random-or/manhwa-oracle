import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

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

engine = create_engine('sqlite:///oracle.db')
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
