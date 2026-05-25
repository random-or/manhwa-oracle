# 🔮 Manhwa Oracle

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)

**The ultimate, plugin-based multi-site Manhwa/Manga tracker and Telegram notifier.**

Manhwa Oracle is a professional-grade automation tool designed to monitor your favorite series across multiple scanlation groups and official sources. When a new chapter drops, you get a clean, grouped notification directly on Telegram.

---

## ✨ Key Features

- 🔌 **Plugin Architecture**: Highly modular design. Adding a new site is as simple as creating a new class in `scrapers/`.
- 🧠 **Smart Tracking**: Fuzzy title matching ensures you don't miss updates even if sites use slightly different naming conventions.
- 🛠️ **Self-Healing URLs**: Automatically detects when a site changes its domain and attempts to find the new one to keep your tracker alive.
- 🗄️ **Robust SQLite Backend**: Moves beyond flat files to a reliable database for history, status tracking, and performance.
- 📲 **Interactive Telegram Bot**: A full-featured bot to manage your watchlist, browse latest updates, and check system health.
- 🛡️ **Graceful Resilience**: Isolated scrapers ensure that one failing site doesn't stop the rest of your notifications.

---

## 🌐 Supported Trackers

| Tracker | Status | Method |
| :--- | :--- | :--- |
| **AsuraScans** | ✅ Active | HTML Scraping |
| **MangaDex** | ✅ Active | Official JSON API |
| **Webtoon** | ✅ Active | HTML Scraping |
| **ManhuaPlus** | ✅ Active | HTML Scraping |
| **Comix** | ✅ Active | JSON API (`comix.to`) |
| **Atsumaru** | ✅ Active | JSON API (`atsu.moe`) |

---

## 🚀 Quick Start

### 1. Installation
```bash
git clone https://github.com/yourusername/manhwa-oracle.git
cd manhwa-oracle
pip install -r requirements.txt
```

### 2. Configuration
Copy the template and add your Telegram credentials.
```bash
cp .env.example .env
# Open .env and set your BOT_TOKEN and CHAT_ID
```

### 3. Initialize Database
If you are upgrading from an older version, migrate your data:
```bash
python oracle.py --migrate
```

---

## 💻 CLI Usage

The `oracle.py` script is your command center.

| Command | Description |
| :--- | :--- |
| `--run` | Primary scan mode. Checks all sites for new chapters. |
| `--flush` | Immediately sends all pending queued notifications to Telegram. |
| `--status` | Displays your current watchlist and last seen chapters. |
| `--add "Title" "Site"` | Adds a new series to track (use `any` for all sites). |
| `--remove "Title"` | Removes a series from your watchlist. |
| `--test` | Tests connectivity to all configured scrapers. |
| `--bot` | Starts the interactive Telegram bot. |
| `--stats` | Shows library and scanning statistics. |
| `--site-status` | View the health and last check times of all scrapers. |

---

## 🤖 Telegram Bot Features

Launch the bot with `python oracle.py --bot` to unlock interactive features:

- 🔔 **Real-time Interaction**: Get instant buttons to track or wishlist new series found in the latest updates.
- 📋 **Watchlist Management**: View and edit your tracked series directly from chat.
- 🌟 **Wishlist**: Save series you want to read later.
- 📊 **Status Reports**: Check if the Oracle is running correctly and which sites are currently active.

---

## ⏱️ Automation (Cron)

Keep your Oracle running 24/7 by setting up a simple cron job.

```cron
# Run every 6 hours and log output
0 */6 * * * cd /path/to/manhwa-oracle && python oracle.py --run >> cron_log.txt 2>&1
```

---

## 🤝 Contributing

Contributions are welcome! Whether it's a new scraper or a UI improvement for the bot, feel free to open a PR. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
