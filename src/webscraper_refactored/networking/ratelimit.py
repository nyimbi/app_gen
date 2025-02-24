"""
RateLimit module

Token bucket rate limiter for controlling request rates.

Implements a thread-safe token bucket algorithm for rate limiting
with support for bursts, dynamic rate adjustment, and statistics tracking.

Attributes:
    rate (int): Maximum requests per period
    period (int): Time period in seconds
    tokens (float): Current token count
    last_update (float): Last token refresh timestamp
    lock (asyncio.Lock): Thread synchronization lock
    stats (Dict): Usage statistics and metrics
    burst_size (int): Maximum burst size allowed
    min_interval (float): Minimum time between requests

Classes:

- RateLimit

"""


class RateLimit:
    """
    Token bucket rate limiter for controlling request rates.

    Implements a thread-safe token bucket algorithm for rate limiting
    with support for bursts, dynamic rate adjustment, and statistics tracking.

    Attributes:
        rate (int): Maximum requests per period
        period (int): Time period in seconds
        tokens (float): Current token count
        last_update (float): Last token refresh timestamp
        lock (asyncio.Lock): Thread synchronization lock
        stats (Dict): Usage statistics and metrics
        burst_size (int): Maximum burst size allowed
        min_interval (float): Minimum time between requests
    """

    def __init__(self, rate: int, period: int, burst_size: Optional[int] = None):
        self.rate = rate
        self.period = period
        self.tokens = rate
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
        self.stats = {"requests": 0, "throttled": 0, "wait_time": 0.0}
        self.burst_size = burst_size or rate
        self.min_interval = period / rate
        self._token_rate = rate / period
        self._last_request = 0.0

    async def acquire(self) -> bool:
        """
        Acquire a rate limit token, waiting if necessary.

        Returns:
            bool: True if token acquired, False if should throttle

        Raises:
            RateLimitExceeded: If rate limit exceeded with no_wait=True
        """
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.burst_size, self.tokens + elapsed * self._token_rate)
            self.last_update = now
            if self.tokens < 1:
                wait_time = (1 - self.tokens) * self.min_interval
                self.stats["throttled"] += 1
                self.stats["wait_time"] += wait_time
                await asyncio.sleep(wait_time)
                self.tokens = 1
            self.tokens -= 1
            self.stats["requests"] += 1
            self._last_request = now
            return True

    async def acquire_nowait(self) -> bool:
        """
        Try to acquire token without waiting.

        Returns:
            bool: True if token acquired, False if would need to wait
        """
        async with self.lock:
            now = time.monotonic()
            if now - self._last_request < self.min_interval:
                return False
            return await self.acquire()

    def get_stats(self) -> Dict[str, Union[int, float]]:
        """Get current rate limiting statistics."""
        return {
            **self.stats,
            "current_tokens": self.tokens,
            "rate": self.rate,
            "period": self.period,
        }

    def update_rate(self, new_rate: int, new_period: Optional[int] = None):
        """
        Update rate limit parameters.

        Args:
            new_rate: New maximum request rate
            new_period: Optional new time period in seconds
        """
        self.rate = new_rate
        if new_period:
            self.period = new_period
        self._token_rate = self.rate / self.period
        self.min_interval = self.period / self.rate

    def reset(self):
        """Reset rate limiter state and statistics."""
        self.tokens = self.rate
        self.last_update = time.monotonic()
        self.stats = {"requests": 0, "throttled": 0, "wait_time": 0.0}
