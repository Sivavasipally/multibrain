"""
Enhanced error handling and logging service
"""

import logging
import traceback
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from functools import wraps
from flask import request, jsonify, current_app
import os


class ErrorHandler:
    """Enhanced error handling with structured logging"""
    
    def __init__(self, app=None):
        self.app = app
        self.error_counts = {}
        self.setup_logging()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize error handler with Flask app"""
        self.app = app
        
        # Register error handlers
        app.errorhandler(400)(self.handle_bad_request)
        app.errorhandler(401)(self.handle_unauthorized)
        app.errorhandler(403)(self.handle_forbidden)
        app.errorhandler(404)(self.handle_not_found)
        app.errorhandler(422)(self.handle_unprocessable_entity)
        app.errorhandler(429)(self.handle_rate_limit)
        app.errorhandler(500)(self.handle_internal_error)
        app.errorhandler(Exception)(self.handle_generic_exception)
    
    def setup_logging(self):
        """Setup structured logging"""
        # Create logs directory if it doesn't exist
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{log_dir}/app.log'),
                logging.StreamHandler()
            ]
        )
        
        # Create specialized loggers
        self.error_logger = logging.getLogger('error')
        self.access_logger = logging.getLogger('access')
        self.security_logger = logging.getLogger('security')
        
        # Add file handlers for specialized logs
        error_handler = logging.FileHandler(f'{log_dir}/errors.log')
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.error_logger.addHandler(error_handler)
        
        access_handler = logging.FileHandler(f'{log_dir}/access.log')
        access_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
        self.access_logger.addHandler(access_handler)
        
        security_handler = logging.FileHandler(f'{log_dir}/security.log')
        security_handler.setFormatter(logging.Formatter(
            '%(asctime)s - SECURITY - %(message)s'
        ))
        self.security_logger.addHandler(security_handler)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context"""
        error_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        # Add request context if available
        try:
            if request:
                error_data['request'] = {
                    'method': request.method,
                    'url': request.url,
                    'endpoint': request.endpoint,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent'),
                    'content_type': request.content_type
                }
        except RuntimeError:
            # Outside request context
            pass
        
        self.error_logger.error(json.dumps(error_data, indent=2))
        
        # Track error counts
        error_key = f"{type(error).__name__}:{str(error)[:100]}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
    
    def log_access(self, response_status: int, response_time: float):
        """Log access information"""
        try:
            if request:
                access_data = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'method': request.method,
                    'url': request.url,
                    'status': response_status,
                    'response_time': response_time,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent')
                }
                
                self.access_logger.info(json.dumps(access_data))
        except RuntimeError:
            pass
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events"""
        security_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': event_type,
            'details': details
        }
        
        try:
            if request:
                security_data['request_info'] = {
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent'),
                    'endpoint': request.endpoint
                }
        except RuntimeError:
            pass
        
        self.security_logger.warning(json.dumps(security_data))
    
    def handle_bad_request(self, error):
        """Handle 400 Bad Request errors"""
        self.log_error(error, {'error_type': 'bad_request'})
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server',
            'status_code': 400
        }), 400
    
    def handle_unauthorized(self, error):
        """Handle 401 Unauthorized errors"""
        self.log_security_event('unauthorized_access', {
            'error': str(error)
        })
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required',
            'status_code': 401
        }), 401
    
    def handle_forbidden(self, error):
        """Handle 403 Forbidden errors"""
        self.log_security_event('forbidden_access', {
            'error': str(error)
        })
        return jsonify({
            'error': 'Forbidden',
            'message': 'Access denied',
            'status_code': 403
        }), 403
    
    def handle_not_found(self, error):
        """Handle 404 Not Found errors"""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404
    
    def handle_unprocessable_entity(self, error):
        """Handle 422 Unprocessable Entity errors"""
        self.log_error(error, {'error_type': 'validation_error'})
        return jsonify({
            'error': 'Unprocessable Entity',
            'message': 'The request was well-formed but contains semantic errors',
            'status_code': 422
        }), 422
    
    def handle_rate_limit(self, error):
        """Handle 429 Rate Limit errors"""
        self.log_security_event('rate_limit_exceeded', {
            'error': str(error)
        })
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later.',
            'status_code': 429
        }), 429
    
    def handle_internal_error(self, error):
        """Handle 500 Internal Server errors"""
        self.log_error(error, {'error_type': 'internal_server_error'})
        
        # Don't expose internal error details in production
        if current_app.debug:
            return jsonify({
                'error': 'Internal Server Error',
                'message': str(error),
                'traceback': traceback.format_exc(),
                'status_code': 500
            }), 500
        else:
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred',
                'status_code': 500
            }), 500
    
    def handle_generic_exception(self, error):
        """Handle any unhandled exceptions"""
        self.log_error(error, {'error_type': 'unhandled_exception'})
        
        if current_app.debug:
            return jsonify({
                'error': 'Unhandled Exception',
                'message': str(error),
                'type': type(error).__name__,
                'traceback': traceback.format_exc(),
                'status_code': 500
            }), 500
        else:
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred',
                'status_code': 500
            }), 500
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'unique_errors': len(self.error_counts),
            'top_errors': sorted(
                self.error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }


def handle_api_errors(func):
    """Decorator for handling API errors gracefully"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return jsonify({
                'error': 'Validation Error',
                'message': str(e),
                'status_code': 400
            }), 400
        except PermissionError as e:
            return jsonify({
                'error': 'Permission Denied',
                'message': str(e),
                'status_code': 403
            }), 403
        except FileNotFoundError as e:
            return jsonify({
                'error': 'Resource Not Found',
                'message': str(e),
                'status_code': 404
            }), 404
        except Exception as e:
            # Log the error
            if hasattr(current_app, 'error_handler'):
                current_app.error_handler.log_error(e)
            
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred',
                'status_code': 500
            }), 500
    
    return wrapper


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class AuthenticationError(Exception):
    """Custom authentication error"""
    pass


class AuthorizationError(Exception):
    """Custom authorization error"""
    pass


class ResourceNotFoundError(Exception):
    """Custom resource not found error"""
    pass


class RateLimitError(Exception):
    """Custom rate limit error"""
    pass


# Global error handler instance
error_handler = ErrorHandler()
