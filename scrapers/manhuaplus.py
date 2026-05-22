from .mangastream_template import MangaStreamTemplate

class ManhuaPlusScraper(MangaStreamTemplate):
    def __init__(self):
        super().__init__(name="ManhuaPlus", base_url="https://manhuaplus.com/")
