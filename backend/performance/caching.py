"""
Caching strategies for RAG Chatbot PWA
Implements Redis-based caching for improved performance
"""

import json
import hashlib
from functools import wraps
from typing import Any, Optional, Union
import redis
from flask import current_app
import pickle
import time

class CacheManager:
    """Centralized cache management with Redis backend."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_ttl = 3600  # 1 hour
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            current_app.logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            ttl = ttl or self.default_ttl
            serialized = pickle.dumps(value)
            return self.redis.setex(key, ttl, serialized)
        except Exception as e:
            current_app.logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            current_app.logger.error(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            current_app.logger.error(f"Cache delete pattern error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            current_app.logger.error(f"Cache exists error: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache."""
        try:
            return self.redis.incr(key, amount)
        except Exception as e:
            current_app.logger.error(f"Cache increment error: {e}")
            return None

# Global cache instance
cache = None

def init_cache(redis_client: redis.Redis):
    """Initialize cache manager."""
    global cache
    cache = CacheManager(redis_client)

def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()

def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache:
                return func(*args, **kwargs)
            
            # Generate cache key
            func_key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            result = cache.get(func_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(func_key, result, ttl)
            return result
        
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Invalidate cache entries matching pattern."""
    if cache:
        return cache.delete_pattern(pattern)
    return 0

# Specific caching strategies

class ContextCache:
    """Caching for context-related operations."""
    
    @staticmethod
    @cached(ttl=1800, key_prefix="context")
    def get_context_embeddings(context_id: int):
        """Cache context embeddings."""
        from models import Context, db
        from services.vector_service import VectorService

        context = db.session.get(Context, context_id)
        if not context or not context.vector_store_path:
            return None

        try:
            vector_service = VectorService(context.embedding_model)
            store_info = vector_service.get_vector_store_info(context.vector_store_path)
            return {
                'context_id': context_id,
                'total_chunks': store_info.get('total_chunks', 0),
                'embedding_model': store_info.get('embedding_model', 'unknown'),
                'dimension': store_info.get('dimension', 0)
            }
        except Exception as e:
            print(f"Error getting context embeddings: {e}")
            return None

    @staticmethod
    @cached(ttl=3600, key_prefix="context_meta")
    def get_context_metadata(context_id: int):
        """Cache context metadata."""
        from models import Context, Document, db

        context = db.session.get(Context, context_id)
        if not context:
            return None

        documents = Document.query.filter_by(context_id=context_id).all()

        return {
            'context_id': context_id,
            'name': context.name,
            'source_type': context.source_type,
            'status': context.status,
            'total_chunks': context.total_chunks,
            'total_tokens': context.total_tokens,
            'document_count': len(documents),
            'created_at': context.created_at.isoformat() if context.created_at else None,
            'updated_at': context.updated_at.isoformat() if context.updated_at else None
        }
    
    @staticmethod
    def invalidate_context(context_id: int):
        """Invalidate all cache entries for a context."""
        patterns = [
            f"context:*:{context_id}*",
            f"context_meta:*:{context_id}*",
            f"search:*:{context_id}*"
        ]
        for pattern in patterns:
            invalidate_cache(pattern)

class SearchCache:
    """Caching for search operations."""
    
    @staticmethod
    @cached(ttl=900, key_prefix="search")
    def get_search_results(query: str, context_ids: list, top_k: int = 5):
        """Cache search results."""
        from models import Context, db
        from services.vector_service import VectorService

        all_results = []

        for context_id in context_ids:
            context = db.session.get(Context, context_id)
            if not context or not context.vector_store_path:
                continue

            try:
                vector_service = VectorService(context.embedding_model)
                results = vector_service.search_similar(
                    context.vector_store_path,
                    query,
                    top_k=top_k
                )

                # Add context information to results
                for result in results:
                    result['context_id'] = context_id
                    result['context_name'] = context.name

                all_results.extend(results)

            except Exception as e:
                print(f"Error searching context {context_id}: {e}")
                continue

        # Sort by score and limit results
        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return all_results[:top_k * len(context_ids)]

    @staticmethod
    @cached(ttl=1800, key_prefix="search_embeddings")
    def get_query_embedding(query: str):
        """Cache query embeddings."""
        from services.gemini_service import GeminiService

        try:
            gemini_service = GeminiService()
            embedding = gemini_service.create_query_embedding(query)
            return {
                'query': query,
                'embedding': embedding,
                'model': 'text-embedding-004'
            }
        except Exception as e:
            print(f"Error creating query embedding: {e}")
            return None

class UserCache:
    """Caching for user-related operations."""
    
    @staticmethod
    @cached(ttl=1800, key_prefix="user")
    def get_user_contexts(user_id: int):
        """Cache user's contexts."""
        from models import Context, db

        contexts = Context.query.filter_by(user_id=user_id).all()

        return [{
            'id': context.id,
            'name': context.name,
            'source_type': context.source_type,
            'status': context.status,
            'total_chunks': context.total_chunks,
            'total_tokens': context.total_tokens,
            'created_at': context.created_at.isoformat() if context.created_at else None,
            'updated_at': context.updated_at.isoformat() if context.updated_at else None
        } for context in contexts]

    @staticmethod
    @cached(ttl=3600, key_prefix="user_profile")
    def get_user_profile(user_id: int):
        """Cache user profile."""
        from models import User, Context, ChatSession, db

        user = db.session.get(User, user_id)
        if not user:
            return None

        # Get user statistics
        context_count = Context.query.filter_by(user_id=user_id).count()
        session_count = ChatSession.query.filter_by(user_id=user_id).count()

        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'stats': {
                'context_count': context_count,
                'session_count': session_count
            }
        }
    
    @staticmethod
    def invalidate_user(user_id: int):
        """Invalidate all cache entries for a user."""
        patterns = [
            f"user:*:{user_id}*",
            f"user_profile:*:{user_id}*"
        ]
        for pattern in patterns:
            invalidate_cache(pattern)

class RateLimitCache:
    """Rate limiting using cache."""
    
    @staticmethod
    def check_rate_limit(identifier: str, limit: int, window: int) -> tuple[bool, int]:
        """
        Check if request is within rate limit.
        Returns (is_allowed, remaining_requests)
        """
        if not cache:
            return True, limit
        
        key = f"rate_limit:{identifier}"
        current_count = cache.get(key) or 0
        
        if current_count >= limit:
            return False, 0
        
        # Increment counter
        new_count = cache.increment(key) or 1
        
        # Set expiration on first request
        if new_count == 1:
            cache.redis.expire(key, window)
        
        remaining = max(0, limit - new_count)
        return True, remaining

class SessionCache:
    """Caching for session data."""
    
    @staticmethod
    def store_session_data(session_id: str, data: dict, ttl: int = 3600):
        """Store session data in cache."""
        if cache:
            key = f"session:{session_id}"
            cache.set(key, data, ttl)
    
    @staticmethod
    def get_session_data(session_id: str) -> Optional[dict]:
        """Get session data from cache."""
        if cache:
            key = f"session:{session_id}"
            return cache.get(key)
        return None
    
    @staticmethod
    def invalidate_session(session_id: str):
        """Invalidate session data."""
        if cache:
            key = f"session:{session_id}"
            cache.delete(key)

# Cache warming strategies
class CacheWarmer:
    """Strategies for warming up cache with frequently accessed data."""
    
    @staticmethod
    def warm_user_data(user_id: int):
        """Pre-load user's frequently accessed data."""
        try:
            # Pre-load user profile
            UserCache.get_user_profile(user_id)

            # Pre-load user contexts
            UserCache.get_user_contexts(user_id)

            # Pre-load context metadata for user's contexts
            from models import Context
            contexts = Context.query.filter_by(user_id=user_id).all()
            for context in contexts:
                ContextCache.get_context_metadata(context.id)
                ContextCache.get_context_embeddings(context.id)

            print(f"Warmed cache for user {user_id}")

        except Exception as e:
            print(f"Error warming user data cache: {e}")

    @staticmethod
    def warm_popular_contexts():
        """Pre-load popular contexts."""
        try:
            from models import Context, Message, db
            from sqlalchemy import func, desc

            # Find most referenced contexts in chat messages
            popular_contexts = db.session.query(
                Context.id,
                func.count(Message.id).label('usage_count')
            ).join(
                Message,
                func.json_contains(Message.context_ids, func.cast(Context.id, db.Text))
            ).group_by(
                Context.id
            ).order_by(
                desc('usage_count')
            ).limit(10).all()

            for context_id, _ in popular_contexts:
                ContextCache.get_context_metadata(context_id)
                ContextCache.get_context_embeddings(context_id)

            print(f"Warmed cache for {len(popular_contexts)} popular contexts")

        except Exception as e:
            print(f"Error warming popular contexts cache: {e}")

    @staticmethod
    def warm_search_cache():
        """Pre-load common search queries."""
        try:
            from models import Message
            from collections import Counter

            # Get common user queries
            recent_messages = Message.query.filter_by(role='user').limit(1000).all()
            query_words = []

            for message in recent_messages:
                words = message.content.lower().split()
                query_words.extend([word for word in words if len(word) > 3])

            # Get most common words/phrases
            common_words = Counter(query_words).most_common(20)

            for word, _ in common_words:
                SearchCache.get_query_embedding(word)

            print(f"Warmed search cache for {len(common_words)} common queries")

        except Exception as e:
            print(f"Error warming search cache: {e}")

# Cache monitoring
class CacheMonitor:
    """Monitor cache performance and health."""
    
    @staticmethod
    def get_cache_stats() -> dict:
        """Get cache statistics."""
        if not cache:
            return {}
        
        try:
            info = cache.redis.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0))
            }
        except Exception as e:
            current_app.logger.error(f"Cache stats error: {e}")
            return {}
    
    @staticmethod
    def get_cache_size() -> int:
        """Get number of keys in cache."""
        if cache:
            try:
                return cache.redis.dbsize()
            except Exception:
                return 0
        return 0
    
    @staticmethod
    def flush_cache():
        """Flush all cache data (use with caution)."""
        if cache:
            try:
                return cache.redis.flushdb()
            except Exception as e:
                current_app.logger.error(f"Cache flush error: {e}")
                return False
        return False

# Cache configuration
CACHE_CONFIG = {
    'default_ttl': 3600,
    'context_ttl': 1800,
    'search_ttl': 900,
    'user_ttl': 1800,
    'session_ttl': 3600,
    'rate_limit_window': 60,
    'max_memory_policy': 'allkeys-lru',
    'key_prefixes': {
        'context': 'ctx',
        'search': 'srch',
        'user': 'usr',
        'session': 'sess',
        'rate_limit': 'rl'
    }
}
