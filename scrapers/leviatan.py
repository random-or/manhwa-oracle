from .mangastream_template import MangaStreamTemplate

class LeviatanScraper(MangaStreamTemplate):
    def __init__(self):
        super().__init__(name="Leviatan Scans", base_url="https://leviatanscans.com/")
