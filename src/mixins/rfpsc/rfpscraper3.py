import requests
from bs4 import BeautifulSoup  # (for fallback parsing, if needed)
from datetime import datetime
import time
import hashlib
import json
import logging
from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import urljoin, urlparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------------------- Configuration -----------------------------
DATABASE_URL = "postgresql://user:password@localhost/rfp_database"  # Replace with your PostgreSQL credentials
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
REQUEST_DELAY = 2  # Seconds between requests
MAX_RETRIES = 3
OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Ollama API endpoint

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
    documents = Column(Text)  # JSON-encoded list of downloadable document URLs

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# ----------------------------- Utility Functions -----------------------------
def check_existing(source_url, content):
    """
    Check whether the content or URL already exists in the database.
    Uses SHA256 for content hashing.
    """
    session = Session()
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    exists = session.query(RFP).filter(
        (RFP.source_url == source_url) | (RFP.content_hash == content_hash)
    ).first()
    session.close()
    return exists is not None, content_hash

def store_rfp(data):
    """
    Stores a new RFP record in the database.
    The 'documents' field is stored as a JSON string.
    """
    session = Session()
    try:
        rfp = RFP(
            title=data.get('title'),
            description=data.get('description'),
            organization=data.get('organization'),
            issue_date=data.get('issue_date'),
            expiry_date=data.get('expiry_date'),
            security_bond_required=data.get('security_bond_required'),
            country=data.get('country'),
            location=data.get('location'),
            activity=data.get('activity'),
            source_url=data.get('source_url'),
            content_hash=data.get('content_hash'),
            is_worth_pursuing=data.get('is_worth_pursuing'),
            documents=json.dumps(data.get('documents', []))
        )
        session.add(rfp)
        session.commit()
        logging.info(f"Stored RFP from {data.get('source_url')}")
    except Exception as e:
        session.rollback()
        logging.error(f"Error storing RFP: {str(e)}")
    finally:
        session.close()

def evaluate_tender(tender_data):
    """
    Evaluates if the tender is worth pursuing based on target criteria.
    Extend the logic as needed.
    """
    try:
        expiry = tender_data.get('expiry_date')
        if isinstance(expiry, str):
            expiry = datetime.strptime(expiry, "%Y-%m-%d").date()
        if expiry < datetime.now().date():
            return False  # Expired tender
    except Exception as e:
        logging.warning(f"Error parsing expiry date: {str(e)}")
        return False
    
    # Additional evaluation criteria
    if tender_data.get('location') not in ["Target Location A", "Target Location B"]:
        return False
    if tender_data.get('activity') not in ["Software Development", "IT Consulting"]:
        return False
    return True

def infer_page_structure(content, context):
    """
    Uses an LLM (via the Ollama API) to infer the structure of a page.
    The LLM is asked to determine whether the page is:
      - A list of tenders (with a key 'tender_links')
      - A single tender page (with a key 'tender_details')
      - Contains downloadable documents (within 'tender_details' under 'documents')
      - An API reference (with an 'api_endpoint')
    The function returns a JSON structure that directs further processing.
    
    The expected output from the LLM is a JSON object similar to:
    {
       "page_type": "list" | "tender" | "api",
       "tender_links": [...],           # if page_type is "list"
       "tender_details": { ... },         # if page_type is "tender"
       "api_endpoint": "https://...",     # if page_type is "api"
       "documents": [...]                 # optional list of document URLs
    }
    """
    prompt = f"""
Analyze the following page content with context {context} and determine its structure.
Please output a JSON object with the following keys:
- "page_type": a string that is either "list", "tender", or "api".
- If "page_type" is "list", include "tender_links": a list of URLs for individual tender pages.
- If "page_type" is "tender", include "tender_details": an object containing:
    - title (string)
    - description (string)
    - organization (string)
    - issue_date (YYYY-MM-DD)
    - expiry_date (YYYY-MM-DD)
    - security_bond_required (boolean)
    - location (string)
    - activity (string)
    - documents: a list of URLs for downloadable documents (if any)
- If "page_type" is "api", include "api_endpoint": the URL of the API endpoint.
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
            return None
    except Exception as e:
        logging.error(f"Error in infer_page_structure: {str(e)}")
        return None

# ----------------------------- Core Scraping Function -----------------------------
def scrape_site(config):
    """
    Scrapes a tender website given its configuration.
    The scraper uses an LLM-driven approach to decide how to process each page.
    It implements a breadth-first search (BFS) to traverse links discovered in list pages.
    """
    visited = set()
    queue = deque([config["base_url"]])
    domain = urlparse(config["base_url"]).netloc

    while queue:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        logging.info(f"Scraping {url}")

        for attempt in range(MAX_RETRIES):
            try:
                headers = {'User-Agent': USER_AGENT}
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code != 200:
                    logging.error(f"Error fetching {url}: {response.status_code}")
                    break

                content = response.text
                exists, content_hash = check_existing(url, content)
                if exists:
                    logging.info(f"Already processed {url}")
                    break

                # Use LLM to infer the page structure and decide the parsing strategy.
                context = {"url": url, "country": config["country"]}
                inference = infer_page_structure(content, context)
                if not inference:
                    logging.warning(f"LLM inference failed for {url}")
                    break

                page_type = inference.get("page_type")
                if page_type == "list":
                    # Enqueue discovered tender links.
                    links = inference.get("tender_links", [])
                    for link in links:
                        full_url = urljoin(url, link)
                        if urlparse(full_url).netloc == domain or config.get("allow_external", False):
                            queue.append(full_url)
                    logging.info(f"Enqueued {len(links)} tender links from list page {url}")

                elif page_type == "tender":
                    tender_data = inference.get("tender_details", {})
                    if not tender_data:
                        logging.warning(f"No tender_details found in inference for {url}")
                        break
                    tender_data['source_url'] = url
                    tender_data['content_hash'] = content_hash
                    # Optional: documents may be provided in tender_details; default to empty list.
                    tender_data['documents'] = tender_data.get('documents', [])
                    tender_data['country'] = config["country"]
                    tender_data['is_worth_pursuing'] = evaluate_tender(tender_data)
                    store_rfp(tender_data)

                    # Also check if the page contains links to additional tenders
                    extra_links = inference.get("tender_links", [])
                    for link in extra_links:
                        full_url = urljoin(url, link)
                        if urlparse(full_url).netloc == domain or config.get("allow_external", False):
                            queue.append(full_url)

                elif page_type == "api":
                    # If the page is an API reference, call the API endpoint.
                    api_url = inference.get("api_endpoint")
                    if api_url:
                        api_response = requests.get(api_url, headers=headers, timeout=30)
                        if api_response.status_code == 200:
                            api_inference = infer_page_structure(api_response.text, {"url": api_url, "country": config["country"]})
                            if api_inference and api_inference.get("page_type") == "tender":
                                tender_data = api_inference.get("tender_details", {})
                                if tender_data:
                                    tender_data['source_url'] = api_url
                                    tender_data['content_hash'] = hashlib.sha256(api_response.text.encode()).hexdigest()
                                    tender_data['documents'] = tender_data.get("documents", [])
                                    tender_data['country'] = config["country"]
                                    tender_data['is_worth_pursuing'] = evaluate_tender(tender_data)
                                    store_rfp(tender_data)
                break  # Processing for the current URL successful; break retry loop.
            except Exception as e:
                logging.error(f"Error scraping {url} (attempt {attempt+1}): {str(e)}")
                time.sleep(REQUEST_DELAY)
        time.sleep(REQUEST_DELAY)

# ----------------------------- Site Configuration Registry -----------------------------
def load_targets():
    """
    Loads target websites for scraping. The list can be extended dynamically.
    Each entry is a dict with at least 'base_url' and 'country'.
    """
    return [
        {"base_url": "https://example-tenders-website.com/tenders", "country": "Country A"},
        # Additional targets can be added dynamically, e.g.:
        {"base_url": "https://procurement.worldbank.org", "country": "International"},
        # Governments, UNDP, WHO, UN, etc.
    ]

# ----------------------------- Main Execution with Concurrency -----------------------------
def main():
    """
    Main execution function that concurrently scrapes multiple target sites.
    """
    targets = load_targets()
    futures = []
    with ThreadPoolExecutor(max_workers=len(targets)) as executor:
        for config in targets:
            futures.append(executor.submit(scrape_site, config))
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Error in concurrent execution: {str(e)}")

if __name__ == "__main__":
    main()
