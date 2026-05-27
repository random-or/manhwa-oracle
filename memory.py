import logging
from typing import Dict, List, Any, Optional, Union
from thefuzz import fuzz
from config import config
import json
import os
from sqlalchemy import func
from database import init_db, SessionLocal, Series, Watchlist, Wishlist, ChapterHistory, SiteStatus, HealingHistory, SystemConfig, DigestQueue, CallbackSession

logger = logging.getLogger("Oracle")

def load_json(file_path: str, default: Any) -> Any:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return default

class DatabaseStateDict:
    def __init__(self, session):
        self.session = session

    def __getitem__(self, key):
        config_val = self.session.query(SystemConfig).filter_by(key=key).first()
        if not config_val:
            if key == "fail_count":
                return 0
            return ""
        if key == "fail_count":
            try:
                return int(config_val.value)
            except ValueError:
                return 0
        return config_val.value

    def __setitem__(self, key, value):
        config_val = self.session.query(SystemConfig).filter_by(key=key).first()
        if not config_val:
            config_val = SystemConfig(key=key, value=str(value))
            self.session.add(config_val)
        else:
            config_val.value = str(value)
        self.session.commit()

    def get(self, key, default=None):
        config_val = self.session.query(SystemConfig).filter_by(key=key).first()
        if not config_val:
            return default
        if key == "fail_count":
            try:
                return int(config_val.value)
            except ValueError:
                return 0
        return config_val.value


class DatabaseQueueList:
    def __init__(self, session):
        self.session = session

    def append(self, item):
        db_item = DigestQueue(
            title=item.get("title", "Unknown"),
            site=item.get("site", "Unknown"),
            chapter=float(item.get("chapter", 0.0)),
            url=item.get("url", ""),
            is_new=bool(item.get("is_new", False))
        )
        self.session.add(db_item)
        self.session.commit()

    def __len__(self):
        return self.session.query(DigestQueue).count()

    def __bool__(self):
        return len(self) > 0

    def __iter__(self):
        items = self.session.query(DigestQueue).order_by(DigestQueue.added_at.asc()).all()
        return iter([
            {
                "title": item.title,
                "site": item.site,
                "chapter": int(item.chapter) if item.chapter.is_integer() else item.chapter,
                "url": item.url,
                "is_new": item.is_new
            }
            for item in items
        ])

    def clear(self):
        self.session.query(DigestQueue).delete()
        self.session.commit()


class MemoryManager:
    def __init__(self):
        init_db()
        self.session = SessionLocal()
        self.state = DatabaseStateDict(self.session)

    @property
    def queue(self):
        return DatabaseQueueList(self.session)

    @queue.setter
    def queue(self, value):
        if isinstance(value, list) and not value:
            self.queue.clear()

    @property
    def _notify_all(self) -> bool:
        config_val = self.session.query(SystemConfig).filter_by(key="notify_all").first()
        if not config_val:
            return False
        return config_val.value.lower() == "true"

    @_notify_all.setter
    def _notify_all(self, value: bool):
        config_val = self.session.query(SystemConfig).filter_by(key="notify_all").first()
        if not config_val:
            config_val = SystemConfig(key="notify_all", value=str(value).lower())
            self.session.add(config_val)
        else:
            config_val.value = str(value).lower()
        self.session.commit()

    def close(self):
        if hasattr(self, 'session') and self.session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def save_all(self):
        pass

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
        items = self.session.query(Watchlist).filter(func.lower(Watchlist.title) == title.lower()).all()
        if not items:
            return False
        for item in items:
            self.session.delete(item)
        self.session.commit()
        return True

    def add_to_wishlist(self, title: str, site: str = "any", note: str = "") -> bool:
        existing = self.session.query(Wishlist).filter_by(site=site, title=title).first()
        if existing:
            if note and existing.note != note:
                existing.note = note
                self.session.commit()
            return False
        item = Wishlist(site=site, title=title, note=note)
        self.session.add(item)
        self.session.commit()
        return True

    def remove_from_wishlist(self, title: str) -> bool:
        items = self.session.query(Wishlist).filter(func.lower(Wishlist.title) == title.lower()).all()
        if not items:
            return False
        for item in items:
            self.session.delete(item)
        self.session.commit()
        return True

    def list_wishlist(self) -> List[Dict[str, str]]:
        items = self.session.query(Wishlist).order_by(Wishlist.added_at.desc()).all()
        return [{"site": item.site, "title": item.title, "note": item.note or ""} for item in items]

    def promote_wishlist_to_watchlist(self, title: str, site: str = "any") -> bool:
        wishlist_items = self.session.query(Wishlist).filter(func.lower(Wishlist.title) == title.lower()).all()
        added = self.add_to_watchlist(site, title)
        for item in wishlist_items:
            self.session.delete(item)
        self.session.commit()
        return added

    def save_callback_choices(self, chat_id: int, session_type: str, choices: List[Dict[str, Any]]):
        from datetime import datetime, timedelta
        # Prune existing entries for this chat_id + session_type
        self.session.query(CallbackSession).filter_by(chat_id=chat_id, session_type=session_type).delete()
        
        # Prune globally expired entries (older than 2 hours)
        expiry_limit = datetime.utcnow() - timedelta(hours=2)
        self.session.query(CallbackSession).filter(CallbackSession.created_at < expiry_limit).delete()
        
        # Save new choices
        for index, item in enumerate(choices):
            session_item = CallbackSession(
                chat_id=chat_id,
                session_type=session_type,
                choice_index=index,
                data_json=json.dumps(item)
            )
            self.session.add(session_item)
        self.session.commit()

    def get_callback_choice(self, chat_id: int, session_type: str, index: int) -> Optional[Dict[str, Any]]:
        from typing import Optional
        session_item = self.session.query(CallbackSession).filter_by(
            chat_id=chat_id,
            session_type=session_type,
            choice_index=index
        ).first()
        if session_item:
            return json.loads(session_item.data_json)
        return None

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
                
        # Migrate state
        state_data = load_json(config.STATE_FILE, {})
        for k, v in state_data.items():
            if not self.session.query(SystemConfig).filter_by(key=k).first():
                config_item = SystemConfig(key=k, value=str(v))
                self.session.add(config_item)
        
        # Migrate notify_all
        notify_all = watchlist_data.get("notify_all", False)
        if not self.session.query(SystemConfig).filter_by(key="notify_all").first():
            notify_item = SystemConfig(key="notify_all", value=str(notify_all).lower())
            self.session.add(notify_item)

        # Migrate queue
        queue_data = load_json(config.QUEUE_FILE, [])
        for item in queue_data:
            if not self.session.query(DigestQueue).filter_by(title=item.get("title"), site=item.get("site"), chapter=float(item.get("chapter", 0.0))).first():
                db_item = DigestQueue(
                    title=item.get("title", "Unknown"),
                    site=item.get("site", "Unknown"),
                    chapter=float(item.get("chapter", 0.0)),
                    url=item.get("url", ""),
                    is_new=bool(item.get("is_new", False))
                )
                self.session.add(db_item)
                
        self.session.commit()
        logger.info("✅ SQLite migration complete!")
