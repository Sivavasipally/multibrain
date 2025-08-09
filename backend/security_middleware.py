"""
Security middleware for RAG Chatbot PWA
Includes rate limiting, security headers, and request validation
"""

import time
import hashlib
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from functools import wraps
from flask import request, jsonify, g
import ipaddress
from logging_config import get_logger

logger = get_logger('security')


class RateLimiter:
    """Token bucket rate limiter with sliding window"""
    
    def __init__(self):
        self.buckets = defaultdict(lambda: {'tokens': 0, 'last_refill': time.time()})
        self.request_history = defaultdict(lambda: deque(maxlen=1000))
        
    def is_allowed(self, key: str, limit: int, window: int = 3600) -> Tuple[bool, Dict]:
        """
        Check if request is allowed under rate limit
        
        Args:
            key: Unique identifier (e.g., IP address, user ID)
            limit: Maximum requests per window
            window: Time window in seconds (default 1 hour)
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        now = time.time()
        bucket = self.buckets[key]
        history = self.request_history[key]
        
        # Clean old requests from history
        cutoff_time = now - window
        while history and history[0] < cutoff_time:
            history.popleft()
        
        # Check current request count
        current_requests = len(history)
        
        if current_requests >= limit:
            return False, {
                'limit': limit,
                'remaining': 0,
                'reset_time': int(history[0] + window) if history else int(now + window),
                'retry_after': int(window - (now - history[0])) if history else window
            }
        
        # Allow request and record it
        history.append(now)
        
        return True, {
            'limit': limit,
            'remaining': limit - len(history),
            'reset_time': int(now + window),
            'retry_after': 0
        }


class SecurityMiddleware:
    """Comprehensive security middleware"""
    
    def __init__(self, app=None):
        self.app = app
        self.rate_limiter = RateLimiter()
        self.blocked_ips = set()
        self.suspicious_activity = defaultdict(int)
        
        # Security configuration
        self.config = {
            'rate_limits': {
                'default': {'limit': 1000, 'window': 3600},  # 1000 requests per hour
                'auth': {'limit': 10, 'window': 300},         # 10 auth attempts per 5 min
                'upload': {'limit': 20, 'window': 3600},      # 20 uploads per hour
                'admin': {'limit': 100, 'window': 3600}       # 100 admin requests per hour
            },
            'blocked_user_agents': [
                'bot', 'crawler', 'spider', 'scraper', 'scanner'
            ],
            'allowed_origins': [
                'http://localhost:3000',
                'http://localhost:5173',
                'http://127.0.0.1:3000',
                'http://127.0.0.1:5173'
            ],
            'max_request_size': 100 * 1024 * 1024,  # 100MB
            'security_headers': {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'",
                'Referrer-Policy': 'strict-origin-when-cross-origin',
                'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
            }
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.errorhandler(429)(self.rate_limit_handler)
        app.errorhandler(403)(self.forbidden_handler)
    
    def before_request(self):
        """Process request before routing"""
        # Record request start time
        g.start_time = time.time()
        
        # Get client IP
        client_ip = self.get_client_ip()
        g.client_ip = client_ip
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return jsonify({'error': 'Access denied'}), 403
        
        # Check request size
        if request.content_length and request.content_length > self.config['max_request_size']:
            logger.warning(f"Request too large: {request.content_length} bytes from {client_ip}")
            return jsonify({'error': 'Request too large'}), 413
        
        # Check User-Agent
        user_agent = request.headers.get('User-Agent', '').lower()
        if any(blocked in user_agent for blocked in self.config['blocked_user_agents']):
            logger.warning(f"Blocked User-Agent: {user_agent} from {client_ip}")
            return jsonify({'error': 'Access denied'}), 403
        
        # Apply rate limiting
        rate_limit_result = self.apply_rate_limiting()
        if rate_limit_result:
            return rate_limit_result
        
        # Check for suspicious patterns
        self.detect_suspicious_activity()
    
    def after_request(self, response):
        """Process response after request handling"""
        # Add security headers
        for header, value in self.config['security_headers'].items():
            response.headers[header] = value
        
        # Add rate limit headers if available
        if hasattr(g, 'rate_limit_info'):
            info = g.rate_limit_info
            response.headers['X-RateLimit-Limit'] = str(info['limit'])
            response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
            response.headers['X-RateLimit-Reset'] = str(info['reset_time'])
        
        # Log request if it took too long
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            if duration > 5:  # Log requests taking more than 5 seconds
                logger.warning(f"Slow request: {request.method} {request.path} took {duration:.2f}s")
        
        return response
    
    def get_client_ip(self) -> str:
        """Get client IP address with proxy support"""
        # Check for forwarded headers (in order of trust)
        forwarded_headers = [
            'X-Forwarded-For',
            'X-Real-IP',
            'CF-Connecting-IP',
            'X-Forwarded'
        ]
        
        for header in forwarded_headers:
            if header in request.headers:
                # Take the first IP in case of multiple
                ip = request.headers[header].split(',')[0].strip()
                try:
                    # Validate IP address
                    ipaddress.ip_address(ip)
                    return ip
                except ValueError:
                    continue
        
        return request.remote_addr or '127.0.0.1'
    
    def apply_rate_limiting(self) -> Optional:
        """Apply rate limiting based on endpoint and user"""
        # Determine rate limit category
        path = request.path
        rate_limit_key = 'default'
        
        if path.startswith('/api/auth/'):
            rate_limit_key = 'auth'
        elif path.startswith('/api/upload/'):
            rate_limit_key = 'upload'
        elif path.startswith('/api/admin/'):
            rate_limit_key = 'admin'
        
        # Create unique key (IP + user if authenticated)
        key_parts = [g.client_ip]
        
        # Add user ID if authenticated
        try:
            from flask_jwt_extended import get_jwt_identity
            user_id = get_jwt_identity()
            if user_id:
                key_parts.append(f"user:{user_id}")
        except:
            pass
        
        rate_key = ":".join(key_parts)
        
        # Check rate limit
        limit_config = self.config['rate_limits'][rate_limit_key]
        is_allowed, rate_info = self.rate_limiter.is_allowed(
            rate_key,
            limit_config['limit'],
            limit_config['window']
        )
        
        # Store rate limit info for headers
        g.rate_limit_info = rate_info
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded: {rate_key} on {path}")
            return self.rate_limit_handler(None)
        
        return None
    
    def detect_suspicious_activity(self):
        """Detect and respond to suspicious activity patterns"""
        client_ip = g.client_ip
        
        # Check for rapid requests
        now = time.time()
        if not hasattr(g, 'request_times'):
            g.request_times = deque(maxlen=10)
        
        g.request_times.append(now)
        
        # If more than 5 requests in 1 second
        if len(g.request_times) >= 5:
            if g.request_times[-1] - g.request_times[-5] < 1:
                self.suspicious_activity[client_ip] += 1
                logger.warning(f"Rapid requests detected from {client_ip}")
        
        # Check for suspicious paths
        suspicious_paths = [
            'admin', 'wp-admin', 'phpmyadmin', '.env', 'config',
            'backup', 'database', 'login.php', 'admin.php'
        ]
        
        if any(suspicious in request.path.lower() for suspicious in suspicious_paths):
            self.suspicious_activity[client_ip] += 1
            logger.warning(f"Suspicious path access: {request.path} from {client_ip}")
        
        # Block IP if too much suspicious activity
        if self.suspicious_activity[client_ip] >= 5:
            self.blocked_ips.add(client_ip)
            logger.error(f"Blocking IP due to suspicious activity: {client_ip}")
    
    def rate_limit_handler(self, error):
        """Handle rate limit exceeded"""
        retry_after = g.rate_limit_info.get('retry_after', 3600) if hasattr(g, 'rate_limit_info') else 3600
        
        response = jsonify({
            'error': 'Rate limit exceeded',
            'message': f'Too many requests. Please try again in {retry_after} seconds.'
        })
        response.status_code = 429
        response.headers['Retry-After'] = str(retry_after)
        
        return response
    
    def forbidden_handler(self, error):
        """Handle forbidden access"""
        return jsonify({
            'error': 'Access forbidden',
            'message': 'You do not have permission to access this resource.'
        }), 403
    
    def unblock_ip(self, ip_address: str) -> bool:
        """Manually unblock an IP address"""
        if ip_address in self.blocked_ips:
            self.blocked_ips.remove(ip_address)
            if ip_address in self.suspicious_activity:
                del self.suspicious_activity[ip_address]
            logger.info(f"Unblocked IP address: {ip_address}")
            return True
        return False
    
    def get_blocked_ips(self) -> List[str]:
        """Get list of currently blocked IPs"""
        return list(self.blocked_ips)
    
    def get_rate_limit_status(self, key: str) -> Dict:
        """Get rate limit status for a key"""
        limit_config = self.config['rate_limits']['default']
        _, rate_info = self.rate_limiter.is_allowed(
            key, 
            limit_config['limit'], 
            limit_config['window']
        )
        return rate_info


def require_rate_limit(category: str = 'default'):
    """Decorator to apply specific rate limiting to endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Rate limiting is handled in middleware
            # This decorator is for documentation and potential custom logic
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_secure_headers():
    """Decorator to ensure secure headers are applied"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            # Additional secure headers for sensitive endpoints
            if hasattr(response, 'headers'):
                response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response.headers['Pragma'] = 'no-cache'
            return response
        return decorated_function
    return decorator


# Example usage
if __name__ == "__main__":
    from flask import Flask
    
    app = Flask(__name__)
    security = SecurityMiddleware(app)
    
    @app.route('/')
    def index():
        return "Hello, World!"
    
    @app.route('/api/test')
    @require_rate_limit('default')
    def test():
        return jsonify({'message': 'Test endpoint'})
    
    app.run(debug=True)