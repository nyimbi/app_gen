"""
Optimized Web Scraper with key features:
- Async support
- Content validation and cleaning
- Caching
- Basic monitoring
- Error handling
"""

import asyncio
import csv
import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
from urllib.parse import urljoin, urlparse

import aiohttp
import langdetect
import nltk
import pandas as pd
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from nltk.tokenize import sent_tokenize, word_tokenize

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ScrapedContent:
    """Structured container for scraped content"""
    url: str
    title: str
    content: str
    metadata: Dict
    timestamp: str
    hash: str
    word_count: int

class Cache:
    """Simple in-memory cache with TTL"""

    def __init__(self, ttl: int = 86400):
        self.cache: Dict[str, tuple] = {}
        self.ttl = ttl
        self.stats = {"hits": 0, "misses": 0}

    def get(self, key: str) -> Optional[Dict]:
        """Get value from cache if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                self.stats["hits"] += 1
                return value
            del self.cache[key]
        self.stats["misses"] += 1
        return None

    def set(self, key: str, value: Dict):
        """Store value in cache with timestamp"""
        self.cache[key] = (value, time.time())

    def clear(self):
        """Clear all cached items"""
        self.cache.clear()
        self.stats = {"hits": 0, "misses": 0}

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0
        return {
            "size": len(self.cache),
            "hit_rate": hit_rate,
            **self.stats
        }

class ContentProcessor:
    """Content cleaning and analysis"""

    def __init__(self):
        self.min_content_length = 100
        self.min_words = 20
        self.allowed_languages = {"en"}
        self.quality_threshold = 0.7

        # Compile regex patterns
        self.noise_patterns = [
            r'cookie\s*policy',
            r'advertisement',
            r'subscribe\s*now',
            r'sign\s*up',
            r'social\s*media',
        ]
        self.noise_regex = re.compile('|'.join(self.noise_patterns), re.I)

    def clean_html(self, html: str) -> str:
        """Remove unwanted HTML elements and clean content"""
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unwanted elements
        for element in soup.select('script, style, nav, footer, iframe, .ad, .social'):
            element.decompose()

        # Extract text blocks
        text_blocks = []
        for element in soup.stripped_strings:
            text = element.strip()
            if text and not self.noise_regex.search(text):
                text_blocks.append(text)

        return ' '.join(text_blocks)

    def validate_content(self, content: str) -> Optional[str]:
        """Validate content meets quality criteria"""
        if len(content) < self.min_content_length:
            return None

        words = word_tokenize(content)
        if len(words) < self.min_words:
            return None

        try:
            if langdetect.detect(content) not in self.allowed_languages:
                return None
        except:
            return None

        if not self._check_quality(content):
            return None

        return content

    def _check_quality(self, content: str) -> bool:
        """Check content quality metrics"""
        sentences = sent_tokenize(content)
        if not sentences:
            return False

        # Check sentence length distribution
        sent_lengths = [len(s.split()) for s in sentences]
        avg_length = sum(sent_lengths) / len(sent_lengths)
        if avg_length < 5 or avg_length > 40:
            return False

        # Check word diversity
        words = word_tokenize(content.lower())
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.4:
            return False

        return True

    def extract_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extract metadata from HTML"""
        metadata = {}

        # Title
        if soup.title:
            metadata['title'] = soup.title.string.strip()

        # Meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            metadata['description'] = meta_desc['content']

        # Language
        if soup.html.get('lang'):
            metadata['language'] = soup.html['lang']

        # OpenGraph tags
        for meta in soup.find_all('meta', property=re.compile(r'^og:')):
            metadata[meta['property'][3:]] = meta['content']

        return metadata

class WebScraper:
    """Async web scraper with content processing and caching"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            'max_retries': 3,
            'timeout': 30,
            'cache_enabled': True,
            'max_connections': 10,
            'user_agent': UserAgent().random,
            'follow_robots': True,
            'max_depth': 5
        }

        self.cache = Cache() if self.config['cache_enabled'] else None
        self.processor = ContentProcessor()
        self.visited_urls: Set[str] = set()
        self.start_time = time.time()
        self.stats = {
            'requests': 0,
            'success': 0,
            'failures': 0,
            'bytes_processed': 0
        }

    async def scrape(self, url: str) -> Optional[ScrapedContent]:
        """Scrape a single URL with caching and error handling"""
        try:
            if url in self.visited_urls:
                return None

            # Check cache first
            if self.cache:
                if cached := self.cache.get(url):
                    return ScrapedContent(**cached)

            # Fetch and process content
            async with self._create_session() as session:
                content = await self._fetch_url(session, url)
                if not content:
                    return None

                result = await self._process_content(content, url)
                if result and self.cache:
                    self.cache.set(url, asdict(result))

                self.visited_urls.add(url)
                return result

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            self.stats['failures'] += 1
            return None

    async def scrape_many(self, urls: List[str]) -> Dict[str, ScrapedContent]:
        """Scrape multiple URLs concurrently"""
        connector = aiohttp.TCPConnector(limit=self.config['max_connections'])
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self._fetch_and_process(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            return {
                url: result
                for url, result in zip(urls, results)
                if isinstance(result, ScrapedContent)
            }

    async def _fetch_and_process(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> Optional[ScrapedContent]:
        """Fetch and process a single URL"""
        try:
            if url in self.visited_urls:
                return None

            # Check cache
            if self.cache:
                if cached := self.cache.get(url):
                    return ScrapedContent(**cached)

            content = await self._fetch_url(session, url)
            if not content:
                return None

            result = await self._process_content(content, url)
            if result and self.cache:
                self.cache.set(url, asdict(result))

            self.visited_urls.add(url)
            return result

        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            self.stats['failures'] += 1
            return None

    async def _fetch_url(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> Optional[str]:
        """Fetch URL content with retries"""
        for attempt in range(self.config['max_retries']):
            try:
                async with session.get(
                    url,
                    timeout=self.config['timeout']
                ) as response:
                    self.stats['requests'] += 1

                    if response.status != 200:
                        logger.warning(
                            f"Failed to fetch {url}: Status {response.status}"
                        )
                        return None

                    content = await response.text()
                    self.stats['bytes_processed'] += len(content)
                    self.stats['success'] += 1
                    return content

            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url}, attempt {attempt + 1}")
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                return None

        return None

    async def _process_content(
        self,
        html: str,
        url: str
    ) -> Optional[ScrapedContent]:
        """Process and validate scraped content"""
        try:
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')

            # Clean and validate content
            cleaned_content = self.processor.clean_html(html)
            if not cleaned_content:
                return None

            validated_content = self.processor.validate_content(cleaned_content)
            if not validated_content:
                return None

            # Extract metadata
            metadata = self.processor.extract_metadata(soup)

            # Create content hash
            content_hash = hashlib.sha256(
                validated_content.encode()
            ).hexdigest()

            return ScrapedContent(
                url=url,
                title=metadata.get('title', ''),
                content=validated_content,
                metadata=metadata,
                timestamp=datetime.now().isoformat(),
                hash=content_hash,
                word_count=len(validated_content.split())
            )

        except Exception as e:
            logger.error(f"Error processing content from {url}: {e}")
            return None

    def _create_session(self) -> aiohttp.ClientSession:
        """Create HTTP session with configured settings"""
        timeout = aiohttp.ClientTimeout(total=self.config['timeout'])
        headers = {
            'User-Agent': self.config['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        return aiohttp.ClientSession(
            timeout=timeout,
            headers=headers,
            connector=aiohttp.TCPConnector(limit=self.config['max_connections'])
        )

    def get_stats(self) -> Dict:
        """Get scraper statistics"""
        elapsed = time.time() - self.start_time
        return {
            'uptime': elapsed,
            'urls_processed': len(self.visited_urls),
            'requests_per_second': self.stats['requests'] / elapsed if elapsed > 0 else 0,
            'success_rate': self.stats['success'] / self.stats['requests'] if self.stats['requests'] > 0 else 0,
            'bytes_processed': self.stats['bytes_processed'],
            'cache_stats': self.cache.get_stats() if self.cache else None,
            **self.stats
        }

    async def close(self):
        """Cleanup resources"""
        if self.cache:
            self.cache.clear()


class ContentExporter:
    """Handles exporting scraped content to different file formats"""

    def __init__(self, output_dir: str = "scraped_data"):
        """
        Initialize exporter with output directory

        Args:
            output_dir: Directory to save exported files
        """
        self.output_dir = Path(output_dir)
        self._ensure_directory()

    def _ensure_directory(self):
        """Create output directory if it doesn't exist"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, base: str, extension: str) -> str:
        """Generate filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base}_{timestamp}.{extension}"

    def save_to_json(self, data: Dict[str, ScrapedContent], filename: Optional[str] = None):
        """
        Save scraped content to JSON file

        Args:
            data: Dictionary of scraped content
            filename: Optional custom filename
        """
        filename = filename or self._generate_filename("scraped_content", "json")
        filepath = self.output_dir / filename

        # Convert ScrapedContent objects to dictionaries
        export_data = {
            url: {
                'url': content.url,
                'title': content.title,
                'content': content.content,
                'metadata': content.metadata,
                'timestamp': content.timestamp,
                'hash': content.hash,
                'word_count': content.word_count
            }
            for url, content in data.items()
        }

        with filepath.open('w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported JSON data to {filepath}")
        return filepath

    def save_to_csv(self, data: Dict[str, ScrapedContent], filename: Optional[str] = None):
        """
        Save scraped content to CSV file

        Args:
            data: Dictionary of scraped content
            filename: Optional custom filename
        """
        filename = filename or self._generate_filename("scraped_content", "csv")
        filepath = self.output_dir / filename

        # Prepare rows for CSV
        rows = []
        for url, content in data.items():
            rows.append({
                'url': content.url,
                'title': content.title,
                'content': content.content[:1000],  # Truncate long content
                'word_count': content.word_count,
                'timestamp': content.timestamp,
                'language': content.metadata.get('language', ''),
                'description': content.metadata.get('description', '')
            })

        # Use pandas for better CSV handling
        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False, encoding='utf-8')

        logger.info(f"Exported CSV data to {filepath}")
        return filepath

    def save_to_text(self, data: Dict[str, ScrapedContent], filename: Optional[str] = None):
        """
        Save scraped content to text file with basic formatting

        Args:
            data: Dictionary of scraped content
            filename: Optional custom filename
        """
        filename = filename or self._generate_filename("scraped_content", "txt")
        filepath = self.output_dir / filename

        with filepath.open('w', encoding='utf-8') as f:
            for url, content in data.items():
                f.write(f"URL: {url}\n")
                f.write(f"Title: {content.title}\n")
                f.write(f"Timestamp: {content.timestamp}\n")
                f.write(f"Word Count: {content.word_count}\n")
                f.write("\nContent:\n")
                f.write(content.content)
                f.write("\n\n" + "="*80 + "\n\n")  # Separator between entries

        logger.info(f"Exported text data to {filepath}")
        return filepath

    def save_to_excel(self, data: Dict[str, ScrapedContent], filename: Optional[str] = None):
        """
        Save scraped content to Excel file with multiple sheets

        Args:
            data: Dictionary of scraped content
            filename: Optional custom filename
        """
        filename = filename or self._generate_filename("scraped_content", "xlsx")
        filepath = self.output_dir / filename

        # Create different dataframes for main content and metadata
        main_data = []
        metadata = []

        for url, content in data.items():
            # Main content
            main_data.append({
                'url': url,
                'title': content.title,
                'content': content.content,
                'word_count': content.word_count,
                'timestamp': content.timestamp
            })

            # Metadata
            metadata.append({
                'url': url,
                **content.metadata
            })

        # Create Excel writer object
        with pd.ExcelWriter(filepath) as writer:
            # Write main content
            pd.DataFrame(main_data).to_excel(writer, sheet_name='Content', index=False)

            # Write metadata
            pd.DataFrame(metadata).to_excel(writer, sheet_name='Metadata', index=False)

        logger.info(f"Exported Excel data to {filepath}")
        return filepath

    def save_all_formats(self, data: Dict[str, ScrapedContent], base_filename: Optional[str] = None):
        """
        Save content in all available formats

        Args:
            data: Dictionary of scraped content
            base_filename: Optional base filename to use

        Returns:
            Dict of formats and their file paths
        """
        files = {}

        if base_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"{base_filename}_{timestamp}"

        files['json'] = self.save_to_json(data, f"{base_filename}.json" if base_filename else None)
        files['csv'] = self.save_to_csv(data, f"{base_filename}.csv" if base_filename else None)
        files['txt'] = self.save_to_text(data, f"{base_filename}.txt" if base_filename else None)
        files['xlsx'] = self.save_to_excel(data, f"{base_filename}.xlsx" if base_filename else None)

        return files



# Example Usage
async def main():
    # Configuration
    config = {
        'cache_enabled': True,
        'max_connections': 5,
        'timeout': 30,
        'max_retries': 3
    }

    # Initialize scraper
    scraper = WebScraper(config)
    exporter = ContentExporter(output_dir="scraped_data")

    # Test URLs
    urls = [
        'https://example.com',
        'https://python.org',
        'https://httpbin.org'
    ]

    try:
        # Scrape multiple URLs
        results = await scraper.scrape_many(urls)

        if results:
            json_file = exporter.save_to_json(results)
            csv_file = exporter.save_to_csv(results)
            text_file = exporter.save_to_text(results)
            excel_file = exporter.save_to_excel(results)

            # Or save all formats at once
            all_files = exporter.save_all_formats(results, base_filename="my_scrape")

        # Print results
        for url, content in results.items():
            print(f"\nURL: {url}")
            print(f"Title: {content.title}")
            print(f"Word count: {content.word_count}")
            print(f"Timestamp: {content.timestamp}")

        # Print statistics
        print("\nScraping Statistics:")
        stats = scraper.get_stats()
        print(json.dumps(stats, indent=2))

    finally:
        await scraper.close()

if __name__ == '__main__':
    asyncio.run(main())
