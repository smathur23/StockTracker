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
    