from datetime import datetime, timezone
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
        url = "https://www.webtoons.com/en/originals"
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
            
            # The old /dailySchedule page now redirects to /originals. Updated titles
            # are flagged with an UP badge; Webtoon does not expose chapter numbers on
            # this page, so use YYYYMMDD as a stable daily update marker.
            daily_marker = int(datetime.now(timezone.utc).strftime("%Y%m%d"))
            for link_tag in soup.select('a[href*="/list?title_no="]'):
                try:
                    item = link_tag.find_parent('li')
                    if not item or not item.select_one('.badge_up, .badge_up2'):
                        continue
                    title_tag = item.select_one('.title')
                    title = title_tag.get_text(strip=True) if title_tag else link_tag.get_text(" ", strip=True)
                    chapter_url = link_tag.get('href')
                    if title and chapter_url:
                        updates.append({
                            "title": title,
                            "chapter": daily_marker,
                            "url": self.absolute_url(chapter_url),
                            "site": self.site_name
                        })
                except Exception as e:
                    logger.debug(f"[{self.site_name}] Error parsing item: {e}")
            return updates
        except Exception as e:
            logger.error(f"[{self.site_name}] Scraper error: {e}")
            return []
