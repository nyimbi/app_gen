"""
RateLimiter module

Advanced rate limiting with domain-specific queues

Classes:

- RateLimiter

"""

from ..networking import RateLimit


class RateLimiter:
    """Advanced rate limiting with domain-specific queues"""

    def __init__(self):
        self.queues = defaultdict(asyncio.Queue)
        self.limits = defaultdict(lambda: RateLimit(10, 60))

    async def acquire(self, domain: str):
        rate_limit = self.limits[domain]
        await rate_limit.acquire()
        return await self.queues[domain].get()

    async def release(self, domain: str, task):
        await self.queues[domain].put(task)
