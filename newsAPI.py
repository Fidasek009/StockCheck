import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()
API_KEY = os.getenv('API_KEY')

ENDPOINT = "https://www.alphavantage.co"
QUERY = f"{ENDPOINT}/query?apikey={API_KEY}"
TICKER = "AAPL"


url = f"{QUERY}&function=NEWS_SENTIMENT&tickers={TICKER}&limit=5"
r = requests.get(url)
data = r.json()


with open("data.json", 'w') as f:
    json.dump(data, f, indent=4)