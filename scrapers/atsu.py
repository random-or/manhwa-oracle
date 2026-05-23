from typing import Dict, List, Union

import requests

from .base import BaseScraper, logger


class AtsuScraper(BaseScraper):
    @property
    def site_name(self) -> str:
        return "Atsumaru"

    @property
    def base_url(self) -> str:
        return "https://atsu.moe/"

    @property
    def home_api_url(self) -> str:
        return f"{self.base_url}api/home/page"

    def test(self) -> bool:
        try:
            response = requests.get(
                self.home_api_url,
                headers={**self.headers, "Accept": "application/json"},
                timeout=15,
            )
            return response.status_code == 200 and "homePage" in response.json()
        except Exception as exc:
            logger.error(f"[{self.site_name}] API test failed: {exc}")
            return False

    def _latest_chapter_for_manga(self, manga_id: str) -> Union[int, float, None]:
        response = requests.get(
            f"{self.base_url}api/manga/info",
            params={"mangaId": manga_id},
            headers={**self.headers, "Accept": "application/json"},
            timeout=15,
        )
        if response.status_code != 200:
            return None
        chapters = response.json().get("chapters", [])
        if not chapters:
            return None
        latest = max(chapters, key=lambda chapter: chapter.get("number") or chapter.get("index") or 0)
        return self.parse_chapter(latest.get("number") or latest.get("title"))

    def get_latest_chapters(self) -> List[Dict[str, Union[str, int, float]]]:
        """Use Atsumaru's public home API and title info endpoints.

        The home API exposes a Recently Updated section, then the manga info API
        provides the actual latest chapter number for each title.
        """
        try:
            self.rotate_user_agent()
            response = requests.get(
                self.home_api_url,
                headers={**self.headers, "Accept": "application/json"},
                timeout=15,
            )
            if response.status_code != 200:
                logger.error(f"[{self.site_name}] Home API returned HTTP {response.status_code}: {response.text[:200]}")
                return []

            sections = response.json().get("homePage", {}).get("sections", [])
            recent_section = next((section for section in sections if section.get("key") == "recently-updated"), None)
            items = (recent_section or {}).get("items", [])
            updates = []
            seen = set()
            for item in items[:20]:
                title = item.get("title")
                manga_id = item.get("id")
                if not title or not manga_id or title in seen:
                    continue
                chapter = self._latest_chapter_for_manga(manga_id)
                if chapter is None:
                    continue
                updates.append({
                    "title": title,
                    "chapter": chapter,
                    "url": self.absolute_url(f"/manga/{manga_id}"),
                    "site": self.site_name,
                })
                seen.add(title)
            return updates
        except Exception as exc:
            logger.error(f"[{self.site_name}] Scraper error: {exc}")
            return []
