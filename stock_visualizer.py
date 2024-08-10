import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from analysis_fetcher import Analysis


def balance_sheet(stock: yf.Ticker) -> float:
    balance_sheet = stock.balance_sheet.T
    assets = balance_sheet['Current Assets'].dropna()[0]
    liabilities = balance_sheet['Current Liabilities'].dropna()[0]
    return assets / liabilities


def income_statement(stock: yf.Ticker) -> float:
    income_stmt = stock.income_stmt.T
    income = income_stmt['Operating Income'].dropna()[0]
    revenue = income_stmt['Total Revenue'].dropna()[0]
    return income / revenue


def cashflow_statement(stock: yf.Ticker) -> list[float]:
    def adjusted_pct_change(previous, current):
        if previous == 0:
            return float('inf')
        change = (current - previous) / abs(previous)
        return change

    cashflow = stock.cash_flow.T['Free Cash Flow'].dropna().iloc[::-1]
    changes = [adjusted_pct_change(cashflow[i], cashflow[i + 1]) for i in range(len(cashflow) - 1)]
    return changes

def intrinsic_value(stock: yf.Ticker) -> float:
    price_targets = Analysis(stock).analyst_price_targets
    return price_targets['low']


def create_plot(stock: yf.Ticker):
    fig = plt.figure(figsize=(8, 5))
    fig.suptitle(f"{stock.info['shortName']} ({stock.ticker})", fontsize=16)

    ax1 = fig.add_subplot(2, 2, 1)
    ax2 = fig.add_subplot(2, 2, 2)
    ax3 = fig.add_subplot(2, 2, 3)
    ax4 = fig.add_subplot(2, 2, 4)

    ax3.axis('off')
    ax4.axis('off')

    # 1. plot stock price over 5 years
    five_years = stock.history(period="5y", interval="1mo")
    if five_years.empty:
        five_years = stock.history(period="max", interval="1mo")
        five_y_title = 'Since Start'
    else:
        five_y_title = '5 years'

    ax1.plot(five_years['Close'])
    ax1.set_title(five_y_title)

    # 2. plot stock price over 1 year
    one_year = stock.history(period="1y", interval="5d")
    ax2.plot(one_year['Close'])
    ax2.set_title('1 year')

    # 3. stock analysis

    # 3.1. balance sheet
    ax3.text(0, 0.7, 'Balance Sheet', fontsize=12)
    _bs = balance_sheet(stock)
    ax3.text(0.8, 0.7, f'{_bs:.2f}', fontsize=12, color='green' if _bs > 1 else 'red')

    # 3.2. income statement
    ax3.text(0, 0.5, 'Income Statement', fontsize=12)
    _is = income_statement(stock)
    ax3.text(0.8, 0.5, f'{_is * 100:.2f}%', fontsize=12, color='green' if _is > 0.15 else 'red')

    # 3.3. cashflow statement
    ax3.text(0, 0.3, 'Cashflow Statement', fontsize=12)
    _cs = cashflow_statement(stock)
    for i, change in enumerate(_cs):
        ax3.text(0.8 + (0.4 * i), 0.3, f'{change * 100:.2f}%', fontsize=12, color='green' if change > 0 else 'red')

    # 3.4. intrinsic value
    ax3.text(0, 0.1, 'Intrinsic Value (low)', fontsize=12)
    _iv = intrinsic_value(stock)
    ax3.text(0.8, 0.1, f'${_iv:.2f}', fontsize=12, color='green' if _iv > stock.fast_info['lastPrice'] else 'red')

    # 3.5. stock industry
    ax3.text(0, -0.1, 'Industry', fontsize=12)
    ax3.text(0.8, -0.1, stock.info['industry'], fontsize=12)

    plt.show()


if __name__ == '__main__':
    tickers = pd.read_csv('instruments/filtered_instruments.csv')['shortName']

    for ticker in tickers:
        stock = yf.Ticker(ticker)
        create_plot(stock)
