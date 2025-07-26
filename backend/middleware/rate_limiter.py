"""
Rate limiting middleware for API endpoints
"""

import time
from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import get_jwt_identity, jwt_required
from performance.caching import RateLimitCache
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self):
        self.default_limits = {
            'per_minute': 60,
            'per_hour': 1000,
            'per_day': 10000
        }
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            '/api/chat/query': {
                'per_minute': 30,
                'per_hour': 500,
                'per_day': 2000
            },
            '/api/upload': {
                'per_minute': 10,
                'per_hour': 100,
                'per_day': 500
            },
            '/api/contexts': {
                'per_minute': 20,
                'per_hour': 200,
                'per_day': 1000
            },
            '/api/auth/login': {
                'per_minute': 5,
                'per_hour': 20,
                'per_day': 100
            },
            '/api/auth/register': {
                'per_minute': 3,
                'per_hour': 10,
                'per_day': 50
            }
        }
        
        # User tier limits (for premium users, etc.)
        self.user_tier_multipliers = {
            'free': 1.0,
            'premium': 3.0,
            'enterprise': 10.0
        }
    
    def get_client_identifier(self) -> str:
        """Get unique identifier for the client"""
        # Try to get user ID if authenticated
        try:
            user_id = get_jwt_identity()
            if user_id:
                return f"user:{user_id}"
        except:
            pass
        
        # Fall back to IP address
        return f"ip:{request.remote_addr}"
    
    def get_user_tier(self, user_id: Optional[int] = None) -> str:
        """Get user tier for rate limiting"""
        if not user_id:
            return 'free'
        
        # TODO: Implement user tier lookup from database
        # For now, return 'free' for all users
        return 'free'
    
    def get_limits_for_endpoint(self, endpoint: str, user_tier: str = 'free') -> Dict[str, int]:
        """Get rate limits for specific endpoint and user tier"""
        base_limits = self.endpoint_limits.get(endpoint, self.default_limits)
        multiplier = self.user_tier_multipliers.get(user_tier, 1.0)
        
        return {
            key: int(value * multiplier)
            for key, value in base_limits.items()
        }
    
    def check_rate_limit(self, identifier: str, endpoint: str, user_tier: str = 'free') -> Dict[str, Any]:
        """Check if request is within rate limits"""
        limits = self.get_limits_for_endpoint(endpoint, user_tier)
        results = {}
        
        # Check each time window
        for window, limit in limits.items():
            if window == 'per_minute':
                window_seconds = 60
            elif window == 'per_hour':
                window_seconds = 3600
            elif window == 'per_day':
                window_seconds = 86400
            else:
                continue
            
            key = f"{identifier}:{endpoint}:{window}"
            is_allowed, remaining = RateLimitCache.check_rate_limit(
                key, limit, window_seconds
            )
            
            results[window] = {
                'allowed': is_allowed,
                'limit': limit,
                'remaining': remaining,
                'window_seconds': window_seconds
            }
            
            # If any window is exceeded, deny the request
            if not is_allowed:
                results['denied'] = True
                results['denied_window'] = window
                return results
        
        results['denied'] = False
        return results
    
    def create_rate_limit_response(self, rate_limit_result: Dict[str, Any]) -> tuple:
        """Create rate limit exceeded response"""
        denied_window = rate_limit_result.get('denied_window', 'unknown')
        window_info = rate_limit_result.get(denied_window, {})
        
        response = jsonify({
            'error': 'Rate Limit Exceeded',
            'message': f'Too many requests {denied_window.replace("_", " ")}',
            'limit': window_info.get('limit', 0),
            'remaining': window_info.get('remaining', 0),
            'reset_in_seconds': window_info.get('window_seconds', 0),
            'status_code': 429
        })
        
        # Add rate limit headers
        response.headers['X-RateLimit-Limit'] = str(window_info.get('limit', 0))
        response.headers['X-RateLimit-Remaining'] = str(window_info.get('remaining', 0))
        response.headers['X-RateLimit-Reset'] = str(
            int(time.time()) + window_info.get('window_seconds', 0)
        )
        response.headers['Retry-After'] = str(window_info.get('window_seconds', 60))
        
        return response, 429


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(endpoint: Optional[str] = None):
    """Decorator for rate limiting endpoints"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get endpoint path
            endpoint_path = endpoint or request.endpoint or request.path
            
            # Get client identifier
            identifier = rate_limiter.get_client_identifier()
            
            # Get user tier
            user_tier = 'free'
            try:
                user_id = get_jwt_identity()
                if user_id:
                    user_tier = rate_limiter.get_user_tier(user_id)
            except:
                pass
            
            # Check rate limits
            rate_limit_result = rate_limiter.check_rate_limit(
                identifier, endpoint_path, user_tier
            )
            
            if rate_limit_result.get('denied', False):
                return rate_limiter.create_rate_limit_response(rate_limit_result)
            
            # Add rate limit info to response headers
            response = func(*args, **kwargs)
            
            # Add rate limit headers to successful responses
            if hasattr(response, 'headers'):
                for window, info in rate_limit_result.items():
                    if isinstance(info, dict) and 'limit' in info:
                        response.headers[f'X-RateLimit-{window.title()}'] = str(info['limit'])
                        response.headers[f'X-RateLimit-{window.title()}-Remaining'] = str(info['remaining'])
            
            return response
        
        return wrapper
    return decorator


def rate_limit_by_user(per_minute: int = 60, per_hour: int = 1000):
    """Simple rate limiting by user ID"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            identifier = f"user:{user_id}"
            
            # Check per-minute limit
            minute_allowed, minute_remaining = RateLimitCache.check_rate_limit(
                f"{identifier}:minute", per_minute, 60
            )
            
            if not minute_allowed:
                return jsonify({
                    'error': 'Rate Limit Exceeded',
                    'message': f'Maximum {per_minute} requests per minute exceeded',
                    'limit': per_minute,
                    'remaining': minute_remaining,
                    'reset_in_seconds': 60
                }), 429
            
            # Check per-hour limit
            hour_allowed, hour_remaining = RateLimitCache.check_rate_limit(
                f"{identifier}:hour", per_hour, 3600
            )
            
            if not hour_allowed:
                return jsonify({
                    'error': 'Rate Limit Exceeded',
                    'message': f'Maximum {per_hour} requests per hour exceeded',
                    'limit': per_hour,
                    'remaining': hour_remaining,
                    'reset_in_seconds': 3600
                }), 429
            
            # Execute the function
            response = func(*args, **kwargs)
            
            # Add rate limit headers
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Minute'] = str(per_minute)
                response.headers['X-RateLimit-Minute-Remaining'] = str(minute_remaining)
                response.headers['X-RateLimit-Hour'] = str(per_hour)
                response.headers['X-RateLimit-Hour-Remaining'] = str(hour_remaining)
            
            return response
        
        return wrapper
    return decorator


def rate_limit_by_ip(per_minute: int = 100):
    """Simple rate limiting by IP address"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            identifier = f"ip:{request.remote_addr}"
            
            allowed, remaining = RateLimitCache.check_rate_limit(
                identifier, per_minute, 60
            )
            
            if not allowed:
                return jsonify({
                    'error': 'Rate Limit Exceeded',
                    'message': f'Maximum {per_minute} requests per minute exceeded',
                    'limit': per_minute,
                    'remaining': remaining,
                    'reset_in_seconds': 60
                }), 429
            
            response = func(*args, **kwargs)
            
            # Add rate limit headers
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(per_minute)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Reset'] = str(int(time.time()) + 60)
            
            return response
        
        return wrapper
    return decorator


class RateLimitMiddleware:
    """Flask middleware for automatic rate limiting"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Check rate limits before processing request"""
        # Skip rate limiting for certain endpoints
        skip_endpoints = ['/api/health', '/api/docs']
        
        if request.endpoint in skip_endpoints:
            return
        
        # Apply rate limiting
        identifier = rate_limiter.get_client_identifier()
        endpoint_path = request.endpoint or request.path
        
        user_tier = 'free'
        try:
            user_id = get_jwt_identity()
            if user_id:
                user_tier = rate_limiter.get_user_tier(user_id)
        except:
            pass
        
        rate_limit_result = rate_limiter.check_rate_limit(
            identifier, endpoint_path, user_tier
        )
        
        if rate_limit_result.get('denied', False):
            return rate_limiter.create_rate_limit_response(rate_limit_result)
        
        # Store rate limit info for after_request
        g.rate_limit_result = rate_limit_result
    
    def after_request(self, response):
        """Add rate limit headers to response"""
        if hasattr(g, 'rate_limit_result'):
            rate_limit_result = g.rate_limit_result
            
            for window, info in rate_limit_result.items():
                if isinstance(info, dict) and 'limit' in info:
                    response.headers[f'X-RateLimit-{window.title()}'] = str(info['limit'])
                    response.headers[f'X-RateLimit-{window.title()}-Remaining'] = str(info['remaining'])
        
        return response
