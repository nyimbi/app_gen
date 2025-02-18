"""
WebScraper module

Advanced web scraper with caching, content extraction and async capabilities.

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

Classes:

- WebScraper

"""

from typing import Any, Dict, List, Optional, Set

from ..cache import CacheManager
from ..content import ContentPipeline
from ..monitoring import ScraperMonitor


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
            "article": re.compile("article|post|story", re.I),
            "date": re.compile("\\d{4}/\\d{2}/\\d{2}"),
            "pagination": re.compile("page|p=\\d+", re.I),
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
            if content:
                content = asyncio.run(self.content_pipeline.process(content))
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
        retries = Retry(
            total=self.config.max_retries,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(
            max_retries=retries,
            pool_connections=self.config.max_workers,
            pool_maxsize=self.config.max_workers * 2,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
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
        if self.config.allowed_domains and domain not in self.config.allowed_domains:
            return False
        if any((re.search(pattern, url) for pattern in self.config.excluded_patterns)):
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
        for element in soup.select(
            "script, style, nav, footer, header, iframe, .ad, .social"
        ):
            element.decompose()
        meta = self._extract_metadata(soup)
        main_content = self._extract_main_content(soup)
        images = self._extract_images(soup, url)
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
        if soup.title:
            meta["title"] = soup.title.string
        desc_tag = soup.find("meta", {"name": "description"})
        if desc_tag and desc_tag.get("content"):
            meta["description"] = desc_tag["content"]
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
        if not main_content:
            main_content = soup.body or soup
        text_blocks = []
        for element in main_content.stripped_strings:
            text = element.strip()
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
            if parsed.netloc == base_domain and any(
                (pattern.search(full_url) for pattern in self.url_patterns.values())
            ):
                links.add(full_url)
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
        if cached := self.cache.get(url):
            self.monitor.record_metric("cache_hit", 1)
            return ScrapedContent(**cached)
        self.monitor.record_metric("cache_miss", 1)
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
