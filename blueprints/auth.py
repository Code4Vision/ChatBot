"""
Local authentication blueprint with username/password system
Mobile-first design focused
"""
import uuid
from datetime import datetime

from flask import Blueprint, redirect, request, url_for, flash, render_template, session
from flask_login import login_required, login_user, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from models import User, UserPreferences

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

class LoginForm(FlaskForm):
    """Local login form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)],
                          render_kw={"placeholder": "Enter your username", "autocomplete": "username"})
    password = PasswordField('Password', validators=[DataRequired()],
                           render_kw={"placeholder": "Enter your password", "autocomplete": "current-password"})
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    """Local registration form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)],
                          render_kw={"placeholder": "Choose a username", "autocomplete": "username"})
    email = EmailField('Email', validators=[DataRequired(), Email()],
                      render_kw={"placeholder": "Enter your email", "autocomplete": "email"})
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)],
                           render_kw={"placeholder": "Create a password", "autocomplete": "new-password"})
    password2 = PasswordField('Confirm Password', 
                            validators=[DataRequired(), EqualTo('password', message='Passwords must match')],
                            render_kw={"placeholder": "Confirm your password", "autocomplete": "new-password"})
    submit = SubmitField('Create Account')
    
    def validate_username(self, username):
        """Check if username is already taken"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """Check if email is already registered"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already registered. Please use a different email.')

@auth_bp.route("/login", methods=['GET', 'POST'])
def login():
    """Local login"""
    if current_user.is_authenticated:
        return redirect(url_for('chat.chat_interface'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=True)
            user.update_last_login()
            flash(f"Welcome back, {user.username}!", "success")
            
            # Redirect to next page or chat interface
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('chat.chat_interface'))
        else:
            flash("Invalid username or password. Please try again.", "error")
    
    return render_template('auth/login.html', form=form)

@auth_bp.route("/register", methods=['GET', 'POST'])
def register():
    """Local registration"""
    if current_user.is_authenticated:
        return redirect(url_for('chat.chat_interface'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Create new user
        user = User()  # type: ignore
        user.username = form.username.data
        user.email = form.email.data
        user.password_hash = generate_password_hash(form.password.data)
        
        db.session.add(user)
        db.session.flush()  # Get the user ID
        
        # Create default preferences
        preferences = UserPreferences()  # type: ignore
        preferences.user_id = user.id
        preferences.preferences_data = {
            "display_name": form.username.data,
            "chat_style": "friendly",
            "topics_of_interest": [],
            "response_length": "medium"
        }
        db.session.add(preferences)
        db.session.commit()
        
        flash(f"Welcome to the chatbot, {user.username}! Your account has been created.", "success")
        login_user(user, remember=True)
        return redirect(url_for("chat.chat_interface"))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    """Log out the current user"""
    username = current_user.username
    logout_user()
    flash(f"Goodbye {username}! You have been logged out.", "info")
    return redirect(url_for("index"))

@auth_bp.route("/preferences")
@login_required
def preferences():
    """User preferences page"""
    user_prefs = current_user.preferences
    if not user_prefs:
        user_prefs = UserPreferences()  # type: ignore
        user_prefs.user_id = current_user.id
        user_prefs.preferences_data = {
            "display_name": current_user.username,
            "chat_style": "friendly",
            "topics_of_interest": [],
            "response_length": "medium"
        }
        db.session.add(user_prefs)
        db.session.commit()
    
    return render_template('preferences.html', preferences=user_prefs)

@auth_bp.route("/preferences", methods=['POST'])
@login_required
def update_preferences():
    """Update user preferences"""
    user_prefs = current_user.preferences
    if not user_prefs:
        user_prefs = UserPreferences()  # type: ignore
        user_prefs.user_id = current_user.id
        db.session.add(user_prefs)
    
    # Update preferences from form data
    prefs_data = user_prefs.preferences_data
    prefs_data.update({
        "display_name": request.form.get("display_name", current_user.username),
        "chat_style": request.form.get("chat_style", "friendly"),
        "topics_of_interest": request.form.getlist("topics_of_interest"),
        "response_length": request.form.get("response_length", "medium")
    })
    user_prefs.preferences_data = prefs_data
    
    db.session.commit()
    flash("Preferences updated successfully!", "success")
    return redirect(url_for('auth.preferences'))