"""
Authentication routes for RAG Chatbot PWA
"""

import os
import requests
from flask import Blueprint, request, jsonify, redirect, url_for
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 409
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 409
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ('username', 'password')):
            return jsonify({'error': 'Missing username or password'}), 400
        
        # Find user
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 401
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/github/login')
def github_login():
    """Initiate GitHub OAuth login"""
    github_client_id = os.getenv('GITHUB_CLIENT_ID')
    if not github_client_id:
        return jsonify({'error': 'GitHub OAuth not configured'}), 500
    
    redirect_uri = url_for('auth.github_callback', _external=True)
    github_auth_url = f"https://github.com/login/oauth/authorize?client_id={github_client_id}&redirect_uri={redirect_uri}&scope=user:email,repo"
    
    return redirect(github_auth_url)

@auth_bp.route('/github/callback')
def github_callback():
    """Handle GitHub OAuth callback"""
    try:
        code = request.args.get('code')
        if not code:
            return jsonify({'error': 'Authorization code not provided'}), 400
        
        # Exchange code for access token
        token_response = requests.post('https://github.com/login/oauth/access_token', {
            'client_id': os.getenv('GITHUB_CLIENT_ID'),
            'client_secret': os.getenv('GITHUB_CLIENT_SECRET'),
            'code': code
        }, headers={'Accept': 'application/json'})
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            return jsonify({'error': 'Failed to get access token'}), 400
        
        # Get user info from GitHub
        user_response = requests.get('https://api.github.com/user', 
                                   headers={'Authorization': f'token {access_token}'})
        user_data = user_response.json()
        
        # Get user email
        email_response = requests.get('https://api.github.com/user/emails',
                                    headers={'Authorization': f'token {access_token}'})
        emails = email_response.json()
        primary_email = next((email['email'] for email in emails if email['primary']), None)
        
        # Find or create user
        user = User.query.filter_by(github_id=str(user_data['id'])).first()
        
        if not user:
            # Check if user exists with same email
            user = User.query.filter_by(email=primary_email).first()
            if user:
                user.github_id = str(user_data['id'])
            else:
                # Create new user
                user = User(
                    username=user_data['login'],
                    email=primary_email,
                    github_id=str(user_data['id'])
                )
                user.set_password(os.urandom(32).hex())  # Random password for OAuth users
        
        db.session.add(user)
        db.session.commit()
        
        # Create JWT token
        jwt_token = create_access_token(identity=user.id)
        
        # Redirect to frontend with token
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        return redirect(f"{frontend_url}/auth/callback?token={jwt_token}")
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client-side token removal)"""
    return jsonify({'message': 'Logout successful'}), 200
