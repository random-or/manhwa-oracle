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
    
    # Time for daily digest (Hour in 24h format, e.g., 21 = 9 PM)
    DIGEST_HOUR: int = 21

config = Config()
