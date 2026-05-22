import re
from typing import List, Dict, Union
from bs4 import BeautifulSoup
from .base import BaseScraper, logger

class WebtoonScraper(BaseScraper):
    @property
    def site_name(self) -> str:
        return "Webtoon"

    @property
    def base_url(self) -> str:
        return "https://www.webtoons.com/en/"

    def get_latest_chapters(self) -> List[Dict[str, Union[str, int, float]]]:
        url = "https://www.webtoons.com/en/dailySchedule"
        try:
            self.rotate_user_agent()
            headers = self.headers.copy()
            headers["Referer"] = "https://www.webtoons.com/en/"
            response = self.scraper.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                logger.error(f"[{self.site_name}] Failed to reach homepage: HTTP {response.status_code}")
                return []
                
            soup = BeautifulSoup(response.text, "html.parser")
            updates = []
            
            # Webtoon daily schedule has lists of items
            daily_lists = soup.find_all('ul', class_='daily_card')
            for d_list in daily_lists:
                items = d_list.find_all('li')
                for item in items:
                    try:
                        title_tag = item.find('p', class_='subj')
                        if not title_tag: continue
                        title = title_tag.get_text(strip=True)
                        
                        # Webtoon's daily schedule doesn't explicitly list chapter numbers easily, 
                        # it just shows it's updated today. We might need to go to the link to get the exact chapter
                        # Or extract it if available. Usually, we can just look at the 'update' icon.
                        # For the sake of standardizing, we will assign chapter 0 for webtoon if we can't find it,
                        # and rely on the fact it was updated today.
                        
                        link_tag = item.find('a')
                        if not link_tag: continue
                        url = link_tag.get('href')
                        
                        # Let's hit the specific series page briefly to get the latest chapter
                        # To avoid hammering, we'll only do a few or just try to extract chapter from URL if possible.
                        # Actually hitting the series page for every update will be too slow and rate limited.
                        # We will use chapter 0.0 or random hash to trigger update if needed, but wait, Webtoon shows updates.
                        # We will just parse the 'up' tag.
                        is_up = item.find('p', class_='icon_area')
                        if is_up and 'up' in is_up.get_text(strip=True).lower():
                             updates.append({
                                 "title": title,
                                 "chapter": 0.0,
                                 "url": url,
                                 "site": self.site_name
                             })
                             
                    except Exception as e:
                        logger.debug(f"[{self.site_name}] Error parsing item: {e}")
            return updates
        except Exception as e:
            logger.error(f"[{self.site_name}] Scraper error: {e}")
            return []
