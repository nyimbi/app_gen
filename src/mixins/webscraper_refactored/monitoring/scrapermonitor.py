"""
ScraperMonitor module

Real-time scraper monitoring

Classes:

- ScraperMonitor

"""

from ..monitoring import PerformanceMonitor


class ScraperMonitor:
    """Real-time scraper monitoring"""

    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.error_handler = ErrorHandler()
        self.stats = defaultdict(int)
        self.start_time = time.time()

    async def monitor(self, scraper: WebScraper):
        """Monitor scraper performance"""
        while True:
            stats = scraper.get_stats()
            await self.performance_monitor.record_metric("scraper_stats", stats)
            memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
            await self.performance_monitor.record_metric("memory_usage", memory_usage)
            self.export_metrics()
            await asyncio.sleep(60)

    def export_metrics(self):
        """Export monitoring metrics"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics = self.performance_monitor.get_statistics()
        with open(f"scraper_metrics_{timestamp}.json", "w") as f:
            json.dump(metrics, f, indent=2)
