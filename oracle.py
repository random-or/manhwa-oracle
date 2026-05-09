import requests
import re
import json # The notebook tool
import os
from bs4 import BeautifulSoup

# 1. YOUR WATCHLIST
watchlist = [
    "https://asurascans.com/comics/eternally-regressing-knight-b6e039fe",
    "https://asurascans.com/comics/the-max-level-hero-has-returned-b6e039fe"
]

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
MEMORY_FILE = "memory.json"

# 2. LOAD THE NOTEBOOK
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        history = json.load(f)
else:
    history = {}

print("--- ORACLE SYSTEM: SCANNING FOR UPDATES ---")

for url in watchlist:
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.get_text().split('|')[0].strip()
            
            for link in soup.find_all('a'):
                text = link.get_text(separator=" ").strip()
                match = re.search(r'Chapter\s*(\d+)', text)
                
                if match:
                    current_ch = match.group(1)
                    
                    # LOGIC: Check if this is different from what's in our history
                    last_seen = history.get(title, "0")
                    
                    if int(current_ch) > int(last_seen):
                        print(f"[!!!] NEW UPDATE: {title} is now at Chapter {current_ch}!")
                        history[title] = current_ch # Update the notebook
                    else:
                        print(f"[ok] {title}: Still at Chapter {current_ch}")
                    break 
    except Exception as e:
        print(f"Error checking {url}: {e}")

# 3. SAVE THE NOTEBOOK FOR NEXT TIME
with open(MEMORY_FILE, "w") as f:
    json.dump(history, f)

print("--- SCAN COMPLETE ---")
