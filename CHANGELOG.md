## [2.0.0] - 2026-05-22
### Added
- **Self-Healing URLs**: Automatically detects dead domains and heals them.
- **SQLite Migration**: Migrated memory.json to SQLite.
- **New CLI Commands**: --history, --site-status, --heal, --stats, --migrate.
### Fixed
- Fixed 9 broken scrapers.

# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-05-22

### Added
- **Plugin Architecture:** Complete refactor to support multiple scraper modules dynamically (`scrapers/__init__.py`).
- **11 New Sites Supported:** 
  - MangaDex (Official API)
  - MangaPlus (Unofficial API)
  - Webtoon
  - Flame Scans
  - Luminous Scans
  - Void (Hive) Scans
  - Drake Scans
  - Night Scans
  - Omega Scans
  - ManhuaPlus
  - Manganato
- **MangaStream Template:** Added generic abstract scraper for common scanlation site themes.
- **Fuzzy Deduplication:** Integrated `thefuzz` for intelligent cross-site tracking of titles.
- **Enhanced Notifications:** Daily digests are now grouped cleanly by site.
- **Robust CLI:** Added multiple new arguments (`--test`, `--sites`, `--add`, `--remove`, `--status`).
- **Dead Man Switch:** Telegram alerts sent if all scrapers fail consecutively.

### Changed
- `memory.json` restructured to group read history by site (`"SiteName": {"Series": Chapter}`).
- `watchlist.json` restructured to support specific site tracking and "any" site fuzzy tracking.
- Switched default `run_oracle` logic to use rate-limiting delays between site requests.

### Removed
- Legacy single-site hardcoded configurations in `config.py`.
