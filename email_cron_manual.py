import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from FinApp import processing

load_dotenv()

port = 465
smtp_server = "smtp.gmail.com"
sender = "adxupdates@gmail.com"
password = os.getenv("APPPW")
user_email = os.getenv("EMAILID")

def send_email():
    stocks = ["SPY", "MSFT", "AAPL", "ARM", "VOO", "NVDA", "AVGO", "MU", "META", "JPM", "AMD"]
    email = user_email
    preferences = "macd,donchian,rsi,adx".split(',')
    message = MIMEMultipart("alternative")
    message["Subject"] = "Financial Data"

    message["From"] = sender
    message["To"] = email

    html = """\
<html>
<body>

<h3>Note: Crossovers in the last 3 days are <em><u>highlighted</u></em>.</h3>
<br>
    """
    stock_data_cache = {}
    for stock in stocks:
        if ".NS" in stock:
            html += f"<h1>{stock.replace('.NS', '')}: {processing.get_price(stock)} INR</h1>"
        else:
            html += f"<h1>{stock}: ${processing.get_price(stock)}</h1>"
        if stock not in stock_data_cache:
            stock_data_cache[stock] = {}
            stock_data_cache[stock]['macd'] = processing.last_macd_crossover(stock)
            stock_data_cache[stock]['donchian'] = processing.donchian_channel_position(stock)
            stock_data_cache[stock]['rsi'] = processing.rsi(stock)
            stock_data_cache[stock]['adx'] = processing.adx(stock)
            stock_data_cache[stock]['earnings'] = processing.get_earnings(stock)
        if 'macd' in preferences:
            html += f'<p><b>MACD:</b> {stock_data_cache[stock]["macd"]}</p>'
        if 'donchian' in preferences:
            html += f'<p><b>Donchian:</b> {stock_data_cache[stock]["donchian"]}</p>'
        if 'rsi' in preferences:
            html += f'<p><b>RSI:</b> {stock_data_cache[stock]["rsi"]}</p>'
        if 'adx' in preferences:
            html += f'<p><b>ADX:</b> {stock_data_cache[stock]["adx"]}</p>'
        html += f'<p><b>Earnings:</b> {stock_data_cache[stock]["earnings"]}</p>'
    html += "<body>\n<html>"
    message.attach(MIMEText(html, "html"))
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender, password)
            server.sendmail(sender, email, message.as_string())
    except Exception as e:
        print(e)


send_email()