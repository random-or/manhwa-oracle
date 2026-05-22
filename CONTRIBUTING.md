# Contributing to Manhwa Oracle

First off, thank you for considering contributing to Manhwa Oracle! It's people like you that make Manhwa Oracle such a great tool.

## How to Contribute

### 1. Adding a New Scraper Plugin
This is the most common way to contribute!

1. Look inside the `scrapers/` folder.
2. Create a new python file (e.g., `mysite.py`).
3. Inherit from `BaseScraper` (or `MangaStreamTemplate` if it's a WordPress MangaStream theme).
4. Implement the required `site_name`, `base_url`, and `get_latest_chapters` properties/methods.
5. The orchestrator will automatically discover and load your scraper on the next run!

**Example:**
```python
from .base import BaseScraper
from typing import List, Dict, Union

class MySiteScraper(BaseScraper):
    @property
    def site_name(self) -> str:
        return "My Site"

    @property
    def base_url(self) -> str:
        return "https://mysite.com/"

    def get_latest_chapters(self) -> List[Dict[str, Union[str, int, float]]]:
        # Your scraping logic here...
        return [
            {"title": "Sample", "chapter": 1, "url": "https://mysite.com/sample/1", "site": self.site_name}
        ]
```

### 2. Testing Your Changes
Before submitting a Pull Request, verify your scraper works:
```bash
python oracle.py --test
```
Make sure your new site prints `✅ PASS`.

### 3. Reporting Bugs
Use the provided `.github/ISSUE_TEMPLATE/bug_report.md` template to submit issues.

### 4. Code Style
- Use clear variable names.
- Provide type hints for all functions.
- Keep the `BaseScraper` returned dictionary standardized.

Thank you!
