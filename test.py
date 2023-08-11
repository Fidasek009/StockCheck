import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt


stock = yf.Ticker("^GSPC")

# Load data
data = stock.history(period="max", actions=False)

WINDOW = 8

# -----------------------Exponential Moving Average--------------------------
data['EMA'] = data['Close'].ewm(span=WINDOW, adjust=False).mean()



# -----------------------Relative Strength Index--------------------------

# Calculate daily price changes (returns)
data['PriceChange'] = data['Close'].diff()

# Calculate the gains losses
data['Gain'] = data['PriceChange'].apply(lambda x: x if x > 0 else 0)
data['Loss'] = data['PriceChange'].apply(lambda x: abs(x) if x < 0 else 0)

# Calculate RSI from a window of Gain and Loss averages
data['RSI'] = 100 - (100 / (1 + (data['Gain'].rolling(window=WINDOW).mean() / data['Loss'].rolling(window=WINDOW).mean())))


# -----------------------Boilinger Bands--------------------------

# Calculate the rolling standard deviation
data['Deviation'] = data['Close'].rolling(window=WINDOW).std()


# Calculate the upper and lower Bollinger Bands
data['UpperBand'] = data['EMA'] + 2 * data['Deviation']
data['LowerBand'] = data['EMA'] - 2 * data['Deviation']


# -----------------------Stochastic Oscillator--------------------------

# Calculate the %K Stochastic Oscillator
data['%K'] = 100 * (data['Close'] - data['Low'].rolling(window=WINDOW).min()) / (data['High'].rolling(window=WINDOW).max() - data['Low'].rolling(window=WINDOW).min())











# ======================= GRAPH ==========================

# Plot the closing prices, Bollinger Bands, and SMA
plt.figure(figsize=(16, 9))
plt.plot(data['Close'], label='Closing Price', color='blue')
plt.plot(data['EMA'], label='Exponential Moving Average', color='green')
plt.plot(data['RSI'], label='Relative Strength Index', color='yellow')
plt.plot(data['%K'], label='Stochastic Oscillator', color='purple')

plt.plot(data['UpperBand'], label='Upper Bollinger Band', color='red', linestyle='dashed')
plt.plot(data['LowerBand'], label='Lower Bollinger Band', color='red', linestyle='dashed')
plt.fill_between(data.index, data['UpperBand'], data['LowerBand'], color='gray', alpha=0.2)

plt.xlabel('Date')
plt.ylabel('Price')
plt.title('TSLA')
plt.legend()
plt.show()

exit()
