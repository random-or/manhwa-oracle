# 🔮 Manhwa Oracle

![Banner](https://via.placeholder.com/1200x300.png?text=Manhwa+Oracle)

**The ultimate, plugin-based multi-site Manhwa/Manga scraper and Telegram notifier.**
Never miss a chapter release again. Track your favorite series across multiple scanlation groups and official sources, all delivered straight to your phone.

---

## ✨ Features

- 🔌 **Plugin Architecture:** Easily expandable with a `BaseScraper` class. Drop new site scrapers into the `scrapers/` folder.
- 🌐 **Multi-Site Support:** Tracks active manga/manhwa sources out-of-the-box (MangaDex, Asura, Webtoon, ManhuaPlus, and more). Blocked/dead scrapers are disabled by default.
- 🧠 **Fuzzy Deduplication:** Intelligently tracks series even if they have slightly different names across sites.
- 🚀 **Free & Direct:** No paid APIs required. Uses official free APIs (MangaDex, MangaPlus) and robust HTML scraping (Cloudflare bypassed).
- 📲 **Telegram Integration:** Get twice-daily digests grouped by site, with chapter links and Telegram watchlist buttons/commands.
- 🛡️ **Graceful Fallbacks:** Isolated error handling ensures that if one site goes down, the orchestrator keeps scanning the rest.
- ⏱️ **Respectful Scanning:** Rate limits and user-agent rotation built-in to prevent IP blocks.

---

## 📚 Supported Sites

| Site | Status | Type |
|---|---|---|
| **AsuraScans** | ✅ Working | Scraping (Cloudflare Bypass) |
| **MangaDex** | ✅ Working | Official API |
| **Webtoon** | ✅ Working | Scraping |
| **ManhuaPlus** | ✅ Working | Scraping |
| **Leviatan Scans** | ⚠️ Disabled by default | Site timeout / blocked |
| **MangaKakalot** | ⚠️ Disabled by default | Site timeout / blocked |
| **Reaper Scans** | ⚠️ Disabled by default | Anti-bot page |
| **Bato.to** | ⚠️ Disabled by default | Domain not serving manga index |
| **MangaPlus** | ⚠️ Disabled by default | API may IP-ban non-browser clients |

---

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/manhwa-oracle.git
   cd manhwa-oracle
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the Environment:**
   Copy the example environment file and add your Telegram bot token.
   ```bash
   cp .env.example .env
   # Edit .env with your BOT_TOKEN and CHAT_ID
   ```

---

## ⚙️ Configuration Guide

All core settings are easily modifiable in `config.py`.

- **DIGEST_HOURS:** Comma-separated 24-hour digest hours. Default is `6,18`, matching the included twice-a-day cron schedule.
- **MAX_FAILURES_BEFORE_ALERT:** Number of consecutive full system failures before sending a Telegram emergency alert.
- **DISABLED_SCRAPERS:** Comma-separated module names to skip. Defaults to known blocked/dead sources: `bato,leviatan,mangakakalot,mangaplus,reaper`. Override with an environment variable if a domain starts working again.

### Adding to Watchlist
You can add specific series to track either on specific sites or "any" site (which fuzzy matches across all trackers).

```bash
# Add to any site
python oracle.py --add "Solo Leveling" any

# Add specifically to MangaDex
python oracle.py --add "Tower of God" MangaDex
```

---

## 💻 CLI Commands

The `oracle.py` script comes with powerful CLI commands:

- **Run Scraper (Cron Mode):**
  ```bash
  python oracle.py --run
  ```
  *(Or just `python oracle.py`)*
  
- **Test All Connections:**
  ```bash
  python oracle.py --test
  ```
  
- **Add Series:**
  ```bash
  python oracle.py --add "Title" "SiteName"
  ```
  
- **Remove Series:**
  ```bash
  python oracle.py --remove "Title"
  ```
  
- **Check Status:**
  ```bash
  python oracle.py --status
  ```
  *(Shows all tracked series and latest read chapters)*
  
- **List Sites:**
  ```bash
  python oracle.py --sites
  ```
  
- **Search (WIP):**
  ```bash
  python oracle.py --search "Title"
  ```

- **Run Telegram Bot:**
  ```bash
  python oracle.py --bot
  ```
  In Telegram, use `/latest` to see recent chapters with `Track this` and `Open chapter` buttons, `/watch Title | any` to add manually, `/unwatch Title` to remove, and `/watchlist` to view tracked titles.

---

## 🤖 Cron Setup Guide

To automate Manhwa Oracle, set up a cron job to run the script twice per day.

1. Open crontab: `crontab -e`
2. Add the following line:
   ```cron
   0 6,18 * * * cd /path/to/manhwa-oracle && python oracle.py --run >> cron_log.txt 2>&1
   ```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to add new scrapers or features.

If you encounter a bug or have a feature request, use our issue templates provided in the `.github` directory.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

### New Features in v2.0:
- **Self-Healing URLs:** Automatically repairs scraper domains when they go offline.
- **SQLite Backend:** Data is now stored reliably in `oracle.db` instead of flat JSON.

### New Commands:
`python oracle.py --migrate` - Migrate JSON to SQLite
`python oracle.py --history "Title"` - Show chapter history
`python oracle.py --site-status` - View health of all trackers
`python oracle.py --heal "Site"` - Manually heal a site
`python oracle.py --stats` - View library statistics
