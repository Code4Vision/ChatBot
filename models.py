"""
Database models for the Flask chatbot application
Includes encryption for sensitive data and user isolation
"""
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
from app import db
import json

# Encryption setup
def get_encryption_key():
    """Get encryption key for data at rest"""
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        raise ValueError("ENCRYPTION_KEY environment variable is required for data encryption. Please set this securely.")
    return key.encode() if isinstance(key, str) else key

cipher_suite = Fernet(get_encryption_key())

class User(UserMixin, db.Model):
    """User model with local authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    chat_history = db.relationship('ChatHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    preferences = db.relationship('UserPreferences', backref='user', lazy=True, cascade='all, delete-orphan', uselist=False)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()

class UserPreferences(db.Model):
    """User personalization preferences"""
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Encrypted preference data
    _preferences_data = db.Column('preferences_data', db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def preferences_data(self):
        """Decrypt and return preferences data"""
        if self._preferences_data:
            try:
                decrypted = cipher_suite.decrypt(self._preferences_data.encode()).decode()
                return json.loads(decrypted)
            except Exception:
                return {}
        return {}
    
    @preferences_data.setter
    def preferences_data(self, value):
        """Encrypt and store preferences data"""
        if value:
            json_str = json.dumps(value)
            encrypted = cipher_suite.encrypt(json_str.encode()).decode()
            self._preferences_data = encrypted
        else:
            self._preferences_data = None
    
    def get_preference(self, key, default=None):
        """Get a specific preference value"""
        return self.preferences_data.get(key, default)
    
    def set_preference(self, key, value):
        """Set a specific preference value"""
        prefs = self.preferences_data
        prefs[key] = value
        self.preferences_data = prefs
        self.updated_at = datetime.utcnow()

class ChatHistory(db.Model):
    """Encrypted chat history for each user"""
    __tablename__ = 'chat_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Encrypted message content
    _user_message = db.Column('user_message', db.Text)
    _bot_response = db.Column('bot_response', db.Text)
    
    # Metadata
    conversation_id = db.Column(db.String(36), nullable=False, index=True)  # UUID for conversation grouping
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    @property
    def user_message(self):
        """Decrypt and return user message"""
        if self._user_message:
            try:
                return cipher_suite.decrypt(self._user_message.encode()).decode()
            except Exception:
                return "[Decryption Error]"
        return ""
    
    @user_message.setter
    def user_message(self, value):
        """Encrypt and store user message"""
        if value:
            encrypted = cipher_suite.encrypt(value.encode()).decode()
            self._user_message = encrypted
    
    @property
    def bot_response(self):
        """Decrypt and return bot response"""
        if self._bot_response:
            try:
                return cipher_suite.decrypt(self._bot_response.encode()).decode()
            except Exception:
                return "[Decryption Error]"
        return ""
    
    @bot_response.setter
    def bot_response(self, value):
        """Encrypt and store bot response"""
        if value:
            encrypted = cipher_suite.encrypt(value.encode()).decode()
            self._bot_response = encrypted
    
    def __repr__(self):
        return f'<ChatHistory User:{self.user_id} at {self.timestamp}>'
    
    @classmethod
    def get_user_history(cls, user_id, limit=50):
        """Get recent chat history for a user"""
        return cls.query.filter_by(user_id=user_id)\
                      .order_by(cls.timestamp.desc())\
                      .limit(limit)\
                      .all()
    
    @classmethod
    def get_conversation_history(cls, user_id, conversation_id):
        """Get chat history for a specific conversation"""
        return cls.query.filter_by(user_id=user_id, conversation_id=conversation_id)\
                      .order_by(cls.timestamp.asc())\
                      .all()