"""
ProxyManager module

Advanced proxy management system with rotation, validation, and monitoring capabilities.

This class handles proxy rotation, health checking, and performance monitoring for web scraping
operations. It supports both synchronous and asynchronous operations, automatic proxy validation,
and intelligent proxy selection based on performance metrics.

Attributes:
    proxies (Iterator[str]): Cyclic iterator of proxy addresses
    failed_proxies (Set[str]): Set of currently failed proxies
    lock (asyncio.Lock): Lock for thread-safe operations
    performance_metrics (Dict[str, Dict]): Proxy performance statistics
    validation_interval (int): Time between proxy validations in seconds
    timeout (float): Proxy connection timeout in seconds
    max_failures (int): Maximum failures before proxy removal
    min_speed (float): Minimum acceptable proxy speed in MB/s

Classes:

- ProxyManager

"""


class ProxyManager:
    """
    Advanced proxy management system with rotation, validation, and monitoring capabilities.

    This class handles proxy rotation, health checking, and performance monitoring for web scraping
    operations. It supports both synchronous and asynchronous operations, automatic proxy validation,
    and intelligent proxy selection based on performance metrics.

    Attributes:
        proxies (Iterator[str]): Cyclic iterator of proxy addresses
        failed_proxies (Set[str]): Set of currently failed proxies
        lock (asyncio.Lock): Lock for thread-safe operations
        performance_metrics (Dict[str, Dict]): Proxy performance statistics
        validation_interval (int): Time between proxy validations in seconds
        timeout (float): Proxy connection timeout in seconds
        max_failures (int): Maximum failures before proxy removal
        min_speed (float): Minimum acceptable proxy speed in MB/s
    """

    def __init__(
        self,
        proxy_list: List[str],
        validation_interval: int = 300,
        timeout: float = 10.0,
        max_failures: int = 3,
        min_speed: float = 0.1,
    ):
        """
        Initialize the proxy manager with configuration parameters.

        Args:
            proxy_list (List[str]): List of proxy URLs
            validation_interval (int): Seconds between validations
            timeout (float): Connection timeout in seconds
            max_failures (int): Maximum failures before removal
            min_speed (float): Minimum acceptable speed in MB/s
        """
        from itertools import cycle

        self.proxies = cycle(proxy_list)
        self.proxy_list = set(proxy_list)
        self.failed_proxies = set()
        self.lock = asyncio.Lock()
        self.validation_interval = validation_interval
        self.timeout = timeout
        self.max_failures = max_failures
        self.min_speed = min_speed
        self.performance_metrics = {
            proxy: {
                "success_count": 0,
                "failure_count": 0,
                "average_speed": 0.0,
                "last_check": time.time(),
                "response_times": [],
            }
            for proxy in proxy_list
        }
        self.validation_task = None

    async def start(self):
        """Start the proxy validation background task."""
        self.validation_task = asyncio.create_task(self.validate_proxies())

    async def stop(self):
        """Stop the proxy validation background task."""
        if self.validation_task:
            self.validation_task.cancel()
            try:
                await self.validation_task
            except asyncio.CancelledError:
                pass

    async def get_proxy(self, requirements: Dict = None) -> str:
        """
        Get the next available proxy meeting specified requirements.

        Args:
            requirements (Dict): Optional performance requirements

        Returns:
            str: Proxy URL meeting requirements

        Raises:
            ProxyError: If no suitable proxy is available
        """
        async with self.lock:
            for _ in range(len(self.proxy_list)):
                proxy = next(self.proxies)
                if proxy not in self.failed_proxies and self._meets_requirements(
                    proxy, requirements
                ):
                    return proxy
            raise ProxyError("No suitable proxy available")

    async def mark_failed(self, proxy: str, error: Exception = None):
        """
        Mark a proxy as failed and update its metrics.

        Args:
            proxy (str): Failed proxy URL
            error (Exception): Optional error details
        """
        async with self.lock:
            self.failed_proxies.add(proxy)
            metrics = self.performance_metrics[proxy]
            metrics["failure_count"] += 1
            metrics["last_error"] = str(error) if error else "Unknown error"
            metrics["last_check"] = time.time()
            if metrics["failure_count"] >= self.max_failures:
                await self._remove_proxy(proxy)

    async def mark_success(self, proxy: str, response_time: float):
        """
        Record a successful proxy use and update metrics.

        Args:
            proxy (str): Successful proxy URL
            response_time (float): Request response time
        """
        async with self.lock:
            if proxy in self.failed_proxies:
                self.failed_proxies.remove(proxy)
            metrics = self.performance_metrics[proxy]
            metrics["success_count"] += 1
            metrics["response_times"].append(response_time)
            metrics["average_speed"] = sum(metrics["response_times"]) / len(
                metrics["response_times"]
            )
            metrics["last_check"] = time.time()

    async def validate_proxies(self):
        """
        Continuously validate all proxies in the background.
        """
        while True:
            try:
                tasks = [self.test_proxy(proxy) for proxy in self.proxy_list]
                await asyncio.gather(*tasks, return_exceptions=True)
                await self._cleanup_metrics()
                await asyncio.sleep(self.validation_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Proxy validation error: {e}")
                await asyncio.sleep(60)

    async def test_proxy(self, proxy: str) -> bool:
        """
        Test a proxy's connectivity and performance.

        Args:
            proxy (str): Proxy URL to test

        Returns:
            bool: True if proxy is working properly
        """
        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://httpbin.org/ip", proxy=proxy, timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        response_time = time.time() - start_time
                        await self.mark_success(proxy, response_time)
                        return True
            await self.mark_failed(proxy)
            return False
        except Exception as e:
            await self.mark_failed(proxy, e)
            return False

    def _meets_requirements(self, proxy: str, requirements: Dict = None) -> bool:
        """
        Check if proxy meets performance requirements.

        Args:
            proxy (str): Proxy URL to check
            requirements (Dict): Performance requirements

        Returns:
            bool: True if requirements are met
        """
        if not requirements:
            return True
        metrics = self.performance_metrics[proxy]
        return metrics["average_speed"] >= requirements.get(
            "min_speed", self.min_speed
        ) and metrics["failure_count"] < requirements.get(
            "max_failures", self.max_failures
        )

    async def _remove_proxy(self, proxy: str):
        """
        Remove a proxy from the rotation.

        Args:
            proxy (str): Proxy URL to remove
        """
        self.proxy_list.remove(proxy)
        self.failed_proxies.discard(proxy)
        del self.performance_metrics[proxy]
        self.proxies = cycle(self.proxy_list)

    async def _cleanup_metrics(self):
        """Clean up old performance metrics."""
        current_time = time.time()
        for proxy in list(self.performance_metrics.keys()):
            metrics = self.performance_metrics[proxy]
            if current_time - metrics["last_check"] > self.validation_interval * 2:
                metrics["response_times"] = metrics["response_times"][-100:]

    def get_metrics(self) -> Dict:
        """
        Get current proxy performance metrics.

        Returns:
            Dict: Current proxy metrics
        """
        return {
            "total_proxies": len(self.proxy_list),
            "failed_proxies": len(self.failed_proxies),
            "performance_metrics": self.performance_metrics,
        }
