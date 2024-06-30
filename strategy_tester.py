import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import multiprocessing as mp
from itertools import product

STOCK = "^GSPC"
# STOCK = "AAPL"
INITIAL_CASH = 500      # starting ammount of money
MONTHLY_DEPOSIT = 0     # money deposited every month
YEARS = 10               # number of years to simulate
# avoid exploding gradinets
MIN_BUY_BALANCE = 20     # minimum ammount of money needed to buy
MIN_SELL_PRICE = 20      # minimum ammount of stock needed to sell
MIN_SELL_AMMOUNT = 0.01 # minimum ammount of stock needed to sell

# avoid overtrading
BUY_COOLDOWN = 5        # number of days to wait before buying again
SELL_COOLDOWN = 5       # number of days to wait before selling again

TRADING_YEAR = 252      # number of trading days in a year
TRADING_MONTH = 21      # number of trading days in a month

# =============================================================================

class Portfolio:
    """
    `initial_cash`:     starting ammount of money
    `cash`:             current ammount of money
    `stock`:            current ammount of stock
    `months`:           number of months passed since the start
    `monthly_deposit`:  money deposited every month
    `start_price`:      price of the stock at the start
    `current_price`:    current price of the stock
    `buys`:             number of buys
    `sells`:            number of sells
    `buy_cooldown`:     if > 0, can't buy
    `sell_cooldown`:    if > 0, can't sell
    """

    def __init__(self, cash, stock, monthly_deposit):
        self.initial_cash = cash
        self.cash = cash
        self.stock = stock
        self.months = 0
        self.monthly_deposit = monthly_deposit
        self.start_price = None
        self.current_price = None
        self.buys = 0
        self.sells = 0
        self.buy_cooldown = 0
        self.sell_cooldown = 0


    def buy(self, stock_price: float, percent: float):
        # don't buy if there isn't enough money
        if self.cash < MIN_BUY_BALANCE:
            return False

        # don't buy if the cooldown isn't over
        if self.buy_cooldown > 0:
            return False

        bought = self.cash * percent / stock_price
        self.cash -= bought * stock_price
        self.stock += bought
        self.buys += 1
        self.buy_cooldown = BUY_COOLDOWN
        return True

    def sell(self, stock_price: float, percent: float):
        # don't sell if there isn't enough stock
        if self.stock * stock_price < MIN_SELL_PRICE:
            return False
        
        # don't sell if the cooldown isn't over
        if self.sell_cooldown > 0:
            return False

        sold = self.stock * percent
        self.cash += sold * stock_price
        self.stock -= sold
        self.sells += 1
        self.sell_cooldown = SELL_COOLDOWN
        return True

    def new_month(self):
        self.cash += self.monthly_deposit
        self.months += 1

    def performance(self) -> float:
        # raw profit without monthly deposits
        profit_cash = self.cash + self.stock * self.current_price - self.monthly_deposit * self.months
        profit = 100 * profit_cash / self.initial_cash

        # profit of the stock without trading
        baseline = 100 * self.current_price / self.start_price

        # return the profit relative to the baseline
        return (100 * profit / baseline) - 100

    def show(self) -> str:
        print(f"Time: {self.months}m ({round(self.months / 12)}y)")
        print(f"Cash: {round(self.cash, 3)}$")
        print(f"Stocks: {round(self.stock, 3)} ({round(self.stock * self.current_price, 3)}$)")
        # raw profit without monthly deposits
        profit = self.cash + self.stock * self.current_price - self.monthly_deposit * self.months
        # profit of the stock
        baseline = self.current_price / self.start_price * 100
        print(f"Profit: {round(100 * profit / self.initial_cash, 3)}% (baseline: {round(baseline, 3)}%)")
        print(f"Performance: {round(self.performance(), 3)}%")
        print(f"Buys/Sells: {self.buys}/{self.sells}")

# =============================================================================

class StrategyTester:
    """
    `buy_window`:       buy if the price is the lowest in the last N days
    `buy_percent`:      % of currently held cash to buy with
    `sell_window`:      sell if the price is the highest in the last N days
    `sell_percent`:     % of currently held stock to sell
    """

    def __init__(self, buy_window, buy_percent, sell_window, sell_percent, sell_bb_multiplier, buy_bb_multiplier):
        self.buy_window = buy_window
        self.buy_percent = buy_percent
        self.sell_window = sell_window
        self.sell_percent = sell_percent
        # bollinger bands
        self.sell_bb_multiplier = sell_bb_multiplier
        self.buy_bb_multiplier = buy_bb_multiplier
        # for plotting
        self.buy_points = []
        self.sell_points = []

    def simulate(self, portfolio: Portfolio, prices: pd.DataFrame, years: int):
        start_idx = max([len(prices) - years * TRADING_YEAR, self.buy_window, self.sell_window])
        portfolio.start_price = prices[start_idx]
        portfolio.current_price = prices[-1]

        # calculate buy and sell indicators
        indicators = self.bb_indicators(prices)

        for i in range(start_idx, len(prices)):
            # decrease cooldowns
            portfolio.buy_cooldown -= 1
            portfolio.sell_cooldown -= 1

            if i % TRADING_MONTH == 0:
                portfolio.new_month()

            if prices[i] <= indicators["buy"][i] and portfolio.buy(prices[i], self.buy_percent):
                self.buy_points.append((prices.index[i], prices[i]))

            if prices[i] >= indicators["sell"][i] and portfolio.sell(prices[i], self.sell_percent):
                self.sell_points.append((prices.index[i], prices[i]))

    def show_params(self):
        print(f"🟩🪟 : {self.buy_window}")
        print(f"🟥🪟 : {self.sell_window}")
        print(f"🟩 %: {self.buy_percent}")
        print(f"🟥 %: {self.sell_percent}")
        print(f"🟩 BB multiplier: {self.buy_bb_multiplier}")
        print(f"🟥 BB multiplier: {self.sell_bb_multiplier}")
    

    def minmax_indicators(self, prices: pd.DataFrame) -> pd.DataFrame:
        indicators = pd.DataFrame(index=prices.index)
        indicators["buy"] = prices.rolling(window=self.buy_window).min()
        indicators["sell"] = prices.rolling(window=self.sell_window).max()
        return indicators


    def bb_indicators(self, prices: pd.DataFrame) -> pd.DataFrame:
        indicators = pd.DataFrame(index=prices.index)
        indicators["sell_ema"] = prices.ewm(span=self.sell_window, adjust=False).mean()
        indicators["sell_std"] = prices.rolling(window=self.sell_window).std()
        indicators["sell"] = indicators["sell_ema"] + self.sell_bb_multiplier * indicators["sell_std"]
        indicators["buy_ema"] = prices.ewm(span=self.buy_window, adjust=False).mean()
        indicators["buy_std"] = prices.rolling(window=self.buy_window).std()
        indicators["buy"] = indicators["buy_ema"] - self.buy_bb_multiplier * indicators["buy_std"]
        return indicators

# =============================================================================

def simulate_p(data, buy_window, buy_percent, sell_window, sell_percent, sell_bb_multiplier, buy_bb_multiplier):
    simulator = StrategyTester(
        buy_window=buy_window,
        buy_percent=buy_percent,
        sell_window=sell_window,
        sell_percent=sell_percent,
        sell_bb_multiplier=sell_bb_multiplier,
        buy_bb_multiplier=buy_bb_multiplier
    )
    portfolio = Portfolio(INITIAL_CASH, 0, MONTHLY_DEPOSIT)
    simulator.simulate(portfolio, data, YEARS)
    return portfolio.performance(), simulator, portfolio


def permutate_mp(data, params: list[list]):
    count = np.prod([len(param) for param in params])
    print(f"Simulating permutations: {count}")

    with mp.Pool(mp.cpu_count() - 4) as pool:
        results = []
        pbar = tqdm(total=count)
    
        def update(result):
            results.append(result)
            pbar.update()

        for param_set in product(*params):
            pool.apply_async(simulate_p, args=(data, *param_set), callback=update)

        pool.close()
        pool.join()
        pbar.close()

    return results


def validate(results: list[tuple[float, StrategyTester, Portfolio]]):
    validate_data = yf.Ticker(STOCK).history(period=f"max", actions=False)
    years = len(validate_data) // TRADING_YEAR
    validate_results: tuple[float, StrategyTester, Portfolio] = []

    # validate top 100 results
    for res in results[:100]:
        portfolio = Portfolio(INITIAL_CASH, 0, MONTHLY_DEPOSIT)
        res[1].simulate(portfolio, validate_data["Close"], years)
        validate_results.append((portfolio.performance(), res[1], portfolio))

    return validate_results

# =============================================================================

def show_top_n(results: list[tuple[float, StrategyTester, Portfolio]], n: int, data: pd.DataFrame):
    results.sort(key=lambda x: x[0] ,reverse=True)

    for i in range(min(n, len(results))):
        print(f"----- {i} -----")
        results[i][2].show()
        print("-----")
        results[i][1].show_params()

    # plot the best result
    draw_best(results[0][1], data)


def draw_best(strategy: StrategyTester, data: pd.DataFrame):
    plt.plot(data["Close"], color='black')

    # buy and sell indicators
    for point in strategy.buy_points:
        plt.scatter(point[0], point[1], color='green', label='Buy Signal', marker='^', alpha=1)
    for point in strategy.sell_points:
        plt.scatter(point[0], point[1], color='red', label='Sell Signal', marker='v', alpha=1)

    # bollinger bands
    data["sell_ema"] = data["Close"].ewm(span=strategy.sell_window, adjust=False).mean()
    data["sell_std"] = data["Close"].rolling(window=strategy.sell_window).std()
    data["sell"] = data["sell_ema"] + strategy.sell_bb_multiplier * data["sell_std"]
    plt.plot(data["sell"], color='orange')

    data["buy_ema"] = data["Close"].ewm(span=strategy.buy_window, adjust=False).mean()
    data["buy_std"] = data["Close"].rolling(window=strategy.buy_window).std()
    data["buy"] = data["buy_ema"] - strategy.buy_bb_multiplier * data["buy_std"]
    plt.plot(data["buy"], color='purple')

    plt.show()


def main():
    print("Downloading data...", end=" ")
    stock = yf.Ticker(STOCK)
    data = stock.history(period=f"{YEARS + 1}y", actions=False)
    print("Done")

    buy_windows = [5, 10, 21, 63, 126, 252]
    sell_windows = [5, 10, 21, 63, 126, 252]

    buy_percents = [0.1, 0.25, 0.5, 0.75, 1]
    sell_percents = [0.1, 0.25, 0.5, 0.75, 1]

    sell_bb_multiplier = [1, 1.5, 2, 2.5, 3]
    buy_bb_multiplier = [1, 1.5, 2, 2.5, 3]

    # buy_windows = [10]
    # buy_percents = [1]
    # sell_windows = [3]
    # sell_percents = [1]
    # sell_bb_multiplier = [1.5]
    # buy_bb_multiplier = [1.5]

    params = [buy_windows, buy_percents, sell_windows, sell_percents, sell_bb_multiplier, buy_bb_multiplier]

    res = permutate_mp(data["Close"], params)
    # print("Validating top 100 results...", end=" ")
    # validate_res = validate(res)
    # print("Done")
    show_top_n(res, 10, data)


if __name__ == "__main__":
    main()
