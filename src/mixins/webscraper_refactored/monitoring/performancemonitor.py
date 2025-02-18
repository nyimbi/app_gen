"""
PerformanceMonitor module

Comprehensive performance monitoring and analytics system for web scraper.

Tracks and analyzes various performance metrics including:
- Request rates and timings
- Success/failure rates
- Memory and CPU usage
- Cache performance
- Network statistics
- Content processing metrics

Supports multiple export formats and real-time monitoring capabilities.

Attributes:
    metrics (defaultdict): Collection of recorded metrics
    start_time (float): Monitor start timestamp
    request_counter (Counter): Prometheus request counter
    response_time (Histogram): Response time histogram
    memory_gauge (Gauge): Memory usage gauge
    scraper_info (Info): Scraper metadata
    alert_thresholds (Dict): Metric alert thresholds
    retention_period (int): Metric retention in seconds

Classes:

- PerformanceMonitor

"""

from ..utils import MetricPoint


class PerformanceMonitor:
    """
    Comprehensive performance monitoring and analytics system for web scraper.

    Tracks and analyzes various performance metrics including:
    - Request rates and timings
    - Success/failure rates
    - Memory and CPU usage
    - Cache performance
    - Network statistics
    - Content processing metrics

    Supports multiple export formats and real-time monitoring capabilities.

    Attributes:
        metrics (defaultdict): Collection of recorded metrics
        start_time (float): Monitor start timestamp
        request_counter (Counter): Prometheus request counter
        response_time (Histogram): Response time histogram
        memory_gauge (Gauge): Memory usage gauge
        scraper_info (Info): Scraper metadata
        alert_thresholds (Dict): Metric alert thresholds
        retention_period (int): Metric retention in seconds
    """

    def __init__(self, retention_period: int = 86400):
        """
        Initialize performance monitor with specified settings.

        Args:
            retention_period: How long to retain metrics in seconds
        """
        self.metrics = defaultdict(list)
        self.start_time = time.time()
        self.retention_period = retention_period
        self.request_counter = Counter("scraper_requests_total", "Total requests made")
        self.response_time = Histogram(
            "scraper_response_seconds", "Response time in seconds"
        )
        self.memory_gauge = Gauge("scraper_memory_bytes", "Memory usage in bytes")
        self.scraper_info = Info("scraper", "Scraper metadata")
        self.alert_thresholds = {
            "response_time": 5.0,
            "error_rate": 0.1,
            "memory_usage": 1024,
        }

    async def record_metric(
        self, metric_name: str, value: float, labels: Dict[str, str] = None
    ):
        """
        Record a metric measurement with optional labels.

        Args:
            metric_name: Name of metric to record
            value: Metric value
            labels: Optional metric labels/tags
        """
        point = MetricPoint(value, time.time(), labels)
        self.metrics[metric_name].append(point)
        if metric_name == "request":
            self.request_counter.inc()
        elif metric_name == "response_time":
            self.response_time.observe(value)
        await self._check_alerts(metric_name, value)
        await self._cleanup_old_metrics()

    def calculate_rps(self) -> float:
        """Calculate current requests per second"""
        if "request" not in self.metrics:
            return 0.0
        now = time.time()
        recent_reqs = [m for m in self.metrics["request"] if now - m.timestamp <= 60]
        return len(recent_reqs) / 60.0

    def calculate_success_rate(self) -> float:
        """Calculate request success rate"""
        if "request" not in self.metrics:
            return 0.0
        total = len(self.metrics["request"])
        if total == 0:
            return 0.0
        successes = len(
            [
                m
                for m in self.metrics["request"]
                if m.labels and m.labels.get("status") == "success"
            ]
        )
        return successes / total

    def get_statistics(self) -> Dict[str, Union[float, int, str]]:
        """
        Get comprehensive statistics and metrics.

        Returns:
            Dictionary containing various performance metrics
        """
        stats = {
            "uptime": time.time() - self.start_time,
            "requests_per_second": self.calculate_rps(),
            "average_response_time": (
                statistics.mean(
                    (m.value for m in self.metrics.get("response_time", []))
                )
                if self.metrics.get("response_time")
                else 0
            ),
            "success_rate": self.calculate_success_rate(),
            "memory_usage": psutil.Process().memory_info().rss / 1024 / 1024,
            "cpu_percent": psutil.Process().cpu_percent(),
            "thread_count": psutil.Process().num_threads(),
            "open_files": len(psutil.Process().open_files()),
            "cache_hit_rate": self.calculate_cache_hit_rate(),
            "network_bytes_received": sum(
                (m.value for m in self.metrics.get("bytes_received", []))
            ),
            "content_processing_time": (
                statistics.mean(
                    (m.value for m in self.metrics.get("processing_time", []))
                )
                if self.metrics.get("processing_time")
                else 0
            ),
        }
        self.memory_gauge.set(stats["memory_usage"] * 1024 * 1024)
        return stats

    def calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        if "cache_access" not in self.metrics:
            return 0.0
        total = len(self.metrics["cache_access"])
        if total == 0:
            return 0.0
        hits = len(
            [
                m
                for m in self.metrics["cache_access"]
                if m.labels and m.labels.get("result") == "hit"
            ]
        )
        return hits / total * 100

    async def _check_alerts(self, metric_name: str, value: float):
        """Check if metric value exceeds alert threshold"""
        if metric_name in self.alert_thresholds:
            threshold = self.alert_thresholds[metric_name]
            if value > threshold:
                await self._send_alert(metric_name, value, threshold)

    async def _send_alert(self, metric_name: str, value: float, threshold: float):
        """Send alert for exceeded threshold"""
        logger.warning(
            f"Alert: {metric_name} value {value} exceeded threshold {threshold}"
        )

    async def _cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        now = time.time()
        for metric_name in self.metrics:
            self.metrics[metric_name] = [
                m
                for m in self.metrics[metric_name]
                if now - m.timestamp <= self.retention_period
            ]

    def export_metrics(self, format: str = "prometheus") -> str:
        """
        Export metrics in specified format.

        Args:
            format: Output format ('prometheus' or 'json')

        Returns:
            Formatted metrics string
        """
        if format == "prometheus":
            return self.format_prometheus_metrics()
        return self.format_json_metrics()

    def format_prometheus_metrics(self) -> str:
        """Format metrics in Prometheus text format"""
        lines = []
        stats = self.get_statistics()
        for name, value in stats.items():
            if isinstance(value, (int, float)):
                lines.append(f"scraper_{name} {value}")
        return "\n".join(lines)

    def format_json_metrics(self) -> str:
        """Format metrics as JSON string"""
        return json.dumps(
            {
                "statistics": self.get_statistics(),
                "metrics": {
                    name: [asdict(m) for m in points]
                    for name, points in self.metrics.items()
                },
            },
            indent=2,
        )
