import logging
import time
from html import escape
import requests
from typing import List, Dict, Any
from config import config

logger = logging.getLogger("Notifier")

TELEGRAM_MAX_MESSAGE_CHARS = 4096
DIGEST_CHUNK_CHARS = 3500

class TelegramNotifier:
    def __init__(self):
        self.bot_token = config.BOT_TOKEN
        self.chat_id = config.CHAT_ID

    def send_message(self, message: str) -> bool:
        """Sends a notification to Telegram."""
        if not self.bot_token or not self.chat_id:
            logger.error("BOT_TOKEN or CHAT_ID missing from environment!")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 429:
                retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                logger.warning("Telegram rate limited; retrying after %s seconds", retry_after)
                time.sleep(min(int(retry_after), 60))
                response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Telegram Send Failed: {e}")
            return False

    def notify_update(self, item: Dict[str, Any]) -> None:
        """Sends an immediate alert for a single chapter update."""
        msg = "🔥 NEW CHAPTER ALERT\n\n"
        msg += f"📖 {escape(str(item['title']))} — Ch.{escape(str(item['chapter']))}\n"
        msg += f"🌐 {escape(str(item['site']))}\n"
        msg += f"🔗 Read Now: {escape(str(item['url']))}"
        return self.send_message(msg)

    def _digest_messages(self, queue: List[Dict[str, Any]]) -> List[str]:
        """Build Telegram-safe digest chunks under the 4096 character limit."""
        header = "📅 <b>DAILY MANHWA DIGEST</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        messages: List[str] = []
        current = header

        grouped = {}
        for item in queue:
            site = str(item.get("site", "Unknown"))
            grouped.setdefault(site, []).append(item)

        for site, items in grouped.items():
            site_line = f"\n🌐 <b>{escape(site)}</b>\n"
            if len(current) + len(site_line) > DIGEST_CHUNK_CHARS and current != header:
                messages.append(current.rstrip())
                current = header
            current += site_line

            for item in items:
                icon = "🌟" if item.get("is_new") else "🔥"
                title = escape(str(item.get("title", "Unknown")))
                chapter = escape(str(item.get("chapter", "?")))
                url = escape(str(item.get("url", "")), quote=True)
                line = f"{icon} <b>{title}</b> - Ch.{chapter}\n"
                if url:
                    line += f"🔗 <a href=\"{url}\">Read Here</a>\n"

                if len(line) > TELEGRAM_MAX_MESSAGE_CHARS:
                    line = line[: DIGEST_CHUNK_CHARS - 20] + "…\n"

                if len(current) + len(line) > DIGEST_CHUNK_CHARS and current != header:
                    messages.append(current.rstrip())
                    current = header + site_line
                current += line

        if current != header:
            messages.append(current.rstrip())
        return messages

    def send_daily_digest(self, queue: List[Dict[str, Any]]) -> bool:
        """Sends a grouped daily digest."""
        if not queue:
            return True

        messages = self._digest_messages(queue)
        logger.info("Sending digest as %s Telegram message(s).", len(messages))
        for index, msg in enumerate(messages, start=1):
            if index > 1:
                time.sleep(2) # Prevent hitting rapid-fire limits
            suffix = f"\n\nPart {index}/{len(messages)}" if len(messages) > 1 else ""
            if not self.send_message(msg + suffix):
                logger.warning("Digest send failed at part %s/%s; queue retained.", index, len(messages))
                return False
        return True
