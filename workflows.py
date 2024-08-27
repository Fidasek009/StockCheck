from dotenv import load_dotenv
from os import getenv
import requests
import pandas as pd
import stock_finder as sf

load_dotenv()
TRADING_API_KEY = getenv('TRADING_API_KEY')
TRADING_API_URL = 'https://live.trading212.com/api/v0'


def get_avaliable_instrumets() -> None:
    # fetch all instruments
    print('Fetching all instruments from Trading 212...')
    url = f'{TRADING_API_URL}/equity/metadata/instruments'
    headers = {'Authorization': TRADING_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # convert to a DataFrame
    data = pd.DataFrame(response.json())
    data = data[['ticker', 'shortName', 'type', 'minTradeQuantity', 'currencyCode']]
    data = data.sort_values(by='shortName')
    data.to_csv('instruments/instruments.csv', index=False)
    data = data.drop_duplicates(subset='shortName')

    # get only instruments avaliable on yfinance
    results = sf.run_threads(data, sf.avaliability, 20, 100)
    results.to_csv('instruments/avaliable_instruments.csv', index=False)


def get_undervalued_instruments() -> None:
    data = pd.read_csv('instruments/avaliable_instruments.csv')
    testers = sf.analyst_undervaluation
    results = sf.run_threads(data, testers, 10, 10)
    results.to_csv('instruments/undervalued_instruments.csv', index=False)


if __name__ == '__main__':
    get_avaliable_instrumets()
    get_undervalued_instruments()
