import yfinance as yf
from time import time
import pandas as pd
import concurrent.futures

DAY = 24 * 60 * 60
WEEK = 7 * DAY
MONTH = 30 * DAY
DATA_DIR = "./instruments/history"

def fetch_history(ticker):
    now = int(time())
    # the farthest back the API can go is 30 days
    range_start = now - MONTH + 1
    stock = yf.Ticker(ticker)

    def fetch_data(start):
        return stock.history(actions=False, interval="1m", start=start, end=start+WEEK)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_data, start) for start in range(range_start, now, WEEK)]
        dataframes = [future.result() for future in concurrent.futures.as_completed(futures)]

    data = pd.concat(dataframes)

    # write to csv (append if file exists)
    try:
        old_data = pd.read_csv(f"{DATA_DIR}/{ticker}.csv", parse_dates=True, index_col="Datetime", date_format="%Y-%m-%d %H:%M:%S%z")
        data = pd.concat([old_data, data])
        data = data[~data.index.duplicated(keep='first')]
    except Exception as e:
        print("Exception:", e)
    finally:
        data.sort_index(inplace=True)
        data.to_csv(f"{DATA_DIR}/{ticker}.csv")

    return data


# DEBUG
if __name__ == '__main__':
    ticker = "GOLD"
    import mplfinance as mpf
    data = fetch_history(ticker)
    exit()

    mpf.plot(data,
            type='candle',
            style='charles',
            title=f'{ticker}',
            ylabel='Price',
            ylabel_lower='Volume',
            volume=True)
