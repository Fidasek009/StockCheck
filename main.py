# Docs: https://github.com/ranaroussi/yfinance
import yfinance as yf
from colorama import init, Fore
init()

stock = yf.Ticker(input(Fore.YELLOW + "Enter stock code: " + Fore.WHITE))


# ------------------------ 1. Balance sheet ------------------------
# total current assets / total current liabilities > 1
print(Fore.BLUE, "1. Balance sheet:", end='')

balance_sheet = stock.balance_sheet.T
assets = balance_sheet['Current Assets'].dropna()[0]
liabilities = balance_sheet['Current Liabilities'].dropna()[0]
balance_sheet_ratio = assets / liabilities

print(Fore.RED if balance_sheet_ratio < 1 else Fore.GREEN, '{:.2f}'.format(balance_sheet_ratio))


# ------------------------ 2. Income statement ------------------------
# (operating income / total revenue) * 100 > 15
print(Fore.BLUE, "2. Income statement:", end='')

income_stmt = stock.income_stmt.T
income = income_stmt['Operating Income'].dropna()[0]
revenue = income_stmt['Total Revenue'].dropna()[0]
income_ratio = (income / revenue) * 100

print(Fore.RED if income_ratio < 15 else Fore.GREEN, "{:.2f}%".format(income_ratio))


# ------------------------ 3. Cashflow statement ------------------------
# has increasing free cashflow
print(Fore.BLUE, "3. Cashflow statement:", end='')


def adjusted_pct_change(previous, current):
    if previous == 0:
        return float('inf')
    change = (current - previous) / abs(previous)
    return change

cashflow = stock.cash_flow.T['Free Cash Flow'].dropna().iloc[::-1]

for i in range(len(cashflow) - 1):
    change = adjusted_pct_change(cashflow[i], cashflow[i + 1])
    print(Fore.RED if change < 0 else Fore.GREEN, "{:.2f}%".format(change * 100), end=' ')
