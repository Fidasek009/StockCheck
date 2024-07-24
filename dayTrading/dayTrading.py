from dataclasses import dataclass
import pandas as pd
from indicators import Indicators
from matplotlib import pyplot as plt

LONG = True
SHORT = False

# Trading 212 rates: https://www.trading212.com/terms/cfd
@dataclass
class StaticParams:
    data: pd.DataFrame  # ["open", "high", "low", "close", "volume"]
    initial_cash: float
    min_cash: float
    leverage: int
    trade_cooldown: int


@dataclass
class DynamicParams:
    stop_loss_pct: float
    take_profit_pct: float
    investment_pct: float
    indicators: Indicators


class Position:
    '''
    attributes:
    - is_long: bool
    - open_price: float
    - upper_bound_price: float
    - lower_bound_price: float
    - leverage: int
    - cash: float
    '''
    def __init__(self, is_long, cash, open_price, stop_loss_pct, take_profit_pct, leverage):
        self.is_long = is_long
        self.open_price = open_price
        self.size = cash * leverage
        self.initial_margin = cash
        self.upper_bound_price = open_price * (1 + (take_profit_pct if is_long else stop_loss_pct))
        self.lower_bound_price = open_price * (1 - (stop_loss_pct if is_long else take_profit_pct))


    def try_close(self, price) -> float | None:
        if self.lower_bound_price < price < self.upper_bound_price:
            return None

        price_change_pct = (price - self.open_price) / self.open_price
        profit = self.size * price_change_pct * (1 if self.is_long else -1)
        return self.initial_margin + profit


class Portfolio:
    '''
    attributes:
    - sp: StaticParams
    - dp: DynamicParams
    - cash: float
    - positions: List[Position]
    '''
    def __init__(self, sp: StaticParams, dp: DynamicParams):
        self.cash = sp.initial_cash
        self.sp = sp
        self.dp = dp
        self.positions = []

    def tick(self, price) -> None:
        for p in self.positions:
            close_cash = p.try_close(price)
            if close_cash is not None:
                self.cash += close_cash
                self.positions.remove(p)

    def open_position(self, is_long, open_price) -> None:
        if self.cash <= self.sp.min_cash:
            return

        investment_cash = self.cash * self.dp.investment_pct
        p = Position(is_long, investment_cash, open_price, self.dp.stop_loss_pct, self.dp.take_profit_pct, self.sp.leverage)
        self.positions.append(p)
        self.cash -= investment_cash


class Simulation:
    '''
    attributes:
    - sp: StaticParams
    - dp: DynamicParams
    - portfolio: Portfolio
    - indicators: pd.DataFrame - ["buy", "sell"]
    '''
    def __init__(self, sp: StaticParams, dp: DynamicParams):
        self.sp = sp
        self.dp = dp
        self.portfolio = Portfolio(sp, dp)
        self.indicators = dp.indicators.get(sp.data)
        self.cooldown = 0

    def run(self):
        for i, price in enumerate(self.sp.data["close"]):
            self.portfolio.tick(price)
            if self.cooldown == 0:
                if self.indicators["buy"][i]:
                    self.portfolio.open_position(LONG, price)
                if self.indicators["sell"][i]:
                    self.portfolio.open_position(SHORT, price)
                self.cooldown = self.sp.trade_cooldown
            else:
                self.cooldown -= 1

        return self.portfolio.cash

    def visualize(self):
        close_prices = self.sp.data["close"]
        buy_signals = self.indicators["buy"] * close_prices
        sell_signals = self.indicators["sell"] * close_prices

        plt.plot(close_prices, label='close Prices')
        plt.plot(buy_signals, 'g^', label='Buy Signals')
        plt.plot(sell_signals, 'rv', label='Sell Signals')
        plt.legend()
        plt.show()


# TESTS
if __name__ == '__main__':
    p = Position(LONG, 1000, 100, 0.05, 0.1, 5)
    assert p.try_close(105) is None
    assert p.try_close(111) == 1550
    assert p.try_close(94) == 700

    p = Position(SHORT, 1000, 100, 0.05, 0.1, 5)
    assert p.try_close(95) is None
    assert p.try_close(89) == 1550
    assert p.try_close(106) == 700

    data = pd.read_csv("instruments/history/GOLD.csv", parse_dates=True, index_col="Datetime", date_format="%Y-%m-%d %H:%M:%S%z")
    data.columns = data.columns.str.lower()

    sp = StaticParams(
        data=data,
        initial_cash=1000,
        min_cash=100,
        leverage=5,
        trade_cooldown=60
    )

    from indicators import RSI

    dp = DynamicParams(
        stop_loss_pct=0.05,
        take_profit_pct=0.1,
        investment_pct=0.5,
        indicators=RSI(window=60, buy_threshold=30, sell_threshold=70)
    )

    s = Simulation(sp, dp)
    print(s.run())
    s.visualize()
