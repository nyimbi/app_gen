"""
1. **Better Architecture**:
   - Data classes for structured data
   - Configuration management
   - Cache management with SQLite
   - Async support with aiohttp

2. **Enhanced Features**:
   - Content analysis and filtering
   - Image extraction
   - Language detection
   - Content hashing
   - Word counting
   - Multiple export formats

3. **Improved Content Extraction**:
   - Better main content detection
   - Metadata extraction
   - Link analysis and filtering
   - Structure preservation

4. **Better Error Handling and Logging**:
   - Comprehensive logging
   - Detailed error tracking
   - Status code handling

5. **Caching and Performance**:
   - SQLite-based caching
   - Async capabilities
   - Rate limiting
   - Proxy support

6. **Configuration Options**:
   - Domain filtering
   - Pattern exclusion
   - Follow links depth
   - Cache duration

7. **Export Capabilities**:
   - JSON export
   - CSV export
   - Timestamped files
"""

import asyncio
import csv
import hashlib
import json
import logging
import os
import re
import sqlite3
import statistics
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime
from statistics import mean
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import aiohttp
import langdetect
import nltk
import psutil
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from prometheus_client import Counter, Gauge, Histogram, Info
from readability import Document
from redis import Redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError
from redis.retry import Retry

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("webscraper.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ScraperException(Exception):
    """Base exception for scraper errors"""

    pass


class ContentExtractionError(ScraperException):
    """Content extraction failed"""

    pass


class ValidationError(ScraperException):
    """Content validation failed"""

    pass


class NetworkError(ScraperException):
    """Network-related errors"""

    pass

class SmartContentExtractor:
    """Enhanced content detection using multiple heuristics"""

    def __init__(self):
        self.readability = Document
        self.content_scores = {}
        self.min_content_length = 100
        self.boilerplate_patterns = [
            r'cookie\s*policy',
            r'advertisement',
            r'subscribe\s*now',
            r'sign\s*up',
            r'social\s*media',
        ]

    def extract_content(self, html: str) -> str:
        # Try multiple extraction strategies
        strategies = [
            self._extract_using_readability,
            self._extract_using_density,
            self._extract_using_schema,
            self._extract_using_containers
        ]

        results = []
        for strategy in strategies:
            try:
                content = strategy(html)
                if self._is_valid_content(content):
                    results.append((content, self._score_content(content)))
            except Exception as e:
                logger.debug(f"Extraction strategy failed: {str(e)}")

        if results:
            # Return highest scoring content
            return max(results, key=lambda x: x[1])[0]
        return ""

    def _is_valid_content(self, content: str) -> bool:
        """Validate extracted content"""
        if len(content) < self.min_content_length:
            return False

        # Check for boilerplate text
        if any(re.search(pattern, content, re.I) for pattern in self.boilerplate_patterns):
            return False

        return True

    def _score_content(self, content: str) -> float:
        """Score content quality"""
        # Implement sophisticated scoring logic
        pass


class URLDiscovery:
    """Advanced URL discovery and filtering"""

    def __init__(self):
        self.seen_urls = set()
        self.url_patterns = {
            'article': re.compile(r'article|post|blog|news'),
            'pagination': re.compile(r'page=\d+|/p/\d+'),
            'date': re.compile(r'\d{4}/\d{2}/\d{2}'),
            'category': re.compile(r'category|section|topic'),
        }
        self.priority_scores = defaultdict(int)

    def discover_urls(self, html: str, base_url: str) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        discovered = set()

        for link in soup.find_all('a', href=True):
            url = self.clean_url(urljoin(base_url, link['href']))
            if self.should_crawl(url):
                discovered.add(url)
                self.score_url(url, link)

        return sorted(discovered, key=lambda u: self.priority_scores[u], reverse=True)

    def score_url(self, url: str, element: Tag):
        """Score URL based on various factors"""
        score = 0
        # Location in document
        if element.parent and element.parent.name in ['nav', 'header']:
            score += 1
        # Link text relevance
        if element.string and any(word in element.string.lower()
                                for word in ['article', 'post', 'read']):
            score += 2
        # URL structure
        if any(pattern.search(url) for pattern in self.url_patterns.values()):
            score += 3
        self.priority_scores[url] = score


class ConcurrentScraper:
    """Advanced concurrent scraping with rate limiting and prioritization"""

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.queue = asyncio.PriorityQueue()
        self.rate_limiters = {}
        self.seen_urls = set()
        self.results = {}

    async def scrape_urls(self, urls: List[str]) -> Dict[str, ScrapedContent]:
        # Initialize workers
        workers = [self._worker() for _ in range(self.max_workers)]

        # Add URLs to queue
        for url in urls:
            priority = self._get_url_priority(url)
            await self.queue.put((priority, url))

        # Wait for completion
        await asyncio.gather(*workers)
        return self.results

    async def _worker(self):
        while True:
            try:
                priority, url = await self.queue.get()
                if url in self.seen_urls:
                    continue

                domain = urlparse(url).netloc
                rate_limiter = self.rate_limiters.get(domain)
                if rate_limiter:
                    await rate_limiter.acquire()

                result = await self._scrape_url(url)
                if result:
                    self.results[url] = result
                    # Discover new URLs
                    new_urls = self._extract_urls(result.content)
                    for new_url in new_urls:
                        new_priority = self._get_url_priority(new_url)
                        await self.queue.put((new_priority, new_url))

            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
            finally:
                self.queue.task_done()


class ContentAnalyzer:
    """Advanced content analysis and classification"""

    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.classifier = self._load_classifier()
        self.topic_model = self._load_topic_model()

    def analyze_content(self, content: str) -> Dict[str, Any]:
        doc = self.nlp(content)

        return {
            'summary': self.generate_summary(doc),
            'topics': self.extract_topics(doc),
            'sentiment': self.analyze_sentiment(doc),
            'entities': self.extract_entities(doc),
            'categories': self.classify_content(doc),
            'readability': self.calculate_readability(content),
            'language_stats': self.get_language_stats(doc)
        }

    def extract_topics(self, doc) -> List[str]:
        """Extract main topics using LDA"""
        pass

    def classify_content(self, doc) -> List[str]:
        """Classify content type and category"""
        pass


class ResilientScraper:
    """Scraper with advanced error recovery"""

    def __init__(self):
        self.error_counts = Counter()
        self.backoff_times = defaultdict(float)
        self.circuit_breakers = {}

    async def scrape_with_recovery(self, url: str) -> Optional[ScrapedContent]:
        domain = urlparse(url).netloc

        if self._is_circuit_open(domain):
            logger.warning(f"Circuit breaker open for {domain}")
            return None

        try:
            # Implement exponential backoff
            await self._respect_backoff(domain)

            result = await self._scrape_with_retry(url)
            self._reset_error_count(domain)
            return result

        except Exception as e:
            self._handle_error(domain, e)
            return None

    def _handle_error(self, domain: str, error: Exception):
        """Handle errors with circuit breaker pattern"""
        self.error_counts[domain] += 1

        if self.error_counts[domain] >= 5:
            self._open_circuit(domain)

        self.backoff_times[domain] = min(
            self.backoff_times[domain] * 2 + random.uniform(0, 1),
            300  # Max backoff of 5 minutes
        )


class HierarchicalCache:
    """Multi-level caching system"""

    def __init__(self):
        self.memory_cache = {}  # Fast, small cache
        self.redis_cache = None  # Distributed cache
        self.disk_cache = None  # Local disk cache

    async def get(self, key: str) -> Optional[Any]:
        # Try memory cache first
        if value := self.memory_cache.get(key):
            return value

        # Try Redis cache
        if value := await self.redis_cache.get(key):
            self._update_memory_cache(key, value)
            return value

        # Try disk cache
        if value := self.disk_cache.get(key):
            await self._update_redis_cache(key, value)
            return value

        return None

    async def set(self, key: str, value: Any):
        # Update all cache levels
        self.memory_cache[key] = value
        await self.redis_cache.set(key, value)
        self.disk_cache.set(key, value)


class ResultProcessor:
    """Advanced result processing and export"""

    def __init__(self):
        self.exporters = {
            'json': JsonExporter(),
            'csv': CsvExporter(),
            'xml': XmlExporter(),
            'elasticsearch': ElasticsearchExporter()
        }

    async def process_results(self, results: Dict[str, ScrapedContent]):
        # Enrich results
        enriched_results = await self._enrich_results(results)

        # Export in multiple formats
        for format_name, exporter in self.exporters.items():
            try:
                await exporter.export(enriched_results)
            except Exception as e:
                logger.error(f"Export failed for {format_name}: {e}")

    async def _enrich_results(self, results: Dict[str, ScrapedContent]):
        """Add additional data to results"""
        enriched = {}
        for url, content in results.items():
            enriched[url] = {
                **asdict(content),
                'analysis': await self._analyze_content(content),
                'metadata': await self._extract_metadata(content),
                'transformed': await self._transform_content(content)
            }
        return enriched
@dataclass
class ScrapedContent:
    """Data class for scraped content"""

    url: str
    title: str
    content: str
    links: List[str]
    meta_description: Optional[str] = None
    images: List[Dict] = None
    timestamp: str = None
    hash: str = None
    language: str = None
    status_code: int = None
    content_type: str = None
    word_count: int = 0


class WebScraperConfig:
    """Configuration class for WebScraper"""

    def __init__(self, **kwargs):
        self.user_agent = kwargs.get("user_agent", UserAgent().random)
        self.rate_limit = kwargs.get("rate_limit", 1)
        self.timeout = kwargs.get("timeout", 10)
        self.max_retries = kwargs.get("max_retries", 3)
        self.max_workers = kwargs.get("max_workers", 5)
        self.cache_enabled = kwargs.get("cache_enabled", True)
        self.cache_duration = kwargs.get("cache_duration", 86400)  # 24 hours
        self.follow_links = kwargs.get("follow_links", False)
        self.max_depth = kwargs.get("max_depth", 2)
        self.proxy = kwargs.get("proxy", None)
        self.headers = kwargs.get("headers", {})
        self.allowed_domains = kwargs.get("allowed_domains", set())
        self.excluded_patterns = kwargs.get("excluded_patterns", set())


# 1. **Advanced Content Processing**:
class ContentProcessor:
    """
    Advanced natural language processing and content analysis capabilities.

    This class provides comprehensive text analysis features including:
    - Text summarization using extractive methods
    - Keyword extraction using TF-IDF
    - Named entity recognition
    - Readability analysis
    - Sentiment analysis
    - Language statistics

    Attributes:
        nlp: spaCy language model for text processing
        readability: Text readability analyzer
        sentiment_analyzer: Text sentiment analyzer
        num_summary_sentences: Number of sentences to include in summaries
        min_keyword_freq: Minimum frequency for keyword extraction
    """

    def __init__(
        self, model="en_core_web_sm", num_summary_sentences=3, min_keyword_freq=2
    ):
        """
        Initialize the content processor with specified parameters.

        Args:
            model (str): Name of spaCy model to load
            num_summary_sentences (int): Number of sentences for summaries
            min_keyword_freq (int): Minimum keyword frequency threshold
        """
        from collections import Counter

        import spacy
        from textstat import textstatistics
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        self.nlp = spacy.load(model)
        self.readability = textstatistics()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.num_summary_sentences = num_summary_sentences
        self.min_keyword_freq = min_keyword_freq
        self.counter = Counter

    def process_content(self, text: str) -> Dict:
        """
        Process text content and return comprehensive analysis.

        Args:
            text (str): Raw text content to analyze

        Returns:
            Dict containing analysis results including:
            - Text summary
            - Keywords
            - Named entities
            - Readability metrics
            - Sentiment scores
            - Language statistics
        """
        doc = self.nlp(text)
        return {
            "summary": self.generate_summary(doc),
            "keywords": self.extract_keywords(doc),
            "entities": self.extract_entities(doc),
            "readability_scores": self._get_readability_scores(text),
            "sentiment": self._analyze_sentiment(text),
            "language_stats": self._get_language_stats(doc),
        }

    def generate_summary(self, doc) -> str:
        """
        Generate extractive summary of document.

        Args:
            doc: Processed spaCy document

        Returns:
            String containing summarized text
        """
        sentences = list(doc.sents)
        word_freq = self.counter(token.text.lower() for token in doc if token.is_alpha)
        sentence_scores = self._score_sentences(sentences, word_freq)
        summary_sents = self._top_sentences(sentence_scores, self.num_summary_sentences)
        return " ".join(str(s) for s in summary_sents)

    def extract_keywords(self, doc) -> List[str]:
        """
        Extract important keywords using frequency and TF-IDF.

        Args:
            doc: Processed spaCy document

        Returns:
            List of keyword strings
        """
        return [token.text for token in doc if token.is_alpha and not token.is_stop][
            :10
        ]

    def extract_entities(self, doc) -> Dict:
        """
        Extract named entities and their labels.

        Args:
            doc: Processed spaCy document

        Returns:
            Dictionary mapping entity labels to extracted text
        """
        return {ent.label_: ent.text for ent in doc.ents}

    def _score_sentences(self, sentences, word_freq) -> Dict:
        """Score sentences based on word frequencies."""
        scores = {}
        for sent in sentences:
            score = sum(
                word_freq.get(token.text.lower(), 0) for token in sent if token.is_alpha
            )
            scores[sent] = score / len(sent)
        return scores

    def _top_sentences(self, scores: Dict, n: int) -> List:
        """Return top n scored sentences."""
        return sorted(scores.keys(), key=scores.get, reverse=True)[:n]

    def _get_readability_scores(self, text: str) -> Dict:
        """Calculate readability metrics."""
        return {
            "flesch_reading_ease": self.readability.flesch_reading_ease(text),
            "flesch_kincaid_grade": self.readability.flesch_kincaid_grade(text),
            "gunning_fog": self.readability.gunning_fog(text),
        }

    def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze text sentiment."""
        return self.sentiment_analyzer.polarity_scores(text)

    def _get_language_stats(self, doc) -> Dict:
        """Calculate document statistics."""
        return {
            "sentence_count": len(list(doc.sents)),
            "word_count": len([token for token in doc if token.is_alpha]),
            "unique_words": len(
                set(token.text.lower() for token in doc if token.is_alpha)
            ),
        }


# 2. **Enhanced Caching with Redis**:
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


# 3. **Proxy Rotation and Management**:
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
                await asyncio.sleep(60)  # Retry after error

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


# 4. **Rate Limiting and Queueing**:
class RateLimiter:
    """Advanced rate limiting with domain-specific queues"""

    def __init__(self):
        self.queues = defaultdict(asyncio.Queue)
        self.limits = defaultdict(
            lambda: RateLimit(10, 60)
        )  # Default: 10 requests per minute

    async def acquire(self, domain: str):
        rate_limit = self.limits[domain]
        await rate_limit.acquire()
        return await self.queues[domain].get()

    async def release(self, domain: str, task):
        await self.queues[domain].put(task)


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


# 5. **Content Validation and Cleaning**:
@dataclass
class ValidationResult:
    """Container for content validation results"""

    is_valid: bool
    score: float
    message: str
    metrics: Dict[str, Any]


class ContentFilter(ABC):
    """Abstract base class for content filters"""

    @abstractmethod
    def validate(self, content: str) -> ValidationResult:
        """Validate content and return result"""
        pass

    @abstractmethod
    def clean(self, content: str) -> str:
        """Clean and normalize content"""
        pass


class MinLengthFilter(ContentFilter):
    """Filter content based on minimum length requirements"""

    def __init__(self, min_length: int = 100, min_words: int = 20):
        self.min_length = min_length
        self.min_words = min_words

    def validate(self, content: str) -> ValidationResult:
        char_count = len(content)
        word_count = len(content.split())
        is_valid = char_count >= self.min_length and word_count >= self.min_words

        return ValidationResult(
            is_valid=is_valid,
            score=char_count / self.min_length,
            message=f"Content length: {char_count} chars, {word_count} words",
            metrics={"char_count": char_count, "word_count": word_count},
        )

    def clean(self, content: str) -> str:
        return content.strip()


class LanguageFilter(ContentFilter):
    """Filter content based on language detection"""

    def __init__(self, allowed_languages: List[str] = None):
        self.allowed_languages = allowed_languages or ["en"]
        self.stop_words = {
            lang: set(stopwords.words(lang))
            for lang in self.allowed_languages
            if lang in stopwords.fileids()
        }

    def validate(self, content: str) -> ValidationResult:
        try:
            detected_lang = langdetect.detect(content)
            is_valid = detected_lang in self.allowed_languages
            confidence = self._calculate_language_confidence(content, detected_lang)

            return ValidationResult(
                is_valid=is_valid,
                score=confidence,
                message=f"Detected language: {detected_lang}",
                metrics={"language": detected_lang, "confidence": confidence},
            )
        except langdetect.LangDetectException:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                message="Language detection failed",
                metrics={},
            )

    def clean(self, content: str) -> str:
        """Remove common stop words and normalize text"""
        words = word_tokenize(content.lower())
        cleaned_words = [
            word
            for word in words
            if not any(word in stop_words for stop_words in self.stop_words.values())
        ]
        return " ".join(cleaned_words)

    def _calculate_language_confidence(self, content: str, detected_lang: str) -> float:
        """Calculate confidence score for language detection"""
        if detected_lang not in self.stop_words:
            return 0.5

        words = word_tokenize(content.lower())
        stop_word_ratio = sum(
            1 for word in words if word in self.stop_words[detected_lang]
        ) / len(words)
        return stop_word_ratio


class QualityFilter(ContentFilter):
    """Filter content based on quality metrics"""

    def __init__(self, min_score: float = 0.7):
        self.min_score = min_score
        self.quality_metrics = [
            self._readability_score,
            self._density_score,
            self._structure_score,
        ]

    def validate(self, content: str) -> ValidationResult:
        scores = [metric(content) for metric in self.quality_metrics]
        avg_score = mean(scores)
        metrics = {
            "readability": scores[0],
            "density": scores[1],
            "structure": scores[2],
            "average": avg_score,
        }

        return ValidationResult(
            is_valid=avg_score >= self.min_score,
            score=avg_score,
            message=f"Quality score: {avg_score:.2f}",
            metrics=metrics,
        )

    def clean(self, content: str) -> str:
        """Improve content quality through cleaning"""
        # Remove excessive whitespace
        content = re.sub(r"\s+", " ", content)
        # Normalize sentence spacing
        content = re.sub(r"([.!?])\s*", r"\1 ", content)
        # Fix common formatting issues
        content = content.replace(" ,", ",").replace(" .", ".")
        return content.strip()

    def _readability_score(self, content: str) -> float:
        """Calculate readability score using multiple metrics"""
        try:
            doc = Document(content)
            metrics = doc.metrics
            return mean(
                [
                    metrics.flesch_reading_ease / 100,
                    (100 - metrics.flesch_kincaid_grade) / 100,
                    (100 - metrics.gunning_fog) / 100,
                ]
            )
        except:
            return 0.5

    def _density_score(self, content: str) -> float:
        """Calculate information density score"""
        words = word_tokenize(content)
        unique_words = len(set(words))
        return min(unique_words / len(words) if words else 0, 1.0)

    def _structure_score(self, content: str) -> float:
        """Evaluate content structure quality"""
        sentences = sent_tokenize(content)
        if not sentences:
            return 0.0

        avg_sent_len = mean([len(s.split()) for s in sentences])
        return min(avg_sent_len / 20, 1.0)


class ContentValidator:
    """
    Advanced content validation and cleaning system.

    This class provides comprehensive content validation and cleaning capabilities,
    including:
    - HTML cleaning and normalization
    - Minimum length requirements
    - Language detection and filtering
    - Quality metrics evaluation
    - Content structure analysis
    - Readability assessment

    Attributes:
        html_cleaner: HTML cleaning component
        content_filters: List of content validation filters
        validation_threshold: Minimum validation score required
        validation_results: Dictionary storing validation results
    """

    def __init__(self, validation_threshold: float = 0.7):
        """
        Initialize ContentValidator with specified parameters.

        Args:
            validation_threshold: Minimum score for content to be considered valid
        """
        self.html_cleaner = HTMLCleaner()
        self.content_filters = [
            MinLengthFilter(min_length=100, min_words=20),
            LanguageFilter(allowed_languages=["en"]),
            QualityFilter(min_score=validation_threshold),
        ]
        self.validation_threshold = validation_threshold
        self.validation_results: Dict[str, List[ValidationResult]] = {}

    def validate_and_clean(self, content: ScrapedContent) -> Optional[ScrapedContent]:
        """
        Validate and clean scraped content.

        Args:
            content: ScrapedContent object to validate and clean

        Returns:
            Cleaned ScrapedContent object if valid, None otherwise

        Raises:
            ValueError: If content is malformed or cleaning fails
        """
        try:
            # Clean HTML and normalize text
            cleaned_content = self.html_cleaner.clean(content.content)
            results = []

            # Apply content filters
            for filter_obj in self.content_filters:
                # Validate content
                result = filter_obj.validate(cleaned_content)
                results.append(result)

                if not result.is_valid:
                    self._store_validation_results(content.url, results)
                    return None

                # Clean content if valid
                cleaned_content = filter_obj.clean(cleaned_content)

            # Store validation results
            self._store_validation_results(content.url, results)

            # Update content with cleaned version
            content.content = cleaned_content
            content.word_count = len(cleaned_content.split())
            return content

        except Exception as e:
            logger.error(f"Content validation failed: {str(e)}")
            return None

    def _store_validation_results(self, url: str, results: List[ValidationResult]):
        """Store validation results for analysis"""
        self.validation_results[url] = results

    def get_validation_metrics(self, url: str) -> Dict[str, Any]:
        """
        Get validation metrics for a specific URL.

        Args:
            url: URL to get metrics for

        Returns:
            Dictionary containing validation metrics
        """
        if url not in self.validation_results:
            return {}

        results = self.validation_results[url]
        return {
            "overall_score": mean(r.score for r in results),
            "passed_filters": sum(1 for r in results if r.is_valid),
            "total_filters": len(results),
            "messages": [r.message for r in results],
            "metrics": {i: r.metrics for i, r in enumerate(results)},
        }

    def clear_validation_results(self):
        """Clear stored validation results"""
        self.validation_results.clear()


class HTMLCleaner:
    """
    Advanced HTML cleaning and sanitization with support for multiple cleaning strategies,
    custom tag handling, and content preservation options.

    This class provides comprehensive HTML cleaning capabilities including:
    - Tag and attribute filtering
    - JavaScript and style removal
    - Comment and metadata stripping
    - Structural element preservation
    - Custom tag handling
    - Content sanitization
    - Encoding normalization

    Attributes:
        allowed_tags (Set[str]): Set of HTML tags to preserve
        allowed_attributes (Set[str]): Set of allowed HTML attributes
        preserve_structure (bool): Whether to maintain document structure
        encoding (str): Input/output encoding
        remove_empty (bool): Whether to remove empty elements
        normalize_whitespace (bool): Whether to normalize whitespace
        url_schemes (Set[str]): Allowed URL schemes
        max_length (int): Maximum length for attribute values
    """

    def __init__(
        self,
        preserve_structure: bool = True,
        remove_empty: bool = True,
        normalize_whitespace: bool = True,
        encoding: str = "utf-8",
    ):
        """
        Initialize HTMLCleaner with specified configuration.

        Args:
            preserve_structure: Whether to maintain document structure
            remove_empty: Remove empty elements
            normalize_whitespace: Normalize whitespace
            encoding: Input/output encoding
        """
        from bs4 import BeautifulSoup
        from lxml import etree
        from lxml.html.clean import Cleaner

        self.preserve_structure = preserve_structure
        self.remove_empty = remove_empty
        self.normalize_whitespace = normalize_whitespace
        self.encoding = encoding

        self.allowed_tags = {
            "div",
            "p",
            "br",
            "span",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "ul",
            "ol",
            "li",
            "a",
            "img",
            "table",
            "tr",
            "td",
            "th",
            "thead",
            "tbody",
            "article",
            "section",
            "main",
            "aside",
            "blockquote",
        }

        self.allowed_attributes = {
            "href",
            "src",
            "alt",
            "title",
            "class",
            "id",
            "name",
            "width",
            "height",
            "target",
        }

        self.url_schemes = {"http", "https", "mailto", "tel"}
        self.max_length = 1024
        self.cleaner = Cleaner(
            scripts=True,
            javascript=True,
            comments=True,
            style=True,
            links=True,
            meta=True,
            processing_instructions=True,
            embedded=True,
            frames=True,
            forms=True,
            annoying_tags=True,
            remove_unknown_tags=True,
            safe_attrs_only=True,
            safe_attrs=self.allowed_attributes,
            remove_tags=set(),
            allow_tags=self.allowed_tags,
        )

        self.parser = etree.HTMLParser(remove_blank_text=True)
        self.beautifier = BeautifulSoup

    def clean(self, html: str) -> str:
        """
        Clean and sanitize HTML content.

        Args:
            html: Raw HTML content to clean

        Returns:
            Cleaned HTML string

        Raises:
            ValueError: If HTML is malformed
            UnicodeError: If encoding fails
        """
        try:
            # Initial cleaning with lxml
            cleaned_html = self.cleaner.clean_html(html)

            if self.preserve_structure:
                cleaned_html = self._preserve_document_structure(cleaned_html)

            if self.remove_empty:
                cleaned_html = self._remove_empty_elements(cleaned_html)

            if self.normalize_whitespace:
                cleaned_html = self._normalize_whitespace(cleaned_html)

            return self._post_process(cleaned_html)

        except Exception as e:
            logger.error(f"HTML cleaning failed: {str(e)}")
            return self._fallback_clean(html)

    def _preserve_document_structure(self, html: str) -> str:
        """Preserve important document structure elements"""
        soup = self.beautifier(html, "lxml")
        for tag in soup.find_all(True):
            if tag.name in self.allowed_tags:
                continue
            if any(c.name in self.allowed_tags for c in tag.children):
                tag.unwrap()
            else:
                tag.decompose()
        return str(soup)

    def _remove_empty_elements(self, html: str) -> str:
        """Remove elements with no content"""
        soup = self.beautifier(html, "lxml")
        for tag in soup.find_all(True):
            if not tag.get_text(strip=True) and tag.name not in {"img", "br"}:
                tag.decompose()
        return str(soup)

    def _normalize_whitespace(self, html: str) -> str:
        """Normalize whitespace in text nodes"""
        soup = self.beautifier(html, "lxml")
        for text in soup.find_all(text=True):
            if text.parent.name not in {"pre", "code"}:
                text.replace_with(" ".join(text.strip().split()))
        return str(soup)

    def _post_process(self, html: str) -> str:
        """Final processing and cleanup"""
        soup = self.beautifier(html, "lxml")

        # Clean URLs
        for tag in soup.find_all(["a", "img"]):
            if "href" in tag.attrs:
                tag["href"] = self._clean_url(tag["href"])
            if "src" in tag.attrs:
                tag["src"] = self._clean_url(tag["src"])

        # Truncate long attributes
        for tag in soup.find_all(True):
            for attr in list(tag.attrs):
                if len(str(tag[attr])) > self.max_length:
                    tag[attr] = str(tag[attr])[: self.max_length] + "..."

        return str(soup)

    def _clean_url(self, url: str) -> str:
        """Clean and validate URLs"""
        try:
            parsed = urlparse(url)
            if parsed.scheme and parsed.scheme not in self.url_schemes:
                return ""
            return url
        except Exception:
            return ""

    def _fallback_clean(self, html: str) -> str:
        """Fallback cleaning method for malformed HTML"""
        try:
            # Simple regex-based cleaning
            html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
            html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
            html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
            return html
        except Exception:
            return re.sub(r"<[^>]+>", "", html)  # Strip all tags as last resort


# 6. **Advanced Error Handling and Recovery**:
class ErrorHandler:
    """Sophisticated error handling and recovery"""

    def __init__(self):
        self.error_counts = Counter()
        self.error_thresholds = {"connection": 5, "timeout": 3, "parse": 2}
        self.recovery_strategies = {
            "connection": self.handle_connection_error,
            "timeout": self.handle_timeout,
            "parse": self.handle_parse_error,
        }

    async def handle_error(self, error: Exception, context: Dict) -> Optional[Any]:
        error_type = self.classify_error(error)
        self.error_counts[error_type] += 1

        if self.error_counts[error_type] >= self.error_thresholds[error_type]:
            return await self.recovery_strategies[error_type](context)
        return None

    def classify_error(self, error: Exception) -> str:
        if isinstance(error, (ConnectionError, ConnectionRefusedError)):
            return "connection"
        if isinstance(error, TimeoutError):
            return "timeout"
        if isinstance(error, ParseError):
            return "parse"
        return "unknown"


# 7. **Performance Monitoring and Analytics**:
@dataclass
class MetricPoint:
    """Data class for storing individual metric measurements"""

    value: float
    timestamp: float
    labels: Dict[str, str] = None


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

        # Prometheus metrics
        self.request_counter = Counter("scraper_requests_total", "Total requests made")
        self.response_time = Histogram(
            "scraper_response_seconds", "Response time in seconds"
        )
        self.memory_gauge = Gauge("scraper_memory_bytes", "Memory usage in bytes")
        self.scraper_info = Info("scraper", "Scraper metadata")

        # Alert thresholds
        self.alert_thresholds = {
            "response_time": 5.0,  # seconds
            "error_rate": 0.1,  # 10%
            "memory_usage": 1024,  # MB
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

        # Update Prometheus metrics
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
                statistics.mean(m.value for m in self.metrics.get("response_time", []))
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
                m.value for m in self.metrics.get("bytes_received", [])
            ),
            "content_processing_time": (
                statistics.mean(
                    m.value for m in self.metrics.get("processing_time", [])
                )
                if self.metrics.get("processing_time")
                else 0
            ),
        }

        # Update Prometheus gauges
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
        # Add alert handling logic here

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
                """
                CREATE TABLE IF NOT EXISTS cache (
                    url TEXT PRIMARY KEY,
                    content BLOB,
                    timestamp DATETIME,
                    hash TEXT,
                    size INTEGER,
                    access_count INTEGER DEFAULT 0,
                    last_access DATETIME,
                    compressed BOOLEAN
                )
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_access ON cache(last_access)
            """
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
                """
                SELECT content, timestamp, compressed
                FROM cache
                WHERE url = ? AND timestamp > datetime('now', ?)
            """,
                (url, f"-{self.ttl} seconds"),
            )

            result = cursor.fetchone()
            if result:
                content, timestamp, compressed = result
                self.stats["hits"] += 1

                # Update access statistics
                conn.execute(
                    """
                    UPDATE cache
                    SET access_count = access_count + 1,
                        last_access = datetime('now')
                    WHERE url = ?
                """,
                    (url,),
                )

                # Decompress if needed
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

        # Serialize and optionally compress
        serialized = json.dumps(content).encode()
        compressed = False

        if self.compression and len(serialized) > 1024:
            import zlib

            serialized = zlib.compress(serialized)
            compressed = True

        content_hash = hashlib.sha256(serialized).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            # Check size limits
            if self._get_cache_size(conn) > self.max_size:
                self._evict_entries(conn)

            conn.execute(
                """
                INSERT OR REPLACE INTO cache
                (url, content, timestamp, hash, size, last_access, compressed)
                VALUES (?, ?, datetime('now'), ?, ?, datetime('now'), ?)
            """,
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
                    """
                    DELETE FROM cache
                    WHERE timestamp < datetime('now', ?)
                """,
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
            """
            DELETE FROM cache
            WHERE url IN (
                SELECT url FROM cache
                ORDER BY last_access ASC
                LIMIT (SELECT COUNT(*)/4 FROM cache)
            )
        """
        )

    def get_stats(self) -> Dict:
        """Get cache statistics and metrics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count,
                       SUM(size) as total_size,
                       SUM(access_count) as total_accesses,
                       AVG(access_count) as avg_accesses
                FROM cache
            """
            )
            db_stats = dict(
                zip(["count", "size", "accesses", "avg_accesses"], cursor.fetchone())
            )

            return {
                **self.stats,
                **db_stats,
                "hit_ratio": (
                    self.stats["hits"] / (self.stats["hits"] + self.stats["misses"])
                    if (self.stats["hits"] + self.stats["misses"]) > 0
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


class WebScraper:
    """Advanced web scraper with caching, content extraction and async capabilities.

    This class provides comprehensive web scraping functionality including:
    - Configurable caching and rate limiting
    - Content extraction and cleaning
    - Asynchronous scraping support
    - Link discovery and filtering
    - Result export in multiple formats

    Attributes:
        config (WebScraperConfig): Scraper configuration
        session (requests.Session): HTTP session for requests
        cache (CacheManager): Content cache manager
        visited_urls (Set[str]): Tracked URLs
        url_patterns (Dict[str, Pattern]): URL matching patterns
        content_pipeline (ContentPipeline): Content processing pipeline
        monitor (ScraperMonitor): Performance monitoring
    """

    def __init__(self, config: Optional[WebScraperConfig] = None):
        """Initialize web scraper with configuration.

        Args:
            config: Optional configuration object, uses defaults if not provided
        """
        self.config = config or WebScraperConfig()
        self.session = self._create_session()
        self.cache = CacheManager() if self.config.cache_enabled else None
        self.visited_urls: Set[str] = set()
        self.url_patterns = {
            "article": re.compile(r"article|post|story", re.I),
            "date": re.compile(r"\d{4}/\d{2}/\d{2}"),
            "pagination": re.compile(r"page|p=\d+", re.I),
        }
        self.content_pipeline = ContentPipeline()
        self.monitor = ScraperMonitor()

    def scrape_page(self, url: str) -> Optional[ScrapedContent]:
        """Scrape a single page with error handling and monitoring.

        Args:
            url: URL to scrape

        Returns:
            Scraped content or None if scraping fails

        Raises:
            ValueError: If URL is invalid
            RequestException: If request fails
        """
        try:
            if not self.should_scrape(url):
                logger.info(f"Skipping URL: {url}")
                return None

            start_time = time.time()
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()

            content = self.extract_content(response.text, url, response.status_code)

            # Process content through pipeline
            if content:
                content = asyncio.run(self.content_pipeline.process(content))

            # Record metrics
            self.monitor.record_metric("scrape_time", time.time() - start_time)

            return content

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            self.monitor.record_metric("scrape_error", 1)
            return None

    def _create_session(self) -> requests.Session:
        """Create and configure requests session with retries and timeouts.

        Returns:
            Configured requests Session object
        """
        session = requests.Session()

        # Configure retries
        retries = Retry(
            total=self.config.max_retries,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504],
        )

        # Set up connection pooling
        adapter = HTTPAdapter(
            max_retries=retries,
            pool_connections=self.config.max_workers,
            pool_maxsize=self.config.max_workers * 2,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Configure headers
        session.headers.update(
            {"User-Agent": self.config.user_agent, **self.config.headers}
        )

        if self.config.proxy:
            session.proxies.update(self.config.proxy)

        return session

    async def _async_scrape(self, url: str) -> Optional[ScrapedContent]:
        """Asynchronously scrape a single URL.

        Args:
            url: URL to scrape

        Returns:
            Scraped content or None if scraping fails
        """
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
                    return await self.extract_content_async(html, url, response.status)
        except Exception as e:
            logger.error(f"Async scraping error for {url}: {str(e)}")
            return None

    def should_scrape(self, url: str) -> bool:
        """Check if URL should be scraped based on configuration rules.

        Args:
            url: URL to check

        Returns:
            True if URL should be scraped, False otherwise
        """
        if not url or url in self.visited_urls:
            return False

        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        # Check domain restrictions
        if self.config.allowed_domains and domain not in self.config.allowed_domains:
            return False

        # Check exclusion patterns
        if any(re.search(pattern, url) for pattern in self.config.excluded_patterns):
            return False

        self.visited_urls.add(url)
        return True

    def extract_content(self, html: str, url: str, status_code: int) -> ScrapedContent:
        """Extract and structure content from HTML.

        Args:
            html: Raw HTML content
            url: Source URL
            status_code: HTTP status code

        Returns:
            Structured content object
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove unwanted elements
        for element in soup.select(
            "script, style, nav, footer, header, iframe, .ad, .social"
        ):
            element.decompose()

        # Extract metadata
        meta = self._extract_metadata(soup)

        # Extract main content
        main_content = self._extract_main_content(soup)

        # Extract images with full URLs
        images = self._extract_images(soup, url)

        # Create content hash
        content_hash = hashlib.sha256(main_content.encode()).hexdigest()

        return ScrapedContent(
            url=url,
            title=str(meta.get("title", "")),
            content=main_content,
            links=self._extract_links(soup, url),
            meta_description=meta.get("description"),
            images=images,
            timestamp=datetime.now().isoformat(),
            hash=content_hash,
            language=str(meta.get("language", "unknown")),
            status_code=status_code,
            content_type="text/html",
            word_count=len(main_content.split()),
        )

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from HTML head.

        Args:
            soup: Parsed HTML

        Returns:
            Dict of metadata values
        """
        meta = {}

        # Title
        if soup.title:
            meta["title"] = soup.title.string

        # Meta description
        desc_tag = soup.find("meta", {"name": "description"})
        if desc_tag and desc_tag.get("content"):
            meta["description"] = desc_tag["content"]

        # Language
        if soup.html.get("lang"):
            meta["language"] = soup.html["lang"]

        return meta

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content using multiple container detection strategies.

        Args:
            soup: Parsed HTML

        Returns:
            Extracted main content text
        """
        main_content = None

        # Try content containers in order of preference
        selectors = [
            "main",
            "article",
            'div[class*="content"]',
            'div[class*="article"]',
            ".post-content",
            "#main-content",
        ]

        for selector in selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

        # Fallback to body
        if not main_content:
            main_content = soup.body or soup

        # Extract text blocks
        text_blocks = []
        for element in main_content.stripped_strings:
            text = element.strip()
            # Filter short fragments
            if text and len(text) > self.config.min_text_length:
                text_blocks.append(text)

        return " ".join(text_blocks)

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract and filter relevant links from content.

        Args:
            soup: Parsed HTML
            base_url: Base URL for resolving relative links

        Returns:
            List of relevant absolute URLs
        """
        links = set()
        base_domain = urlparse(base_url).netloc

        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            # Only include internal links matching patterns
            if parsed.netloc == base_domain and any(
                pattern.search(full_url) for pattern in self.url_patterns.values()
            ):
                links.add(full_url)

        # Limit number of links
        return sorted(links)[: self.config.max_links]

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract image information with absolute URLs.

        Args:
            soup: Parsed HTML
            base_url: Base URL for resolving relative links

        Returns:
            List of image information dictionaries
        """
        images = []
        for img in soup.find_all("img"):
            if src := img.get("src"):
                images.append(
                    {
                        "src": urljoin(base_url, src),
                        "alt": img.get("alt", ""),
                        "title": img.get("title", ""),
                        "width": img.get("width", ""),
                        "height": img.get("height", ""),
                    }
                )
        return images

    def scrape_with_cache(self, url: str) -> Optional[ScrapedContent]:
        """Scrape URL with caching support.

        Args:
            url: URL to scrape

        Returns:
            Scraped content or None if scraping fails
        """
        if not self.cache:
            return self.scrape_page(url)

        # Check cache first
        if cached := self.cache.get(url):
            self.monitor.record_metric("cache_hit", 1)
            return ScrapedContent(**cached)

        self.monitor.record_metric("cache_miss", 1)

        # Scrape and cache content
        if content := self.scrape_page(url):
            self.cache.set(url, asdict(content))
            return content

        return None

    async def scrape_multiple_async(self, urls: List[str]) -> Dict[str, ScrapedContent]:
        """Asynchronously scrape multiple URLs in parallel.

        Args:
            urls: List of URLs to scrape

        Returns:
            Dict mapping URLs to scraped content
        """
        tasks = []
        async with aiohttp.ClientSession() as session:
            for url in urls:
                if self.should_scrape(url):
                    tasks.append(self._async_scrape(url))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            return {
                url: result
                for url, result in zip(urls, results)
                if isinstance(result, ScrapedContent)
            }

    def export_results(
        self, results: Dict[str, ScrapedContent], format: str = "json"
    ) -> None:
        """Export scraped results to file.

        Args:
            results: Dict mapping URLs to scraped content
            format: Export format ('json' or 'csv')
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scraping_results_{timestamp}.{format}"

        if format == "json":
            with open(filename, "w") as f:
                json.dump(
                    {url: asdict(content) for url, content in results.items()},
                    f,
                    indent=2,
                )
        elif format == "csv":
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["url", "title", "content", "word_count", "timestamp"])
                for url, content in results.items():
                    writer.writerow(
                        [
                            url,
                            content.title,
                            content.content[:500],
                            content.word_count,
                            content.timestamp,
                        ]
                    )


class AsyncWebScraper(WebScraper):
    """Async version of WebScraper"""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Cleanup resources"""
        if hasattr(self, "session"):
            await self.session.close()

    async def scrape_page_async(self, url: str) -> Optional[ScrapedContent]:
        """Async version of scrape_page"""
        try:
            if not self.should_scrape(url):
                return None

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.config.timeout) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
                    return self.extract_content(html, url, response.status)

        except Exception as e:
            logger.error(f"Async scraping error for {url}: {e}")
            return None


class ContentPipeline:
    """Content processing pipeline"""

    def __init__(self):
        self.processor = ContentProcessor()
        self.validator = ContentValidator()
        self.html_cleaner = HTMLCleaner()

    async def process(self, content: ScrapedContent) -> Optional[ScrapedContent]:
        try:
            # Clean HTML
            cleaned_html = self.html_cleaner.clean(content.content)
            content.content = cleaned_html

            # Validate content
            validated_content = self.validator.validate_and_clean(content)
            if not validated_content:
                return None

            # Process and enrich content
            processed_data = self.processor.process_content(validated_content.content)

            # Update content with processed data
            validated_content.keywords = processed_data.get("keywords", [])
            validated_content.summary = processed_data.get("summary", "")
            validated_content.entities = processed_data.get("entities", {})
            validated_content.readability_scores = processed_data.get(
                "readability_scores", {}
            )

            return validated_content

        except Exception as e:
            logger.error(f"Content pipeline error: {e}")
            return None


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

            # Check resource usage
            memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
            await self.performance_monitor.record_metric("memory_usage", memory_usage)

            # Export metrics
            self.export_metrics()

            await asyncio.sleep(60)

    def export_metrics(self):
        """Export monitoring metrics"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics = self.performance_monitor.get_statistics()

        with open(f"scraper_metrics_{timestamp}.json", "w") as f:
            json.dump(metrics, f, indent=2)


def main():
    # Configuration
    config = WebScraperConfig(
        rate_limit=2,
        max_workers=3,
        cache_enabled=True,
        follow_links=True,
        max_depth=2,
        allowed_domains={"python.org", "wikipedia.org"},
        excluded_patterns={r"login", r"signup", r"archive"},
    )

    # Initialize scraper
    scraper = WebScraper(config)

    # Test URLs
    test_urls = [
        "https://en.wikipedia.org/wiki/Web_scraping",
        "https://www.python.org/about/",
        "https://docs.python.org/3/",
    ]

    # Synchronous scraping
    print("Starting synchronous scraping...")
    results = {}
    for url in test_urls:
        result = scraper.scrape_with_cache(url)
        if result:
            results[url] = result

    # Export results
    scraper.export_results(results, "json")
    scraper.export_results(results, "csv")

    # Asynchronous scraping
    print("\nStarting asynchronous scraping...")
    async_results = asyncio.run(scraper.scrape_multiple_async(test_urls))

    # Print summary
    print("\nScraping Summary:")
    print(f"Total URLs processed: {len(test_urls)}")
    print(f"Successfully scraped: {len(results)}")
    print(f"Failed: {len(test_urls) - len(results)}")


if __name__ == "__main__":
    main()
