import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration settings."""
    
    # Telegram settings
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    CHAT_ID: str = os.getenv("CHAT_ID", "")
    
    # File paths
    MEMORY_FILE: str = "memory.json"
    WATCHLIST_FILE: str = "watchlist.json"
    STATE_FILE: str = "state.json"
    QUEUE_FILE: str = "queue.json"
    
    # Application limits
    MAX_RETRIES: int = 3
    RETRY_DELAY_SEC: int = 5
    
    # Dead man switch limit
    MAX_FAILURES_BEFORE_ALERT: int = 3
    
    # Times for Telegram digests (24h hours). Default matches the Termux cron
    # schedule: 06:00 and 18:00.
    DIGEST_HOURS: set[int] = {
        int(hour.strip())
        for hour in os.getenv("DIGEST_HOURS", "6,18").split(",")
        if hour.strip()
    }

    # Optional comma-separated scraper module names to skip at runtime.
    # Broken/dead scrapers were removed from the codebase; keep this for quick
    # temporary disabling if a working site starts blocking requests later.
    DISABLED_SCRAPERS: set[str] = {
        name.strip().lower()
        for name in os.getenv("DISABLED_SCRAPERS", "").split(",")
        if name.strip()
    }

config = Config()
