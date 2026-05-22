import requests
import re
import json
import os
import time
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- 1. LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cron_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Oracle")

# --- 2. SETUP & SECRETS ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Configuration
TARGET_URL = "https://asurascans.com/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
MEMORY_FILE = "memory.json"
WATCHLIST_FILE = "watchlist.json"
STATE_FILE = "state.json"
QUEUE_FILE = "queue.json"

# --- 3. THE MESSENGER ---
def send_telegram(message):
    """Sends a notification to your phone via Telegram."""
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("BOT_TOKEN or CHAT_ID missing from .env!")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logger.warning(f"Telegram Send Failed: {e}")

# --- 4. STATE HELPERS ---
def load_json(file_path, default):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"File {file_path} corrupted.")
    return default

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# --- 5. THE ENGINE ---
def run_oracle():
    # Load Data
    history = load_json(MEMORY_FILE, {})
    watchlist = load_json(WATCHLIST_FILE, [])
    state = load_json(STATE_FILE, {"fail_count": 0, "last_summary_date": ""})
    queue = load_json(QUEUE_FILE, [])

    logger.info("--- ORACLE IS SCANNING THE HOMEPAGE ---")

    # --- RETRY LOGIC (Dead Man Switch) ---
    max_retries = 3
    retry_delay = 5
    response = None

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to reach the tower (Try {attempt + 1}/{max_retries})...")
            response = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                logger.info("Connection Successful!")
                state["fail_count"] = 0 # Reset on success
                break
        except Exception as e:
            logger.warning(f"Connection flicker: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

    # If connection failed after all retries in this run
    if not response or response.status_code != 200:
        state["fail_count"] += 1
        logger.error(f"Oracle failed to reach the server. Fail count: {state['fail_count']}")
        
        if state["fail_count"] >= 3:
            logger.error("DEAD MAN SWITCH TRIGGERED!")
            send_telegram("⚠️ <b>SYSTEM ALERT</b>\nThe Manhwa Oracle has failed to connect 3 times in a row. The bot might be down or Asura Scans is blocking us.")
        
        save_json(STATE_FILE, state)
        return

    # --- DATA EXTRACTION ---
    soup = BeautifulSoup(response.text, "html.parser")
    titles = soup.find_all('a', class_=re.compile(r'font-bold.*text-base'))
    logger.info(f"Detected {len(titles)} series on the homepage.")
    
    new_updates_count = 0
    
    for title_tag in titles:
        try:
            title = title_tag.get_text(strip=True)
            
            # Whitelist filter
            if os.path.exists(WATCHLIST_FILE) and title not in watchlist:
                continue
            
            chapters_div = title_tag.find_next_sibling('div')
            if not chapters_div: continue
                
            latest_ch_tag = chapters_div.find('a')
            if not latest_ch_tag: continue
                
            chapter_link = latest_ch_tag.get('href', TARGET_URL)
            ch_text = latest_ch_tag.get_text(separator=" ", strip=True)
            match = re.search(r'Chapter\s*(\d+)', ch_text)
            
            if match:
                current_ch = int(match.group(1))
                last_seen = int(history.get(title, 0))
                
                if current_ch > last_seen:
                    # Queue the update instead of sending immediately
                    update_entry = {
                        "title": title,
                        "chapter": current_ch,
                        "link": chapter_link,
                        "is_new": last_seen == 0
                    }
                    queue.append(update_entry)
                    
                    logger.info(f"QUEUED: {title} Ch.{current_ch}")
                    history[title] = current_ch
                    new_updates_count += 1
        except Exception as item_err:
            logger.debug(f"Skipping item: {item_err}")
            continue

    # --- DAILY SUMMARY LOGIC (9 PM) ---
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    # Check if it's 9 PM (hour 21) and we haven't sent a summary today
    if now.hour == 21 and state.get("last_summary_date") != today_str:
        if queue:
            msg = "📅 <b>DAILY MANHWA SUMMARY</b>\n"
            msg += "----------------------------\n"
            for item in queue:
                icon = "🌟" if item["is_new"] else "🔥"
                msg += f"{icon} <b>{item['title']}</b> - Ch. {item['chapter']}\n"
                msg += f"🔗 <a href='{item['link']}'>Read Now</a>\n\n"
            
            send_telegram(msg)
            logger.info(f"Summary sent with {len(queue)} updates.")
            queue = [] # Clear queue after sending
        else:
            logger.info("9 PM reached but queue is empty. No summary sent.")
        
        state["last_summary_date"] = today_str

    if new_updates_count == 0:
        logger.info("No new updates found this run.")
            
    # Save everything
    save_json(MEMORY_FILE, history)
    save_json(STATE_FILE, state)
    save_json(QUEUE_FILE, queue)

    logger.info("--- SCAN COMPLETE ---")

if __name__ == "__main__":
    run_oracle()
