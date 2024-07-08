'''
Pick suitable stocks for day trading

Requirements:
- daily volume > 1M (enough buyers/sellers)
- balance sheet > 0.9 (company is not in debt)
- last year had increasing cashflow (company is growing)
- medium/high volatility (opportunities to trade)
'''

import yfinance as yf
import pandas as pd
from math import isnan
import numpy as np
from concurrent.futures import ThreadPoolExecutor


MIN_VOLUME = 1_000_000  # in the last month
MIN_ASSET_LIABILITY_RATIO = 0.9
MEDIUM_VOLATILITY = 0.2
HIGH_VOLATILITY = 0.4


def check_avaliability(instrument: yf.Ticker) -> bool:
    return instrument.history(period='1d', actions=False, raise_errors=True).empty


def check_volume(instrument: yf.Ticker) -> bool:
    history = instrument.history(period='1mo', actions=False, raise_errors=True)
    return history['Volume'].min() > MIN_VOLUME


def check_balance_sheet(instrument: yf.Ticker) -> bool:
    balance_sheet = instrument.balance_sheet.T
    assets = balance_sheet['Current Assets'][0]
    liabilities = balance_sheet['Current Liabilities'][0]

    if isnan(assets) or isnan(liabilities):
        return False

    return assets / liabilities > MIN_ASSET_LIABILITY_RATIO


def check_cashflow(instrument: yf.Ticker) -> bool:
    cashflow = instrument.cashflow.T
    free_cashflow = cashflow['Free Cash Flow']

    # last index can be NaN
    last_idx = len(free_cashflow) - 1
    if isnan(free_cashflow[last_idx]):
        last_idx -= 1

    # no data
    if isnan(free_cashflow[last_idx]) or isnan(free_cashflow[last_idx - 1]):
        return False

    return free_cashflow[last_idx] > free_cashflow[last_idx - 1]


def check_volatility(instrument: yf.Ticker) -> bool:
    history = instrument.history(interval='1m', period='max', actions=False, raise_errors=True)
    history['log_HL'] = np.log(history['High'] / history['Low']) ** 2
    history['log_CO'] = np.log(history['Close'] / history['Open']) ** 2
    garman_klass_volatility = np.sqrt((0.5 * history['log_HL'] - (2 * np.log(2) - 1) * history['log_CO']).mean())
    annualized_garman_klass_volatility = garman_klass_volatility * np.sqrt(252 * 390)
    return annualized_garman_klass_volatility > MEDIUM_VOLATILITY


def test_instrument(ticker: str) -> str | None:
    msg = f"{ticker}\t"

    try:
        instrument = yf.Ticker(str(ticker))

        if not check_volume(instrument):
            raise Exception("Volume")
        msg += "✔️ "

        if not check_balance_sheet(instrument):
            raise Exception("Balance Sheet")
        msg += "✔️ "

        if not check_cashflow(instrument):
            raise Exception("Cashflow")
        msg += "✔️ "

        if not check_volatility(instrument):
            raise Exception("Volatility")

        print(f"{msg}✅")
        return ticker

    except Exception as e:
        print(f"{msg}❌", e)
        return None


if __name__ == "__main__":
    data = pd.read_csv("instruments/instruments.csv")

    # Using ThreadPoolExecutor to run test_instrument in parallel
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Map test_instrument over the DataFrame's 'shortName' column
        results = list(executor.map(test_instrument, data['shortName']))

    # Filter None values from the results
    results = [result for result in results if result is not None]

    # Filter the DataFrame based on the results
    filtered_data = data[data['shortName'].isin(results)]
    filtered_data.to_csv("instruments/filtered_instruments.csv", index=False)
