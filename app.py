"""
Secure Flask Chatbot Application with Google OAuth 2.0
Features: Local LLM integration, encrypted database storage, personalized chat memory
"""
import os
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase

# Database configuration
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def create_app():
    """Application factory pattern for Flask app creation"""
    app = Flask(__name__)
    
    # Configuration
    secret_key = os.environ.get('SESSION_SECRET')
    if not secret_key:
        if os.environ.get('FLASK_ENV') != 'development':
            raise ValueError("SESSION_SECRET environment variable is required for production deployment")
        secret_key = 'dev-secret-key-change-in-production'
    app.config['SECRET_KEY'] = secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Security configuration - only use secure cookies in production
    is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('REPLIT_ENVIRONMENT') == 'production'
    app.config['SESSION_COOKIE_SECURE'] = is_production
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['REMEMBER_COOKIE_SECURE'] = is_production
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    
    # Initialize extensions
    db.init_app(app)
    
    # CSRF Protection
    csrf = CSRFProtect(app)
    
    # Flask-Login configuration
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # type: ignore
    login_manager.login_message = 'Please log in to access the chatbot.'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # Create database tables first
    with app.app_context():
        # Import models to ensure tables are created
        import models
        db.create_all()
    
    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.chat import chat_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    
    # Main routes
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('chat.chat_interface'))
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    # Only enable debug in development
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)