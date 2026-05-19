import requests
import re
import json
import os
import time
import logging
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

# --- 3. THE MESSENGER ---
def send_telegram(message):
    """Sends a notification to your phone via Telegram."""
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("BOT_TOKEN or CHAT_ID missing from .env!")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logger.warning(f"Telegram Send Failed: {e}")

# --- 4. THE ENGINE ---
def run_oracle():
    # Load Memory
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                history = json.load(f)
        except json.JSONDecodeError:
            logger.error("Memory file corrupted. Resetting.")
            history = {}
    else:
        history = {}

    logger.info("--- ORACLE IS SCANNING THE HOMEPAGE ---")

    # --- RETRY LOGIC ---
    max_retries = 3
    retry_delay = 5
    response = None

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to reach the tower (Try {attempt + 1}/{max_retries})...")
            response = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                logger.info("Connection Successful!")
                break
        except Exception as e:
            logger.warning(f"Connection flicker: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

    if not response or response.status_code != 200:
        logger.error(f"Oracle failed to reach the server. Status: {response.status_code if response else 'No Response'}")
        return

    # --- DATA EXTRACTION (Updated with Scout V3 logic) ---
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Scout V3 Logic: Find titles with specific Tailwind classes
    titles = soup.find_all('a', class_=re.compile(r'font-bold.*text-base'))
    logger.info(f"Detected {len(titles)} series on the homepage.")
    
    new_updates_count = 0
    
    for title_tag in titles:
        try:
            title = title_tag.get_text(strip=True)
            
            # Find the chapter div (next sibling)
            chapters_div = title_tag.find_next_sibling('div')
            if not chapters_div:
                continue
                
            latest_ch_tag = chapters_div.find('a')
            if not latest_ch_tag:
                continue
                
            ch_text = latest_ch_tag.get_text(separator=" ", strip=True)
            match = re.search(r'Chapter\s*(\d+)', ch_text)
            
            if match:
                current_ch = int(match.group(1))
                last_seen = int(history.get(title, 0))
                
                if current_ch > last_seen:
                    if last_seen == 0:
                        msg = f"🌟 NEW SERIES TRACKED!\n{title}\nStarting at Chapter {current_ch}"
                    else:
                        msg = f"🔥 NEW CHAPTER!\n{title}\nNow at Chapter {current_ch}"
                    
                    logger.info(f"PING: {title} Ch.{current_ch}")
                    send_telegram(msg)
                    history[title] = current_ch
                    new_updates_count += 1
        except Exception as item_err:
            logger.debug(f"Skipping item due to error: {item_err}")
            continue

    if new_updates_count == 0:
        logger.info("Everything is up to date.")
            
    # Save Memory
    with open(MEMORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

    logger.info("--- SCAN COMPLETE ---")

if __name__ == "__main__":
    run_oracle()
