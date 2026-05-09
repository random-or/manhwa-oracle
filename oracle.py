import requests
import re
import json
import os
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- 1. SETUP & SECRETS ---
# Loads your BOT_TOKEN and CHAT_ID from the hidden .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Configuration
TARGET_URL = "https://asurascans.com/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
MEMORY_FILE = "memory.json"

# --- 2. THE MESSENGER ---
def send_telegram(message):
    """Sends a notification to your phone via Telegram."""
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Error: BOT_TOKEN or CHAT_ID missing from .env!")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Telegram Send Failed: {e}")

# --- 3. THE ENGINE ---
def run_oracle():
    # Load Memory from the JSON 'notebook'
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            history = json.load(f)
    else:
        history = {}

    print("--- ORACLE IS SCANNING THE HOMEPAGE ---")

    # --- RETRY LOGIC (To handle 50% packet loss/unstable internet) ---
    max_retries = 3
    retry_delay = 5  # seconds
    response = None

    for attempt in range(max_retries):
        try:
            print(f"Attempting to reach the tower (Try {attempt + 1}/{max_retries})...")
            response = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                print("✅ Connection Successful!")
                break
        except Exception as e:
            print(f"⚠️ Connection flicker: {e}")
            if attempt < max_retries - 1:
                print(f"Waiting {retry_delay}s to try again...")
                time.sleep(retry_delay)

    # --- DATA EXTRACTION ---
    if response and response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Scrape all update containers
        items = soup.find_all('div', class_='utao')
        
        # THE HEALTH CHECK LINE
        print(f"DEBUG: Detected {len(items)} items on the homepage.")
        
        new_updates_count = 0
        
        for item in items:
            try:
                # Get Title
                title_tag = item.find('h4')
                if not title_tag: continue
                title = title_tag.text.strip()
                
                # Get Chapter
                chapter_li = item.find('li')
                if not chapter_li: continue
                chapter_text = chapter_li.text.strip()
                
                # Extract Number (e.g., "Chapter 108" -> 108)
                match = re.search(r'Chapter\s*(\d+)', chapter_text)
                
                if match:
                    current_ch = int(match.group(1))
                    last_seen = int(history.get(title, 0))
                    
                    # Logic: Is it actually new?
                    if current_ch > last_seen:
                        if last_seen == 0:
                            msg = f"🌟 NEW SERIES TRACKED!\n{title}\nStarting at Chapter {current_ch}"
                        else:
                            msg = f"🔥 NEW CHAPTER!\n{title}\nNow at Chapter {current_ch}"
                        
                        print(f"[!] {msg}")
                        send_telegram(msg)
                        history[title] = str(current_ch)
                        new_updates_count += 1
            except Exception as item_err:
                continue # Skip one broken item rather than crashing everything
        
        if new_updates_count == 0:
            print("Everything is up to date. No new pings sent.")
            
    else:
        print("❌ Oracle failed to reach the server. Check your connection.")

    # Save Memory
    with open(MEMORY_FILE, "w") as f:
        json.dump(history, f)

    print("--- SCAN COMPLETE ---")

if __name__ == "__main__":
    run_oracle()
