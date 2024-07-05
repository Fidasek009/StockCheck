# Docs: https://github.com/ranaroussi/yfinance
import yfinance as yf
from colorama import init, Fore
from math import isnan
init()

stock = yf.Ticker(input(Fore.YELLOW + "Enter stock code: " + Fore.WHITE))


# ------------------------ 1. Balance sheet ------------------------
# total current assets / total current liabilities > 1
print(Fore.BLUE, "1. Balance sheet:", end='')

BS = stock.balance_sheet
currentYear = BS.keys()[0]
currentAssets = BS[currentYear].loc['Current Assets']
currentLiabilities = BS[currentYear].loc['Current Liabilities']
balanceSheet = round(currentAssets/currentLiabilities, 3)

print(Fore.RED if balanceSheet < 1 else Fore.GREEN, balanceSheet)


# ------------------------ 2. Income statement ------------------------
# (operating income / total revenue) * 100 > 15
print(Fore.BLUE, "2. Income statement:", end='')

IS = stock.income_stmt
currentYear = IS.keys()[0]
operatingIncome = IS[currentYear].loc['Operating Income']
totalRevenue = IS[currentYear].loc['Total Revenue']
incomeStatement = round((operatingIncome/totalRevenue)*100, 2)

print(Fore.RED if incomeStatement < 15 else Fore.GREEN, f"{incomeStatement} %")


# ------------------------ 3. Cashflow statement ------------------------
# has increasing free cashflow
print(Fore.BLUE, "3. Cashflow statement:", end='')
CF = stock.cash_flow
yearlyCashFlow = [CF[year].loc['Free Cash Flow'] for year in CF.keys()]

for i in range(1, len(yearlyCashFlow)):
    if isnan(yearlyCashFlow[i]):
        continue

    diff = round(100/(yearlyCashFlow[i]/(yearlyCashFlow[i-1] - yearlyCashFlow[i])), 2)
    print(Fore.RED if diff < 0 else Fore.GREEN, f"{diff}%", end=' ')
