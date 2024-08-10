import yfinance as yf
import pandas as pd
import requests
from analysis_fetcher import Analysis


# ================================ HELPER FUNCTIONS ================================


GSPC_CHANGES = yf.Ticker('^GSPC').history(period='5y')['Close'].pct_change()

def calculate_beta(stock: yf.Ticker) -> float:
    '''
    Measure of a stock's volatility in relation to the S&P 500.
    '''
    hist = stock.history(period='5y')
    return hist['Close'].pct_change().corr(GSPC_CHANGES)


# -----------------


US_BOND_YIELD = yf.Ticker('^TNX').fast_info['lastPrice'] / 100
MARKET_RETURN = 0.08

def calculate_waac(stock: yf.Ticker) -> float:
    '''
    Weighted Average Cost of Capital - Discount Rate.
    Video: https://www.youtube.com/watch?v=yIJjUzyNGqg
    '''
    balance_sheet = stock.balance_sheet.T
    income_statement = stock.income_stmt.T

    # Cost of Debt
    interest_expense = income_statement['Interest Expense Non Operating'].dropna()[0]
    total_debt = balance_sheet['Total Debt'].dropna()[0]
    cost_of_debt = interest_expense / total_debt

    tax_expense = income_statement['Tax Provision'].dropna()[0]
    before_tax = income_statement['Pretax Income'].dropna()[0]
    tax_rate = tax_expense / before_tax

    cost_of_debt_after_tax = cost_of_debt * (1 - tax_rate)

    # Cost of Equity
    try:
        beta = stock.info['beta']
    except KeyError:
        beta = calculate_beta(stock)

    cost_of_equity = US_BOND_YIELD + beta * (MARKET_RETURN - US_BOND_YIELD)

    # Weight of Debt and Equity
    market_cap = stock.fast_info['marketCap']
    total_cap = market_cap + total_debt
    weight_of_debt = total_debt / total_cap
    weight_of_equity = market_cap / total_cap

    # WACC
    return weight_of_debt * cost_of_debt_after_tax + weight_of_equity * cost_of_equity


# -----------------


def get_estimated_growth(stock: yf.Ticker) -> float:
    '''
    Fetch the growth estimates from Yahoo Finance API.
    '''
    growth_estimates = Analysis(stock).growth_estimates
    growth = growth_estimates['stock']['+5y']

    if growth < 0:
        raise ValueError("Negative estimated growth is bad.")

    return growth


# -----------------


def get_aaa_yield() -> float:
    '''
    AAA Corporate Bond Yield.
    '''
    url = "https://ycharts.com/charts/fund_data.json"
    params = {
        "securities": "id:I:USCAAAEY,include:true,,",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    return data['chart_data'][0][0]['last_value'] / 100


# ================================ MAIN FUNCTIONS ================================


def ddm_value(stock: yf.Ticker) -> float:
    '''
    Intrinsic Value of a stock using Dividend Discount Model.
    Video: https://www.youtube.com/watch?v=7ls5XX7hdqs
    ⚠️ VERY INACCURATE ⚠️
    '''
    # dividend history
    data = stock.dividends.last('5Y')

    if len(data) < 16:
        raise ValueError("Not enough data to calculate the intrinsic value.")

    current_year = data.iloc[-1] * 4
    annual_dividends = data.resample('Y').sum()
    annual_dividends.iloc[-1] = current_year

    # predicted growth
    growth = annual_dividends.pct_change().mean()
    discount_rate = calculate_waac(stock)

    # DDM formula
    return (current_year * (1 + growth)) / (discount_rate - growth)


# -----------------


# 2-3% is the average growth rate of the US economy
PERPETUAL_GROWTH_RATE = 0.025

def dcf_value(stock: yf.Ticker, future_years: int) -> float:
    '''
    Intrinsic Value of a stock using Discounted Cash Flow method.
    Video: https://www.youtube.com/watch?v=EhWiHVt8xOg
    '''
    # ----------------- Present Data -----------------

    free_cashflow = stock.info['freeCashflow']
    growth_rate = get_estimated_growth(stock)
    discount_rate = calculate_waac(stock)

    # ----------------- Future Cash Flow -----------------

    future_cashflow = pd.DataFrame(index=range(future_years))

    # calculate future cashflow from the last known Free Cash Flow
    future_cashflow['Free Cash Flow'] = free_cashflow * (1 + growth_rate)
    for i in range(1, future_years):
        future_cashflow['Free Cash Flow'][i] = future_cashflow['Free Cash Flow'][i - 1] * (1 + growth_rate)

    # value after 5 years
    terminal_value = future_cashflow['Free Cash Flow'].iloc[-1] * (1 + PERPETUAL_GROWTH_RATE) / (discount_rate - PERPETUAL_GROWTH_RATE)

    # calculate the discounted value of predictions
    future_cashflow['Present Value'] = future_cashflow['Free Cash Flow'] / (1 + discount_rate) ** (future_cashflow.index + 1)
    present_terminal_value = terminal_value / (1 + discount_rate) ** (future_years + 1)

    # ----------------- Equity -----------------

    balance_sheet = stock.balance_sheet.T

    # calculate equity based on predictions
    total_free_cash_flow = future_cashflow['Present Value'].sum() + present_terminal_value
    cash = balance_sheet['Cash Cash Equivalents And Short Term Investments'].dropna()[0]
    debt = balance_sheet['Total Debt'].dropna()[0]
    equity = total_free_cash_flow + cash - debt

    # ----------------- Intrinsic Value -----------------

    shares_outstanding = stock.info['sharesOutstanding']
    return equity / shares_outstanding


# -----------------


AAA_YIELD = get_aaa_yield()

def graham_value(stock: yf.Ticker) -> float:
    '''
    Revised Benjamin Graham Formula for Intrinsic Value.
    Video: https://www.youtube.com/watch?v=mkqyaBYSgiY
    '''
    eps = stock.info['forwardEps']
    growth_rate = get_estimated_growth(stock) * 100
    return (eps * (7 + growth_rate) * 4.4) / (AAA_YIELD * 100)


# -----------------


def lynch_value(stock: yf.Ticker) -> float:
    '''
    Peter Lynch Formula for Intrinsic Value.
    '''
    eps = stock.info['forwardEps']
    dividend_yield = stock.info['dividendYield']
    pe = stock.info['forwardPE']
    ratio = (eps + dividend_yield) / pe
    return stock.fast_info['lastPrice'] * ratio


# ================================ DEBUG ================================


if __name__ == '__main__':
    ticker = 'AAPL'
    stock = yf.Ticker(ticker)

    try:
        ddm = ddm_value(stock)
        print("DDM: ${:.2f}".format(ddm))
    except ValueError as e:
        print(e)

    dcf = dcf_value(stock, 5)
    print("DCF: ${:.2f}".format(dcf))

    graham = graham_value(stock)
    print("Graham: ${:.2f}".format(graham))

    lynch = lynch_value(stock)
    print("Lynch: ${:.2f}".format(lynch))

    weighted_average = dcf * 0.6 + graham * 0.3 + lynch * 0.1

    print("{} value: ${:.2f}".format(ticker, weighted_average))
