# 🔮 Manhwa Oracle

A robust, automated scraper designed to monitor [Asura Scans](https://asurascans.com/) for new manhwa chapter releases and deliver instant notifications via Telegram.

## 🚀 Features

- **Whitelist System**: Only get notified for series you care about via `watchlist.json`.
- **Daily Summary**: At 9 PM, receive a single combined message of all updates found during the day.
- **Dead Man Switch**: Receive a notification if the script fails to connect 3 times in a row.
- **Rich Notifications**: Clean Telegram messages with bold titles and direct links to chapters.
- **Tailwind-Resistant**: Uses advanced selector logic to stay functional even when site CSS changes.
- **Automated Logging**: Detailed logs in `cron_log.txt` for monitoring health and activity.

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/manhwa-oracle.git
cd manhwa-oracle
```

### 2. Set up a Virtual Environment
```bash
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## 🔑 Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in your Telegram credentials:
   - **`BOT_TOKEN`**: Obtain this by creating a bot through [@BotFather](https://t.me/BotFather).
   - **`CHAT_ID`**: Find your unique ID by messaging [@userinfobot](https://t.me/userinfobot).

3. **Whitelist**: Add the exact titles of manhwa you want to track to `watchlist.json`:
   ```json
   [
     "The Novel’s Extra",
     "Dungeon Odyssey"
   ]
   ```

## 🏃 Usage

Run the Oracle manually:
```bash
python3 oracle.py
```

### Automation (Cron)
To run the Oracle every 30 minutes, add this to your crontab (`crontab -e`):
```cron
*/30 * * * * /path/to/manhwa-oracle/env/bin/python3 /path/to/manhwa-oracle/oracle.py
```

## 📁 Project Structure

- `oracle.py`: The main automation engine.
- `memory.json`: Tracks the last seen chapter for each series.
- `watchlist.json`: Your list of followed manhwa.
- `state.json`: Tracks failure counts and summary dates.
- `queue.json`: Stores updates for the daily summary.
- `cron_log.txt`: Execution logs.
- `requirements.txt`: Python dependencies.

## 📝 License
MIT
