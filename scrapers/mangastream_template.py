import re
from typing import List, Dict, Union
from bs4 import BeautifulSoup
from .base import BaseScraper, logger

class MangaStreamTemplate(BaseScraper):
    """
    A generic scraper template for sites using the MangaStream / Madara WordPress themes.
    """
    def __init__(self, name: str, base_url: str):
        super().__init__()
        self._name = name
        self._base_url = base_url if base_url.endswith('/') else f"{base_url}/"

    @property
    def site_name(self) -> str:
        return self._name
        
    @property
    def base_url(self) -> str:
        return self._base_url

    def get_latest_chapters(self) -> List[Dict[str, Union[str, int, float]]]:
        try:
            self.rotate_user_agent()
            response = self.scraper.get(self.base_url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                logger.error(f"[{self.site_name}] HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Common MangaStream update block selectors
            items = soup.select('.utao .uta .imgu, .bsx, .page-item-detail, .luf, .post-title')
            
            updates = []
            seen = set()
            for item in items:
                try:
                    title_tag = item.find('a', title=True) or item.find('a')
                    if not title_tag: continue
                    
                    h_tag = item.find(['h3', 'h4'])
                    if h_tag and h_tag.find('a'):
                        title_tag = h_tag.find('a')
                        
                    title = title_tag.get('title') or title_tag.get_text(strip=True)
                    if not title or title in seen: continue
                        
                    ch_tags = item.select('ul li a, .epxs, .chapter-item a, .btn-link')
                    if not ch_tags: continue
                        
                    latest_ch_tag = ch_tags[0]
                    chapter_link = latest_ch_tag.get('href', self.base_url)
                    ch_text = latest_ch_tag.get_text(separator=" ", strip=True)
                    
                    match = re.search(r'(?:Chapter|Ch\.)?\s*(\d+(?:\.\d+)?)', ch_text, re.IGNORECASE)
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
                        seen.add(title)
                except Exception as e:
                    logger.debug(f"[{self.site_name}] Error parsing item: {e}")
            
            return updates
        except Exception as e:
            logger.error(f"[{self.site_name}] Error during homepage update check: {e}")
            return []
