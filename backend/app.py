"""
RAG Chatbot PWA - Flask Backend Application
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.url_map.strict_slashes = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ragchatbot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')

# Celery configuration
app.config['CELERY_BROKER_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Initialize extensions
from database import db
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
# COMPREHENSIVE CORS CONFIGURATION
# Allow ALL requests from localhost and 127.0.0.1 on ANY port
CORS(app, 
     origins=["*"],  # Allow all origins
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
     supports_credentials=False,
     send_wildcard=True)

# Add manual CORS headers as backup for complex requests
@app.after_request
def after_request_cors(response):
    origin = request.headers.get('Origin')
    if origin and ('localhost' in origin or '127.0.0.1' in origin):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
        response.headers['Access-Control-Max-Age'] = '86400'
    return response

# Handle preflight OPTIONS requests
@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        origin = request.headers.get('Origin')
        if origin and ('localhost' in origin or '127.0.0.1' in origin):
            from flask import make_response
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
            response.headers['Access-Control-Max-Age'] = '86400'
            return response

# Initialize Celery
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

# Import models and routes
from models import User, Context, ChatSession, Message
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.contexts import contexts_bp
from routes.chat import chat_bp
from routes.upload import upload_bp
from routes.versions import versions_bp
from routes.tasks import tasks_bp
from routes.preferences import preferences_bp

# Register blueprints
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(contexts_bp, url_prefix='/api/contexts')
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(upload_bp, url_prefix='/api/upload')
app.register_blueprint(versions_bp, url_prefix='/api')
app.register_blueprint(tasks_bp, url_prefix='/api')
app.register_blueprint(preferences_bp)

@app.route('/api/errors/report', methods=['POST'])
def report_error():
    """Simple error reporting endpoint"""
    try:
        error_data = request.get_json()
        logger.warning(f"Frontend error reported: {error_data}")
        return jsonify({'status': 'error_reported', 'timestamp': datetime.now().isoformat()}), 200
    except Exception as e:
        logger.error(f"Error handling error report: {e}")
        return jsonify({'error': 'Failed to process error report'}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'RAG Chatbot API is running'})

@app.route('/api/cors-test', methods=['GET', 'POST', 'OPTIONS'])
def cors_test():
    """Test endpoint to verify CORS is working"""
    return jsonify({'message': 'CORS is working!', 'method': request.method})

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Start background task service
    from services.task_service import start_task_service
    start_task_service(num_workers=3)  # More workers for production
    print("Background task service started with 3 workers")
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )
