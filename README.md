# StockCheck
Checks if a stock is worth investing in or if you should avoid it

# TODO:

## 1. Historical Price Data:
Historical stock price data is fundamental for any stock price prediction model. It includes the opening, closing, high, and low prices of the stock over a specific period. This data helps identify trends and patterns in stock price movements.

### Solution
add these columns to training data
- Open
- Close
- High
- Low
- Volume

```
data = stock.history(period="max", actions=False)
```

## 2. Technical Indicators:
Technical indicators are mathematical calculations based on price and volume data that help identify trends, momentum, and potential turning points in a stock's price. Examples include moving averages, Relative Strength Index (RSI), Moving Average Convergence Divergence (MACD), and Bollinger Bands.

### Exponential Moving Average (EMA)
`EMA = Current Price + (Previous EMA * (1 - Smoothing Factor))`
```
data['EMA'] = data['Close'].ewm(span=8, adjust=False).mean()
```

### Relative Strength Index (RSI)
`RSI = 100 – [100 / ( 1 + (Average Gains / Average Losses ) ) ]`
```
# Calculate daily price changes (returns)
data['PriceChange'] = data['Close'].diff()

# Calculate the gains losses
data['Gain'] = data['PriceChange'].apply(lambda x: x if x > 0 else 0)
data['Loss'] = data['PriceChange'].apply(lambda x: abs(x) if x < 0 else 0)

# Calculate RSI from a window of Gain and Loss averages
data['RSI'] = 100 - (100 / (1 + (data['Gain'].rolling(window=8).mean() / data['Loss'].rolling(window=8).mean())))
```

### Bollinger Bands
```
# Calculate the rolling standard deviation
data['Deviation'] = data['Close'].rolling(window=20).std()

# Calculate the upper and lower Bollinger Bands
data['UpperBand'] = data['EMA'] + 2 * data['Deviation']
data['LowerBand'] = data['EMA'] - 2 * data['Deviation']
```

### Stochastic Oscillator
`%K = 100 * ((Latest Close - Lowest Low) / (Highest High - Lowest Low))`
```
data['%K'] = 100 * (data['Close'] - data['Low'].rolling(window=WINDOW).min()) / (data['High'].rolling(window=WINDOW).max() - data['Low'].rolling(window=WINDOW).min())
```


## 4. Fundamental Data:
Consider fundamental data related to the company, such as earnings reports, revenue, profit margins, debt levels, and dividend history. These factors can influence a company's valuation and, consequently, its stock price.


## 5. Market Sentiment:
Sentiment analysis involves gauging the overall sentiment and opinion of market participants about a stock or the market as a whole. Positive or negative sentiment can influence stock prices.


## 6. Economic Indicators:
Economic indicators, such as GDP growth, inflation rates, interest rates, and unemployment data, can impact the overall market and specific industries, affecting stock prices.

- [NASDAQ Stock Screener](https://www.nasdaq.com/market-activity/stocks/screener)

**API calls:**
```
https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=25&recommendation=strong_buy
```

## 7. Industry-specific Factors:
Some industries may be influenced by specific factors like regulatory changes, technological advancements, or geopolitical events. Understanding these industry-specific influences is crucial for accurate predictions.


## 8. News and Events:
Major news and events, such as earnings announcements, mergers and acquisitions, product launches, and legal issues, can cause significant price movements in individual stocks.

### Solution
- get ***news screener*** (eg.: https://www.alphavantage.co/documentation/#news-sentiment)
- When to fetch the news?
- How to translate the news into the dataset?

### Keywords
| HOT | Very Good | Good | OK |
|:-:|:-:|:-:|:-:|
| Positive Endpoint | Positive | Recives | Grants |
| Positive CEO Statement | Top-Line | FDA | Any Large Sum of money |
| Positive Italic Font | Significant | Approval | Investors |
|  | Demonstrates | Benefit(s) / Benefitial | Accepted |
|  | Treatment | Launches | New |
|  | Agreement | Fast Track | Signs |
|  | Partnership | Breakout | Merger |
|  | Collaboration | Acquire(s) | Gain |
|  | Improvement(s) | Acquisition |  |
|  | Successful | Expand / Expansion |  |
|  | Billionare | Contract |  |
|  | Increase | Completes |  |
|  | Awarded | Promising |  |
|  | Primary | Achive(s) / Achivement(s) |  |


## 9. Correlations and Market Indices:
Analyze how a particular stock correlates with broader market indices like the S&P 500 or sector-specific indices. Understanding these relationships can provide valuable insights into overall market trends.


## 10. Market Order Flow:
Monitoring the flow of buy and sell orders (order flow) can reveal real-time market dynamics and supply-demand imbalances, impacting short-term price movements.


## 11. Volatility:
Consider the historical volatility of the stock, which indicates the magnitude of price fluctuations over time. Higher volatility can lead to greater risks and potential rewards.


## 12. Seasonality:
Some stocks exhibit seasonal patterns based on specific events, economic cycles, or consumer behavior.

### Solution
- Put the current quartal into dataset?
