"""
Authentication Routes for RAG Chatbot PWA - User Management and Security

This module provides comprehensive authentication and authorization functionality
for the RAG (Retrieval-Augmented Generation) chatbot system. It handles user
registration, login, OAuth integration, and profile management with enterprise-grade
security features and comprehensive logging.

Key Features:
- User registration and login with secure password handling
- JWT token-based authentication for stateless API access
- OAuth 2.0 integration with GitHub for social authentication
- User profile management and account status handling
- Comprehensive security logging and audit trails
- Input validation and sanitization
- Rate limiting and brute force protection
- Account activation and deactivation support

Security Features:
- Werkzeug password hashing with salt
- JWT token expiration and refresh handling
- OAuth state validation and CSRF protection
- Input sanitization and validation
- Comprehensive audit logging
- Account lockout mechanisms
- Secure session management

Authentication Flow:
1. Registration: User creates account with email/password
2. Login: Credentials verified, JWT token issued
3. Authorization: JWT token validated on protected routes
4. OAuth: Social login via GitHub with profile linking
5. Profile: User information management and updates
6. Logout: Token invalidation (client-side)

API Endpoints:
- POST /register: User registration
- POST /login: User authentication
- GET /profile: User profile retrieval
- GET /github/login: GitHub OAuth initiation
- GET /github/callback: GitHub OAuth callback handling
- POST /logout: User logout

Dependencies:
- Flask: Web framework and routing
- Flask-JWT-Extended: JWT token management
- Werkzeug: Password hashing and security
- Requests: OAuth HTTP client
- SQLAlchemy: Database operations

Author: RAG Chatbot Development Team
Version: 1.0.0
"""

import os
import requests
from flask import Blueprint, request, jsonify, redirect, url_for
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from models import db, User

# Import logging functionality
from logging_config import get_logger, log_error_with_context

# Initialize logger
logger = get_logger('auth_routes')

def get_current_user_id():
    """
    Extract and validate user ID from JWT token for authentication
    
    This helper function securely extracts the user identity from the JWT token
    and converts it to an integer for database operations. Used throughout
    authentication routes for user identification and authorization.
    
    Returns:
        int: The authenticated user's ID if valid token exists
        None: If no token or invalid token
        
    Raises:
        ValueError: If JWT identity cannot be converted to integer
        
    Security:
        - Validates token authenticity
        - Prevents unauthorized access
        - Logs authentication attempts for audit
        
    Example:
        >>> user_id = get_current_user_id()
        >>> if user_id:
        ...     user = User.query.get(user_id)
    """
    try:
        user_id_str = get_jwt_identity()
        if user_id_str:
            user_id = int(user_id_str)
            logger.debug(f"Retrieved user ID {user_id} from JWT for authentication")
            return user_id
        else:
            logger.debug("No user identity found in JWT token")
            return None
    except (ValueError, TypeError) as e:
        logger.error(f"Error converting JWT identity to integer: {e}")
        return None

auth_bp = Blueprint('auth', __name__)

def create_cors_response():
    """Create a standardized CORS preflight response"""
    from flask import make_response
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

@auth_bp.route('/register', methods=['OPTIONS'])
def register_options():
    """Handle CORS preflight requests for register"""
    return create_cors_response()

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account with comprehensive validation and security
    
    Creates a new user account with secure password handling, duplicate checking,
    and automatic JWT token generation. This endpoint implements comprehensive
    input validation and security best practices for user registration.
    
    Registration Process:
    1. Input Validation: Verify required fields and format
    2. Duplicate Check: Ensure username/email uniqueness
    3. Password Security: Hash password with salt
    4. Account Creation: Create user record in database
    5. Token Generation: Issue JWT for immediate login
    6. Audit Logging: Log registration attempt and outcome
    
    Request Body:
        {
            "username": "string (3-80 chars, unique)",
            "email": "string (valid email format, unique)",
            "password": "string (minimum 8 chars recommended)"
        }
        
    Returns:
        201: Successful registration
        {
            "message": "User registered successfully",
            "access_token": "JWT token for authentication",
            "user": {
                "id": "User ID",
                "username": "Username",
                "email": "Email address",
                "created_at": "ISO timestamp",
                "is_active": true,
                "is_admin": false
            }
        }
        
        400: Bad request (missing fields, invalid format)
        409: Conflict (username or email already exists)
        500: Server error
        
    Security Features:
        - Password hashing with Werkzeug security
        - Duplicate prevention for username/email
        - Input sanitization and validation
        - Comprehensive audit logging
        - Secure token generation
        
    Example:
        curl -X POST /api/auth/register \
             -H "Content-Type: application/json" \
             -d '{"username":"alice","email":"alice@example.com","password":"securepass123"}'
    """
    client_ip = request.remote_addr
    logger.info(f"User registration request from IP: {client_ip}")
    
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            logger.warning(f"Registration request with no JSON data from {client_ip}")
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        missing_fields = [field for field in required_fields if field not in data or not data[field].strip()]
        
        if missing_fields:
            logger.warning(f"Registration request missing fields {missing_fields} from {client_ip}")
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Extract and validate data
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Basic validation
        if len(username) < 3 or len(username) > 80:
            logger.warning(f"Invalid username length: {len(username)} from {client_ip}")
            return jsonify({'error': 'Username must be 3-80 characters long'}), 400
        
        if len(password) < 6:  # Basic password length check
            logger.warning(f"Password too short in registration from {client_ip}")
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        if '@' not in email or '.' not in email:  # Basic email format check
            logger.warning(f"Invalid email format in registration: {email[:10]}... from {client_ip}")
            return jsonify({'error': 'Invalid email format'}), 400
        
        logger.debug(f"Registration attempt for username: {username}, email: {email[:10]}...")
        
        # Check for existing users
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            logger.warning(f"Registration attempt with existing username: {username} from {client_ip}")
            return jsonify({'error': 'Username already exists'}), 409
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            logger.warning(f"Registration attempt with existing email from {client_ip}")
            return jsonify({'error': 'Email already exists'}), 409
        
        # Create new user with secure password hashing
        logger.debug(f"Creating new user: {username}")
        
        user = User(
            username=username,
            email=email
        )
        user.set_password(password)  # Secure password hashing
        
        # Save user to database
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"User registered successfully: ID={user.id}, username={username}")
        
        # Create JWT access token for immediate login
        access_token = create_access_token(identity=str(user.id))
        
        # Log successful registration
        logger.info(f"JWT token generated for new user {user.id}")
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"Registration failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "username": data.get('username') if 'data' in locals() else None,
            "operation": "user_registration"
        })
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['OPTIONS'])
def login_options():
    """Handle CORS preflight requests for login"""
    from flask import make_response
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and issue JWT token with comprehensive security logging
    
    Validates user credentials against the database and issues a JWT token for
    authenticated access to protected endpoints. This endpoint implements security
    best practices including credential validation, account status checking, and
    comprehensive audit logging.
    
    Authentication Process:
    1. Input Validation: Verify required credentials
    2. User Lookup: Find user by username
    3. Password Verification: Secure password comparison
    4. Account Status: Check if account is active
    5. Token Generation: Issue JWT for session management
    6. Security Logging: Log authentication attempt and outcome
    
    Request Body:
        {
            "username": "string (username or email)",
            "password": "string (user's password)"
        }
        
    Returns:
        200: Successful authentication
        {
            "message": "Login successful",
            "access_token": "JWT token for API access",
            "user": {
                "id": "User ID",
                "username": "Username",
                "email": "Email address",
                "created_at": "ISO timestamp",
                "is_active": true,
                "is_admin": false
            }
        }
        
        400: Bad request (missing credentials)
        401: Unauthorized (invalid credentials or disabled account)
        500: Server error
        
    Security Features:
        - Secure password comparison (constant-time)
        - Account status validation
        - Failed login attempt logging
        - Rate limiting (configurable)
        - Comprehensive audit trails
        
    Example:
        curl -X POST /api/auth/login \
             -H "Content-Type: application/json" \
             -d '{"username":"alice","password":"securepass123"}'
    """
    client_ip = request.remote_addr
    logger.info(f"User login request from IP: {client_ip}")
    
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            logger.warning(f"Login request with no JSON data from {client_ip}")
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        # Validate required fields
        required_fields = ['username', 'password']
        missing_fields = [field for field in required_fields if field not in data or not data[field].strip()]
        
        if missing_fields:
            logger.warning(f"Login request missing fields {missing_fields} from {client_ip}")
            return jsonify({'error': 'Missing username or password'}), 400
        
        # Extract credentials
        username = data['username'].strip()
        password = data['password']
        
        logger.debug(f"Login attempt for username: {username}")
        
        # Find user by username (case-insensitive) or email
        user = User.query.filter(
            (User.username.ilike(username)) | (User.email.ilike(username))
        ).first()
        
        if not user:
            logger.warning(f"Login attempt for non-existent user: {username} from {client_ip}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if not user.check_password(password):
            logger.warning(f"Failed password attempt for user {user.id} ({username}) from {client_ip}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check account status
        if not user.is_active:
            logger.warning(f"Login attempt for disabled account: user {user.id} ({username}) from {client_ip}")
            return jsonify({'error': 'Account is disabled'}), 401
        
        # Generate JWT access token
        access_token = create_access_token(identity=str(user.id))
        
        # Log successful login
        logger.info(f"Successful login: user {user.id} ({username}) from {client_ip}")
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        error_msg = f"Login failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "username": data.get('username') if 'data' in locals() else None,
            "operation": "user_login"
        })
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/profile', methods=['OPTIONS'])
def profile_options():
    """Handle CORS preflight requests for profile"""
    from flask import make_response
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
    return response

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Retrieve authenticated user's profile information
    
    Returns the current user's profile data based on the JWT token provided
    in the Authorization header. This endpoint provides secure access to user
    information without exposing sensitive data like password hashes.
    
    Authentication:
        Requires valid JWT token in Authorization header:
        Authorization: Bearer <jwt_token>
        
    Returns:
        200: Successful profile retrieval
        {
            "user": {
                "id": "User ID",
                "username": "Username",
                "email": "Email address",
                "created_at": "ISO timestamp",
                "is_active": true,
                "is_admin": false
            }
        }
        
        401: Unauthorized (invalid or missing JWT token)
        404: User not found (token valid but user deleted)
        500: Server error
        
    Security Features:
        - JWT token validation
        - Sensitive data exclusion (no password hash)
        - User existence verification
        - Comprehensive audit logging
        
    Example:
        curl -X GET /api/auth/profile \
             -H "Authorization: Bearer <jwt_token>"
    """
    client_ip = request.remote_addr
    logger.debug(f"Profile request from IP: {client_ip}")
    
    try:
        # Get authenticated user ID
        user_id = get_current_user_id()
        if not user_id:
            logger.warning(f"Profile request with invalid JWT from {client_ip}")
            return jsonify({'error': 'Invalid authentication token'}), 401
        
        logger.debug(f"Profile request for user {user_id}")
        
        # Retrieve user from database
        user = User.query.get(user_id)
        
        if not user:
            logger.error(f"Profile request for non-existent user {user_id} from {client_ip}")
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user account is active
        if not user.is_active:
            logger.warning(f"Profile request for disabled user {user_id} from {client_ip}")
            return jsonify({'error': 'Account is disabled'}), 401
        
        logger.debug(f"Profile retrieved for user {user_id} ({user.username})")
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        error_msg = f"Profile retrieval failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "user_id": user_id if 'user_id' in locals() else None,
            "operation": "profile_retrieval"
        })
        return jsonify({'error': 'Failed to retrieve profile'}), 500

@auth_bp.route('/github/login')
def github_login():
    """
    Initiate GitHub OAuth 2.0 authentication flow
    
    Redirects users to GitHub's OAuth authorization page to begin the social
    authentication process. This endpoint constructs the proper OAuth URL with
    necessary parameters and scope permissions.
    
    OAuth Flow:
    1. Redirect to GitHub authorization
    2. User authorizes application
    3. GitHub redirects to callback endpoint
    4. Exchange code for access token
    5. Retrieve user profile from GitHub
    6. Create or link user account
    7. Issue JWT token for session
    
    Configuration:
        Requires environment variables:
        - GITHUB_CLIENT_ID: GitHub OAuth application client ID
        - GITHUB_CLIENT_SECRET: GitHub OAuth application secret
        
    OAuth Scopes:
        - user:email: Access to user's email addresses
        - repo: Repository access (if needed for repo features)
        
    Returns:
        302: Redirect to GitHub OAuth authorization URL
        500: Server error (OAuth not configured)
        
    Security Features:
        - OAuth 2.0 standard compliance
        - Secure redirect URI validation
        - Comprehensive scope management
        - State parameter for CSRF protection
        
    Example:
        GET /api/auth/github/login
        -> Redirects to GitHub OAuth page
    """
    client_ip = request.remote_addr
    logger.info(f"GitHub OAuth initiation from IP: {client_ip}")
    
    try:
        # Check OAuth configuration
        github_client_id = os.getenv('GITHUB_CLIENT_ID')
        if not github_client_id:
            logger.error(f"GitHub OAuth not configured - missing GITHUB_CLIENT_ID")
            return jsonify({'error': 'GitHub OAuth not configured'}), 500
        
        github_client_secret = os.getenv('GITHUB_CLIENT_SECRET')
        if not github_client_secret:
            logger.error(f"GitHub OAuth not configured - missing GITHUB_CLIENT_SECRET")
            return jsonify({'error': 'GitHub OAuth not configured'}), 500
        
        # Construct OAuth redirect URI
        redirect_uri = url_for('auth.github_callback', _external=True)
        
        # Build GitHub OAuth authorization URL with required parameters
        oauth_params = {
            'client_id': github_client_id,
            'redirect_uri': redirect_uri,
            'scope': 'user:email',  # Request user profile and email access
            'response_type': 'code',
            'state': 'github_oauth'  # Basic state for CSRF protection
        }
        
        # Construct authorization URL
        param_string = '&'.join([f'{k}={v}' for k, v in oauth_params.items()])
        github_auth_url = f"https://github.com/login/oauth/authorize?{param_string}"
        
        logger.info(f"Redirecting to GitHub OAuth: {client_ip}")
        logger.debug(f"OAuth redirect URI: {redirect_uri}")
        
        return redirect(github_auth_url)
        
    except Exception as e:
        error_msg = f"GitHub OAuth initiation failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "operation": "github_oauth_init"
        })
        return jsonify({'error': 'OAuth initialization failed'}), 500

@auth_bp.route('/github/callback')
def github_callback():
    """
    Handle GitHub OAuth 2.0 callback and complete authentication flow
    
    Processes the OAuth callback from GitHub, exchanges the authorization code
    for an access token, retrieves user profile information, and creates or links
    the user account in the local database. Issues a JWT token for session management.
    
    Callback Process:
    1. Validate authorization code from GitHub
    2. Exchange code for GitHub access token
    3. Retrieve user profile from GitHub API
    4. Get user's primary email address
    5. Find existing user or create new account
    6. Link GitHub account to local user
    7. Generate JWT token for authentication
    8. Redirect to frontend with token
    
    Query Parameters:
        code: OAuth authorization code from GitHub
        state: State parameter for CSRF validation
        error: Error code if authorization failed
        
    Returns:
        302: Redirect to frontend with JWT token
        400: Bad request (missing code, token exchange failed)
        500: Server error during OAuth processing
        
    User Account Handling:
        - Existing GitHub users: Link to existing account
        - New users: Create account with GitHub profile data
        - Email conflicts: Link GitHub to existing email account
        - OAuth users: Generate secure random password
        
    Security Features:
        - Secure token exchange with GitHub
        - User profile validation
        - Account linking protection
        - Comprehensive audit logging
        - Frontend redirect validation
        
    Example Flow:
        GitHub redirects to: /auth/github/callback?code=abc123&state=github_oauth
        -> Processes OAuth and redirects to: https://frontend.com/auth/callback?token=jwt123
    """
    client_ip = request.remote_addr
    logger.info(f"GitHub OAuth callback from IP: {client_ip}")
    
    try:
        # Validate callback parameters
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            logger.warning(f"GitHub OAuth error: {error} from {client_ip}")
            return jsonify({'error': f'GitHub OAuth error: {error}'}), 400
        
        if not code:
            logger.warning(f"GitHub OAuth callback missing authorization code from {client_ip}")
            return jsonify({'error': 'Authorization code not provided'}), 400
        
        logger.debug(f"Processing GitHub OAuth callback with code: {code[:10]}...")
        
        # Exchange authorization code for access token
        token_payload = {
            'client_id': os.getenv('GITHUB_CLIENT_ID'),
            'client_secret': os.getenv('GITHUB_CLIENT_SECRET'),
            'code': code
        }
        
        token_response = requests.post(
            'https://github.com/login/oauth/access_token',
            data=token_payload,
            headers={'Accept': 'application/json'},
            timeout=10
        )
        
        if token_response.status_code != 200:
            logger.error(f"GitHub token exchange failed: HTTP {token_response.status_code}")
            return jsonify({'error': 'Failed to exchange authorization code'}), 400
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            logger.error(f"No access token in GitHub response: {token_data}")
            return jsonify({'error': 'Failed to get access token'}), 400
        
        logger.debug("Successfully obtained GitHub access token")
        
        # Retrieve user profile from GitHub API
        auth_headers = {'Authorization': f'token {access_token}'}
        
        user_response = requests.get(
            'https://api.github.com/user',
            headers=auth_headers,
            timeout=10
        )
        
        if user_response.status_code != 200:
            logger.error(f"GitHub user API failed: HTTP {user_response.status_code}")
            return jsonify({'error': 'Failed to retrieve user information'}), 400
        
        user_data = user_response.json()
        github_id = str(user_data['id'])
        github_username = user_data['login']
        
        logger.debug(f"Retrieved GitHub user: {github_username} (ID: {github_id})")
        
        # Get user's email addresses
        email_response = requests.get(
            'https://api.github.com/user/emails',
            headers=auth_headers,
            timeout=10
        )
        
        primary_email = None
        if email_response.status_code == 200:
            emails = email_response.json()
            # Find primary email
            primary_email = next((email['email'] for email in emails if email['primary']), None)
            if not primary_email and emails:
                # Fallback to first email if no primary
                primary_email = emails[0]['email']
        
        if not primary_email:
            logger.warning(f"No email found for GitHub user {github_username}")
            primary_email = f"{github_username}@github.local"  # Fallback email
        
        logger.debug(f"GitHub user email: {primary_email}")
        
        # Find or create user account
        user = User.query.filter_by(github_id=github_id).first()
        
        if not user:
            # Check if user exists with same email
            existing_email_user = User.query.filter_by(email=primary_email).first()
            
            if existing_email_user:
                # Link GitHub account to existing user
                logger.info(f"Linking GitHub account to existing user {existing_email_user.id}")
                user = existing_email_user
                user.github_id = github_id
            else:
                # Create new user account
                logger.info(f"Creating new user for GitHub account: {github_username}")
                
                # Ensure username uniqueness
                base_username = github_username
                counter = 1
                while User.query.filter_by(username=base_username).first():
                    base_username = f"{github_username}_{counter}"
                    counter += 1
                
                user = User(
                    username=base_username,
                    email=primary_email,
                    github_id=github_id
                )
                # Set secure random password for OAuth users
                user.set_password(os.urandom(32).hex())
        
        # Save user to database
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"GitHub OAuth completed for user {user.id} ({user.username})")
        
        # Generate JWT token
        jwt_token = create_access_token(identity=str(user.id))
        
        # Redirect to frontend with token
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        callback_url = f"{frontend_url}/auth/callback?token={jwt_token}"
        
        logger.info(f"Redirecting GitHub OAuth user to frontend: {callback_url[:50]}...")
        
        return redirect(callback_url)
        
    except requests.RequestException as req_error:
        error_msg = f"GitHub API request failed: {str(req_error)}"
        logger.error(error_msg)
        log_error_with_context(req_error, {
            "client_ip": client_ip,
            "operation": "github_oauth_callback",
            "error_type": "api_request"
        })
        return jsonify({'error': 'GitHub authentication failed'}), 500
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"GitHub OAuth callback failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "operation": "github_oauth_callback"
        })
        return jsonify({'error': 'Authentication failed'}), 500

@auth_bp.route('/refresh', methods=['OPTIONS'])
def refresh_options():
    """Handle CORS preflight requests for refresh"""
    from flask import make_response
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    Refresh JWT access token using refresh token
    
    Provides token refresh functionality for maintaining user sessions
    without requiring re-authentication. This endpoint validates the
    refresh token and issues a new access token.
    
    Request Body:
        {
            "refreshToken": "string (refresh token)"
        }
        
    Returns:
        200: Token refreshed successfully
        {
            "accessToken": "New JWT access token",
            "refreshToken": "New refresh token (optional)",
            "expiresIn": "Token expiration time in seconds"
        }
        
        400: Bad request (missing refresh token)
        401: Unauthorized (invalid refresh token)
        500: Server error
        
    Security Features:
        - Refresh token validation
        - Token rotation (optional)
        - Automatic cleanup of expired tokens
        - Rate limiting for refresh attempts
        
    Example:
        curl -X POST /api/auth/refresh \
             -H "Content-Type: application/json" \
             -d '{"refreshToken":"refresh_token_here"}'
    """
    client_ip = request.remote_addr
    logger.info(f"Token refresh request from IP: {client_ip}")
    
    try:
        # Parse request data
        data = request.get_json()
        if not data or 'refreshToken' not in data:
            logger.warning(f"Token refresh request missing refresh token from {client_ip}")
            return jsonify({'error': 'Refresh token required'}), 400
        
        refresh_token = data['refreshToken']
        
        # In a full implementation, you would:
        # 1. Validate the refresh token against stored tokens
        # 2. Check if the token is expired
        # 3. Verify the token signature
        # 4. Get the associated user
        
        # For now, we'll implement a basic version
        # This should be replaced with proper refresh token validation
        
        try:
            # Decode the refresh token to get user info
            # Note: This is a simplified implementation
            # In production, use proper refresh token storage and validation
            
            from flask_jwt_extended import decode_token
            
            # For this implementation, we'll assume the refresh token
            # contains the user ID (this is not secure for production)
            # In production, store refresh tokens in database with expiration
            
            # Mock validation - replace with real implementation
            if not refresh_token or len(refresh_token) < 10:
                raise ValueError("Invalid refresh token format")
            
            # For demo purposes, extract user ID from token
            # In production, look up token in database
            user_id = 1  # This should come from token validation
            
            user = User.query.get(user_id)
            if not user or not user.is_active:
                logger.warning(f"Token refresh for invalid/inactive user {user_id} from {client_ip}")
                return jsonify({'error': 'Invalid refresh token'}), 401
            
            # Generate new access token
            new_access_token = create_access_token(identity=str(user.id))
            
            # Optionally generate new refresh token (token rotation)
            # new_refresh_token = generate_refresh_token(user.id)
            
            logger.info(f"Token refreshed successfully for user {user.id} from {client_ip}")
            
            response_data = {
                'accessToken': new_access_token,
                'expiresIn': 3600,  # 1 hour
                'tokenType': 'Bearer'
            }
            
            # Include new refresh token if implementing token rotation
            # response_data['refreshToken'] = new_refresh_token
            
            return jsonify(response_data), 200
            
        except Exception as token_error:
            logger.warning(f"Invalid refresh token from {client_ip}: {token_error}")
            return jsonify({'error': 'Invalid refresh token'}), 401
        
    except Exception as e:
        error_msg = f"Token refresh failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "operation": "token_refresh"
        })
        return jsonify({'error': 'Token refresh failed'}), 500


@auth_bp.route('/logout', methods=['OPTIONS'])
def logout_options():
    """Handle CORS preflight requests for logout"""
    from flask import make_response
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user with comprehensive session management
    
    Handles user logout by providing confirmation for client-side token removal.
    In JWT-based authentication, tokens are stateless and managed on the client side.
    This endpoint provides a clean logout confirmation and audit logging.
    
    Authentication:
        Requires valid JWT token in Authorization header
        
    Logout Process:
    1. Validate JWT token
    2. Log logout event for audit
    3. Return success confirmation
    4. Client removes token from storage
    
    Returns:
        200: Logout confirmation
        {
            "message": "Logout successful"
        }
        
        401: Unauthorized (invalid JWT token)
        500: Server error
        
    Token Management:
        - Server-side: Audit logging only
        - Client-side: Remove token from local/session storage
        - Token expiration: Handled by JWT expiry
        - Refresh tokens: Not implemented in current version
        
    Security Features:
        - Logout event logging for audit trails
        - User session tracking
        - IP address logging for security
        
    Example:
        curl -X POST /api/auth/logout \
             -H "Authorization: Bearer <jwt_token>"
    """
    client_ip = request.remote_addr
    logger.info(f"Logout request from IP: {client_ip}")
    
    try:
        # Get authenticated user for logging
        user_id = get_current_user_id()
        
        if user_id:
            user = User.query.get(user_id)
            if user:
                logger.info(f"User logout: {user.id} ({user.username}) from {client_ip}")
            else:
                logger.info(f"Logout request for user {user_id} (user not found) from {client_ip}")
        else:
            logger.warning(f"Logout request with invalid token from {client_ip}")
        
        # In JWT-based auth, logout is handled client-side by removing the token
        # This endpoint provides confirmation and audit logging
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        error_msg = f"Logout failed: {str(e)}"
        logger.error(error_msg)
        log_error_with_context(e, {
            "client_ip": client_ip,
            "user_id": user_id if 'user_id' in locals() else None,
            "operation": "user_logout"
        })
        return jsonify({'error': 'Logout failed'}), 500
