import smtplib, ssl
import os
from dotenv import load_dotenv
from FinApp import extensions
from FinApp import processing
from FinApp import model
from FinApp import create_app
from datetime import timedelta, datetime

app = create_app()

load_dotenv()

port = 465
smtp_server = "smtp.gmail.com"
sender = "adxupdates@gmail.com"
password = os.getenv("APPPW")

def should_send_email(user):
    if user.preferences == '': return False
    if user.email_frequency == 'none': return False
    stockExists = model.Stock.query.filter_by(user_id=user.id).first()
    if not stockExists: return False
    if user.email_frequency == 'daily':
        return True
    elif user.email_frequency == 'weekly':
        last_sent = user.last_email_sent
        if last_sent is None or last_sent < datetime.now() - timedelta(weeks=1):
            return True
    elif user.email_frequency == 'monthly':
        last_sent = user.last_email_sent
        if last_sent is None or last_sent < datetime.now() - timedelta(weeks=4):
            return True
    return False

def send_emails():
    users = model.User.query.all()
    for user in users:
        if should_send_email(user):
            send_email(user)
            user.last_email_sent = datetime.now()
    extensions.db.session.commit()
    return "Emails sent", 200

def send_email(user):
    stocks = model.Stock.query.filter_by(user_id=user.id).all()
    email = user.email
    preferences = user.preferences.split(',')
    message = """\
Subject: Financial Data
        """
    message += f'\n'
    stock_data_cache = {}
    for stock in stocks:
        if stock.ticker not in stock_data_cache:
            stock_data_cache[stock.ticker] = {}
            stock_data_cache[stock.ticker]['macd'] = processing.last_macd_crossover(stock.ticker)
            stock_data_cache[stock.ticker]['donchian'] = processing.donchian_channel_position(stock.ticker)
            stock_data_cache[stock.ticker]['rsi'] = processing.rsi(stock.ticker)
            stock_data_cache[stock.ticker]['adx'] = processing.adx(stock.ticker)

        if 'macd' in preferences:
            message += f'{stock_data_cache[stock.ticker]["macd"]}\n'
        if 'donchian' in preferences:
            message += f'{stock_data_cache[stock.ticker]["donchian"]}\n'
        if 'rsi' in preferences:
            message += f'{stock_data_cache[stock.ticker]["rsi"]}\n'
        if 'adx' in preferences:
            message += f'{stock_data_cache[stock.ticker]["adx"]}\n'
        message += '\n'
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender, password)
            server.sendmail(sender, email, message)
    except Exception as e:
        print(e)

with app.app_context():
    send_emails()