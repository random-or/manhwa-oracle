import logging
from typing import Dict, List, Any

import telebot
from telebot import types

from config import config
from memory import MemoryManager
from scrapers import SCRAPERS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("TelegramBot")

# callback_data is limited by Telegram, so store selected rows in-process by chat.
LATEST_CHOICES: Dict[int, List[Dict[str, Any]]] = {}


def _require_config() -> None:
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing from .env")


def _allowed_chat(message) -> bool:
    if not config.CHAT_ID:
        return True
    return str(message.chat.id) == str(config.CHAT_ID)


def _chapter_label(chapter: object) -> str:
    if isinstance(chapter, float) and chapter.is_integer():
        return str(int(chapter))
    return str(chapter)


def _help_text() -> str:
    return (
        "🔮 Manhwa Oracle\n\n"
        "Commands:\n"
        "/latest - show recent chapters with Track buttons\n"
        "/watch <title> | <site> - add a title, site can be any\n"
        "/unwatch <title> - remove a title\n"
        "/watchlist - show what you track\n"
        "/sites - show active scraper sites\n\n"
        "Example:\n"
        "/watch Solo Leveling | any"
    )


def create_bot() -> telebot.TeleBot:
    _require_config()
    bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode="HTML")

    @bot.message_handler(commands=["start", "help"])
    def handle_start(message):
        if not _allowed_chat(message):
            return
        bot.reply_to(message, _help_text())

    @bot.message_handler(commands=["sites"])
    def handle_sites(message):
        if not _allowed_chat(message):
            return
        names = "\n".join(f"- {scraper.site_name}" for scraper in SCRAPERS)
        bot.reply_to(message, f"🌐 Active sites:\n{names}")

    @bot.message_handler(commands=["watchlist"])
    def handle_watchlist(message):
        if not _allowed_chat(message):
            return
        memory = MemoryManager()
        try:
            items = memory.watchlist.get("watching", [])
            if not items:
                bot.reply_to(message, "Your watchlist is empty. Use /latest and tap Track, or /watch Title | any.")
                return
            lines = ["📚 Watchlist:"]
            for item in items:
                lines.append(f"- {item['title']} ({item['site']})")
            bot.reply_to(message, "\n".join(lines))
        finally:
            memory.session.close()

    @bot.message_handler(commands=["watch"])
    def handle_watch(message):
        if not _allowed_chat(message):
            return
        text = message.text.partition(" ")[2].strip()
        if not text:
            bot.reply_to(message, "Usage: /watch <title> | <site>\nExample: /watch Solo Leveling | any")
            return
        if "|" in text:
            title, site = [part.strip() for part in text.split("|", 1)]
        else:
            title, site = text, "any"
        if not title:
            bot.reply_to(message, "Title cannot be empty.")
            return
        memory = MemoryManager()
        try:
            added = memory.add_to_watchlist(site or "any", title)
            if added:
                bot.reply_to(message, f"✅ Tracking <b>{title}</b> on <b>{site or 'any'}</b>.")
            else:
                bot.reply_to(message, f"⚠️ Already tracking <b>{title}</b> on <b>{site or 'any'}</b>.")
        finally:
            memory.session.close()

    @bot.message_handler(commands=["unwatch"])
    def handle_unwatch(message):
        if not _allowed_chat(message):
            return
        title = message.text.partition(" ")[2].strip()
        if not title:
            bot.reply_to(message, "Usage: /unwatch <title>")
            return
        memory = MemoryManager()
        try:
            removed = memory.remove_from_watchlist(title)
            if removed:
                bot.reply_to(message, f"🗑️ Removed <b>{title}</b> from watchlist.")
            else:
                bot.reply_to(message, f"⚠️ <b>{title}</b> is not in your watchlist.")
        finally:
            memory.session.close()

    @bot.message_handler(commands=["latest", "choose"])
    def handle_latest(message):
        if not _allowed_chat(message):
            return
        bot.reply_to(message, "Scanning latest chapters now. This can take a bit...")
        choices: List[Dict[str, Any]] = []
        for scraper in SCRAPERS:
            try:
                for item in scraper.get_latest_chapters()[:5]:
                    if item.get("title") and item.get("url"):
                        choices.append(item)
                    if len(choices) >= 20:
                        break
            except Exception as exc:
                logger.warning("Failed latest scan for %s: %s", scraper.site_name, exc)
            if len(choices) >= 20:
                break

        if not choices:
            bot.send_message(message.chat.id, "No latest chapters found right now.")
            return

        LATEST_CHOICES[message.chat.id] = choices
        for index, item in enumerate(choices):
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("➕ Track this", callback_data=f"watch:{index}"))
            keyboard.add(types.InlineKeyboardButton("🔗 Open chapter", url=item["url"]))
            text = (
                f"📖 <b>{item['title']}</b>\n"
                f"🌐 {item['site']}\n"
                f"🔥 Ch.{_chapter_label(item['chapter'])}"
            )
            bot.send_message(message.chat.id, text, reply_markup=keyboard, disable_web_page_preview=True)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("watch:"))
    def handle_watch_callback(call):
        chat_id = call.message.chat.id
        if config.CHAT_ID and str(chat_id) != str(config.CHAT_ID):
            bot.answer_callback_query(call.id, "Not authorized")
            return
        try:
            index = int(call.data.split(":", 1)[1])
            item = LATEST_CHOICES.get(chat_id, [])[index]
        except Exception:
            bot.answer_callback_query(call.id, "That choice expired. Run /latest again.")
            return

        memory = MemoryManager()
        try:
            added = memory.add_to_watchlist(item["site"], item["title"])
        finally:
            memory.session.close()

        if added:
            bot.answer_callback_query(call.id, "Added to watchlist")
            bot.send_message(chat_id, f"✅ Tracking <b>{item['title']}</b> on <b>{item['site']}</b>.")
        else:
            bot.answer_callback_query(call.id, "Already tracked")
            bot.send_message(chat_id, f"⚠️ Already tracking <b>{item['title']}</b> on <b>{item['site']}</b>.")

    return bot


def main() -> None:
    bot = create_bot()
    logger.info("Telegram bot is running. Use Ctrl+C to stop.")
    bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)


if __name__ == "__main__":
    main()
