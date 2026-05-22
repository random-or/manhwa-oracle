from typing import List, Dict, Union
import requests
from .base import BaseScraper, logger

class MangaDexScraper(BaseScraper):
    @property
    def site_name(self) -> str:
        return "MangaDex"

    @property
    def base_url(self) -> str:
        return "https://mangadex.org/"

    def get_latest_chapters(self) -> List[Dict[str, Union[str, int, float]]]:
        # official API for latest chapters
        api_url = "https://api.mangadex.org/chapter"
        params = {
            "translatedLanguage[]": "en",
            "order[publishAt]": "desc",
            "limit": 30,
            "includes[]": "manga"
        }
        
        try:
            self.rotate_user_agent()
            response = requests.get(api_url, headers=self.headers, params=params, timeout=15)
            if response.status_code != 200:
                logger.error(f"[{self.site_name}] API returned {response.status_code}")
                return []
                
            data = response.json().get("data", [])
            updates = []
            
            for item in data:
                try:
                    chapter_num_str = item.get("attributes", {}).get("chapter")
                    if not chapter_num_str:
                        continue
                        
                    chapter_num = float(chapter_num_str)
                    if chapter_num.is_integer():
                        chapter_num = int(chapter_num)
                        
                    # Find manga title
                    manga_title = "Unknown"
                    for rel in item.get("relationships", []):
                        if rel.get("type") == "manga":
                            title_dict = rel.get("attributes", {}).get("title", {})
                            manga_title = title_dict.get("en") or list(title_dict.values())[0] if title_dict else "Unknown"
                            break
                            
                    chapter_id = item.get("id")
                    url = f"{self.base_url}chapter/{chapter_id}"
                    
                    updates.append({
                        "title": manga_title,
                        "chapter": chapter_num,
                        "url": url,
                        "site": self.site_name
                    })
                except Exception as e:
                    logger.debug(f"[{self.site_name}] Error parsing item: {e}")
                    
            return updates
            
        except Exception as e:
            logger.error(f"[{self.site_name}] Scraper error: {e}")
            return []

    def test(self) -> bool:
        """Override test to ping the API directly."""
        try:
            api_url = "https://api.mangadex.org/ping"
            response = requests.get(api_url, timeout=10)
            return response.status_code == 200
        except:
            return False
