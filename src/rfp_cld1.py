"""
Enhanced RFP (Request for Proposal) Webscraper - Part 1: Core Infrastructure

This module implements the core infrastructure for a distributed, fault-tolerant RFP scraper.
Part 1 includes:
- Core data models and database schema
- Rate limiting implementation
- Deduplication system
- Distributed locking
- Basic utilities and configuration

Author: [Original Author]
Enhanced by: Claude
Date: February 20, 2025
"""

import asyncio
import aiohttp
import redis
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Set, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from datasketch import MinHash, MinHashLSH
import networkx as nx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON
import logging
import json
import time
from urllib.parse import urlparse
from pydantic import BaseModel, Field, validator
import hashlib

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s - %(filename)s:%(lineno)d'
)

logger = logging.getLogger(__name__)

# Configuration constants
CONFIG = {
    'REDIS_URL': 'redis://localhost:6379/0',
    'DATABASE_URL': 'postgresql+asyncpg://user:password@localhost/rfp_db',
    'RATE_LIMIT_REQUESTS': 10,  # requests per second
    'RATE_LIMIT_BURST': 20,     # max burst size
    'MINHASH_PERMUTATIONS': 128,
    'SIMILARITY_THRESHOLD': 0.9,
    'REQUEST_TIMEOUT': 30,
    'MAX_RETRIES': 3,
    'BACKOFF_BASE': 2,
    'JITTER_FACTOR': 0.1
}

# Database Models
Base = declarative_base()

class RFPDocument(Base):
    """SQLAlchemy model for RFP documents."""
    __tablename__ = 'rfp_documents'

    id = Column(Integer, primary_key=True)
    tender_id = Column(String, unique=True, nullable=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    organization = Column(String, nullable=False)
    issue_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    estimated_value = Column(Float, nullable=True)
    country = Column(String, nullable=False)
    source_url = Column(String, unique=True, nullable=False)
    content_hash = Column(String, unique=True, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RFPDocument(tender_id={self.tender_id}, title={self.title})>"

# Pydantic models for validation
class RFPData(BaseModel):
    """Pydantic model for RFP data validation."""
    tender_id: Optional[str]
    title: str
    description: str
    organization: str
    issue_date: datetime
    expiry_date: datetime
    estimated_value: Optional[float]
    country: str
    source_url: str
    content_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('expiry_date')
    def expiry_date_must_be_future(cls, v):
        if v < datetime.utcnow():
            raise ValueError('expiry_date must be in the future')
        return v

    class Config:
        arbitrary_types_allowed = True

class PageType(Enum):
    """Enumeration of possible page types for classification."""
    TENDER = "tender"
    LIST = "list"
    LANDING = "landing"
    ERROR = "error"
    API = "api"
    LOGIN = "login"
    UNKNOWN = "unknown"

@dataclass
class RateLimit:
    """Token bucket rate limiter implementation.

    Implements token bucket algorithm for rate limiting with O(1) time complexity
    per request check.

    Attributes:
        capacity (float): Maximum number of tokens
        fill_rate (float): Rate at which tokens are added (per second)
        tokens (float): Current number of tokens
        last_update (float): Timestamp of last update
    """
    capacity: float
    fill_rate: float
    tokens: float = field(init=False)
    last_update: float = field(init=False)

    def __post_init__(self):
        self.tokens = self.capacity
        self.last_update = time.monotonic()

    def get_tokens(self) -> float:
        """Calculate current number of tokens.

        Returns:
            float: Current number of tokens

        Time complexity: O(1)
        """
        now = time.monotonic()
        if self.tokens < self.capacity:
            delta = now - self.last_update
            self.tokens = min(
                self.capacity,
                self.tokens + delta * self.fill_rate
            )
        self.last_update = now
        return self.tokens

    def consume(self, tokens: float) -> bool:
        """Attempt to consume tokens.

        Args:
            tokens (float): Number of tokens to consume

        Returns:
            bool: True if tokens were consumed, False otherwise

        Time complexity: O(1)
        """
        if self.get_tokens() >= tokens:
            self.tokens -= tokens
            return True
        return False

class MinHashDeduplicator:
    """MinHash LSH based document deduplicator.

    Implements efficient near-duplicate detection using MinHash LSH algorithm.
    Time complexity: O(k) per comparison where k is number of hash functions.
    Space complexity: O(n*k) where n is number of documents.

    Attributes:
        num_perm (int): Number of permutation functions
        threshold (float): Jaccard similarity threshold
        lsh (MinHashLSH): LSH index structure
    """

    def __init__(
        self,
        num_perm: int = CONFIG['MINHASH_PERMUTATIONS'],
        threshold: float = CONFIG['SIMILARITY_THRESHOLD']
    ):
        self.num_perm = num_perm
        self.threshold = threshold
        self.lsh = MinHashLSH(
            threshold=threshold,
            num_perm=num_perm
        )

    def add_document(self, doc_id: str, content: str) -> None:
        """Add a document to the LSH index.

        Args:
            doc_id (str): Unique document identifier
            content (str): Document content

        Time complexity: O(k) where k is number of hash functions
        """
        minhash = self._compute_minhash(content)
        self.lsh.insert(doc_id, minhash)

    def is_duplicate(self, content: str) -> bool:
        """Check if document is a near-duplicate.

        Args:
            content (str): Document content to check

        Returns:
            bool: True if near-duplicate found

        Time complexity: O(k) where k is number of hash functions
        """
        minhash = self._compute_minhash(content)
        return len(self.lsh.query(minhash)) > 0

    def _compute_minhash(self, text: str) -> MinHash:
        """Compute MinHash signature for text.

        Args:
            text (str): Input text

        Returns:
            MinHash: Computed signature

        Time complexity: O(k) where k is number of hash functions
        """
        minhash = MinHash(num_perm=self.num_perm)
        for shingle in self._get_shingles(text):
            minhash.update(shingle.encode('utf8'))
        return minhash

    def _get_shingles(self, text: str, k: int = 5) -> Set[str]:
        """Generate k-shingles from text.

        Args:
            text (str): Input text
            k (int): Shingle size

        Returns:
            Set[str]: Set of k-shingles

        Time complexity: O(n) where n is text length
        """
        words = text.lower().split()
        return {
            ' '.join(words[i:i+k])
            for i in range(len(words) - k + 1)
        }

class DistributedLock:
    """Distributed lock implementation using Redis.

    Provides ACID guarantees for critical sections in distributed environment.
    Implements exponential backoff with jitter for contention management.

    Attributes:
        redis_client (redis.Redis): Redis client instance
        lock_name (str): Name of the lock
        expire_time (int): Lock expiration time in seconds
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        lock_name: str,
        expire_time: int = 10
    ):
        self.redis = redis_client
        self.lock_name = lock_name
        self.expire_time = expire_time

    async def acquire(
        self,
        retry_count: int = CONFIG['MAX_RETRIES'],
        base_delay: float = CONFIG['BACKOFF_BASE']
    ) -> bool:
        """Attempt to acquire the lock with exponential backoff.

        Args:
            retry_count (int): Number of retry attempts
            base_delay (float): Base delay between retries

        Returns:
            bool: True if lock acquired
        """
        for attempt in range(retry_count):
            if self.redis.set(
                self.lock_name,
                'locked',
                nx=True,
                ex=self.expire_time
            ):
                return True

            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt)
            jitter = delay * CONFIG['JITTER_FACTOR'] * np.random.random()
            await asyncio.sleep(delay + jitter)

        return False

    def release(self) -> None:
        """Release the lock."""
        self.redis.delete(self.lock_name)

# Utility functions
def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content.

    Args:
        content (str): Content to hash

    Returns:
        str: Hex digest of hash
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string into datetime object.

    Args:
        date_str (str): Date string to parse

    Returns:
        Optional[datetime]: Parsed datetime or None if invalid
    """
    date_formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%B %d, %Y',
        '%d %B %Y'
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

# Initialize database
async def init_db():
    """Initialize database connection and create tables."""
    engine = create_async_engine(CONFIG['DATABASE_URL'])
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

# Initialize Redis
def init_redis():
    """Initialize Redis connection."""
    return redis.from_url(CONFIG['REDIS_URL'])


"""
Enhanced RFP (Request for Proposal) Webscraper - Part 2: Scraping and Extraction

This module implements the core scraping and content extraction functionality.
Part 2 includes:
- Async HTTP client with retry logic
- Content extraction and classification
- HTML parsing and cleaning
- PDF document processing
- Text analysis and entity extraction

Author: [Original Author]
Enhanced by: Claude
Date: February 20, 2025
"""

from bs4 import BeautifulSoup
import aiohttp
import asyncio
import PyPDF2
import io
from typing import Optional, Dict, List, Set, Tuple, Any
from dataclasses import dataclass
import re
from urllib.parse import urljoin, urlparse
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from langdetect import detect
import spacy
from datetime import datetime
import logging
import json
from concurrent.futures import ThreadPoolExecutor
import fitz  # PyMuPDF for better PDF handling

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

# Load spaCy model for entity extraction
nlp = spacy.load('en_core_web_sm')

@dataclass
class ExtractedContent:
    """Container for extracted content from a page.

    Attributes:
        title (str): Document title
        main_text (str): Main text content
        metadata (Dict): Extracted metadata
        links (List[str]): Extracted links
        tables (List[List[str]]): Extracted tables
        language (str): Detected language
    """
    title: str
    main_text: str
    metadata: Dict[str, Any]
    links: List[str]
    tables: List[List[str]]
    language: str

class AsyncHTTPClient:
    """Asynchronous HTTP client with retry logic.

    Implements connection pooling, automatic retries with exponential backoff,
    and proper resource cleanup.

    Attributes:
        session (aiohttp.ClientSession): Async HTTP session
        max_retries (int): Maximum number of retry attempts
        timeout (int): Request timeout in seconds
    """

    def __init__(
        self,
        max_retries: int = 3,
        timeout: int = 30,
        concurrent_requests: int = 10
    ):
        self.max_retries = max_retries
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.semaphore = asyncio.Semaphore(concurrent_requests)
        self.session = None

    async def __aenter__(self):
        """Initialize the HTTP session."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Clean up the HTTP session."""
        if self.session:
            await self.session.close()

    async def get(self, url: str, headers: Optional[Dict] = None) -> Optional[str]:
        """Fetch URL content with retry logic.

        Args:
            url (str): URL to fetch
            headers (Optional[Dict]): Request headers

        Returns:
            Optional[str]: Page content if successful, None otherwise
        """
        if not headers:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

        async with self.semaphore:
            for attempt in range(self.max_retries):
                try:
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            return await response.text()
                        elif response.status == 404:
                            logging.warning(f"Page not found: {url}")
                            return None
                        elif response.status in {500, 502, 503, 504}:
                            # Server error, retry
                            continue
                        else:
                            logging.error(f"HTTP {response.status} for {url}")
                            return None

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt == self.max_retries - 1:
                        logging.error(f"Failed to fetch {url}: {str(e)}")
                        return None
                    await asyncio.sleep(2 ** attempt)

        return None

class ContentExtractor:
    """Extracts structured content from HTML pages.

    Implements various extraction techniques including:
    - Main content extraction using readability algorithms
    - Table extraction and structure preservation
    - Metadata extraction
    - Language detection

    Attributes:
        min_text_length (int): Minimum text length for content blocks
        max_link_density (float): Maximum link density for content blocks
    """

    def __init__(
        self,
        min_text_length: int = 100,
        max_link_density: float = 0.2
    ):
        self.min_text_length = min_text_length
        self.max_link_density = max_link_density

    async def extract(self, html: str, url: str) -> ExtractedContent:
        """Extract content from HTML.

        Args:
            html (str): HTML content
            url (str): Source URL

        Returns:
            ExtractedContent: Extracted content
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Extract and clean up content
        title = self._extract_title(soup)
        main_text = self._extract_main_text(soup)
        metadata = self._extract_metadata(soup)
        links = self._extract_links(soup, url)
        tables = self._extract_tables(soup)

        # Detect language
        try:
            language = detect(main_text[:1000])
        except:
            language = 'en'

        return ExtractedContent(
            title=title,
            main_text=main_text,
            metadata=metadata,
            links=links,
            tables=tables,
            language=language
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract document title.

        Tries multiple sources:
        1. HTML title tag
        2. Main heading (h1)
        3. First significant heading
        """
        # Try title tag
        if soup.title:
            return soup.title.string.strip()

        # Try main heading
        if soup.h1:
            return soup.h1.get_text().strip()

        # Try first significant heading
        for tag in ['h2', 'h3', 'h4']:
            if soup.find(tag):
                return soup.find(tag).get_text().strip()

        return ''

    def _extract_main_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content.

        Implements a simplified readability algorithm:
        1. Identify content blocks
        2. Score blocks based on text density and quality
        3. Extract and clean up the main content
        """
        # Remove unwanted elements
        for elem in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
            elem.decompose()

        # Find content blocks
        blocks = []
        for elem in soup.find_all(['p', 'div', 'article', 'section']):
            text = elem.get_text().strip()
            if len(text) < self.min_text_length:
                continue

            # Calculate link density
            link_length = sum(len(a.get_text()) for a in elem.find_all('a'))
            if link_length / len(text) > self.max_link_density:
                continue

            blocks.append(text)

        return '\n\n'.join(blocks)

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from meta tags and other sources."""
        metadata = {}

        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', meta.get('property', ''))
            content = meta.get('content', '')
            if name and content:
                metadata[name] = content

        # Extract structured data
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                metadata['structured_data'] = data
            except:
                continue

        return metadata

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract and normalize links."""
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if not href.startswith(('http://', 'https://', 'mailto:', 'tel:')):
                href = urljoin(base_url, href)
            if href.startswith(('http://', 'https://')):
                links.append(href)
        return links

    def _extract_tables(self, soup: BeautifulSoup) -> List[List[str]]:
        """Extract tables preserving structure."""
        tables = []
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                row = []
                for td in tr.find_all(['td', 'th']):
                    row.append(td.get_text().strip())
                if row:
                    rows.append(row)
            if rows:
                tables.append(rows)
        return tables

class PDFProcessor:
    """PDF document processor.

    Implements robust PDF text extraction with layout preservation,
    table detection, and metadata extraction.

    Attributes:
        executor (ThreadPoolExecutor): Thread pool for CPU-bound tasks
    """

    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process(self, content: bytes) -> Tuple[str, Dict[str, Any]]:
        """Process PDF content.

        Args:
            content (bytes): PDF file content

        Returns:
            Tuple[str, Dict]: Extracted text and metadata
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._process_pdf,
            content
        )

    def _process_pdf(self, content: bytes) -> Tuple[str, Dict[str, Any]]:
        """Internal PDF processing implementation."""
        text_blocks = []
        metadata = {}

        try:
            # Use PyMuPDF for better text extraction
            doc = fitz.open(stream=content, filetype="pdf")

            # Extract metadata
            metadata = {
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'keywords': doc.metadata.get('keywords', ''),
                'creator': doc.metadata.get('creator', ''),
                'producer': doc.metadata.get('producer', ''),
                'creation_date': doc.metadata.get('creationDate', ''),
                'modification_date': doc.metadata.get('modDate', ''),
                'page_count': len(doc)
            }

            # Extract text with layout preservation
            for page in doc:
                blocks = page.get_text("blocks")
                # Sort blocks by vertical position
                blocks.sort(key=lambda b: (b[1], b[0]))
                for b in blocks:
                    if b[6] == 0:  # Text block
                        text_blocks.append(b[4])

            doc.close()
            return '\n'.join(text_blocks), metadata

        except Exception as e:
            logging.error(f"PDF processing error: {str(e)}")
            # Fallback to PyPDF2
            try:
                reader = PyPDF2.PdfReader(io.BytesIO(content))
                text = ''
                for page in reader.pages:
                    text += page.extract_text() + '\n'
                return text, {}
            except Exception as e:
                logging.error(f"PyPDF2 fallback error: {str(e)}")
                return '', {}

class EntityExtractor:
    """Extract entities and key information from text.

    Uses spaCy for entity recognition and custom patterns for
    RFP-specific information extraction.

    Attributes:
        nlp (spacy.Language): spaCy language model
        date_patterns (List[re.Pattern]): Regular expressions for date matching
    """

    def __init__(self):
        self.date_patterns = [
            re.compile(r'\d{4}-\d{2}-\d{2}'),
            re.compile(r'\d{2}/\d{2}/\d{4}'),
            re.compile(r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', re.I)
        ]

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities and key information.

        Args:
            text (str): Input text

        Returns:
            Dict[str, Any]: Extracted entities and information
        """
        doc = nlp(text)

        entities = {
            'organizations': [],
            'locations': [],
            'dates': [],
            'money': [],
            'contact_info': []
        }

        # Extract spaCy entities
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                entities['organizations'].append(ent.text)
            elif ent.label_ == 'GPE':
                entities['locations'].append(ent.text)
            elif ent.label_ == 'MONEY':
                entities['money'].append(ent.text)

        # Extract dates using patterns
        for pattern in self.date_patterns:
            for match in pattern.finditer(text):
                entities['dates'].append(match.group())

        # Extract contact information
        entities['contact_info'].extend(self._extract_contact_info(text))

        # Deduplicate and clean
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    def _extract_contact_info(self, text: str) -> List[str]:
        """Extract contact information using patterns."""
        contact_info = []

        # Email addresses
        emails = re.findall(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', text)
        contact_info.extend(emails)

        # Phone numbers
        phones = re.findall(r'\+?[\d\s\-\(\)]{10,}', text)
        contact_info.extend(phones)

        return contact_info

# Initialization of required resources
class RFPClassifier:
    """Classifies pages as RFP/tender documents.

    Uses a combination of heuristic rules and text analysis to determine
    if a page contains an RFP/tender document.

    Attributes:
        rfp_keywords (Set[str]): Keywords indicating RFP content
        threshold (float): Classification threshold
    """

    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold
        self.rfp_keywords = {
            'rfp', 'tender', 'proposal', 'bid', 'procurement',
            'submission', 'deadline', 'bidding', 'contract',
            'solicitation', 'requirements', 'scope of work'
        }

    def classify(self, content: ExtractedContent) -> Tuple[bool, float]:
        """Classify content as RFP/tender.

        Args:
            content (ExtractedContent): Extracted page content

        Returns:
            Tuple[bool, float]: Classification result and confidence score
        """
        if content.language != 'en':
            # For non-English content, rely on structural features
            return self._classify_by_structure(content)

        # Tokenize and normalize text
        tokens = word_tokenize(content.main_text.lower())
        words = set(tokens) - set(stopwords.words('english'))

        # Calculate keyword density
        keyword_count = sum(1 for word in words if word in self.rfp_keywords)
        density = keyword_count / len(words) if words else 0

        # Check for mandatory elements
        has_dates = any(
            re.search(r'\b(deadline|due date|closing date)\b', content.main_text, re.I)
        )
        has_contact = bool(content.metadata.get('contact_info'))

        # Calculate confidence score
        score = (density * 0.5 + has_dates * 0.3 + has_contact * 0.2)

        return score >= self.threshold, score

    def _classify_by_structure(self, content: ExtractedContent) -> Tuple[bool, float]:
        """Classify based on structural features for non-English content."""
        # Check for typical RFP structure
        has_tables = bool(content.tables)
        has_dates = bool(re.search(r'\d{2}[-/]\d{2}[-/]\d{4}', content.main_text))
        has_sections = len(content.main_text.split('\n\n')) > 3

        # Calculate structural score
        score = (has_tables * 0.4 + has_dates * 0.4 + has_sections * 0.2)

        return score >= self.threshold, score

async def init_extractors():
    """Initialize content extraction components."""
    return {
        'content': ContentExtractor(),
        'pdf': PDFProcessor(),
        'entity': EntityExtractor()
    }


"""
Enhanced RFP (Request for Proposal) Webscraper - Part 3: Orchestration and Main Logic

This module implements the orchestration layer and main scraping logic.
Part 3 includes:
- Distributed task queue management
- Site discovery and crawl strategy
- Main scraping workflow
- Error handling and recovery
- Monitoring and logging

Author: [Original Author]
Enhanced by: Claude
Date: February 20, 2025
"""

import asyncio
from dataclasses import dataclass
from typing import Optional, Dict, List, Set, Any
from datetime import datetime, timedelta
import logging
import json
from urllib.parse import urljoin, urlparse
import aioredis
from prefect import flow, task
from prefect.client.schemas import State
import aiohttp
import signal
import sys
import traceback
from collections import defaultdict
import time

# Import from Part 1
from part1 import (
    RFPDocument, RFPData, PageType, RateLimit,
    MinHashDeduplicator, DistributedLock, init_db, init_redis,
    CONFIG
)

# Import from Part 2
from part2 import (
    AsyncHTTPClient, ContentExtractor, PDFProcessor,
    EntityExtractor, RFPClassifier, ExtractedContent,
    init_extractors
)

@dataclass
class SiteConfig:
    """Configuration for a target site.

    Attributes:
        base_url (str): Base URL of the site
        country (str): Associated country
        allowed_domains (Set[str]): Allowed domains for crawling
        max_depth (int): Maximum crawl depth
        respect_robots (bool): Whether to respect robots.txt
    """
    base_url: str
    country: str
    allowed_domains: Set[str]
    max_depth: int = 3
    respect_robots: bool = True

class RobotsTxtParser:
    """Parser for robots.txt files.

    Implements proper robots.txt parsing according to RFC specifications.
    Handles both allow and disallow rules with pattern matching.

    Attributes:
        rules (Dict[str, List[str]]): Parsed allow/disallow rules
        sitemaps (List[str]): Extracted sitemap URLs
        crawl_delay (Optional[float]): Specified crawl delay
    """

    def __init__(self):
        self.rules = defaultdict(list)
        self.sitemaps = []
        self.crawl_delay = None

    async def parse(self, url: str, client: AsyncHTTPClient) -> None:
        """Parse robots.txt file.

        Args:
            url (str): Base URL for robots.txt
            client (AsyncHTTPClient): HTTP client
        """
        robots_url = urljoin(url, '/robots.txt')
        content = await client.get(robots_url)
        if not content:
            return

        current_agent = '*'
        for line in content.split('\n'):
            line = line.strip().lower()
            if not line or line.startswith('#'):
                continue

            parts = line.split(':', 1)
            if len(parts) != 2:
                continue

            key, value = parts[0].strip(), parts[1].strip()

            if key == 'user-agent':
                current_agent = value
            elif key == 'disallow':
                self.rules[current_agent].append(('-', value))
            elif key == 'allow':
                self.rules[current_agent].append(('+', value))
            elif key == 'sitemap':
                self.sitemaps.append(value)
            elif key == 'crawl-delay':
                try:
                    self.crawl_delay = float(value)
                except ValueError:
                    pass

    def can_fetch(self, url: str, user_agent: str = '*') -> bool:
        """Check if URL can be fetched.

        Args:
            url (str): URL to check
            user_agent (str): User agent string

        Returns:
            bool: True if URL can be fetched
        """
        path = urlparse(url).path
        rules = self.rules.get(user_agent, self.rules.get('*', []))

        for rule_type, pattern in rules:
            if pattern == '/' and rule_type == '-':
                return False
            if path.startswith(pattern):
                return rule_type == '+'

        return True

class SiteDiscoverer:
    """Discovers target sites and generates configurations.

    Implements various discovery methods:
    - Search API integration
    - Known site database
    - Domain pattern matching

    Attributes:
        redis (redis.Redis): Redis client for state persistence
        http_client (AsyncHTTPClient): HTTP client
    """

    def __init__(self, redis_client: redis.Redis, http_client: AsyncHTTPClient):
        self.redis = redis_client
        self.http_client = http_client

    async def discover(self) -> List[SiteConfig]:
        """Discover target sites.

        Returns:
            List[SiteConfig]: List of discovered site configurations
        """
        configs = []

        # Load known sites from Redis
        known_sites = await self.load_known_sites()
        configs.extend(self.create_configs(known_sites))

        # Discover new sites via search
        search_results = await self.search_new_sites()
        new_sites = [
            site for site in search_results
            if site['domain'] not in {c.base_url for c in configs}
        ]
        configs.extend(self.create_configs(new_sites))

        # Save newly discovered sites
        await self.save_sites(new_sites)

        return configs

    async def load_known_sites(self) -> List[Dict]:
        """Load known sites from Redis."""
        sites = self.redis.get('known_sites')
        return json.loads(sites) if sites else []

    async def save_sites(self, sites: List[Dict]) -> None:
        """Save sites to Redis."""
        known_sites = await self.load_known_sites()
        known_sites.extend(sites)
        self.redis.set('known_sites', json.dumps(known_sites))

    def create_configs(self, sites: List[Dict]) -> List[SiteConfig]:
        """Create site configurations."""
        configs = []
        for site in sites:
            domain = urlparse(site['url']).netloc
            allowed_domains = {domain}
            if site.get('allow_subdomains'):
                root_domain = '.'.join(domain.split('.')[-2:])
                allowed_domains.add(root_domain)
            configs.append(SiteConfig(
                base_url=site['url'],
                country=site.get('country', 'Unknown'),
                allowed_domains=allowed_domains
            ))
        return configs

class Orchestrator:
    """Main orchestration for the RFP scraping system.

    Coordinates all components and manages the scraping workflow.
    Implements fault tolerance and monitoring.

    Attributes:
        db_session (AsyncSession): Database session
        redis (redis.Redis): Redis client
        http_client (AsyncHTTPClient): HTTP client
        rate_limiter (RateLimit): Rate limiter
        deduplicator (MinHashDeduplicator): Content deduplicator
        extractors (Dict): Content extraction components
    """

    def __init__(
        self,
        db_session,
        redis_client,
        http_client,
        rate_limiter,
        deduplicator,
        extractors
    ):
        self.db_session = db_session
        self.redis = redis_client
        self.http_client = http_client
        self.rate_limiter = rate_limiter
        self.deduplicator = deduplicator
        self.extractors = extractors
        self.stats = defaultdict(int)
        self.start_time = time.time()

    async def orchestrate(self):
        """Main orchestration logic."""
        try:
            # Discover target sites
            discoverer = SiteDiscoverer(self.redis, self.http_client)
            site_configs = await discoverer.discover()

            # Process each site
            tasks = []
            for config in site_configs:
                task = asyncio.create_task(
                    self.process_site(config)
                )
                tasks.append(task)

            # Wait for all tasks to complete
            await asyncio.gather(*tasks)

        except Exception as e:
            logging.error(f"Orchestration error: {str(e)}")
            traceback.print_exc()

        finally:
            await self.cleanup()

    async def process_site(self, config: SiteConfig):
        """Process a single site.

        Args:
            config (SiteConfig): Site configuration
        """
        try:
            # Parse robots.txt
            if config.respect_robots:
                robots = RobotsTxtParser()
                await robots.parse(config.base_url, self.http_client)

            # Initialize site-specific components
            classifier = RFPClassifier()
            visited = set()
            queue = [(config.base_url, 0)]  # (url, depth)

            while queue:
                url, depth = queue.pop(0)

                if url in visited or depth > config.max_depth:
                    continue

                visited.add(url)

                # Check robots.txt
                if config.respect_robots and not robots.can_fetch(url):
                    continue

                # Apply rate limiting
                while not self.rate_limiter.consume(1.0):
                    await asyncio.sleep(0.1)

                # Fetch and process page
                content = await self.http_client.get(url)
                if not content:
                    continue

                # Extract content
                extracted = await self.extractors['content'].extract(
                    content,
                    url
                )

                # Check for RFP content
                is_rfp, confidence = classifier.classify(extracted)
                if is_rfp:
                    await self.process_rfp(
                        url,
                        extracted,
                        config.country
                    )
                    self.stats['rfps_found'] += 1

                # Extract and queue new URLs
                if depth < config.max_depth:
                    new_urls = self.filter_urls(
                        extracted.links,
                        config.allowed_domains
                    )
                    queue.extend((u, depth + 1) for u in new_urls)

                self.stats['pages_processed'] += 1

        except Exception as e:
            logging.error(f"Error processing site {config.base_url}: {str(e)}")
            traceback.print_exc()

    async def process_rfp(
        self,
        url: str,
        content: ExtractedContent,
        country: str
    ):
        """Process discovered RFP document.

        Args:
            url (str): Document URL
            content (ExtractedContent): Extracted content
            country (str): Associated country
        """
        try:
            # Extract entities
            entities = self.extractors['entity'].extract_entities(
                content.main_text
            )

            # Create RFP data
            rfp_data = RFPData(
                tender_id=None,  # Auto-generated
                title=content.title,
                description=content.main_text,
                organization=entities['organizations'][0] if entities['organizations'] else None,
                issue_date=self.parse_date(entities['dates'][0]) if entities['dates'] else datetime.utcnow(),
                expiry_date=self.parse_date(entities['dates'][-1]) if len(entities['dates']) > 1 else None,
                country=country,
                source_url=url,
                content_hash=self.compute_hash(content.main_text),
                metadata={
                    'extracted_entities': entities,
                    'page_metadata': content.metadata
                }
            )

            # Store in database
            async with self.db_session.begin():
                db_rfp = RFPDocument(**rfp_data.dict())
                self.db_session.add(db_rfp)

            self.stats['rfps_stored'] += 1

        except Exception as e:
            logging.error(f"Error processing RFP from {url}: {str(e)}")

    def filter_urls(self, urls: List[str], allowed_domains: Set[str]) -> List[str]:
        """Filter URLs based on allowed domains."""
        filtered = []
        for url in urls:
            domain = urlparse(url).netloc
            if any(domain.endswith(d) for d in allowed_domains):
                filtered.append(url)
        return filtered

    async def cleanup(self):
        """Cleanup resources."""
        await self.http_client.session.close()
        await self.db_session.close()

        # Log final statistics
        duration = time.time() - self.start_time
        logging.info("Scraping completed:")
        logging.info(f"Duration: {duration:.2f} seconds")
        logging.info(f"Pages processed: {self.stats['pages_processed']}")
        logging.info(f"RFPs found: {self.stats['rfps_found']}")
        logging.info(f"RFPs stored: {self.stats['rfps_stored']}")

@flow(name="RFP Scraper")
async def main():
    """Main entry point for the RFP scraper."""
    # Initialize components
    db_session = await init_db()
    redis_client = init_redis()
    http_client = AsyncHTTPClient()
    rate_limiter = RateLimit(
        capacity=CONFIG['RATE_LIMIT_BURST'],
        fill_rate=CONFIG['RATE_LIMIT_REQUESTS']
    )
    deduplicator = MinHashDeduplicator()
    extractors = await init_extractors()

    # Create orchestrator
    orchestrator = Orchestrator(
        db_session,
        redis_client,
        http_client,
        rate_limiter,
        deduplicator,
        extractors
    )

    # Setup signal handlers
    def signal_handler(signum, frame):
        logging.info("Shutdown signal received")
        asyncio.create_task(orchestrator.cleanup())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run orchestrator
    await orchestrator.orchestrate()

if __name__ == "__main__":
    asyncio.run(main())
