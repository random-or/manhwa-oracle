import requests
import cloudscraper

scraper = cloudscraper.create_scraper()

sites = [
    'https://hivetoons.com', 'https://hivetoons.org/',
    'https://chapmanganato.com', 'https://manganelo.com/', 'https://chapmanganato.to/',
    'https://flamecomics.com', 'https://flamecomics.xyz', 'https://flamecomics.me',
    'https://luminouscomics.com', 'https://luminousscans.gg', 'https://luminousscans.net',
    'https://drakescan.com', 'https://drakescans.org', 'https://drakescans.net',
    'https://nightscans.org', 'https://nightscans.com', 'https://night-scans.com',
    'https://omegascans.org', 'https://omegascans.net', 'https://omegascans.com'
]

for url in sites:
    try:
        r = scraper.get(url, timeout=5)
        print(f"URL: {url} -> {r.status_code} (Final: {r.url})")
    except Exception as e:
        print(f"URL: {url} -> Failed ({type(e).__name__})")
