import logging
from typing import Dict, List, Any

import requests
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

# Choices are now persisted in SQLite (CallbackSession table) to handle restarts gracefully.


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


def _main_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add("🆕 Latest", "📚 Watchlist")
    keyboard.add("⭐ Wishlist", "🌐 Sites")
    keyboard.add("📊 Status", "❓ Help")
    return keyboard


def _help_text() -> str:
    return (
        "🔮 <b>Manhwa Oracle</b>\n\n"
        "Tap the menu buttons, or use commands:\n"
        "/latest - show recent chapters with Track/Wishlist buttons\n"
        "/search &lt;title&gt; - search MangaDex and others to track/wishlist\n"
        "/watch &lt;title&gt; | &lt;site&gt; - track a title, site can be any\n"
        "/trackall &lt;title&gt; - shortcut for /watch title | any\n"
        "/unwatch &lt;title&gt; - remove a tracked title\n"
        "/watchlist - show tracked titles with remove buttons\n"
        "/wish &lt;title&gt; | &lt;site&gt; | &lt;note&gt; - save for later\n"
        "/unwish &lt;title&gt; - remove from wishlist\n"
        "/wishlist - show saved-for-later titles\n"
        "/sites - show active scraper sites\n"
        "/status - bot, Telegram, and scraper status\n\n"
        "Examples:\n"
        "/watch Solo Leveling | any\n"
        "/wish Omniscient Reader | any | read later"
    )


def _parse_title_site_note(text: str) -> tuple[str, str, str]:
    parts = [part.strip() for part in text.split("|")]
    title = parts[0] if parts else ""
    site = parts[1] if len(parts) >= 2 and parts[1] else "any"
    note = parts[2] if len(parts) >= 3 else ""
    return title, site, note


def _telegram_api_status() -> tuple[bool, str]:
    if not config.BOT_TOKEN:
        return False, "BOT_TOKEN missing"
    try:
        response = requests.get(f"https://api.telegram.org/bot{config.BOT_TOKEN}/getMe", timeout=10)
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"
        data = response.json()
        if not data.get("ok"):
            return False, data.get("description", "Telegram returned ok=false")
        username = data.get("result", {}).get("username", "unknown")
        return True, f"@{username} reachable"
    except Exception as exc:
        return False, str(exc)


def create_bot() -> telebot.TeleBot:
    _require_config()
    bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode="HTML")

    @bot.message_handler(commands=["start", "help", "menu"])
    def handle_start(message):
        if not _allowed_chat(message):
            return
        bot.reply_to(message, _help_text(), reply_markup=_main_keyboard())

    @bot.message_handler(func=lambda message: message.text in {"❓ Help"})
    def handle_help_button(message):
        handle_start(message)

    @bot.message_handler(commands=["sites"])
    def handle_sites(message):
        if not _allowed_chat(message):
            return
        names = "\n".join(f"- {scraper.site_name}" for scraper in SCRAPERS)
        bot.reply_to(message, f"🌐 <b>Active sites</b>:\n{names or 'No active scrapers loaded.'}", reply_markup=_main_keyboard())

    @bot.message_handler(func=lambda message: message.text == "🌐 Sites")
    def handle_sites_button(message):
        handle_sites(message)

    @bot.message_handler(commands=["status"])
    def handle_status(message):
        if not _allowed_chat(message):
            return
        ok, telegram_status = _telegram_api_status()
        memory = MemoryManager()
        try:
            watch_count = len(memory.watchlist.get("watching", []))
            wish_count = len(memory.list_wishlist())
            queue_count = len(memory.queue)
            site_count = len(SCRAPERS)
            notify_all = memory._notify_all
            lines = [
                "📊 <b>Oracle Status</b>",
                f"Telegram: {'✅' if ok else '❌'} {telegram_status}",
                f"Authorized chat: {'set' if config.CHAT_ID else 'not restricted'}",
                f"Mode: <b>{'Notify All 📢' if notify_all else 'Watchlist Only 📚'}</b>",
                f"Active scrapers: {site_count}",
                f"Watchlist: {watch_count}",
                f"Wishlist: {wish_count}",
                f"Queued digest items: {queue_count}",
                f"Digest hours: {', '.join(str(h) for h in sorted(config.DIGEST_HOURS))}",
            ]
            keyboard = types.InlineKeyboardMarkup()
            toggle_text = "📢 Switch to Notify All" if not notify_all else "📚 Switch to Watchlist Only"
            keyboard.add(types.InlineKeyboardButton(toggle_text, callback_data="toggle_notify_all"))
            bot.reply_to(message, "\n".join(lines), reply_markup=keyboard)
        finally:
            memory.session.close()

    @bot.message_handler(func=lambda message: message.text == "📊 Status")
    def handle_status_button(message):
        handle_status(message)

    @bot.message_handler(commands=["watchlist"])
    def handle_watchlist(message):
        if not _allowed_chat(message):
            return
        memory = MemoryManager()
        try:
            items = memory.watchlist.get("watching", [])
            memory.save_callback_choices(message.chat.id, "watchlist", items)
            if not items:
                bot.reply_to(message, "Your watchlist is empty. Use /latest and tap Track, or /watch Title | any.", reply_markup=_main_keyboard())
                return
            bot.reply_to(message, f"📚 <b>Watchlist</b> ({len(items)}):", reply_markup=_main_keyboard())
            for index, item in enumerate(items):
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton("🗑 Remove", callback_data=f"unwatch:{index}"))
                bot.send_message(message.chat.id, f"- <b>{item['title']}</b> ({item['site']})", reply_markup=keyboard)
        finally:
            memory.session.close()

    @bot.message_handler(func=lambda message: message.text == "📚 Watchlist")
    def handle_watchlist_button(message):
        handle_watchlist(message)

    @bot.message_handler(commands=["wishlist"])
    def handle_wishlist(message):
        if not _allowed_chat(message):
            return
        memory = MemoryManager()
        try:
            items = memory.list_wishlist()
            memory.save_callback_choices(message.chat.id, "wishlist", items)
            if not items:
                bot.reply_to(message, "Your wishlist is empty. Use /latest and tap Wishlist, or /wish Title | any.", reply_markup=_main_keyboard())
                return
            bot.reply_to(message, f"⭐ <b>Wishlist</b> ({len(items)}):", reply_markup=_main_keyboard())
            for index, item in enumerate(items):
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton("✅ Track now", callback_data=f"promote:{index}"))
                keyboard.add(types.InlineKeyboardButton("🗑 Remove", callback_data=f"unwish:{index}"))
                note = f" — {item['note']}" if item.get("note") else ""
                bot.send_message(message.chat.id, f"- <b>{item['title']}</b> ({item['site']}){note}", reply_markup=keyboard)
        finally:
            memory.session.close()

    @bot.message_handler(func=lambda message: message.text == "⭐ Wishlist")
    def handle_wishlist_button(message):
        handle_wishlist(message)

    @bot.message_handler(commands=["watch", "trackall"])
    def handle_watch(message):
        if not _allowed_chat(message):
            return
        text = message.text.partition(" ")[2].strip()
        if not text:
            bot.reply_to(message, "Usage: /watch <title> | <site>\nExample: /watch Solo Leveling | any")
            return
        title, site, _note = _parse_title_site_note(text)
        if message.text.startswith("/trackall"):
            site = "any"
        if not title:
            bot.reply_to(message, "Title cannot be empty.")
            return
        memory = MemoryManager()
        try:
            added = memory.add_to_watchlist(site or "any", title)
            if added:
                bot.reply_to(message, f"✅ Tracking <b>{title}</b> on <b>{site or 'any'}</b>.", reply_markup=_main_keyboard())
            else:
                bot.reply_to(message, f"⚠️ Already tracking <b>{title}</b> on <b>{site or 'any'}</b>.", reply_markup=_main_keyboard())
        finally:
            memory.session.close()

    @bot.message_handler(commands=["wish"])
    def handle_wish(message):
        if not _allowed_chat(message):
            return
        text = message.text.partition(" ")[2].strip()
        if not text:
            bot.reply_to(message, "Usage: /wish <title> | <site> | <note>\nExample: /wish Solo Leveling | any | read later")
            return
        title, site, note = _parse_title_site_note(text)
        if not title:
            bot.reply_to(message, "Title cannot be empty.")
            return
        memory = MemoryManager()
        try:
            added = memory.add_to_wishlist(title, site or "any", note)
            if added:
                bot.reply_to(message, f"⭐ Saved <b>{title}</b> to wishlist.", reply_markup=_main_keyboard())
            else:
                bot.reply_to(message, f"⚠️ <b>{title}</b> is already in wishlist.", reply_markup=_main_keyboard())
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
                bot.reply_to(message, f"🗑️ Removed <b>{title}</b> from watchlist.", reply_markup=_main_keyboard())
            else:
                bot.reply_to(message, f"⚠️ <b>{title}</b> is not in your watchlist.", reply_markup=_main_keyboard())
        finally:
            memory.session.close()

    @bot.message_handler(commands=["unwish"])
    def handle_unwish(message):
        if not _allowed_chat(message):
            return
        title = message.text.partition(" ")[2].strip()
        if not title:
            bot.reply_to(message, "Usage: /unwish <title>")
            return
        memory = MemoryManager()
        try:
            removed = memory.remove_from_wishlist(title)
            if removed:
                bot.reply_to(message, f"🗑️ Removed <b>{title}</b> from wishlist.", reply_markup=_main_keyboard())
            else:
                bot.reply_to(message, f"⚠️ <b>{title}</b> is not in your wishlist.", reply_markup=_main_keyboard())
        finally:
            memory.session.close()

    @bot.message_handler(commands=["search"])
    def handle_search(message):
        if not _allowed_chat(message):
            return
        query = message.text.partition(" ")[2].strip()
        if not query:
            bot.reply_to(message, "Usage: /search <title>\nExample: /search Solo Leveling")
            return
            
        bot.reply_to(message, f"🔍 Searching for '{query}'...", reply_markup=_main_keyboard())
        results = []
        for scraper in SCRAPERS:
            try:
                res = scraper.search(query)
                if res:
                    results.extend(res)
            except Exception as e:
                logger.warning(f"Search failed for {scraper.site_name}: {e}")
                
        if not results:
            bot.send_message(message.chat.id, "No matching titles found across any sites.", reply_markup=_main_keyboard())
            return
            
        # Limit to top 10 results
        results = results[:10]
        
        # Save to database session
        memory = MemoryManager()
        try:
            memory.save_callback_choices(message.chat.id, "search", results)
            
            for index, item in enumerate(results):
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton("➕ Track site", callback_data=f"watch_search:{index}"))
                keyboard.add(types.InlineKeyboardButton("🌍 Track any site", callback_data=f"watchany_search:{index}"))
                keyboard.add(types.InlineKeyboardButton("⭐ Wishlist", callback_data=f"wish_search:{index}"))
                if item.get("url"):
                    keyboard.add(types.InlineKeyboardButton("🔗 Open details", url=item["url"]))
                    
                text = (
                    f"📖 <b>{item['title']}</b>\n"
                    f"🌐 Site: {item['site']}"
                )
                bot.send_message(message.chat.id, text, reply_markup=keyboard, disable_web_page_preview=True)
        finally:
            memory.session.close()

    @bot.message_handler(commands=["latest", "choose"])
    def handle_latest(message):
        if not _allowed_chat(message):
            return
        bot.reply_to(message, "Scanning latest chapters now. This can take a bit...", reply_markup=_main_keyboard())
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
            bot.send_message(message.chat.id, "No latest chapters found right now.", reply_markup=_main_keyboard())
            return

        memory = MemoryManager()
        try:
            memory.save_callback_choices(message.chat.id, "latest", choices)
        finally:
            memory.session.close()
            
        for index, item in enumerate(choices):
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("➕ Track site", callback_data=f"watch:{index}"))
            keyboard.add(types.InlineKeyboardButton("🌍 Track any site", callback_data=f"watchany:{index}"))
            keyboard.add(types.InlineKeyboardButton("⭐ Wishlist", callback_data=f"wish:{index}"))
            keyboard.add(types.InlineKeyboardButton("🔗 Open chapter", url=item["url"]))
            text = (
                f"📖 <b>{item['title']}</b>\n"
                f"🌐 {item['site']}\n"
                f"🔥 Ch.{_chapter_label(item['chapter'])}"
            )
            bot.send_message(message.chat.id, text, reply_markup=keyboard, disable_web_page_preview=True)

    @bot.message_handler(func=lambda message: message.text == "🆕 Latest")
    def handle_latest_button(message):
        handle_latest(message)

    @bot.callback_query_handler(func=lambda call: call.data.startswith(("watch:", "watchany:", "wish:", "unwatch:", "unwish:", "promote:", "toggle_notify_all", "watch_search:", "watchany_search:", "wish_search:")))
    def handle_callback(call):
        chat_id = call.message.chat.id
        if config.CHAT_ID and str(chat_id) != str(config.CHAT_ID):
            bot.answer_callback_query(call.id, "Not authorized")
            return

        if call.data == "toggle_notify_all":
            memory = MemoryManager()
            try:
                current = memory._notify_all
                new_val = not current
                memory._notify_all = new_val
                
                # Edit status message to reflect new status
                ok, telegram_status = _telegram_api_status()
                watch_count = len(memory.watchlist.get("watching", []))
                wish_count = len(memory.list_wishlist())
                queue_count = len(memory.queue)
                site_count = len(SCRAPERS)
                
                lines = [
                    "📊 <b>Oracle Status</b>",
                    f"Telegram: {'✅' if ok else '❌'} {telegram_status}",
                    f"Authorized chat: {'set' if config.CHAT_ID else 'not restricted'}",
                    f"Mode: <b>{'Notify All 📢' if new_val else 'Watchlist Only 📚'}</b>",
                    f"Active scrapers: {site_count}",
                    f"Watchlist: {watch_count}",
                    f"Wishlist: {wish_count}",
                    f"Queued digest items: {queue_count}",
                    f"Digest hours: {', '.join(str(h) for h in sorted(config.DIGEST_HOURS))}",
                ]
                
                keyboard = types.InlineKeyboardMarkup()
                toggle_text = "📢 Switch to Notify All" if not new_val else "📚 Switch to Watchlist Only"
                keyboard.add(types.InlineKeyboardButton(toggle_text, callback_data="toggle_notify_all"))
                
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    text="\n".join(lines),
                    reply_markup=keyboard
                )
                bot.answer_callback_query(call.id, f"Mode set to {'Notify All' if new_val else 'Watchlist Only'}")
            finally:
                memory.session.close()
            return

        action, raw_index = call.data.split(":", 1)
        try:
            index = int(raw_index)
        except ValueError:
            bot.answer_callback_query(call.id, "Invalid action")
            return

        memory = MemoryManager()
        try:
            if action in {"watch_search", "watchany_search", "wish_search"}:
                item = memory.get_callback_choice(chat_id, "search", index)
                if not item:
                    bot.answer_callback_query(call.id, "That search choice expired. Run the command again.")
                    return
                if action == "wish_search":
                    added = memory.add_to_wishlist(item["title"], item["site"], "from /search")
                    bot.answer_callback_query(call.id, "Saved to wishlist" if added else "Already in wishlist")
                    bot.send_message(chat_id, f"⭐ Wishlist: <b>{item['title']}</b>.")
                else:
                    site = "any" if action == "watchany_search" else item["site"]
                    added = memory.add_to_watchlist(site, item["title"])
                    bot.answer_callback_query(call.id, "Added to watchlist" if added else "Already tracked")
                    bot.send_message(chat_id, f"✅ Tracking <b>{item['title']}</b> on <b>{site}</b>.")
                return

            if action in {"watch", "watchany", "wish"}:
                item = memory.get_callback_choice(chat_id, "latest", index)
                if not item:
                    bot.answer_callback_query(call.id, "That choice expired. Run the command again.")
                    return
                if action == "wish":
                    added = memory.add_to_wishlist(item["title"], item["site"], "from /latest")
                    bot.answer_callback_query(call.id, "Saved to wishlist" if added else "Already in wishlist")
                    bot.send_message(chat_id, f"⭐ Wishlist: <b>{item['title']}</b>.")
                else:
                    site = "any" if action == "watchany" else item["site"]
                    added = memory.add_to_watchlist(site, item["title"])
                    bot.answer_callback_query(call.id, "Added to watchlist" if added else "Already tracked")
                    bot.send_message(chat_id, f"✅ Tracking <b>{item['title']}</b> on <b>{site}</b>.")
                return

            if action == "unwatch":
                item = memory.get_callback_choice(chat_id, "watchlist", index)
                if not item:
                    bot.answer_callback_query(call.id, "That choice expired. Run the command again.")
                    return
                removed = memory.remove_from_watchlist(item["title"])
                bot.answer_callback_query(call.id, "Removed" if removed else "Not found")
                bot.send_message(chat_id, f"🗑 Removed <b>{item['title']}</b> from watchlist.")
                return

            if action == "unwish":
                item = memory.get_callback_choice(chat_id, "wishlist", index)
                if not item:
                    bot.answer_callback_query(call.id, "That choice expired. Run the command again.")
                    return
                removed = memory.remove_from_wishlist(item["title"])
                bot.answer_callback_query(call.id, "Removed" if removed else "Not found")
                bot.send_message(chat_id, f"🗑 Removed <b>{item['title']}</b> from wishlist.")
                return

            if action == "promote":
                item = memory.get_callback_choice(chat_id, "wishlist", index)
                if not item:
                    bot.answer_callback_query(call.id, "That choice expired. Run the command again.")
                    return
                added = memory.promote_wishlist_to_watchlist(item["title"], item.get("site") or "any")
                bot.answer_callback_query(call.id, "Moved to watchlist" if added else "Already tracked; removed from wishlist")
                bot.send_message(chat_id, f"✅ Now tracking <b>{item['title']}</b>.")
                return
        except Exception:
            bot.answer_callback_query(call.id, "That choice expired. Run the command again.")
        finally:
            memory.session.close()

    return bot


def main() -> None:
    bot = create_bot()
    logger.info("Telegram bot is running. Use Ctrl+C to stop.")
    bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)


if __name__ == "__main__":
    main()
