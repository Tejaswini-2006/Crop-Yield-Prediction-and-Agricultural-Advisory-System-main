from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    location = db.Column(db.String(100), default='Maharashtra, India')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    predictions = db.relationship('PredictionHistory', backref='user', lazy=True, cascade="all, delete-orphan")
    posts = db.relationship('ForumPost', backref='author', lazy=True)
    listings = db.relationship('MarketListing', backref='seller', lazy=True)

    def __repr__(self):
        return f"<User {self.email}>"

class PredictionHistory(db.Model):
    __tablename__ = 'prediction_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    prediction_type = db.Column(db.String(50), nullable=False) # 'yield', 'disease', 'fertilizer', 'crop', 'leaf_disease'
    title = db.Column(db.String(150), nullable=False)
    input_data = db.Column(db.Text, nullable=False) # JSON string
    result_data = db.Column(db.Text, nullable=False) # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_input_json(self):
        try:
            return json.loads(self.input_data)
        except Exception:
            return {}

    def get_result_json(self):
        try:
            return json.loads(self.result_data)
        except Exception:
            return {}

class ForumPost(db.Model):
    __tablename__ = 'forum_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    farmer_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    crop_type = db.Column(db.String(100), default='General')
    category = db.Column(db.String(100), nullable=False)
    question = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    responses = db.relationship('ForumResponse', backref='post', lazy=True, cascade="all, delete-orphan")

class ForumResponse(db.Model):
    __tablename__ = 'forum_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    responder_name = db.Column(db.String(100), nullable=False)
    response_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MarketListing(db.Model):
    __tablename__ = 'market_listings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    farmer_name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    listing_type = db.Column(db.String(20), nullable=False) # 'sell', 'buy'
    item_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.String(50), nullable=False)
    price = db.Column(db.String(50), default='Negotiable')
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
