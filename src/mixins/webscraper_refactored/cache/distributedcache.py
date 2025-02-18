"""
DistributedCache module

Redis-based distributed cache with advanced features for web scraping data.

This cache implementation provides distributed caching capabilities using Redis,
with support for:
- Hierarchical key namespacing
- Automatic serialization/deserialization
- Key expiration and TTL management
- Pattern-based cache invalidation
- Cache statistics and monitoring
- Circuit breaker for Redis failures
- Bulk operations and pipelining
- Cache warming and prefetching

Attributes:
    redis: Redis client instance
    prefix: Key prefix for namespacing
    serializer: JSON serializer instance
    stats: Cache statistics tracker
    circuit_breaker: Circuit breaker for fault tolerance

Classes:

- DistributedCache

"""


class DistributedCache:
    """Redis-based distributed cache with advanced features for web scraping data.

    This cache implementation provides distributed caching capabilities using Redis,
    with support for:
    - Hierarchical key namespacing
    - Automatic serialization/deserialization
    - Key expiration and TTL management
    - Pattern-based cache invalidation
    - Cache statistics and monitoring
    - Circuit breaker for Redis failures
    - Bulk operations and pipelining
    - Cache warming and prefetching

    Attributes:
        redis: Redis client instance
        prefix: Key prefix for namespacing
        serializer: JSON serializer instance
        stats: Cache statistics tracker
        circuit_breaker: Circuit breaker for fault tolerance
    """

    def __init__(
        self,
        redis_url: str,
        prefix: str = "webscraper:",
        default_ttl: int = 86400,
        max_retries: int = 3,
    ):
        """Initialize the distributed cache.

        Args:
            redis_url: Redis connection URL
            prefix: Key prefix for namespacing
            default_ttl: Default TTL in seconds
            max_retries: Maximum retry attempts for Redis operations
        """
        retry = Retry(ExponentialBackoff(), max_retries)
        self.redis = Redis.from_url(redis_url, retry=retry)
        self.prefix = prefix
        self.default_ttl = default_ttl
        self._stats = {"hits": 0, "misses": 0, "errors": 0}
        self._pipeline = self.redis.pipeline()
        self._circuit_open = False
        self._error_threshold = 5
        self._error_count = 0
        self._warm_keys = set()

    def get(self, key: str, default: Any = None) -> Optional[Dict]:
        """Retrieve a value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default if not found

        Raises:
            CacheError: If Redis operation fails
        """
        if self._circuit_open:
            return default
        try:
            data = self.redis.get(f"{self.prefix}{key}")
            if data:
                self._stats["hits"] += 1
                return json.loads(data)
            self._stats["misses"] += 1
            return default
        except Exception as e:
            self._handle_error(e)
            return default

    def set(
        self,
        key: str,
        value: Dict,
        expire: int = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Store a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            expire: TTL in seconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists

        Returns:
            bool indicating success

        Raises:
            CacheError: If Redis operation fails
        """
        if self._circuit_open:
            return False
        try:
            return self.redis.setex(
                f"{self.prefix}{key}",
                expire or self.default_ttl,
                json.dumps(value),
                nx=nx,
                xx=xx,
            )
        except Exception as e:
            self._handle_error(e)
            return False

    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values at once.

        Args:
            keys: List of cache keys

        Returns:
            Dict mapping keys to values
        """
        if self._circuit_open:
            return {}
        prefixed_keys = [f"{self.prefix}{k}" for k in keys]
        try:
            values = self.redis.mget(prefixed_keys)
            return {k: json.loads(v) if v else None for k, v in zip(keys, values)}
        except Exception as e:
            self._handle_error(e)
            return {}

    def mset(self, mapping: Dict[str, Any], expire: int = None) -> bool:
        """Set multiple key-value pairs atomically.

        Args:
            mapping: Dict of key-value pairs
            expire: TTL in seconds

        Returns:
            bool indicating success
        """
        if self._circuit_open:
            return False
        prefixed = {f"{self.prefix}{k}": json.dumps(v) for k, v in mapping.items()}
        try:
            with self.redis.pipeline() as pipe:
                pipe.mset(prefixed)
                if expire:
                    for key in prefixed:
                        pipe.expire(key, expire)
                return all(pipe.execute())
        except Exception as e:
            self._handle_error(e)
            return False

    def invalidate(self, pattern: str) -> int:
        """Invalidate keys matching pattern.

        Args:
            pattern: Key pattern to match

        Returns:
            Number of keys invalidated
        """
        if self._circuit_open:
            return 0
        try:
            keys = self.redis.keys(f"{self.prefix}{pattern}")
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            self._handle_error(e)
            return 0

    def invalidate_all(self) -> bool:
        """Clear all cached data.

        Returns:
            bool indicating success
        """
        return self.invalidate("*")

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics.

        Returns:
            Dict of cache stats
        """
        return {
            **self._stats,
            "keys": self.redis.dbsize(),
            "circuit_breaker": self._circuit_open,
        }

    def warm_cache(self, keys: List[str], values: List[Any]) -> None:
        """Pre-warm cache with data.

        Args:
            keys: Keys to warm
            values: Values to cache
        """
        self.mset(dict(zip(keys, values)))
        self._warm_keys.update(keys)

    def _handle_error(self, error: Exception) -> None:
        """Handle Redis errors and manage circuit breaker."""
        self._stats["errors"] += 1
        self._error_count += 1
        if self._error_count >= self._error_threshold:
            self._circuit_open = True
        logger.error(f"Cache error: {error}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.redis.close()
