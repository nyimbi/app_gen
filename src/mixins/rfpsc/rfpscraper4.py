import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import math
import random
import hashlib
import json
import logging
import io

# Document processing
import PyPDF2

# Data normalization
from pydantic import BaseModel, ValidationError, Field

# Deduplication via TF-IDF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# SQLAlchemy for persistence
from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL parsing and queuing
from urllib.parse import urljoin, urlparse
from collections import deque

# Prefect integration for workflow management
from prefect import flow, task, get_run_logger
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------------------- Configuration -----------------------------
DATABASE_URL = "postgresql://user:password@localhost/rfp_database"  # Replace with real credentials
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36'
REQUEST_DELAY = 2  # seconds delay between requests
MAX_RETRIES = 3
BASE_BACKOFF = 2  # base backoff time (seconds)
OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Ollama API endpoint
DUPLICATE_SIM_THRESHOLD = 0.9  # Cosine similarity threshold for near duplicates

# Global logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# ----------------------------- SQLAlchemy Setup -----------------------------
Base = declarative_base()

class RFP(Base):
    __tablename__ = 'rfps'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text)
    organization = Column(String)
    issue_date = Column(Date)
    expiry_date = Column(Date)
    security_bond_required = Column(Boolean)
    country = Column(String)
    location = Column(String)
    activity = Column(String)
    source_url = Column(String, unique=True)
    content_hash = Column(String, unique=True)
    is_worth_pursuing = Column(Boolean)
    documents = Column(Text)  # JSON encoded list of document URLs and text
    metadata = Column(Text)   # JSON encoded meta information

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# ----------------------------- Pydantic Model for Data Validation -----------------------------
class TenderModel(BaseModel):
    title: str
    description: str
    organization: str
    issue_date: datetime
    expiry_date: datetime
    security_bond_required: bool
    country: str
    location: str
    activity: str
    source_url: str
    content_hash: str
    is_worth_pursuing: bool
    documents: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

# ----------------------------- Deduplication Utilities -----------------------------
def get_all_rfp_texts():
    """
    Retrieve all tender descriptions from the database for deduplication comparison.
    """
    session = Session()
    try:
        records = session.query(RFP.description).all()
        texts = [record[0] for record in records if record[0]]
        return texts
    except Exception as e:
        logging.error(f"Error retrieving RFP texts: {str(e)}")
        return []
    finally:
        session.close()

def is_similar_duplicate(new_text, threshold=DUPLICATE_SIM_THRESHOLD):
    """
    Uses TF-IDF vectorization and cosine similarity to check if the new_text is near-duplicate
    of any existing tender description.
    """
    existing_texts = get_all_rfp_texts()
    if not existing_texts:
        return False
    vectorizer = TfidfVectorizer().fit(existing_texts + [new_text])
    vectors = vectorizer.transform(existing_texts + [new_text])
    cosine_sim = cosine_similarity(vectors[-1], vectors[:-1])
    if cosine_sim.max() > threshold:
        return True
    return False

# ----------------------------- Exponential Backoff for Requests -----------------------------
def fetch_with_retries(url, headers, max_retries=MAX_RETRIES):
    """
    Fetch a URL with retries using exponential backoff with jitter.
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response
            else:
                logging.error(f"HTTP error {response.status_code} for {url}")
        except Exception as e:
            logging.error(f"Request error for {url}: {str(e)}")
        delay = BASE_BACKOFF * (2 ** attempt) + random.uniform(0, 1)
        time.sleep(delay)
    return None

# ----------------------------- Downloadable Document Processing -----------------------------
def download_document(doc_url):
    """
    Downloads a document from a given URL.
    Returns the content bytes if successful.
    """
    headers = {'User-Agent': USER_AGENT}
    response = fetch_with_retries(doc_url, headers)
    if response:
        return response.content
    return None

def parse_pdf_document(doc_url):
    """
    Download and extract text from a PDF document.
    """
    content = download_document(doc_url)
    if not content:
        return ""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        logging.error(f"Error parsing PDF {doc_url}: {str(e)}")
        return ""

# ----------------------------- Metadata Harvesting -----------------------------
def extract_meta_data(content):
    """
    Extracts metadata from HTML using BeautifulSoup.
    Returns a dictionary with keys like published_time, keywords, etc.
    """
    meta_data = {}
    soup = BeautifulSoup(content, 'html.parser')
    for meta in soup.find_all("meta"):
        if meta.get("name"):
            meta_data[meta["name"]] = meta.get("content", "")
        elif meta.get("property"):
            meta_data[meta["property"]] = meta.get("content", "")
    return meta_data

# ----------------------------- LLM-Driven Inference with Expanded Page Types -----------------------------
def infer_page_structure(content, context):
    """
    Uses an LLM (via Ollama API) to infer the page structure.
    Expected JSON output includes:
      - "page_type": one of "list", "tender", "api", "landing", "search", "category",
        "document_repository", "announcement", "archived", "calendar", "guidelines",
        "api_documentation", "login", "redirect", "error", "multimedia", "comparison", "profile"
      - If the page is a navigational or aggregation page (e.g., list, landing, search, category,
        document_repository, announcement, archived, calendar, guidelines, api_documentation,
        multimedia, comparison, profile), then it should include "tender_links" (a list of URLs)
      - If the page is a tender (or announcement) page, it should include "tender_details": an object
         containing: title, description, organization, issue_date (YYYY-MM-DD), expiry_date (YYYY-MM-DD),
         security_bond_required (boolean), location, activity, and optionally "documents" (list of URLs)
      - If the page is an API reference, include "api_endpoint": URL.
    """
    prompt = f"""
Analyze the following page content with context {context} and determine its structure.
Output a JSON object with:
- "page_type": one of ["list", "tender", "api", "landing", "search", "category", "document_repository", "announcement", "archived", "calendar", "guidelines", "api_documentation", "login", "redirect", "error", "multimedia", "comparison", "profile"].
- If "page_type" is one of ["list", "landing", "search", "category", "document_repository", "announcement", "archived", "calendar", "guidelines", "api_documentation", "multimedia", "comparison", "profile"], include "tender_links": a list of URLs for additional navigation.
- If "page_type" is "tender" or "announcement", include "tender_details": an object with keys: title, description, organization, issue_date (YYYY-MM-DD), expiry_date (YYYY-MM-DD), security_bond_required (boolean), location, activity, and optionally "documents" (list of URLs).
- If "page_type" is "api", include "api_endpoint": URL.
Page Content:
{content}
    """
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "qwen2.5",
                "prompt": prompt,
                "format": "json",
                "stream": False
            },
            timeout=30
        )
        if response.status_code == 200:
            llm_output = response.json()['response'].strip()
            return json.loads(llm_output)
        else:
            logging.error(f"Ollama API error: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error in infer_page_structure: {str(e)}")
    return None

# ----------------------------- Fallback Link Extraction -----------------------------
def extract_links_bs4(content, base_url):
    """
    Uses BeautifulSoup to extract all anchor tag hrefs from a page.
    """
    soup = BeautifulSoup(content, 'html.parser')
    links = []
    for a in soup.find_all("a", href=True):
        href = a['href']
        full_url = urljoin(base_url, href)
        links.append(full_url)
    return links

# ----------------------------- Data Storage -----------------------------
def store_rfp(data):
    """
    Validates tender data using Pydantic and stores it in the database.
    Also logs a sample record for human review.
    """
    try:
        tender = TenderModel(**data)
    except ValidationError as ve:
        logging.error(f"Data validation error: {ve}")
        return

    session = Session()
    try:
        rfp = RFP(
            title=tender.title,
            description=tender.description,
            organization=tender.organization,
            issue_date=tender.issue_date.date(),
            expiry_date=tender.expiry_date.date(),
            security_bond_required=tender.security_bond_required,
            country=tender.country,
            location=tender.location,
            activity=tender.activity,
            source_url=tender.source_url,
            content_hash=tender.content_hash,
            is_worth_pursuing=tender.is_worth_pursuing,
            documents=json.dumps(tender.documents),
            metadata=json.dumps(tender.metadata)
        )
        session.add(rfp)
        session.commit()
        logging.info(f"Stored RFP from {tender.source_url}")
    except Exception as e:
        session.rollback()
        logging.error(f"Error storing RFP: {str(e)}")
    finally:
        session.close()

# ----------------------------- Tender Evaluation -----------------------------
def evaluate_tender(tender_data):
    """
    Evaluates if the tender is worth pursuing.
    Checks expiry date and target location/activity.
    """
    try:
        expiry = tender_data.get('expiry_date')
        if isinstance(expiry, str):
            expiry = datetime.strptime(expiry, "%Y-%m-%d").date()
        if expiry < datetime.now().date():
            return False
    except Exception as e:
        logging.warning(f"Error parsing expiry date: {str(e)}")
        return False

    if tender_data.get('location') not in ["Target Location A", "Target Location B"]:
        return False
    if tender_data.get('activity') not in ["Software Development", "IT Consulting"]:
        return False
    return True

# ----------------------------- Prefect Tasks and Flows -----------------------------
@task
def process_page(url, country, allow_external=False):
    """
    Processes a single page: fetches the URL, infers page structure,
    extracts metadata, downloads documents if any, and returns a tuple:
    (inference, content_hash, metadata, content).
    """
    logger = get_run_logger()
    headers = {'User-Agent': USER_AGENT}
    response = fetch_with_retries(url, headers)
    if not response:
        logger.error(f"Failed to fetch {url}")
        return None

    content = response.text
    meta = extract_meta_data(content)
    exists, content_hash = check_existing(url, content)
    if exists or is_similar_duplicate(content):
        logger.info(f"Duplicate found for {url}")
        return None

    context = {"url": url, "country": country}
    inference = infer_page_structure(content, context)
    if inference is None:
        # Fallback: extract all links using BS4
        links = extract_links_bs4(content, url)
        inference = {"page_type": "list", "tender_links": links}
    return inference, content_hash, meta, content

@task
def process_inference(url, inference, content_hash, meta, country, domain, allow_external=False):
    """
    Based on the inference result and the expanded page types,
    process the page accordingly:
      - For navigational pages (e.g. list, landing, search, category,
        document_repository, multimedia, comparison, profile, redirect, error, login):
          extract and enqueue tender links.
      - For tender-type pages (tender, announcement, archived), extract details.
      - For API pages, query the endpoint.
    """
    logger = get_run_logger()
    page_type = inference.get("page_type")
    headers = {'User-Agent': USER_AGENT}

    # Define page types that are treated as navigational/aggregation:
    navigational_types = ["list", "landing", "search", "category", "document_repository",
                           "multimedia", "comparison", "profile", "redirect", "error", "login"]
    # Types that may still yield tender details:
    tender_like = ["tender", "announcement", "archived", "calendar", "guidelines", "api_documentation"]

    if page_type in navigational_types:
        tender_links = inference.get("tender_links", [])
        if not tender_links:
            tender_links = extract_links_bs4(inference.get("content", ""), url)
        logger.info(f"Enqueueing {len(tender_links)} links from navigational page {url}")
        return {"enqueue": tender_links}

    elif page_type in tender_like:
        tender_data = inference.get("tender_details", {})
        if not tender_data:
            logger.warning(f"No tender details found for {url} in page type {page_type}")
            # Fall back to link extraction from BS4
            links = extract_links_bs4(inference.get("content", ""), url)
            return {"enqueue": links}
        tender_data['source_url'] = url
        tender_data['content_hash'] = content_hash
        tender_data['documents'] = tender_data.get('documents', [])
        tender_data['metadata'] = meta
        tender_data['country'] = country
        tender_data['is_worth_pursuing'] = evaluate_tender(tender_data)

        # Process downloadable documents (e.g., PDFs)
        processed_docs = []
        for doc_url in tender_data.get('documents', []):
            if doc_url.lower().endswith('.pdf'):
                doc_text = parse_pdf_document(doc_url)
                processed_docs.append({"url": doc_url, "extracted_text": doc_text})
            else:
                processed_docs.append({"url": doc_url})
        tender_data['documents'] = processed_docs

        if not is_similar_duplicate(tender_data.get("description", "")):
            store_rfp(tender_data)
        return None

    elif page_type == "api":
        api_url = inference.get("api_endpoint")
        if api_url:
            api_response = fetch_with_retries(api_url, headers)
            if api_response and api_response.status_code == 200:
                api_inference = infer_page_structure(api_response.text, {"url": api_url, "country": country})
                if api_inference and api_inference.get("page_type") in tender_like:
                    tender_data = api_inference.get("tender_details", {})
                    if tender_data:
                        tender_data['source_url'] = api_url
                        tender_data['content_hash'] = hashlib.sha256(api_response.text.encode()).hexdigest()
                        tender_data['documents'] = tender_data.get("documents", [])
                        tender_data['metadata'] = extract_meta_data(api_response.text)
                        tender_data['country'] = country
                        tender_data['is_worth_pursuing'] = evaluate_tender(tender_data)
                        store_rfp(tender_data)
        return None

@task
def scrape_site(config):
    """
    Scrapes a site using a breadth-first search (BFS) driven by LLM inference and BS4 fallback.
    Enqueues new links and processes them until the queue is exhausted.
    """
    logger = get_run_logger()
    country = config["country"]
    base_url = config["base_url"]
    allow_external = config.get("allow_external", False)
    domain = urlparse(base_url).netloc

    visited = set()
    queue = deque([base_url])

    while queue:
        current_url = queue.popleft()
        if current_url in visited:
            continue
        visited.add(current_url)
        logger.info(f"Processing {current_url}")

        result = process_page(current_url, country, allow_external=allow_external)
        if not result:
            continue

        inference, content_hash, meta, content = result
        outcome = process_inference(current_url, inference, content_hash, meta, country, domain, allow_external=allow_external)
        if outcome and isinstance(outcome, dict) and outcome.get("enqueue"):
            for link in outcome["enqueue"]:
                if urlparse(link).netloc == domain or allow_external:
                    queue.append(link)
        time.sleep(REQUEST_DELAY)

@flow(name="RFP Scraper Workflow")
def main_flow():
    """
    Main Prefect flow that loads target sites and concurrently executes the scraping workflow.
    """
    logger = get_run_logger()
    targets = [
        {"base_url": "https://example-tenders-website.com/tenders", "country": "Country A", "allow_external": False},
        {"base_url": "https://procurement.worldbank.org", "country": "International", "allow_external": True},
        # Additional targets can be added dynamically.
    ]
    with ThreadPoolExecutor(max_workers=len(targets)) as executor:
        futures = [executor.submit(scrape_site, config) for config in targets]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error in concurrent execution: {str(e)}")
    logger.info("Scraping completed. Please review sample records from the database for quality assurance.")

if __name__ == "__main__":
    main_flow()
