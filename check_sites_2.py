import requests
import cloudscraper

scraper = cloudscraper.create_scraper()

print("Manganato:", scraper.get('https://manganato.com/', timeout=20).status_code)
print("Manganato TO:", scraper.get('https://chapmanganato.to/', timeout=20).status_code)

print("Hive:", scraper.get('https://hivetoons.org/').status_code)
print("Hive 2:", scraper.get('https://hivescans.com/').status_code)

print("Webtoon:", scraper.get('https://www.webtoons.com/en/dailySchedule').status_code)
