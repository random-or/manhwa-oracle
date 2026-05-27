import argparse
import time
import random
import logging
from datetime import datetime, timezone
from config import config
from memory import MemoryManager
from notifier import TelegramNotifier
from scrapers import SCRAPERS

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cron_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Oracle")

class OracleOrchestrator:
    def __init__(self):
        self.memory = MemoryManager()
        self.notifier = TelegramNotifier()

    def action_test(self):
        """Tests all site connections."""
        print("\n🧪 Testing Scraper Connections...")
        print("================================")
        all_passed = True
        
        for scraper in SCRAPERS:
            print(f"Testing {scraper.site_name}...", end=" ", flush=True)
            if scraper.test():
                print("✅ PASS")
            else:
                print("❌ FAIL")
                all_passed = False
                
        print("================================")
        if all_passed:
            print("🎉 All systems are operational!")
        else:
            print("⚠️ Some scrapers failed. Check logs for details.")

    def action_sites(self):
        """Lists all available sites."""
        print("\n🌐 Supported Sites:")
        print("===================")
        for scraper in SCRAPERS:
            print(f"- {scraper.site_name}")
            
    def action_status(self):
        """Shows all tracked series."""
        watching = self.memory.watchlist.get("watching", [])
        notify_all = self.memory.watchlist.get("notify_all", False)
        
        print("\n📊 Oracle Status Report")
        print("=========================")
        print(f"Mode: {'Notify All' if notify_all else 'Watchlist Only'}")
        print(f"Tracking {len(watching)} series explicitly.\n")
        
        if not watching and not notify_all:
            print("Your watchlist is empty and notify_all is false.")
            return
            
        for item in watching:
            site = item.get("site", "any")
            title = item.get("title", "Unknown")
            ch = self.memory.get_last_seen_chapter(site, title) if site != "any" else "Variable"
            print(f"📖 {title} ({site}) -> Ch. {ch}")

    def action_add(self, title: str, site: str):
        """Adds a series to the watchlist."""
        if self.memory.add_to_watchlist(site, title):
            print(f"✅ Added '{title}' on '{site}' to watchlist.")
        else:
            print(f"⚠️ '{title}' on '{site}' is already in your watchlist.")

    def action_remove(self, title: str):
        """Removes a series from the watchlist."""
        if self.memory.remove_from_watchlist(title):
            print(f"🗑️ Removed '{title}' from watchlist.")
        else:
            print(f"⚠️ '{title}' is not in your watchlist.")

    def action_search(self, title: str):
        """Searches all sites. (Not fully implemented for all in BaseScraper, but skeleton provided)"""
        print(f"🔍 Searching for '{title}' across all sites is not fully supported yet.")
        print("Please check individual sites directly.")

    def action_history(self, title: str):
        """Shows chapter history for a series."""
        from database import SessionLocal, ChapterHistory
        session = SessionLocal()
        try:
            history = session.query(ChapterHistory).filter_by(series_title=title).order_by(ChapterHistory.read_at.desc()).limit(10).all()
            if not history:
                print(f"No history found for '{title}'.")
                return
            print(f"\n📖 History for '{title}':")
            for h in history:
                print(f"  - Ch. {h.chapter} on {h.site} ({h.read_at.strftime('%Y-%m-%d %H:%M')})")
        finally:
            session.close()

    def action_site_status(self):
        """Shows status of all sites."""
        from database import SessionLocal, SiteStatus
        session = SessionLocal()
        try:
            statuses = session.query(SiteStatus).all()
            print("\n🌐 Site Statuses:")
            if not statuses:
                print("  No site statuses recorded yet.")
            for s in statuses:
                print(f"  - {s.site_name}: {s.status} (Last Checked: {s.last_checked.strftime('%Y-%m-%d %H:%M')})")
        finally:
            session.close()

    def action_heal(self, site: str):
        """Attempts to manually heal a site."""
        from healer import SiteHealer
        healer = SiteHealer()
        scraper = next((s for s in SCRAPERS if s.site_name.lower() == site.lower()), None)
        if not scraper:
            print(f"Scraper for '{site}' not found.")
            return
        print(f"Attempting to heal {scraper.site_name}...")
        new_url = healer.heal(scraper.site_name, scraper.base_url)
        if new_url:
            print(f"✅ Successfully healed! New URL: {new_url}")
        else:
            print(f"❌ Failed to heal {scraper.site_name}.")
        healer.close()

    def action_stats(self):
        """Shows overall statistics."""
        from database import SessionLocal, Series, ChapterHistory
        session = SessionLocal()
        try:
            total_series = session.query(Series).count()
            total_chapters = session.query(ChapterHistory).count()
            print("\n📈 Oracle Statistics:")
            print(f"  - Total Series Tracked: {total_series}")
            print(f"  - Total Chapters Read: {total_chapters}")
        finally:
            session.close()

    def action_migrate(self):
        """Migrates data from JSON to SQLite."""
        self.memory.migrate_from_json()
        print("Migration complete!")

    def action_flush(self):
        """Manually flushes the notification queue."""
        if not self.memory.queue:
            print("Queue is empty.")
            return
            
        print(f"Flushing {len(self.memory.queue)} notifications...")
        if self.notifier.send_daily_digest(self.memory.queue):
            print("✅ Successfully flushed queue to Telegram.")
            self.memory.queue = []
            self.memory.save_all()
        else:
            print("❌ Failed to flush queue. Check logs.")

    def run_oracle(self):
        """Main scanning routine."""
        logger.info("--- ORACLE IS SCANNING ---")
        
        total_failures = 0
        new_updates_count = 0
        
        from healer import SiteHealer
        from database import SessionLocal, SiteStatus
        healer = SiteHealer()
        session = SessionLocal()
        
        for i, scraper in enumerate(SCRAPERS):
            logger.info(f"Checking {scraper.site_name}...")
            
            # Update last_checked for the site
            status = session.query(SiteStatus).filter_by(site_name=scraper.site_name).first()
            if not status:
                status = SiteStatus(site_name=scraper.site_name, status="ACTIVE")
                session.add(status)
            else:
                status.last_checked = datetime.now(timezone.utc).replace(tzinfo=None)
            status.status = "ACTIVE"
            session.commit()

            updates = scraper.get_latest_chapters()
            
            if not updates:
                logger.warning(f"No updates found or failed to fetch for {scraper.site_name}.")
                total_failures += 1
                
                # Check if it was a connection error by running test()
                if not scraper.test():
                    logger.warning(f"Site {scraper.site_name} appears down. Initiating self-healing...")
                    new_url = healer.heal(scraper.site_name, scraper.base_url)
                    if new_url:
                        self.notifier.send_message(f"🔧 <b>Healer</b>\nAutomatically updated {scraper.site_name} to {new_url}")
                    else:
                        healer.mark_dead(scraper.site_name)
                        self.notifier.send_message(f"💀 <b>Healer</b>\n{scraper.site_name} is marked as DEAD.")
            else:
                logger.info(f"[{scraper.site_name}] Scraped {len(updates)} chapters.")
                for item in updates:
                    title = item["title"]
                    site = item["site"]
                    current_ch = item["chapter"]
                    
                    if not self.memory.is_watched(site, title):
                        continue
                        
                    last_seen = self.memory.get_last_seen_chapter(site, title)
                    
                    if current_ch > last_seen:
                        item["is_new"] = (last_seen == 0.0)
                        if config.NOTIFY_IMMEDIATELY:
                            logger.info(f"NOTIFYING IMMEDIATELY: {title} Ch.{current_ch} from {site}")
                            if self.notifier.notify_update(item):
                                self.memory.update_last_seen_chapter(site, title, current_ch)
                                new_updates_count += 1
                            else:
                                logger.error(f"Failed to send immediate notification for {title}. Queueing instead.")
                                self.memory.queue.append(item)
                                self.memory.update_last_seen_chapter(site, title, current_ch)
                                new_updates_count += 1
                        else:
                            self.memory.queue.append(item)
                            logger.info(f"QUEUED: {title} Ch.{current_ch} from {site}")
                            self.memory.update_last_seen_chapter(site, title, current_ch)
                            new_updates_count += 1
            
            # Rate limiting between sites
            if i < len(SCRAPERS) - 1:
                delay = random.uniform(2.0, 3.5)
                logger.debug(f"Sleeping for {delay:.2f}s before next site...")
                time.sleep(delay)

        # Dead man switch
        if total_failures == len(SCRAPERS) and len(SCRAPERS) > 0:
            self.memory.state["fail_count"] += 1
            logger.error(f"Oracle failed to fetch updates from ALL sites. Fail count: {self.memory.state['fail_count']}")
            
            if self.memory.state["fail_count"] >= config.MAX_FAILURES_BEFORE_ALERT:
                logger.error("DEAD MAN SWITCH TRIGGERED!")
                self.notifier.send_message("⚠️ <b>SYSTEM ALERT</b>\nThe Manhwa Oracle has failed on ALL sites consecutively. Scrapers might be blocked.")
        else:
            self.memory.state["fail_count"] = 0

        # Send scan updates immediately if there are any
        now = datetime.now()
        digest_key = now.strftime("%Y-%m-%d-%H")

        if self.memory.queue:
            logger.info(f"Flushing {len(self.memory.queue)} updates to Telegram...")
            if self.notifier.send_scan_digest(self.memory.queue):
                logger.info(f"Scan digest sent with {len(self.memory.queue)} updates.")
                self.memory.queue = [] # Clear queue after sending
                self.memory.state["last_digest_key"] = digest_key
                self.memory.state["last_summary_date"] = now.strftime("%Y-%m-%d")
            else:
                logger.error("Failed to send scan digest; queue retained.")
        else:
            logger.info("No queued updates to send.")

        if new_updates_count == 0:
            logger.info("No new updates found this run.")
            
        # Save all states
        self.memory.save_all()
        healer.close()
        session.close()
        logger.info("--- SCAN COMPLETE ---")

def main():
    parser = argparse.ArgumentParser(description="🔮 Manhwa Oracle - Multi-Site Tracker")
    parser.add_argument("--run", action="store_true", help="Run the orchestrator to check all sites")
    parser.add_argument("--test", action="store_true", help="Test all site connections")
    parser.add_argument("--add", nargs=2, metavar=("TITLE", "SITE"), help="Add a series to watchlist (e.g. 'Solo Leveling' 'any')")
    parser.add_argument("--remove", type=str, metavar="TITLE", help="Remove a series from watchlist")
    parser.add_argument("--search", type=str, metavar="TITLE", help="Search for a manhwa by name")
    parser.add_argument("--status", action="store_true", help="Show all tracked series")
    parser.add_argument("--sites", action="store_true", help="List all available sites")
    parser.add_argument("--history", type=str, metavar="TITLE", help="Show chapter history for a series")
    parser.add_argument("--site-status", action="store_true", help="Show status of all sites")
    parser.add_argument("--heal", type=str, metavar="SITE", help="Attempt to heal a broken site URL")
    parser.add_argument("--stats", action="store_true", help="Show overall statistics")
    parser.add_argument("--migrate", action="store_true", help="Migrate data from JSON to SQLite")
    parser.add_argument("--flush", action="store_true", help="Manually send all pending notifications")
    parser.add_argument("--bot", action="store_true", help="Run the Telegram watchlist bot")
    parser.add_argument("--notify-all", choices=["true", "false", "on", "off"], help="Toggle global Notify All mode")
    
    args = parser.parse_args()
    oracle = OracleOrchestrator()
    
    try:
        if args.test:
            oracle.action_test()
        elif args.sites:
            oracle.action_sites()
        elif args.status:
            oracle.action_status()
        elif args.history:
            oracle.action_history(args.history)
        elif args.site_status:
            oracle.action_site_status()
        elif args.heal:
            oracle.action_heal(args.heal)
        elif args.stats:
            oracle.action_stats()
        elif args.migrate:
            oracle.action_migrate()
        elif args.flush:
            oracle.action_flush()
        elif args.bot:
            from telegram_bot import main as run_telegram_bot
            run_telegram_bot()
        elif args.notify_all:
            val = args.notify_all.lower() in ("true", "on")
            oracle.memory._notify_all = val
            print(f"✅ Global 'Notify All' mode set to: {'ON' if val else 'OFF'}")
        elif args.add:
            oracle.action_add(args.add[0], args.add[1])
        elif args.remove:
            oracle.action_remove(args.remove)
        elif args.search:
            oracle.action_search(args.search)
        elif args.run or not any(vars(args).values()):
            oracle.run_oracle()
    finally:
        oracle.memory.close()

if __name__ == "__main__":
    main()
