import re
from typing import List, Dict, Union
from bs4 import BeautifulSoup
from .base import BaseScraper, logger

class MangaKakalotScraper(BaseScraper):
    @property
    def site_name(self) -> str:
        return "MangaKakalot"

    @property
    def base_url(self) -> str:
        return "https://mangakakalot.com/"

    def test(self) -> bool:
        """Override test to ping the site with a longer timeout."""
        try:
            self.rotate_user_agent()
            response = self.scraper.get(self.base_url, headers=self.headers, timeout=25)
            if response.status_code != 200:
                return False
            return "522: connection timed out" not in response.text[:3000].lower()
        except Exception as e:
            logger.error(f"[{self.site_name}] Connection test failed: {e}")
            return False
    def get_latest_chapters(self) -> List[Dict[str, Union[str, int, float]]]:
        try:
            self.rotate_user_agent()
            response = self.scraper.get(self.base_url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                logger.error(f"[{self.site_name}] Failed to reach homepage: HTTP {response.status_code}")
                return []
                
            soup = BeautifulSoup(response.text, "html.parser")
            updates = []
            
            items = soup.find_all('div', class_='content-homepage-item')
            for item in items:
                try:
                    title_info = item.find('h3', class_='item-title')
                    if not title_info: continue
                        
                    title_tag = title_info.find('a')
                    if not title_tag: continue
                        
                    title = title_tag.get('title') or title_tag.get_text(strip=True)
                    
                    chapters_div = item.find('p', class_='item-chapter')
                    if not chapters_div: continue
                        
                    latest_ch_tag = chapters_div.find('a')
                    if not latest_ch_tag: continue
                        
                    chapter_link = latest_ch_tag.get('href', self.base_url)
                    ch_text = latest_ch_tag.get_text(strip=True)
                    
                    current_ch = self.parse_chapter(ch_text)
                    if current_ch is not None:
                            
                        updates.append({
                            "title": title,
                            "chapter": current_ch,
                            "url": self.absolute_url(chapter_link),
                            "site": self.site_name
                        })
                except Exception as e:
                    logger.debug(f"[{self.site_name}] Error parsing item: {e}")
            return updates
        except Exception as e:
            logger.error(f"[{self.site_name}] Scraper error: {e}")
            return []
