"""
Cache service for API responses and LLM results
"""

import json
import hashlib
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import redis
from config import settings

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based cache service for API responses and LLM results"""
    
    def __init__(self):
        try:
            # Try to connect to Redis (fallback to in-memory if not available)
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1
            )
            # Test connection
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory cache: {e}")
            self.redis_client = None
            self.use_redis = False
            self._memory_cache = {}
    
    def _generate_cache_key(self, prefix: str, data: Any) -> str:
        """Generate a cache key from data"""
        if isinstance(data, str):
            key_data = data
        else:
            key_data = json.dumps(data, sort_keys=True)
        
        hash_obj = hashlib.md5(key_data.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.use_redis:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                # Check if key exists and is not expired
                if key in self._memory_cache:
                    cached_data = self._memory_cache[key]
                    if datetime.now() < cached_data['expires_at']:
                        return cached_data['value']
                    else:
                        # Remove expired entry
                        del self._memory_cache[key]
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set value in cache with TTL"""
        try:
            if self.use_redis:
                self.redis_client.setex(key, ttl_seconds, json.dumps(value))
            else:
                # Store with expiration time
                self._memory_cache[key] = {
                    'value': value,
                    'expires_at': datetime.now() + timedelta(seconds=ttl_seconds)
                }
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def get_api_response(self, source: str, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached API response"""
        cache_key = self._generate_cache_key(f"api:{source}", query)
        return self.get(cache_key)
    
    def set_api_response(self, source: str, query: str, papers: List[Dict[str, Any]], ttl_hours: int = 24) -> bool:
        """Cache API response for 24 hours"""
        cache_key = self._generate_cache_key(f"api:{source}", query)
        return self.set(cache_key, papers, ttl_hours * 3600)
    
    def get_llm_response(self, query: str, papers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get cached LLM response"""
        # Create a hash of the query + paper IDs for cache key
        paper_ids = [p.get('id', '') for p in papers]
        cache_data = {'query': query, 'paper_ids': sorted(paper_ids)}
        cache_key = self._generate_cache_key("llm", cache_data)
        return self.get(cache_key)
    
    def set_llm_response(self, query: str, papers: List[Dict[str, Any]], response: Dict[str, Any], ttl_hours: int = 48) -> bool:
        """Cache LLM response for 48 hours"""
        paper_ids = [p.get('id', '') for p in papers]
        cache_data = {'query': query, 'paper_ids': sorted(paper_ids)}
        cache_key = self._generate_cache_key("llm", cache_data)
        return self.set(cache_key, response, ttl_hours * 3600)
    
    def get_query_similarity(self, query: str) -> Optional[List[str]]:
        """Get similar queries from cache"""
        cache_key = self._generate_cache_key("similar_queries", query)
        return self.get(cache_key)
    
    def set_query_similarity(self, query: str, similar_queries: List[str], ttl_hours: int = 72) -> bool:
        """Cache similar queries for 72 hours"""
        cache_key = self._generate_cache_key("similar_queries", query)
        return self.set(cache_key, similar_queries, ttl_hours * 3600)
    
    def clear_cache(self, pattern: str = "*") -> bool:
        """Clear cache entries matching pattern"""
        try:
            if self.use_redis:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            else:
                # Clear in-memory cache
                if pattern == "*":
                    self._memory_cache.clear()
                else:
                    # Simple pattern matching for in-memory cache
                    keys_to_remove = [k for k in self._memory_cache.keys() if pattern.replace("*", "") in k]
                    for key in keys_to_remove:
                        del self._memory_cache[key]
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if self.use_redis:
                info = self.redis_client.info()
                return {
                    'type': 'redis',
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': info.get('used_memory_human', '0B'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'total_keys': len(self.redis_client.keys("*"))
                }
            else:
                return {
                    'type': 'memory',
                    'total_keys': len(self._memory_cache),
                    'expired_keys': len([k for k, v in self._memory_cache.items() 
                                       if datetime.now() >= v['expires_at']])
                }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'type': 'error', 'error': str(e)}

# Global cache instance
cache_service = CacheService()
