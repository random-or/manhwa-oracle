import requests
import logging
import os
import glob
from typing import Optional
from database import SessionLocal, SiteStatus, HealingHistory

logger = logging.getLogger("Oracle")

class SiteHealer:
    def __init__(self):
        self.session = SessionLocal()
        
    def _update_scraper_file(self, site_name: str, old_url: str, new_url: str):
        # Find the scraper file
        for filepath in glob.glob("scrapers/*.py"):
            try:
                with open(filepath, "r", encoding='utf-8') as f:
                    content = f.read()
                if site_name in content and old_url in content:
                    new_content = content.replace(old_url, new_url)
                    with open(filepath, "w", encoding='utf-8') as f:
                        f.write(new_content)
                    logger.info(f"Updated {filepath} with new URL: {new_url}")
                    return True
            except Exception as e:
                logger.error(f"Error updating scraper file {filepath}: {e}")
        return False

    def heal(self, site_name: str, old_url: str) -> Optional[str]:
        logger.info(f"Attempting to heal {site_name} (Old URL: {old_url})")
        # Try different TLDs
        tlds = [".com", ".net", ".org", ".gg", ".to", ".cc", ".me", ".io"]
        base_name = old_url.replace("https://", "").replace("http://", "").split(".")[0]
        if "www." in base_name:
            base_name = base_name.replace("www.", "")
            
        found_url = None
        for tld in tlds:
            test_url = f"https://{base_name}{tld}/"
            try:
                response = requests.get(test_url, timeout=5, allow_redirects=True)
                if response.status_code == 200 and len(response.text) > 1000:
                    found_url = response.url
                    break
            except Exception:
                continue
                
        if found_url:
            logger.info(f"Successfully found new URL for {site_name}: {found_url}")
            self._update_scraper_file(site_name, old_url, found_url)
            history = HealingHistory(site_name=site_name, old_url=old_url, new_url=found_url)
            self.session.add(history)
            self.session.commit()
            return found_url
            
        logger.warning(f"Failed to find new URL for {site_name}")
        return None
        
    def mark_dead(self, site_name: str):
        status = self.session.query(SiteStatus).filter_by(site_name=site_name).first()
        if not status:
            status = SiteStatus(site_name=site_name, status="DEAD")
            self.session.add(status)
        else:
            status.status = "DEAD"
        self.session.commit()
        logger.error(f"Marked {site_name} as DEAD in database.")
