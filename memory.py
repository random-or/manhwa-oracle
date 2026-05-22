import logging
from typing import Dict, List, Any
from thefuzz import fuzz
from config import config
import json
import os
from database import init_db, SessionLocal, Series, Watchlist, ChapterHistory, SiteStatus, HealingHistory

logger = logging.getLogger("Oracle")

def load_json(file_path: str, default: Any) -> Any:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return default

class MemoryManager:
    def __init__(self):
        init_db()
        self.session = SessionLocal()
        # Fallback state/queue mapping
        self.state = load_json(config.STATE_FILE, {"fail_count": 0, "last_summary_date": ""})
        self.queue = load_json(config.QUEUE_FILE, [])
        self._notify_all = load_json(config.WATCHLIST_FILE, {}).get("notify_all", False)

    def save_all(self):
        with open(config.STATE_FILE, "w", encoding='utf-8') as f:
            json.dump(self.state, f, indent=4)
        with open(config.QUEUE_FILE, "w", encoding='utf-8') as f:
            json.dump(self.queue, f, indent=4)
        # SQLite is auto-saved on commit, so we don't need to dump memory/watchlist

    @property
    def watchlist(self):
        """Mock the watchlist property to return the format expected by oracle.py action_status"""
        watching_items = self.session.query(Watchlist).all()
        return {
            "notify_all": self._notify_all,
            "watching": [{"site": w.site, "title": w.title} for w in watching_items]
        }

    def get_last_seen_chapter(self, site: str, title: str) -> float:
        series = self.session.query(Series).filter_by(site=site, title=title).first()
        return series.last_chapter if series else 0.0

    def update_last_seen_chapter(self, site: str, title: str, chapter: float):
        series = self.session.query(Series).filter_by(site=site, title=title).first()
        if not series:
            series = Series(site=site, title=title, last_chapter=chapter)
            self.session.add(series)
        else:
            series.last_chapter = chapter
        
        # Add to chapter history
        history = ChapterHistory(series_title=title, site=site, chapter=chapter)
        self.session.add(history)
        self.session.commit()

    def is_watched(self, site: str, title: str) -> bool:
        if self._notify_all:
            return True
            
        watchlist_items = self.session.query(Watchlist).all()
        for item in watchlist_items:
            watched_site = item.site
            watched_title = item.title
            
            if watched_site == "any" or watched_site == site:
                if watched_title.lower() == title.lower():
                    return True
                elif fuzz.ratio(watched_title.lower(), title.lower()) > 85:
                    return True
        return False
        
    def add_to_watchlist(self, site: str, title: str) -> bool:
        existing = self.session.query(Watchlist).filter_by(site=site, title=title).first()
        if existing:
            return False
        item = Watchlist(site=site, title=title)
        self.session.add(item)
        self.session.commit()
        return True

    def remove_from_watchlist(self, title: str) -> bool:
        items = self.session.query(Watchlist).filter_by(title=title).all()
        if not items:
            return False
        for item in items:
            self.session.delete(item)
        self.session.commit()
        return True

    def migrate_from_json(self):
        """Migrates data from memory.json and watchlist.json to SQLite."""
        memory_data = load_json(config.MEMORY_FILE, {})
        watchlist_data = load_json(config.WATCHLIST_FILE, {})
        
        # Migrate memory
        for site, titles in memory_data.items():
            for title, chapter in titles.items():
                if not self.session.query(Series).filter_by(site=site, title=title).first():
                    series = Series(site=site, title=title, last_chapter=chapter)
                    self.session.add(series)
                    history = ChapterHistory(series_title=title, site=site, chapter=chapter)
                    self.session.add(history)

        # Migrate watchlist
        watching = watchlist_data.get("watching", [])
        for item in watching:
            if isinstance(item, str):
                site = "any"
                title = item
            else:
                site = item.get("site", "any")
                title = item.get("title", "")
                
            if not self.session.query(Watchlist).filter_by(site=site, title=title).first():
                w = Watchlist(site=site, title=title)
                self.session.add(w)
                
        self.session.commit()
        logger.info("✅ SQLite migration complete!")
