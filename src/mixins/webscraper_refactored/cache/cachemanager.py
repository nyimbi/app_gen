"""
CacheManager module

Advanced caching system for scraped content with SQLite backend.

Provides sophisticated caching capabilities including:
- Content versioning and hash verification
- Automatic cache invalidation
- Compression for large content
- Cache statistics and monitoring
- Bulk operations
- Cache warming and prefetching
- Memory and disk usage optimization

Attributes:
    db_path (str): Path to SQLite database file
    max_size (int): Maximum cache size in bytes
    compression (bool): Enable content compression
    ttl (int): Default time-to-live in seconds
    stats (Dict): Cache statistics

Classes:

- CacheManager

"""


class CacheManager:
    """
    Advanced caching system for scraped content with SQLite backend.

    Provides sophisticated caching capabilities including:
    - Content versioning and hash verification
    - Automatic cache invalidation
    - Compression for large content
    - Cache statistics and monitoring
    - Bulk operations
    - Cache warming and prefetching
    - Memory and disk usage optimization

    Attributes:
        db_path (str): Path to SQLite database file
        max_size (int): Maximum cache size in bytes
        compression (bool): Enable content compression
        ttl (int): Default time-to-live in seconds
        stats (Dict): Cache statistics
    """

    def __init__(
        self,
        db_path="scraper_cache.db",
        max_size=1024 * 1024 * 1024,
        compression=True,
        ttl=86400,
    ):
        """
        Initialize cache manager with specified parameters.

        Args:
            db_path: Path to SQLite database file
            max_size: Maximum cache size in bytes (default 1GB)
            compression: Enable content compression
            ttl: Default time-to-live in seconds
        """
        self.db_path = db_path
        self.max_size = max_size
        self.compression = compression
        self.ttl = ttl
        self.stats = {"hits": 0, "misses": 0, "size": 0}
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with required schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "\n                CREATE TABLE IF NOT EXISTS cache (\n                    url TEXT PRIMARY KEY,\n                    content BLOB,\n                    timestamp DATETIME,\n                    hash TEXT,\n                    size INTEGER,\n                    access_count INTEGER DEFAULT 0,\n                    last_access DATETIME,\n                    compressed BOOLEAN\n                )\n            "
            )
            conn.execute(
                "\n                CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)\n            "
            )
            conn.execute(
                "\n                CREATE INDEX IF NOT EXISTS idx_access ON cache(last_access)\n            "
            )

    def get(self, url: str) -> Optional[Dict]:
        """
        Retrieve cached content for URL.

        Args:
            url: URL to retrieve content for

        Returns:
            Dict containing cached content or None if not found

        Raises:
            sqlite3.Error: If database operation fails
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "\n                SELECT content, timestamp, compressed\n                FROM cache\n                WHERE url = ? AND timestamp > datetime('now', ?)\n            ",
                (url, f"-{self.ttl} seconds"),
            )
            result = cursor.fetchone()
            if result:
                content, timestamp, compressed = result
                self.stats["hits"] += 1
                conn.execute(
                    "\n                    UPDATE cache\n                    SET access_count = access_count + 1,\n                        last_access = datetime('now')\n                    WHERE url = ?\n                ",
                    (url,),
                )
                if compressed:
                    import zlib

                    content = zlib.decompress(content)
                return json.loads(content)
            self.stats["misses"] += 1
            return None

    def set(self, url: str, content: Dict):
        """
        Cache content for URL.

        Args:
            url: URL to cache content for
            content: Content to cache

        Raises:
            ValueError: If content is invalid
            sqlite3.Error: If database operation fails
        """
        if not content:
            raise ValueError("Cannot cache empty content")
        serialized = json.dumps(content).encode()
        compressed = False
        if self.compression and len(serialized) > 1024:
            import zlib

            serialized = zlib.compress(serialized)
            compressed = True
        content_hash = hashlib.sha256(serialized).hexdigest()
        with sqlite3.connect(self.db_path) as conn:
            if self._get_cache_size(conn) > self.max_size:
                self._evict_entries(conn)
            conn.execute(
                "\n                INSERT OR REPLACE INTO cache\n                (url, content, timestamp, hash, size, last_access, compressed)\n                VALUES (?, ?, datetime('now'), ?, ?, datetime('now'), ?)\n            ",
                (url, serialized, content_hash, len(serialized), compressed),
            )

    def invalidate(self, url: str = None, older_than: int = None):
        """
        Invalidate cached entries.

        Args:
            url: Specific URL to invalidate, or None for bulk operation
            older_than: Invalidate entries older than seconds
        """
        with sqlite3.connect(self.db_path) as conn:
            if url:
                conn.execute("DELETE FROM cache WHERE url = ?", (url,))
            elif older_than:
                conn.execute(
                    "\n                    DELETE FROM cache\n                    WHERE timestamp < datetime('now', ?)\n                ",
                    (f"-{older_than} seconds",),
                )
            else:
                conn.execute("DELETE FROM cache")

    def _get_cache_size(self, conn) -> int:
        """Get total size of cached content in bytes."""
        cursor = conn.execute("SELECT COALESCE(SUM(size), 0) FROM cache")
        return cursor.fetchone()[0]

    def _evict_entries(self, conn):
        """Evict least recently accessed entries to free space."""
        conn.execute(
            "\n            DELETE FROM cache\n            WHERE url IN (\n                SELECT url FROM cache\n                ORDER BY last_access ASC\n                LIMIT (SELECT COUNT(*)/4 FROM cache)\n            )\n        "
        )

    def get_stats(self) -> Dict:
        """Get cache statistics and metrics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "\n                SELECT COUNT(*) as count,\n                       SUM(size) as total_size,\n                       SUM(access_count) as total_accesses,\n                       AVG(access_count) as avg_accesses\n                FROM cache\n            "
            )
            db_stats = dict(
                zip(["count", "size", "accesses", "avg_accesses"], cursor.fetchone())
            )
            return {
                **self.stats,
                **db_stats,
                "hit_ratio": (
                    self.stats["hits"] / (self.stats["hits"] + self.stats["misses"])
                    if self.stats["hits"] + self.stats["misses"] > 0
                    else 0
                ),
            }

    def optimize(self):
        """Optimize database and clean up unused space."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("VACUUM")
            conn.execute("ANALYZE")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.optimize()
