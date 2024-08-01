from .extensions import db
from datetime import datetime
from flask_login import UserMixin   

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    preferences = db.Column(db.String(500), default='')
    email_frequency = db.Column(db.String(50), default='none')
    last_email_sent = db.Column(db.DateTime, default=None)
    stocks = db.relationship('Stock', backref='user', lazy=True)

    def __repr__(self):
        return '<User %r>' % self.email

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    recent_price = db.Column(db.Float, default=0)
    percent_change = db.Column(db.Float, default=0)

    def __repr__(self):
        return '<Stock %r>' % self.id