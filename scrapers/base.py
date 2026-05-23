import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union
from urllib.parse import urljoin
import cloudscraper
from fake_useragent import UserAgent

logger = logging.getLogger("Scraper")
ua = UserAgent()

class BaseScraper(ABC):
    """Abstract base class for all manga/manhwa site scrapers."""

    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        self.headers = {}
        self.rotate_user_agent()

    def rotate_user_agent(self):
        """Sets realistic headers with a rotating user agent."""
        try:
            user_agent = ua.random
        except Exception:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

        self.headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    def absolute_url(self, href: str) -> str:
        """Return an absolute URL for site-relative chapter links."""
        return urljoin(self.base_url, href or "")

    @staticmethod
    def parse_chapter(value: object) -> Optional[Union[int, float]]:
        """Parse a chapter value into int/float, returning None when unavailable."""
        import re

        if value is None:
            return None
        text = str(value).strip()
        match = re.search(r'(?:chapter|ch\.?|episode|ep\.?)\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        if not match:
            match = re.fullmatch(r'\d+(?:\.\d+)?', text)
        if not match:
            return None
        chapter_text = match.group(1) if match.lastindex else match.group(0)
        chapter = float(chapter_text)
        return int(chapter) if chapter.is_integer() else chapter

    @property
    @abstractmethod
    def site_name(self) -> str:
        """Name of the scraper/site."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL of the site."""
        pass

    @abstractmethod
    def get_latest_chapters(self) -> List[Dict[str, Union[str, int, float]]]:
        """
        Scrapes the site for the latest chapter updates.
        
        Returns:
            List[Dict]: A list of dictionaries with standardized format:
            {
                "title": "Series Name",
                "chapter": 123,
                "url": "direct link to chapter",
                "site": "SiteName"
            }
        """
        pass

    def test(self) -> bool:
        """
        Tests if the site is reachable.
        
        Returns:
            bool: True if reachable, False otherwise.
        """
        try:
            self.rotate_user_agent()
            response = self.scraper.get(self.base_url, headers=self.headers, timeout=15)
            # Accept 200 OK or 403 (often cloudflare/bot protection but site is up)
            if response.status_code == 403:
                return True
            if response.status_code != 200:
                return False
            response.encoding = response.apparent_encoding or response.encoding
            lowered = response.text[:3000].lower()
            blocked_markers = ("522: connection timed out", "account banned", "fingerprintjs", "domain parking")
            return not any(marker in lowered for marker in blocked_markers)
        except Exception as e:
            logger.error(f"[{self.site_name}] Connection test failed: {e}")
            return False
