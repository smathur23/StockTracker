import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime

'''
    This function will return the most recent price for a given stock ticker.
'''
def get_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        return round(stock.history(period='1d')['Close'].iloc[-1], 2)
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return 0

'''
    This function will return the most recent percent change for a stock price for a given stock ticker.
'''
def pct_change(symbol):
    try:
        stock = yf.Ticker(symbol)
        history = stock.history(period='2d')
        if len(history) < 2:
            raise ValueError("Not enough data to calculate percent change")
        
        close_prices = history['Close']
        pct_change = ((close_prices.iloc[-1] - close_prices.iloc[-2]) / close_prices.iloc[-2]) * 100
        return round(pct_change, 2)
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return 0

'''
    This function will return the most recent MACD crossover signal for a given stock ticker.
'''
def last_macd_crossover(ticker):
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - pd.DateOffset(years=1)).strftime('%Y-%m-%d')
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    
    macd = ta.macd(stock_data['Close'])
    stock_data = pd.concat([stock_data, macd], axis=1).dropna()
    
    stock_data['MACD_Cross_Signal'] = stock_data['MACD_12_26_9'] - stock_data['MACDs_12_26_9']
    stock_data['Signal'] = stock_data['MACD_Cross_Signal'].apply(lambda x: 'Bullish' if x > 0 else 'Bearish')
    stock_data['Crossover'] = stock_data['Signal'].ne(stock_data['Signal'].shift())

    crossovers = stock_data[stock_data['Crossover']]
    
    if crossovers.empty:
        return f"No MACD crossovers found for {ticker} in the past year."
    else:
        last_crossover = crossovers.iloc[-1]
        last_crossover_date = last_crossover.name.strftime('%Y-%m-%d')
        crossover_signal = last_crossover['Signal']
        return f"{crossover_signal} MACD crossover for {ticker} on {last_crossover_date}."


'''
    This function will return the current position of a stock price relative to its Donchian Channel.
'''
def donchian_channel_position(ticker, lookback_period=20):
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - pd.DateOffset(days=lookback_period*2)).strftime('%Y-%m-%d')
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    
    donchian = ta.donchian(stock_data['High'], stock_data['Low'])
    stock_data = pd.concat([stock_data, donchian], axis=1).dropna()

    latest_data = stock_data.iloc[-1]
    current_price = latest_data['Close']
    upper_band = latest_data['DCU_20_20']
    lower_band = latest_data['DCL_20_20']
    middle_band = (upper_band + lower_band) / 2

    if current_price > upper_band:
        position = "above"
    elif current_price < lower_band:
        position = "below"
    elif current_price >= middle_band:
        position = "in the upper half of"
    else:
        position = "in the lower half of"

    return f"The current price of {ticker} is {position} the Donchian Channel."


'''
    This method returns the most recent RSI of a stock and determines if it is overbought or oversold.
'''
def rsi(ticker):
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - pd.DateOffset(days=200)).strftime('%Y-%m-%d')  
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    
    rsi = ta.rsi(stock_data['Close'])
    stock_data = pd.concat([stock_data, rsi], axis=1).dropna()
    
    latest_data = stock_data.iloc[-1]
    current_rsi = round(latest_data['RSI_14'], 2)
    
    if current_rsi > 70:
        return f"{ticker} is overbought with an RSI of {current_rsi}."
    elif current_rsi < 30:
        return f"{ticker} is oversold with an RSI of {current_rsi}."
    else:
        return f"{ticker} has an RSI of {current_rsi}."


'''
    This method returns the most recent ADX of a stock and determines if it is trending or not along
    with returning the most recent directional crossover.
'''
def adx(ticker):
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - pd.DateOffset(days=300)).strftime('%Y-%m-%d')  
    stock_data = yf.download(ticker, start=start_date, end=end_date)

    adx = ta.adx(stock_data['High'], stock_data['Low'], stock_data['Close'])
    stock_data = pd.concat([stock_data, adx], axis=1).dropna()

    latest_data = stock_data.iloc[-1]
    current_adx = round(latest_data['ADX_14'], 2)

    res = ""

    if current_adx < 25:
        res += f"{ticker} is showing a weak trend with an ADX of {current_adx}."
    elif current_adx < 50:
        res += f"{ticker} is trending with an ADX of {current_adx}."
    else:
        res += f"{ticker} is showing a very strond trend with an ADX of {current_adx}."

    stock_data['ADX_Cross'] = stock_data['DMP_14'] - stock_data['DMN_14']
    stock_data['Signal'] = stock_data['ADX_Cross'].apply(lambda x: '+DI' if x > 0 else '-DI')
    stock_data['Crossover'] = stock_data['Signal'].ne(stock_data['Signal'].shift())

    crossovers = stock_data[stock_data['Crossover']]

    if not crossovers.empty:
        last_crossover = crossovers.iloc[-1]
        last_crossover_date = last_crossover.name.strftime('%Y-%m-%d')
        crossover_signal = last_crossover['Signal']
        res += f" {crossover_signal} ADX crossover for {ticker} on {last_crossover_date}."

    return res