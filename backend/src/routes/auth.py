import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session, redirect, url_for
from authlib.integrations.flask_client import OAuth
from authlib.common.errors import AuthlibBaseError
import requests
from ..middleware.rate_limiter import api_rate_limit, strict_rate_limit

auth_bp = Blueprint('auth', __name__)

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', 'your-google-client-id')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', 'your-google-client-secret')

# Initialize OAuth
oauth = OAuth()

def init_oauth(app):
    """Initialize OAuth with Flask app"""
    oauth.init_app(app)
    
    # Register Google OAuth provider
    google = oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    return google

# In-memory user storage (use database in production)
users_db = {}
sessions_db = {}

@auth_bp.route('/auth/login', methods=['GET'])
@strict_rate_limit
def login():
    """Initiate Google OAuth login"""
    try:
        google = oauth.google
        redirect_uri = url_for('auth.callback', _external=True)
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        return jsonify({'error': f'Login initiation failed: {str(e)}'}), 500

@auth_bp.route('/auth/callback', methods=['GET'])
@strict_rate_limit
def callback():
    """Handle Google OAuth callback"""
    try:
        google = oauth.google
        token = google.authorize_access_token()
        
        if not token:
            return jsonify({'error': 'Authorization failed'}), 400
        
        # Get user info from Google
        user_info = token.get('userinfo')
        if not user_info:
            # Fallback: fetch user info manually
            resp = google.get('https://www.googleapis.com/oauth2/v2/userinfo')
            user_info = resp.json()
        
        # Create or update user
        user_id = user_info.get('id')
        email = user_info.get('email')
        name = user_info.get('name')
        picture = user_info.get('picture')
        
        if not user_id or not email:
            return jsonify({'error': 'Invalid user information from Google'}), 400
        
        # Store user in database
        users_db[user_id] = {
            'id': user_id,
            'email': email,
            'name': name,
            'picture': picture,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Create session
        session_token = f"session_{user_id}_{datetime.utcnow().timestamp()}"
        session_expires = datetime.utcnow() + timedelta(days=7)
        
        sessions_db[session_token] = {
            'user_id': user_id,
            'expires_at': session_expires.isoformat(),
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Set session cookie
        session['user_id'] = user_id
        session['session_token'] = session_token
        
        # Redirect to upload page
        return redirect('/upload')
        
    except AuthlibBaseError as e:
        return jsonify({'error': f'OAuth error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Callback processing failed: {str(e)}'}), 500

@auth_bp.route('/auth/logout', methods=['POST'])
@api_rate_limit
def logout():
    """Logout user and clear session"""
    try:
        session_token = session.get('session_token')
        
        if session_token and session_token in sessions_db:
            del sessions_db[session_token]
        
        session.clear()
        
        return jsonify({'message': 'Logged out successfully'})
    except Exception as e:
        return jsonify({'error': f'Logout failed: {str(e)}'}), 500

@auth_bp.route('/auth/user', methods=['GET'])
@api_rate_limit
def get_user():
    """Get current user information"""
    try:
        user_id = session.get('user_id')
        session_token = session.get('session_token')
        
        if not user_id or not session_token:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Check session validity
        if session_token not in sessions_db:
            session.clear()
            return jsonify({'error': 'Session expired'}), 401
        
        session_data = sessions_db[session_token]
        expires_at = datetime.fromisoformat(session_data['expires_at'])
        
        if datetime.utcnow() > expires_at:
            del sessions_db[session_token]
            session.clear()
            return jsonify({'error': 'Session expired'}), 401
        
        # Get user data
        if user_id not in users_db:
            session.clear()
            return jsonify({'error': 'User not found'}), 404
        
        user = users_db[user_id]
        return jsonify({
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'picture': user['picture']
            },
            'authenticated': True
        })
        
    except Exception as e:
        return jsonify({'error': f'User fetch failed: {str(e)}'}), 500

@auth_bp.route('/auth/status', methods=['GET'])
@api_rate_limit
def auth_status():
    """Check authentication status"""
    try:
        user_id = session.get('user_id')
        session_token = session.get('session_token')
        
        if not user_id or not session_token:
            return jsonify({'authenticated': False})
        
        # Check session validity
        if session_token not in sessions_db:
            return jsonify({'authenticated': False})
        
        session_data = sessions_db[session_token]
        expires_at = datetime.fromisoformat(session_data['expires_at'])
        
        if datetime.utcnow() > expires_at:
            return jsonify({'authenticated': False})
        
        return jsonify({'authenticated': True, 'user_id': user_id})
        
    except Exception as e:
        return jsonify({'error': f'Status check failed: {str(e)}'}), 500

def require_auth(f):
    """Decorator to require authentication for routes"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        session_token = session.get('session_token')
        
        if not user_id or not session_token:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check session validity
        if session_token not in sessions_db:
            return jsonify({'error': 'Session expired'}), 401
        
        session_data = sessions_db[session_token]
        expires_at = datetime.fromisoformat(session_data['expires_at'])
        
        if datetime.utcnow() > expires_at:
            return jsonify({'error': 'Session expired'}), 401
        
        # Add user_id to request context
        request.current_user_id = user_id
        return f(*args, **kwargs)
    
    return decorated_function

