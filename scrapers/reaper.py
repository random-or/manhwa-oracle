from .mangastream_template import MangaStreamTemplate

class ReaperScraper(MangaStreamTemplate):
    def __init__(self):
        super().__init__(name="Reaper Scans", base_url="https://reaperscans.org/")
