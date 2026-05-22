from typing import List, Dict, Union
import requests
from .base import BaseScraper, logger

class MangaPlusScraper(BaseScraper):
    @property
    def site_name(self) -> str:
        return "MangaPlus"

    @property
    def base_url(self) -> str:
        return "https://mangaplus.shueisha.co.jp/"

    def get_latest_chapters(self) -> List[Dict[str, Union[str, int, float]]]:
        # Unofficial Web API for MangaPlus
        api_url = "https://jumpg-webapi.tokyo-cdn.com/api/title_list/updated?format=json"
        
        try:
            self.rotate_user_agent()
            response = requests.get(api_url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                logger.error(f"[{self.site_name}] API returned {response.status_code}")
                return []
                
            data = response.json()
            error = data.get("error")
            if error:
                subject = "API error"
                if isinstance(error, dict):
                    subject = error.get("englishPopup", {}).get("subject", subject)
                logger.error(f"[{self.site_name}] API returned error: {subject}")
                return []
            updates = []
            
            def find_titles(node):
                if isinstance(node, dict):
                    if "title" in node and isinstance(node["title"], dict) and "name" in node["title"]:
                        title_info = node["title"]
                        title = title_info.get("name")
                        title_id = title_info.get("titleId")
                        if not title or not title_id:
                            return
                        chapter = self.parse_chapter(title_info.get("chapterName") or title_info.get("latestChapterName")) or 0.0
                        
                        updates.append({
                            "title": title,
                            "chapter": chapter,
                            "url": f"{self.base_url}titles/{title_id}",
                            "site": self.site_name
                        })
                    for key, value in node.items():
                        find_titles(value)
                elif isinstance(node, list):
                    for item in node:
                        find_titles(item)
                        
            find_titles(data)
            
            unique_updates = []
            seen = set()
            for u in updates:
                if u["title"] not in seen:
                    unique_updates.append(u)
                    seen.add(u["title"])
                    
            return unique_updates
            
        except Exception as e:
            logger.error(f"[{self.site_name}] Scraper error: {e}")
            return []

    def test(self) -> bool:
        """Override test to ping the API directly."""
        try:
            api_url = "https://jumpg-webapi.tokyo-cdn.com/api/title_list/updated?format=json"
            self.rotate_user_agent()
            response = requests.get(api_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return False
            data = response.json()
            return not data.get("error")
        except Exception:
            return False
