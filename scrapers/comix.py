from typing import Dict, List, Union

import requests

from .base import BaseScraper, logger


class ComixScraper(BaseScraper):
    @property
    def site_name(self) -> str:
        return "Comix"

    @property
    def base_url(self) -> str:
        return "https://comix.to/"

    @property
    def api_url(self) -> str:
        return f"{self.base_url}api/v1/manga"

    def test(self) -> bool:
        try:
            response = requests.get(
                self.api_url,
                params={"order[chapter_updated_at]": "desc", "limit": 1},
                headers={**self.headers, "Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
                timeout=15,
            )
            return response.status_code == 200 and bool(response.json().get("result", {}).get("items"))
        except Exception as exc:
            logger.error(f"[{self.site_name}] API test failed: {exc}")
            return False

    def get_latest_chapters(self) -> List[Dict[str, Union[str, int, float]]]:
        try:
            self.rotate_user_agent()
            response = requests.get(
                self.api_url,
                params={"order[chapter_updated_at]": "desc", "limit": 30},
                headers={**self.headers, "Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
                timeout=15,
            )
            if response.status_code != 200:
                logger.error(f"[{self.site_name}] API returned HTTP {response.status_code}")
                return []

            items = response.json().get("result", {}).get("items", [])
            updates = []
            seen = set()
            for item in items:
                title = item.get("title")
                chapter = item.get("latestChapter")
                slug = item.get("url")
                if not title or chapter in (None, "") or not slug or title in seen:
                    continue
                parsed_chapter = self.parse_chapter(chapter)
                if parsed_chapter is None:
                    continue
                updates.append({
                    "title": title,
                    "chapter": parsed_chapter,
                    "url": self.absolute_url(slug),
                    "site": self.site_name,
                })
                seen.add(title)
            return updates
        except Exception as exc:
            logger.error(f"[{self.site_name}] Scraper error: {exc}")
            return []
