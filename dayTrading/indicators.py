from dataclasses import dataclass
import pandas as pd


@dataclass
class Indicators:
    def get(self, data: pd.DataFrame) -> pd.DataFrame:
        '''
        data: ["open", "high", "low", "close", "volume"]
        '''
        raise NotImplementedError


@dataclass
class MinMax:
    buy_window: int
    sell_window: int

    def get(self, data: pd.DataFrame) -> pd.DataFrame:
        prices = data["close"]
        aux = pd.DataFrame(index=prices.index)
        indicators = pd.DataFrame(index=prices.index)
        aux["min"] = prices.rolling(window=self.buy_window).min()
        aux["max"] = prices.rolling(window=self.sell_window).max()
        indicators["buy"] = prices < aux["min"]
        indicators["sell"] = prices > aux["max"]
        return indicators


@dataclass
class BollingerBands:
    buy_window: int
    sell_window: int
    lower_band_multiplier: float
    upper_band_multiplier: float

    def get(self, data: pd.DataFrame) -> pd.DataFrame:
        prices = data["close"]
        aux = pd.DataFrame(index=data.index)
        indicators = pd.DataFrame(index=data.index)
        aux["upper_ema"] = prices.ewm(span=self.sell_window, adjust=False).mean()
        aux["upper_std"] = prices.rolling(window=self.sell_window).std()
        aux["upper_band"] = aux["upper_ema"] + self.lower_band_multiplier * aux["upper_std"]
        aux["lower_ema"] = prices.ewm(span=self.buy_window, adjust=False).mean()
        aux["lower_std"] = prices.rolling(window=self.buy_window).std()
        aux["lower_band"] = aux["lower_ema"] - self.upper_band_multiplier * aux["lower_std"]
        indicators["buy"] = prices < aux["lower_band"]
        indicators["sell"] = prices > aux["upper_band"]
        return indicators


@dataclass
class RSI:
    window: int
    buy_threshold: float
    sell_threshold: float

    def get(self, data: pd.DataFrame) -> pd.DataFrame:
        prices = data["close"]
        indicators = pd.DataFrame(index=data.index)
        price_change = prices.diff()
        gain = price_change.where(price_change > 0, 0)
        loss = -price_change.where(price_change < 0, 0)
        avg_gain = gain.rolling(window=self.window).mean()
        avg_loss = loss.rolling(window=self.window).mean()
        rs = avg_gain / avg_loss
        indicators["rsi"] = 100 - 100 / (1 + rs)
        indicators["buy"] = indicators["rsi"] < self.buy_threshold
        indicators["sell"] = indicators["rsi"] > self.sell_threshold
        return indicators


@dataclass
class MACD:
    short_window: int
    long_window: int
    signal_window: int

    def get(self, data: pd.DataFrame) -> pd.DataFrame:
        prices = data["close"]
        aux = pd.DataFrame(index=data.index)
        indicators = pd.DataFrame(index=data.index)
        short_ema = prices.ewm(span=self.short_window, adjust=False).mean()
        long_ema = prices.ewm(span=self.long_window, adjust=False).mean()
        aux["macd"] = short_ema - long_ema
        aux["signal"] = aux["macd"].ewm(span=self.signal_window, adjust=False).mean()
        indicators["buy"] = aux["macd"] > aux["signal"]
        indicators["sell"] = aux["macd"] < aux["signal"]
        return indicators


if __name__ == '__main__':
    data = pd.read_csv("instruments/history/GOLD.csv", parse_dates=True, index_col="Datetime", date_format="%Y-%m-%d %H:%M:%S%z")
    indicators = RSI(window=14, buy_threshold=30, sell_threshold=70).get(data["close"])

    from matplotlib import pyplot as plt
    plt.plot(data["close"], label="close", color="black")
    plt.plot(indicators["buy"], label="Buy", color="green")
    plt.plot(indicators["sell"], label="Sell", color="red")
    plt.show()
