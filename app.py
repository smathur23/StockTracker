from flask import Flask, jsonify, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
import yfinance as yf
import smtplib, ssl
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

port = 465
smtp_server = "smtp.gmail.com"
sender = "adxupdates@gmail.com"
password = os.getenv("APPPW")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stocks.db'
db = SQLAlchemy(app)

def get_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        return round(stock.history(period='1d')['Close'].iloc[-1], 2)
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return 0

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

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False)
    recent_price = db.Column(db.Float, default=0.0)  # Change to db.Float
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    percent_change = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return '<Stock %r>' % self.id 

@app.route('/', methods=['POST', 'GET'])
def home():
    alert_flag = ""

    if request.method == 'POST':
        stock_name = request.form['content'].upper()
        new_stock = Todo(ticker=stock_name)

        existing_stock = Todo.query.filter_by(ticker=stock_name).first()
        if existing_stock:
            alert_flag = "Error with existing stock."
        else:
            try:
                price = get_price(stock_name)
                if price == 0:
                    alert_flag = "Stock does not exist!"
                else:
                    pct = pct_change(stock_name)
                    new_stock.percent_change = pct
                    new_stock.recent_price = price
                    db.session.add(new_stock)
                    db.session.commit()
                    return redirect('/')
            except Exception as e:
                alert_flag = f"Error adding new stock: {e}"

    # Update prices for all stocks
    stocks = Todo.query.order_by(Todo.date_created).all()
    for stock in stocks:
        try:
            stock.recent_price = get_price(stock.ticker)
            stock.percent_change = pct_change(stock.ticker)
        except Exception as e:
            print(f'Error updating price for {stock.ticker}: {e}')
    
    db.session.commit()

    return render_template('index.html', stocks=stocks, alert_flag=alert_flag)

@app.route('/email_prices', methods=['POST', 'GET'])
def email_prices():
    if request.method == 'POST':
        stocks = Todo.query.all()
        email = request.form['content']
        message = """\
Subject: Financial Data
        """
        message += f'\n'
        for stock in stocks:
            message += f'Most Recent Price of {stock.ticker}: {stock.recent_price} with {stock.percent_change}% change\n'
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(sender, password)
                server.sendmail(sender, email, message)
            stocks = Todo.query.order_by(Todo.date_created).all()
            return render_template('index.html', stocks=stocks, alert_flag="")
        except Exception as e:
            stocks = Todo.query.order_by(Todo.date_created).all()
            return render_template('index.html', stocks=stocks, alert_flag=e)
    else:
        stocks = Todo.query.order_by(Todo.date_created).all()
        return render_template('index.html', stocks=stocks, alert_flag="")

@app.route('/delete/<int:id>')
def delete(id):
    stock_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(stock_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'Error in deleting stock'

if __name__ == '__main__':
    app.run(debug=True)
