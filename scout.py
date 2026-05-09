import requests
from bs4 import BeautifulSoup
import re

url = "https://asurascans.com/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

print("--- DEPLOYING SCOUT V3 (TAILWIND BYPASS) ---")

try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 1. THE MAP YOU FOUND:
        # We look for <a> tags (links) that contain 'font-bold' and 'text-base'
        # re.compile allows us to find classes that just contain these words
        titles = soup.find_all('a', class_=re.compile(r'font-bold.*text-base'))
        
        if not titles:
            print("[-] Still blind. The HTML might be loading via JavaScript.")
            
        for title_tag in titles:
            # Extract the actual name (e.g., "Dungeon Odyssey")
            title = title_tag.get_text(strip=True)
            
            # 2. THE SIBLING SEARCH:
            # In your HTML, the chapters were in a <div> right after the title.
            # We tell Python: "Look at the very next block of code after the title."
            chapters_div = title_tag.find_next_sibling('div')
            
            if chapters_div:
                # 3. GRAB THE FIRST CHAPTER:
                latest_ch_tag = chapters_div.find('a')
                
                if latest_ch_tag:
                    # We grab the text. Your HTML had a weird comment 'Chapter <!-- -->159'
                    # get_text(strip=True) ignores that garbage.
                    ch_text = latest_ch_tag.get_text(separator=" ", strip=True)
                    
                    # 4. SNIPER FILTER: Get only the number
                    match = re.search(r'Chapter\s*(\d+)', ch_text)
                    ch_num = match.group(1) if match else "Unknown"
                    
                    print(f"[LIVE] {title} -> Chapter {ch_num}")
                    
    else:
        print(f"Connection Failed: {response.status_code}")

except Exception as e:
    print(f"Critical Error: {e}")

print("--- SCOUT MISSION COMPLETE ---")
