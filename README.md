# 🔮 Manhwa Oracle

A robust, automated scraper designed to monitor [Asura Scans](https://asurascans.com/) for new manhwa chapter releases and deliver instant notifications via Telegram.

## 🚀 Features

- **Real-time Monitoring**: Scans the homepage for the latest updates.
- **Smart Tracking**: Remembers the last chapter you saw to avoid duplicate pings.
- **Tailwind-Resistant**: Uses advanced selector logic to stay functional even when site CSS changes.
- **Automated Logging**: Detailed logs in `cron_log.txt` for monitoring health and activity.
- **Reliable**: Built-in retry logic to handle network flickers and unstable connections.

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
- `memory.json`: Local database for tracking chapter history.
- `cron_log.txt`: Execution logs.
- `requirements.txt`: Python dependencies.
- `.env`: (Private) Your secret credentials.

## 📝 License
MIT
