import os
import time
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

# Redis connection for production rate limiting
try:
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_available = True
except:
    redis_available = False
    # Fallback to in-memory storage
    memory_store = {}

class AdvancedRateLimiter:
    """Advanced rate limiter with user-based and IP-based limits"""
    
    def __init__(self):
        self.redis_available = redis_available
        
    def get_key(self, identifier, endpoint):
        """Generate cache key for rate limiting"""
        return f"rate_limit:{identifier}:{endpoint}"
    
    def get_user_key(self, user_id, endpoint):
        """Generate user-based rate limit key"""
        return f"rate_limit:user:{user_id}:{endpoint}"
    
    def get_ip_key(self, ip, endpoint):
        """Generate IP-based rate limit key"""
        return f"rate_limit:ip:{ip}:{endpoint}"
    
    def check_rate_limit(self, key, limit, window_seconds):
        """Check if request is within rate limit"""
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        if self.redis_available:
            try:
                # Use Redis for production
                pipe = redis_client.pipeline()
                
                # Remove old entries
                pipe.zremrangebyscore(key, 0, window_start)
                
                # Count current requests
                pipe.zcard(key)
                
                # Add current request
                pipe.zadd(key, {str(current_time): current_time})
                
                # Set expiry
                pipe.expire(key, window_seconds)
                
                results = pipe.execute()
                current_count = results[1]
                
                return current_count < limit, current_count
                
            except Exception as e:
                print(f"Redis error: {e}")
                # Fallback to memory store
                pass
        
        # Memory-based fallback
        if key not in memory_store:
            memory_store[key] = []
        
        # Clean old entries
        memory_store[key] = [
            timestamp for timestamp in memory_store[key] 
            if timestamp > window_start
        ]
        
        current_count = len(memory_store[key])
        
        if current_count < limit:
            memory_store[key].append(current_time)
            return True, current_count + 1
        
        return False, current_count
    
    def rate_limit(self, limits):
        """
        Decorator for rate limiting endpoints
        
        Args:
            limits: dict with rate limit configurations
                {
                    'per_ip': {'limit': 100, 'window': 3600},  # 100 requests per hour per IP
                    'per_user': {'limit': 1000, 'window': 3600},  # 1000 requests per hour per user
                    'anonymous': {'limit': 10, 'window': 3600}  # 10 requests per hour for anonymous
                }
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                endpoint = request.endpoint or f.__name__
                ip_address = get_remote_address()
                user_id = getattr(request, 'current_user_id', None)
                
                # Check IP-based rate limit
                if 'per_ip' in limits:
                    ip_key = self.get_ip_key(ip_address, endpoint)
                    ip_limit = limits['per_ip']['limit']
                    ip_window = limits['per_ip']['window']
                    
                    allowed, count = self.check_rate_limit(ip_key, ip_limit, ip_window)
                    if not allowed:
                        return jsonify({
                            'error': 'Rate limit exceeded for IP address',
                            'limit': ip_limit,
                            'window': ip_window,
                            'current_count': count
                        }), 429
                
                # Check user-based rate limit (if authenticated)
                if user_id and 'per_user' in limits:
                    user_key = self.get_user_key(user_id, endpoint)
                    user_limit = limits['per_user']['limit']
                    user_window = limits['per_user']['window']
                    
                    allowed, count = self.check_rate_limit(user_key, user_limit, user_window)
                    if not allowed:
                        return jsonify({
                            'error': 'Rate limit exceeded for user',
                            'limit': user_limit,
                            'window': user_window,
                            'current_count': count
                        }), 429
                
                # Check anonymous rate limit (if not authenticated)
                elif not user_id and 'anonymous' in limits:
                    anon_key = self.get_ip_key(ip_address, f"{endpoint}:anonymous")
                    anon_limit = limits['anonymous']['limit']
                    anon_window = limits['anonymous']['window']
                    
                    allowed, count = self.check_rate_limit(anon_key, anon_limit, anon_window)
                    if not allowed:
                        return jsonify({
                            'error': 'Rate limit exceeded for anonymous users',
                            'limit': anon_limit,
                            'window': anon_window,
                            'current_count': count,
                            'message': 'Please sign in for higher rate limits'
                        }), 429
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator

# Global rate limiter instance
advanced_limiter = AdvancedRateLimiter()

# Pre-configured rate limit decorators
def upload_rate_limit(f):
    """Rate limit for upload endpoints"""
    return advanced_limiter.rate_limit({
        'per_ip': {'limit': 50, 'window': 3600},  # 50 uploads per hour per IP
        'per_user': {'limit': 200, 'window': 3600},  # 200 uploads per hour per user
        'anonymous': {'limit': 5, 'window': 3600}  # 5 uploads per hour for anonymous
    })(f)

def download_rate_limit(f):
    """Rate limit for download endpoints"""
    return advanced_limiter.rate_limit({
        'per_ip': {'limit': 200, 'window': 3600},  # 200 downloads per hour per IP
        'per_user': {'limit': 1000, 'window': 3600},  # 1000 downloads per hour per user
        'anonymous': {'limit': 50, 'window': 3600}  # 50 downloads per hour for anonymous
    })(f)

def api_rate_limit(f):
    """Rate limit for general API endpoints"""
    return advanced_limiter.rate_limit({
        'per_ip': {'limit': 1000, 'window': 3600},  # 1000 requests per hour per IP
        'per_user': {'limit': 5000, 'window': 3600},  # 5000 requests per hour per user
        'anonymous': {'limit': 100, 'window': 3600}  # 100 requests per hour for anonymous
    })(f)

def strict_rate_limit(f):
    """Strict rate limit for sensitive endpoints"""
    return advanced_limiter.rate_limit({
        'per_ip': {'limit': 10, 'window': 600},  # 10 requests per 10 minutes per IP
        'per_user': {'limit': 50, 'window': 600},  # 50 requests per 10 minutes per user
        'anonymous': {'limit': 2, 'window': 600}  # 2 requests per 10 minutes for anonymous
    })(f)

