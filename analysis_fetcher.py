'''
Extension of yfinance to fetch some analyst data.
'''
import yfinance as yf
import pandas as pd


class Analysis:
    def __init__(self, stock: yf.Ticker) -> None:
        self._stock = stock
        self._symbol = stock.ticker

        # In quoteSummary the 'earningsTrend' module contains most of the data below.
        # The format of data is not optimal so each function will process it's part of the data.
        # This variable works as a cache.
        self._earnings_trend = None

        self._earnings_estimate = None
        self._revenue_estimate = None
        self._earnings_history = None
        self._eps_trend = None
        self._eps_revisions = None
        self._growth_estimates = None
        self._analyst_price_targets = None

    def _fetch_earnings_trend(self) -> None:
        data = self._stock._quote._fetch(proxy=self._stock.proxy, modules=['earningsTrend'])
        self._earnings_trend = data['quoteSummary']['result'][0]['earningsTrend']['trend'] if data else []

    @property
    def earnings_estimate(self) -> pd.DataFrame:
        if self._earnings_estimate is not None:
            return self._earnings_estimate

        if self._earnings_trend is None:
            self._fetch_earnings_trend()

        data_dict = {
            'avg': [],
            'low': [],
            'high': [],
            'yearAgoEps': [],
            'numberOfAnalysts': [],
            'growth': []
        }
        periods = []

        for item in self._earnings_trend[:-2]:
            periods.append(item['period'])
            earnings_estimate = item.get('earningsEstimate', {})

            for key in data_dict.keys():
                data_dict[key].append(earnings_estimate.get(key, {}).get('raw', None))

        self._earnings_estimate = pd.DataFrame(data_dict, index=periods).T
        return self._earnings_estimate

    @property
    def revenue_estimate(self) -> pd.DataFrame:
        if self._revenue_estimate is not None:
            return self._revenue_estimate

        if self._earnings_trend is None:
            self._fetch_earnings_trend()

        data_dict = {
            'avg': [],
            'low': [],
            'high': [],
            'yearAgoRevenue': [],
            'numberOfAnalysts': [],
            'growth': []
        }
        periods = []

        for item in self._earnings_trend[:-2]:
            periods.append(item['period'])
            revenue_estimate = item.get('revenueEstimate', {})

            for key in data_dict.keys():
                data_dict[key].append(revenue_estimate.get(key, {}).get('raw', None))

        self._revenue_estimate = pd.DataFrame(data_dict, index=periods).T
        return self._revenue_estimate

    @property
    def earnings_history(self) -> pd.DataFrame:
        if self._earnings_history is not None:
            return self._earnings_history
        
        earnings_history = self._stock._quote._fetch(proxy=self._stock.proxy, modules=['earningsHistory'])
        earnings_history = earnings_history['quoteSummary']['result'][0]['earningsHistory']['history'] if earnings_history else []

        data_dict = {
            'epsActual': [],
            'epsEstimate': [],
            'epsDifference': [],
            'surprisePercent': [],
            'quarter': []
        }
        periods = []

        for item in earnings_history:
            periods.append(item['period'])

            for key in data_dict.keys():
                data_dict[key].append(item.get(key, {}).get('raw', None))

        self._earnings_history = pd.DataFrame(data_dict, index=periods).T
        return self._earnings_history

    @property
    def eps_trend(self) -> pd.DataFrame:
        if self._eps_trend is not None:
            return self._eps_trend
        
        if self._earnings_trend is None:
            self._fetch_earnings_trend()

        data_dict = {
            'current': [],
            '7daysAgo': [],
            '30daysAgo': [],
            '60daysAgo': [],
            '90daysAgo': []
        }
        periods = []

        for item in self._earnings_trend[:-2]:
            periods.append(item['period'])
            eps_trend = item.get('epsTrend', {})

            for key in data_dict.keys():
                data_dict[key].append(eps_trend.get(key, {}).get('raw', None))

        self._eps_trend = pd.DataFrame(data_dict, index=periods).T
        return self._eps_trend

    @property
    def eps_revisions(self) -> pd.DataFrame:
        if self._eps_revisions is not None:
            return self._eps_revisions
        
        if self._earnings_trend is None:
            self._fetch_earnings_trend()
        
        data_dict = {
            'upLast7days': [],
            'upLast30days': [],
            'downLast30days': [],
            'downLast90days': []
        }
        periods = []

        for item in self._earnings_trend[:-2]:
            periods.append(item['period'])
            eps_revisions = item.get('epsRevisions', {})

            for key in data_dict.keys():
                data_dict[key].append(eps_revisions.get(key, {}).get('raw', None))

        self._eps_revisions = pd.DataFrame(data_dict, index=periods).T
        return self._eps_revisions

    @property
    def growth_estimates(self) -> pd.DataFrame:
        if self._growth_estimates is not None:
            return self._growth_estimates

        if self._earnings_trend is None:
            self._fetch_earnings_trend()

        trends = self._stock._quote._fetch(proxy=self._stock.proxy, modules=['industryTrend', 'sectorTrend', 'indexTrend'])
        if trends is None:
            return pd.DataFrame()

        data_dict = {
            '0q': [],
            '+1q': [],
            '0y': [],
            '+1y': [],
            '+5y': [],
            '-5y': []
        }

        # If there is no data for a period, fill it with None
        empty_trend = [{'period': key, 'growth': None} for key in data_dict.keys()]
        industry_trend = trends['quoteSummary']['result'][0]['industryTrend']['estimates'] or empty_trend
        sector_trend = trends['quoteSummary']['result'][0]['sectorTrend']['estimates'] or empty_trend
        index_trend = trends['quoteSummary']['result'][0]['indexTrend']['estimates'] or empty_trend

        for item in self._earnings_trend:
            period = item['period']
            data_dict[period].append(item.get('growth', {}).get('raw', None))

        for item in industry_trend:
            period = item['period']
            data_dict[period].append(item.get('growth', None))

        for item in sector_trend:
            period = item['period']
            data_dict[period].append(item.get('growth', None))

        for item in index_trend:
            period = item['period']
            data_dict[period].append(item.get('growth', None))

        cols = ['stock', 'industry', 'sector', 'index']
        self._growth_estimates = pd.DataFrame(data_dict, index=cols).T
        return self._growth_estimates

    @property
    def analyst_price_targets(self) -> dict:
        if self._analyst_price_targets is not None:
            return self._analyst_price_targets

        data = self._stock._quote._fetch(proxy=self._stock.proxy, modules=['financialData'])
        data = data['quoteSummary']['result'][0]['financialData'] if data else {}

        keys = [
            ('currentPrice', 'current'),
            ('targetLowPrice', 'low'),
            ('targetHighPrice', 'high'),
            ('targetMeanPrice', 'mean'),
            ('targetMedianPrice', 'median'),
        ]

        return {newKey: data.get(oldKey, None) for oldKey, newKey in keys}


# ================= TESTS =================

if __name__ == '__main__':
    stock = yf.Ticker('AAPL')
    analysis = Analysis(stock)

    print('Earnings Estimate:\n', analysis.earnings_estimate)
    print('\nRevenue Estimate:\n', analysis.revenue_estimate)
    print('\nEarnings History:\n', analysis.earnings_history)
    print('\nEPS Trend:\n', analysis.eps_trend)
    print('\nEPS Revisions:\n', analysis.eps_revisions)
    print('\nGrowth Estimates:\n', analysis.growth_estimates)
    print('\nAnalyst Price Targets:\n', analysis.analyst_price_targets)
