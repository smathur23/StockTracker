from flask import Flask, jsonify, render_template, url_for, request, redirect, Blueprint
from flask_login import login_user, login_required, logout_user, current_user
import smtplib, ssl
import os
from dotenv import load_dotenv
from .processing import *
from .extensions import db, supabase
from .model import Stock, User

load_dotenv()

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)

port = 465
smtp_server = "smtp.gmail.com"
sender = "adxupdates@gmail.com"
password = os.getenv("APPPW")

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        exists = User.query.filter_by(email=email).first()
        if not exists:
            return render_template('register.html', alert_flag="User does not exist! Please register.")
        password = request.form['password']
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
        except Exception as e:
            return render_template('login.html', alert_flag=f"Error: {e}")
        
        user_data = response.user
        user = User.query.filter_by(email=user_data.email).first()
        if not user:
            user = User(email=user_data['email'])
            db.session.add(user)
            db.session.commit()

        login_user(user)
        return redirect(url_for('main.preferences'))
    
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            return render_template('register.html', alert_flag="Passwords do not match.")

        try:
            response = supabase.auth.sign_up(
                credentials={"email": email, "password": password}
            )
        except Exception as e:
            return render_template('register.html', alert_flag=f"Error: {e}")

        user_data = response.user
        new_user = User(email=user_data.email)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        return redirect(url_for('main.preferences', alert_flag=""))
    
    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    supabase.auth.sign_out()
    return redirect(url_for('auth.login'))

@main.route('/', methods=['GET', 'POST'])
@login_required
def home():
    alert_flag = ""

    if request.method == 'POST':
        stock_name = request.form['content'].upper()
        new_stock = Stock(ticker=stock_name)

        existing_stock = Stock.query.filter_by(ticker=stock_name, user_id=current_user.id).first()
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
                    current_user.stocks.append(new_stock)
                    db.session.add(new_stock)
                    db.session.commit()
                    return redirect('/')
            except Exception as e:
                alert_flag = f"Error adding new stock: {e}"

    stocks = Stock.query.filter_by(user_id=current_user.id).order_by(Stock.date_created).all()
    for stock in stocks:
        try:
            stock.recent_price = get_price(stock.ticker)
            stock.percent_change = pct_change(stock.ticker)
        except Exception as e:
            print(f'Error updating price/percent for {stock.ticker}: {e}')
    
    db.session.commit()

    return render_template('index.html', stocks=stocks, alert_flag=alert_flag)

@main.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    if request.method == 'POST':
        indicators = request.form.getlist('indicators')
        preferences = ','.join(indicators)
        frequency = request.form['frequency']
        
        current_user.preferences = preferences
        current_user.email_frequency = frequency
        
        db.session.commit()

        return redirect(url_for('main.preferences'))
    
    return render_template('preferences.html', user=current_user)

@main.route('/set_preferences', methods=['POST'])
@login_required
def set_preferences():
    indicators = request.form.getlist('indicators')
    preferences = ','.join(indicators)
    frequency = request.form['frequency']
    
    current_user.preferences = preferences
    current_user.email_frequency = frequency
    
    db.session.commit()

    return redirect(url_for('main.home'))

@main.route('/email_prices', methods=['POST', 'GET'])
def email_prices():
    if request.method == 'POST':
        stocks = Stock.query.filter_by(user_id=current_user.id).order_by(Stock.date_created).all()
        email = current_user.email
        preferences = current_user.preferences.split(',')
        if len(preferences) == 0:
            stocks = Stock.query.filter_by(user_id=current_user.id).order_by(Stock.date_created).all()
            return render_template('index.html', stocks=stocks, alert_flag="No preferences set.")
        
        message = """\
Subject: Financial Data
        """
        message += f'\n'
        for stock in stocks:
            if 'macd' in preferences:
                message += f'{last_macd_crossover(stock.ticker)}\n'
            if 'donchian' in preferences:
                message += f'{donchian_channel_position(stock.ticker)}\n'
            if 'rsi' in preferences:
                message += f'{rsi(stock.ticker)}\n'
            if 'adx' in preferences:
                message += f'{adx(stock.ticker)}\n'
            message += '\n'
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(sender, password)
                server.sendmail(sender, email, message)
            stocks = Stock.query.filter_by(user_id=current_user.id).order_by(Stock.date_created).all()
            return render_template('index.html', stocks=stocks, alert_flag="")
        except Exception as e:
            stocks = Stock.query.filter_by(user_id=current_user.id).order_by(Stock.date_created).all()
            return render_template('index.html', stocks=stocks, alert_flag=e)
    else:
        stocks = Stock.query.filter_by(user_id=current_user.id).order_by(Stock.date_created).all()
        return render_template('index.html', stocks=stocks, alert_flag="")

@main.route('/delete/<int:id>')
@login_required
def delete(id):
    stock_to_delete = Stock.query.get_or_404(id)

    try:
        db.session.delete(stock_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'Error in deleting stock'

