import logging
import requests
from typing import List, Dict, Any
from config import config

logger = logging.getLogger("Notifier")

class TelegramNotifier:
    def __init__(self):
        self.bot_token = config.BOT_TOKEN
        self.chat_id = config.CHAT_ID

    def send_message(self, message: str) -> None:
        """Sends a notification to Telegram."""
        if not self.bot_token or not self.chat_id:
            logger.error("BOT_TOKEN or CHAT_ID missing from environment!")
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logger.warning(f"Telegram Send Failed: {e}")

    def notify_update(self, item: Dict[str, Any]) -> None:
        """Sends an immediate alert for a single chapter update."""
        msg = "🔥 NEW CHAPTER ALERT\n\n"
        msg += f"📖 {item['title']} — Ch.{item['chapter']}\n"
        msg += f"🌐 {item['site']}\n"
        msg += f"🔗 Read Now: {item['url']}"
        self.send_message(msg)

    def send_daily_digest(self, queue: List[Dict[str, Any]]) -> None:
        """Sends a grouped daily digest."""
        if not queue:
            return
            
        msg = "📅 <b>DAILY MANHWA DIGEST</b>\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        
        # Group by site
        grouped = {}
        for item in queue:
            site = item.get("site", "Unknown")
            if site not in grouped:
                grouped[site] = []
            grouped[site].append(item)
            
        for site, items in grouped.items():
            msg += f"\n🌐 <b>{site}</b>\n"
            for item in items:
                icon = "🌟" if item.get("is_new") else "🔥"
                msg += f"{icon} <b>{item['title']}</b> - Ch.{item['chapter']}\n"
                msg += f"🔗 <a href='{item['url']}'>Read Here</a>\n"
                
        self.send_message(msg)
