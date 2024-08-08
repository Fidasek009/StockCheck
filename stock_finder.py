'''
Find stocks that meet the required criteria.
'''

import yfinance as yf
import pandas as pd
from math import isnan
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from intrinsic_valuation import dcf_value, graham_value, lynch_value
from analysis_fetcher import analyst_price_targets
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import RequestRate, Limiter


class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass


# ================= TESTERS =================

def test_avaliability(instrument: yf.Ticker) -> bool:
    '''
    Test if the stock is on Yahoo Finance.
    '''
    return instrument.fast_info['lastPrice'] > 0

# -----------------

MIN_VOLUME = 1_000_000  # per day in the last month

def test_volume(instrument: yf.Ticker) -> bool:
    '''
    Daily trading volume.
    '''
    history = instrument.history(period='1mo', actions=False, raise_errors=True)
    return history['Volume'].min() > MIN_VOLUME

# -----------------

MIN_ASSET_LIABILITY_RATIO = 0.95

def test_balance_sheet(instrument: yf.Ticker) -> bool:
    '''
    Company's ability to pay off liabilities with its assets.
    '''
    balance_sheet = instrument.balance_sheet.T
    assets = balance_sheet['Current Assets'][0]
    liabilities = balance_sheet['Current Liabilities'][0]

    if isnan(assets) or isnan(liabilities):
        return False

    return assets / liabilities > MIN_ASSET_LIABILITY_RATIO

# -----------------

def adjusted_pct_change(previous, current):
    if previous == 0:
        return float('inf')
    return (current - previous) / abs(previous)


MIN_CASHFLOW_GROWTH = 0.07

def test_growth(instrument: yf.Ticker) -> bool:
    '''
    Free cashflow average increase is at least 5%.
    '''
    free_cashflow = instrument.cashflow.T['Free Cash Flow'].dropna().iloc[::-1]
    # company can operate in negative cashflow and still grow
    adjusted_changes = [adjusted_pct_change(free_cashflow[i], free_cashflow[i + 1]) for i in range(len(free_cashflow) - 1)]
    return np.mean(adjusted_changes) > MIN_CASHFLOW_GROWTH

# -----------------

MIN_PROFIT_MARGIN = 0.15    # between average(10%) and high(20%)

def test_profitability(instrument: yf.Ticker) -> bool:
    '''
    Company's ability to generate profit.
    '''
    income_stmt = instrument.income_stmt.T
    income = income_stmt['Operating Income'].dropna()[0]
    revenue = income_stmt['Total Revenue'].dropna()[0]
    return (income / revenue) > MIN_PROFIT_MARGIN

# -----------------

MEDIUM_VOLATILITY = 0.2
HIGH_VOLATILITY = 0.4

def test_volatility(instrument: yf.Ticker) -> bool:
    '''
    Stock's volatility.
    '''
    history = instrument.history(interval='1m', period='max', actions=False, raise_errors=True)
    history['log_HL'] = np.log(history['High'] / history['Low']) ** 2
    history['log_CO'] = np.log(history['Close'] / history['Open']) ** 2
    garman_klass_volatility = np.sqrt((0.5 * history['log_HL'] - (2 * np.log(2) - 1) * history['log_CO']).mean())
    annualized_garman_klass_volatility = garman_klass_volatility * np.sqrt(252 * 390)
    return annualized_garman_klass_volatility > HIGH_VOLATILITY

# -----------------

MIN_UNDERVALUATION = 0.5

def test_undervaluation(instrument: yf.Ticker) -> bool:
    '''
    Test if the stock is undervalued based on it's intrinsic value.
    '''
    dcf = dcf_value(instrument, 5)
    graham = graham_value(instrument)

    # Lynch only works for dividend companies
    try:
        lynch = lynch_value(instrument)
        intrinsic_val = 0.6 * dcf + 0.3 * graham + 0.1 * lynch
    except Exception:
        intrinsic_val = 0.7 * dcf + 0.3 * graham

    price = instrument.fast_info['lastPrice']
    diff = (intrinsic_val - price) / price
    return diff > MIN_UNDERVALUATION

# -----------------

MIN_ANALYST_UNDERVALUATION = 0.3

def test_analyst_undervaluation(instrument: yf.Ticker) -> bool:
    '''
    Test if the stock is undervalued based on analyst valuation.
    '''
    price_targets = analyst_price_targets(instrument)
    return price_targets['current'] < (1 - MIN_ANALYST_UNDERVALUATION) * price_targets['low']

# -----------------

MIN_ANALYSTS = 5
MIN_STRONG_BUY = 0.5

def test_recommendations(instrument: yf.Ticker) -> bool:
    '''
    Test if the stock has strong buy recommendation.
    '''
    rec = instrument.recommendations.iloc[0, 1:]
    if rec.empty or rec.sum() < MIN_ANALYSTS:
        return False

    strong_buy_pct = rec['strongBuy'] / rec.sum()
    return strong_buy_pct > MIN_STRONG_BUY


# ================= RUNNERS =================

def run_tests(ticker: str, testers: list[callable], session) -> str | None:
    msg = f"{ticker}\t"
    ticker = str(ticker)

    try:
        instrument = yf.Ticker(ticker, session=session)

        for tester in testers:
            if not tester(instrument):
                raise Exception(tester.__name__)
            msg += "✔️ "

        print(f"{msg}✅")
    except Exception as e:
        print(f"{msg}❌", e)
        ticker = None
    finally:
        return ticker

# -----------------

def run_threads(data: pd.DataFrame, testers: list[callable], threads: int) -> pd.DataFrame:
    session = CachedLimiterSession(
        limiter=Limiter(RequestRate(limit=10, interval=1)),
        bucket_class=MemoryQueueBucket,
        backend=SQLiteCache("stock-picker.cache"),
    )
    session.headers['User-agent'] = 'stock-picker/1.0'
    test = partial(run_tests, testers=testers, session=session)

    # Using ThreadPoolExecutor to run test_instrument in parallel
    with ThreadPoolExecutor(max_workers=threads) as executor:
        # Map test_instrument over the DataFrame's 'shortName' column
        results = list(executor.map(test, data['shortName']))

    session.cache.clear()
    session.close()

    # Filter out None values
    results = [res for res in results if res is not None]

    # Filter the DataFrame based on the results
    return data[data['shortName'].isin(results)]


# ================= DEBUG/RUN =================

# some pre-defined tester groups
avaliability = [test_avaliability]
basic_financials = [test_balance_sheet, test_profitability, test_growth]
undervaluation = basic_financials + [test_undervaluation]
analyst_undervaluation = basic_financials + [test_analyst_undervaluation]
recommendations = basic_financials + [test_recommendations]
day_trading = basic_financials + [test_volume, test_volatility]


if __name__ == "__main__":
    data = pd.read_csv("instruments/avaliable_instruments.csv")
    testers = analyst_undervaluation
    results = run_threads(data, testers, 10)
    results.to_csv("instruments/filtered_instruments.csv", index=False)
