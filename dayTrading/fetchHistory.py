import yfinance as yf
from time import time
import pandas as pd
import concurrent.futures

STOCK = "AAPL"

now = int(time())
# the farthest back the API can go is 30 days
range_start = now - 30 * 24 * 60 * 60 + 1
week = 7 * 24 * 60 * 60
stock = yf.Ticker(STOCK)


def fetch_data(start):
    return stock.history(actions=False, interval="1m", start=start, end=start+week)

with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(fetch_data, start) for start in range(range_start, now, week)]
    dataframes = [future.result() for future in concurrent.futures.as_completed(futures)]


data = pd.concat(dataframes).sort_index()

# write to csv (append if file exists)
try:
    old_data = pd.read_csv(f"{STOCK}.csv", parse_dates=True, index_col="Datetime", date_format="%Y-%m-%d %H:%M:%S%z")
    data = pd.concat([old_data, data]).drop_duplicates(subset=["Datetime"], keep='first')
except Exception as e:
    pass
finally:
    data.to_csv(f"{STOCK}.csv")


# DEBUG
import mplfinance as mpf

mpf.plot(data,
         type='candle',
         style='charles',
         title=f'{STOCK}',
         ylabel='Price',
         ylabel_lower='Volume',
         volume=True)
