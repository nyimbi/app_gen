"""
HierarchicalCache module

Multi-level caching system

Classes:

- HierarchicalCache

"""


class HierarchicalCache:
    """Multi-level caching system"""

    def __init__(self):
        self.memory_cache = {}
        self.redis_cache = None
        self.disk_cache = None

    async def get(self, key: str) -> Optional[Any]:
        if value := self.memory_cache.get(key):
            return value
        if value := (await self.redis_cache.get(key)):
            self._update_memory_cache(key, value)
            return value
        if value := self.disk_cache.get(key):
            await self._update_redis_cache(key, value)
            return value
        return None

    async def set(self, key: str, value: Any):
        self.memory_cache[key] = value
        await self.redis_cache.set(key, value)
        self.disk_cache.set(key, value)
