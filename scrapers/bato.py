from .mangastream_template import MangaStreamTemplate

class BatoScraper(MangaStreamTemplate):
    def __init__(self):
        super().__init__(name="Bato.to", base_url="https://www.bato.io/")
