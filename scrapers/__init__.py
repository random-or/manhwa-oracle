import os
import importlib
import inspect
import logging
from typing import List, Type
from config import config
from .base import BaseScraper

logger = logging.getLogger("Scraper")

def load_scrapers() -> List[BaseScraper]:
    """
    Dynamically loads and instantiates all scraper plugins 
    from the current directory.
    """
    scrapers = []
    current_dir = os.path.dirname(__file__)
    
    for filename in os.listdir(current_dir):
        if filename.endswith(".py") and filename not in ("__init__.py", "base.py", "mangastream_template.py"):
            plugin_name = filename[:-3]
            if plugin_name.lower() in config.DISABLED_SCRAPERS:
                logger.info(f"Skipping disabled scraper plugin: {filename}")
                continue
            module_name = f"scrapers.{plugin_name}"
            try:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Only grab concrete subclasses of BaseScraper defined in that specific module
                    if issubclass(obj, BaseScraper) and obj is not BaseScraper:
                        if obj.__module__ == module_name:
                            scrapers.append(obj())
                            logger.debug(f"Loaded scraper: {obj.__name__}")
            except Exception as e:
                logger.error(f"Failed to load scraper plugin {filename}: {e}")
                
    return scrapers

# Expose a ready-to-use list of instantiated scrapers
SCRAPERS = load_scrapers()
