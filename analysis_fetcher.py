'''
Extension of yfinance to fetch some analyst data.
'''

import yfinance as yf

# ================= MAIN FUNCTIONS =================

def growth_estimates(stock: yf.Ticker) -> dict:
    '''
    Fetch the growth estimates from Yahoo Finance API.

    Keys:
    - `0q`: Current Qtr.
    - `+1q`: Next Qtr.
    - `0y`: Current Year
    - `+1y`: Next Year
    - `+5y`: Next 5 Years (per annum)
    - `-5y`: Past 5 Years (per annum)
    '''
    response = stock._quote._fetch(proxy=stock.proxy, modules=['indexTrend'])
    table_data = response['quoteSummary']['result'][0]['indexTrend']['estimates']
    return {item['period']: item.get('growth', None) for item in table_data}

# -----------------

def analyst_price_targets(stock: yf.Ticker) -> dict:
    '''
    Fetch the analyst price targets from Yahoo Finance API.

    Keys:
    - `current`: Current Price
    - `low`: Lowest estimate
    - `high`: Highest estimate
    - `mean`: Average of estimates
    - `median`: Median of estimates
    '''
    response = stock._quote._fetch(proxy=stock.proxy, modules=['financialData'])
    table_data = response['quoteSummary']['result'][0]['financialData']

    keys = [
        ('currentPrice', 'current'),
        ('targetLowPrice', 'low'),
        ('targetHighPrice', 'high'),
        ('targetMeanPrice', 'mean'),
        ('targetMedianPrice', 'median'),
    ]

    return {key[1]: table_data[key[0]] for key in keys}


# ================= DEBUG =================

if __name__ == "__main__":
    stock = yf.Ticker("AAPL")
    print(growth_estimates(stock))
    print(analyst_price_targets(stock))
