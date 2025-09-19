"""
Authentication blueprint using Google OAuth 2.0
Based on blueprint:flask_google_oauth integration
"""
import json
import os
import uuid
import secrets
from datetime import datetime

import requests
from flask import Blueprint, redirect, request, url_for, flash, render_template, session
from flask_login import login_required, login_user, logout_user, current_user
from oauthlib.oauth2 import WebApplicationClient

from app import db
from models import User, UserPreferences

# OAuth credentials loaded at runtime to avoid import-time failures
def get_google_oauth_config():
    """Get Google OAuth configuration with proper error handling"""
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("Google OAuth credentials (GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET) are required for authentication.")
    
    return client_id, client_secret
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Make sure to use this redirect URL. It has to match the one in the whitelist
try:
    DEV_REDIRECT_URL = f'https://{os.environ["REPLIT_DEV_DOMAIN"]}/auth/google_login/callback'
except KeyError:
    # Fallback for local development
    DEV_REDIRECT_URL = "http://localhost:5000/auth/google_login/callback"

# Display setup instructions
print(f"""To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add {DEV_REDIRECT_URL} to Authorized redirect URIs

For detailed instructions, see:
https://docs.replit.com/additional-resources/google-auth-in-flask#set-up-your-oauth-app--client
""")

# OAuth client will be initialized at runtime

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login")
def login():
    """Redirect to Google OAuth login"""
    if current_user.is_authenticated:
        return redirect(url_for('chat.chat_interface'))
    
    try:
        client_id, client_secret = get_google_oauth_config()
        client = WebApplicationClient(client_id)
        
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Generate and store OAuth state for CSRF protection
        oauth_state = secrets.token_urlsafe(32)
        session['oauth_state'] = oauth_state

        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            # Use proper URL construction to match the actual callback route
            redirect_uri=url_for('auth.callback', _external=True, _scheme='https'),
            scope=["openid", "email", "profile"],
            state=oauth_state,  # CSRF protection
        )
        return redirect(request_uri)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for('index'))

@auth_bp.route("/google_login")
def google_login():
    """Alternative route for Google login"""
    return redirect(url_for('auth.login'))

@auth_bp.route("/google_login/callback")
def callback():
    """Handle Google OAuth callback with state validation"""
    code = request.args.get("code")
    state = request.args.get("state")
    
    if not code:
        flash("Authorization failed. Please try again.", "error")
        return redirect(url_for('index'))
    
    # Validate OAuth state to prevent CSRF attacks
    expected_state = session.pop('oauth_state', None)
    if not state or not expected_state or state != expected_state:
        flash("Invalid authentication state. Please try again.", "error")
        return redirect(url_for('index'))
    
    try:
        client_id, client_secret = get_google_oauth_config()
        client = WebApplicationClient(client_id)
        
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]

        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            # Use proper URL construction for consistent redirect handling
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=url_for('auth.callback', _external=True, _scheme='https'),
            code=code,
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(client_id, client_secret),
        )

        client.parse_request_body_response(json.dumps(token_response.json()))

        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        userinfo = userinfo_response.json()
        if userinfo.get("email_verified"):
            users_email = userinfo["email"]
            users_name = userinfo.get("given_name", userinfo.get("name", "User"))
        else:
            flash("User email not available or not verified by Google.", "error")
            return redirect(url_for('index'))

        # Check if user exists, create if not
        user = User.query.filter_by(email=users_email).first()
        if not user:
            user = User()  # type: ignore
            user.username = users_name
            user.email = users_email
            db.session.add(user)
            db.session.flush()  # Get the user ID
            
            # Create default preferences
            preferences = UserPreferences()  # type: ignore
            preferences.user_id = user.id
            preferences.preferences_data = {
                "display_name": users_name,
                "chat_style": "friendly",
                "topics_of_interest": [],
                "response_length": "medium"
            }
            db.session.add(preferences)
            db.session.commit()
            
            flash(f"Welcome {users_name}! Your account has been created.", "success")
        else:
            user.update_last_login()
            flash(f"Welcome back {user.username}!", "success")

        login_user(user, remember=True)
        return redirect(url_for("chat.chat_interface"))
        
    except Exception as e:
        flash("Authentication failed. Please try again.", "error")
        print(f"OAuth error: {e}")
        return redirect(url_for('index'))

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