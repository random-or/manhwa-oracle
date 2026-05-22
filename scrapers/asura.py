import re
from typing import List, Dict, Union
from bs4 import BeautifulSoup
from .base import BaseScraper, logger

class AsuraScraper(BaseScraper):
    @property
    def site_name(self) -> str:
        return "AsuraScans"

    @property
    def base_url(self) -> str:
        return "https://asuracomic.net/" 

    def get_latest_chapters(self) -> List[Dict[str, Union[str, int, float]]]:
        try:
            self.rotate_user_agent()
            response = self.scraper.get(self.base_url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                logger.error(f"[{self.site_name}] Failed to reach homepage: HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, "html.parser")
            titles = soup.find_all('a', class_=re.compile(r'font-bold.*text-base|text-\[15px\]'))
            
            updates = []
            for title_tag in titles:
                try:
                    title = title_tag.get_text(strip=True)
                    if not title: continue
                        
                    chapters_div = title_tag.find_next_sibling('div')
                    if not chapters_div: continue
                        
                    latest_ch_tag = chapters_div.find('a')
                    if not latest_ch_tag: continue
                        
                    chapter_link = latest_ch_tag.get('href', self.base_url)
                    ch_text = latest_ch_tag.get_text(separator=" ", strip=True)
                    match = re.search(r'Chapter\s*(\d+(?:\.\d+)?)', ch_text, re.IGNORECASE)
                    
                    if match:
                        current_ch = float(match.group(1))
                        if current_ch.is_integer():
                            current_ch = int(current_ch)
                            
                        updates.append({
                            "title": title,
                            "chapter": current_ch,
                            "url": chapter_link,
                            "site": self.site_name
                        })
                except Exception as e:
                    logger.debug(f"[{self.site_name}] Error parsing item: {e}")
            return updates
        except Exception as e:
            logger.error(f"[{self.site_name}] Scraper error: {e}")
            return []
