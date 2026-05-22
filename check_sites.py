import requests

sites = {
    'Void': 'https://hivescans.com/',
    'Manganato': 'https://manganato.com/',
    'MangaPlus': 'https://mangaplus.shueisha.co.jp/',
    'Webtoon': 'https://www.webtoons.com/en/dailySchedule',
    'Flame': 'https://flamescans.org/',
    'Luminous': 'https://luminousscans.com/',
    'Drake': 'https://drakescans.com/',
    'Night': 'https://nightscans.net/',
    'Omega': 'https://omegascans.org/'
}

for name, url in sites.items():
    try:
        r = requests.get(url, timeout=10)
        print(f"{name}: {r.status_code} - Final URL: {r.url}")
    except Exception as e:
        print(f"{name}: Failed - {e}")
