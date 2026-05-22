import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Union
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
        self.headers = {
            "User-Agent": ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

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
            return response.status_code in (200, 403)
        except Exception as e:
            logger.error(f"[{self.site_name}] Connection test failed: {e}")
            return False
