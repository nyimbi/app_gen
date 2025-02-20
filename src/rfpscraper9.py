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

# Document processing libraries
import PyPDF2
import pytesseract  # for OCR on images (requires Tesseract installed)
from PIL import Image

# Data normalization and validation
from pydantic import BaseModel, ValidationError, Field
from typing import Optional, List

# Deduplication via TF-IDF (and placeholder for graph clustering)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# SQLAlchemy for persistence
from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL parsing and BFS queue
from urllib.parse import urljoin, urlparse
from collections import deque

# Prefect for workflow orchestration
from prefect import flow, task, get_run_logger
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------------------- CONFIGURATION -----------------------------
DATABASE_URL = "postgresql://user:password@localhost/rfp_database"  # update credentials
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36'
REQUEST_DELAY = 2            # delay between requests
MAX_RETRIES = 3
BASE_BACKOFF = 2             # seconds
OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Ollama endpoint
DUPLICATE_SIM_THRESHOLD = 0.9

# SerpApi configuration for discovery
SERPAPI_KEY = "YOUR_SERPAPI_KEY"  # update your key
SERPAPI_ENDPOINT = "https://serpapi.com/search"

# Model configuration: map task names to open-weight LLM model names (when available via Ollama)
LLM_MODELS = {
    "extraction": "llama-2-7b-chat",      # For detailed extraction tasks.
    "optimization": "falcon-7b-instruct",   # For prompt refinement.
    "quality_scoring": "mpt-7b-chat"        # For quality evaluation (if needed).
}

# Global logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# ----------------------------- SQLAlchemy SETUP -----------------------------
Base = declarative_base()

class RFP(Base):
    __tablename__ = 'rfps'
    id = Column(Integer, primary_key=True)
    tender_id = Column(String, unique=True, nullable=True)
    title = Column(String)
    description = Column(Text)
    scope = Column(Text, nullable=True)
    organization = Column(String)
    contact_info = Column(Text, nullable=True)
    eligibility_criteria = Column(Text, nullable=True)
    procurement_method = Column(String, nullable=True)
    submission_instructions = Column(Text, nullable=True)
    issue_date = Column(Date)
    prebid_date = Column(Date, nullable=True)
    evaluation_date = Column(Date, nullable=True)
    award_date = Column(Date, nullable=True)
    contract_commencement_date = Column(Date, nullable=True)
    contract_duration = Column(String, nullable=True)
    expiry_date = Column(Date)
    estimated_contract_value = Column(Float, nullable=True)
    legal_details = Column(Text, nullable=True)
    sector = Column(String, nullable=True)
    subnational_location = Column(String, nullable=True)
    donor_info = Column(Text, nullable=True)
    funding_program = Column(String, nullable=True)
    strategic_context = Column(Text, nullable=True)
    application_process = Column(Text, nullable=True)
    security_bond_required = Column(Boolean)
    country = Column(String)
    location = Column(String)
    activity = Column(String)
    source_url = Column(String, unique=True)
    content_hash = Column(String, unique=True)
    is_worth_pursuing = Column(Boolean)
    documents = Column(Text)  # JSON encoded list
    metadata = Column(Text)   # JSON encoded meta info

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# ----------------------------- Pydantic MODEL -----------------------------
class TenderModel(BaseModel):
    tender_id: Optional[str] = None
    title: str
    description: str
    scope: Optional[str] = None
    organization: str
    contact_info: Optional[str] = None
    eligibility_criteria: Optional[str] = None
    procurement_method: Optional[str] = None
    submission_instructions: Optional[str] = None
    issue_date: datetime
    prebid_date: Optional[datetime] = None
    evaluation_date: Optional[datetime] = None
    award_date: Optional[datetime] = None
    contract_commencement_date: Optional[datetime] = None
    contract_duration: Optional[str] = None
    expiry_date: datetime
    estimated_contract_value: Optional[float] = None
    legal_details: Optional[str] = None
    sector: Optional[str] = None
    subnational_location: Optional[str] = None
    donor_info: Optional[str] = None
    funding_program: Optional[str] = None
    strategic_context: Optional[str] = None
    application_process: Optional[str] = None
    security_bond_required: bool
    country: str
    location: str
    activity: str
    source_url: str
    content_hash: str
    is_worth_pursuing: bool
    documents: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

# ----------------------------- DEDUPLICATION UTILITIES -----------------------------
def get_all_rfp_texts():
    session = Session()
    try:
        records = session.query(RFP.description).all()
        texts = [record[0] for record in records if record[0]]
        return texts
    except Exception as e:
        logging.error(f"Error retrieving texts: {str(e)}")
        return []
    finally:
        session.close()

def is_similar_duplicate(new_text, threshold=DUPLICATE_SIM_THRESHOLD):
    existing_texts = get_all_rfp_texts()
    if not existing_texts:
        return False
    vectorizer = TfidfVectorizer().fit(existing_texts + [new_text])
    vectors = vectorizer.transform(existing_texts + [new_text])
    cosine_sim = cosine_similarity(vectors[-1], vectors[:-1])
    return cosine_sim.max() > threshold

# (Placeholder) Additional graph–based clustering could be added here using networkx.

# ----------------------------- EXPONENTIAL BACKOFF -----------------------------
def fetch_with_retries(url, headers, max_retries=MAX_RETRIES):
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

# ----------------------------- DOCUMENT PROCESSING -----------------------------
def download_document(doc_url):
    headers = {'User-Agent': USER_AGENT}
    response = fetch_with_retries(doc_url, headers)
    if response:
        return response.content
    return None

def parse_pdf_document(doc_url):
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

def ocr_image(image_path: str) -> str:
    """
    Runs OCR on an image file using pytesseract.
    """
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        logging.error(f"OCR error for image {image_path}: {str(e)}")
        return ""

# ----------------------------- METADATA HARVESTING -----------------------------
def extract_meta_data(content: str) -> dict:
    meta_data = {}
    soup = BeautifulSoup(content, 'html.parser')
    for meta in soup.find_all("meta"):
        if meta.get("name"):
            meta_data[meta["name"]] = meta.get("content", "")
        elif meta.get("property"):
            meta_data[meta["property"]] = meta.get("content", "")
    return meta_data

# ----------------------------- LLM CALL & ITERATIVE PROMPT OPTIMIZATION -----------------------------
def call_llm(prompt: str, model: str = LLM_MODELS["extraction"]) -> Optional[str]:
    """
    Calls the LLM using the specified model via Ollama.
    """
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": model,
                "prompt": prompt,
                "format": "json",
                "stream": False
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['response'].strip()
        else:
            logging.error(f"Ollama API error: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error calling LLM: {str(e)}")
    return None

def is_valid_json(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except Exception:
        return False

def meets_quality(response_text: str, prompt: str) -> bool:
    """
    Heuristically checks if the JSON response contains required keys.
    """
    try:
        resp = json.loads(response_text)
        if "page_type" not in resp:
            return False
        # For tender-like pages, require "tender_details".
        if resp["page_type"] in ["tender", "announcement", "archived", "calendar", "guidelines", "api_documentation"]:
            if "tender_details" not in resp:
                return False
        return True
    except Exception:
        return False

def optimize_prompt(original_prompt: str, response_text: str) -> str:
    """
    Asks the LLM to compare the original prompt and its response,
    then return an improved version of the prompt.
    """
    optimization_prompt = f"""
You are an expert in prompt engineering. Compare the following prompt and response.
Original Prompt:
{original_prompt}

Response:
{response_text}

Identify discrepancies or missing information and provide a revised version of the prompt that better extracts the required data.
Return only the revised prompt.
    """
    optimized = call_llm(optimization_prompt, model=LLM_MODELS["optimization"])
    return optimized if optimized else original_prompt

def iterative_infer_page_structure(content: str, context: dict, max_iterations: int = 2) -> dict:
    """
    Iteratively obtains a classification (and if tender-like, detailed fields) from the LLM.
    """
    # Step 1: Get classification.
    classification_prompt = f"""
Based on the following page content, determine the page type from this list:
["list", "tender", "api", "landing", "search", "category", "document_repository",
 "announcement", "archived", "calendar", "guidelines", "api_documentation", "login", "redirect", "error",
 "multimedia", "comparison", "profile"].
Return your answer in JSON format, e.g.:
{{"page_type": "tender", "tender_links": []}}
Page Content:
{content}
Context: {context}
    """
    iteration = 0
    classification_response_text = call_llm(classification_prompt, model=LLM_MODELS["extraction"])
    while iteration < max_iterations and (not is_valid_json(classification_response_text) or not meets_quality(classification_response_text, classification_prompt)):
         classification_prompt = optimize_prompt(classification_prompt, classification_response_text)
         classification_response_text = call_llm(classification_prompt, model=LLM_MODELS["extraction"])
         iteration += 1
    try:
         classification_response = json.loads(classification_response_text)
    except Exception as e:
         logging.error(f"Failed to parse classification response: {str(e)}")
         classification_response = {}
    # Step 2: For tender-like pages, get details.
    tender_like_types = ["tender", "announcement", "archived", "calendar", "guidelines", "api_documentation"]
    if classification_response.get("page_type") in tender_like_types:
         details_prompt = f"""
Extract detailed tender information from the page content.
Return a JSON object with the following fields:
tender_id, title, description, scope, organization, contact_info, eligibility_criteria,
procurement_method, submission_instructions, issue_date (YYYY-MM-DD), prebid_date (YYYY-MM-DD, optional),
evaluation_date (YYYY-MM-DD, optional), award_date (YYYY-MM-DD, optional), contract_commencement_date (YYYY-MM-DD, optional),
contract_duration, expiry_date (YYYY-MM-DD), estimated_contract_value, legal_details,
sector, subnational_location, donor_info, funding_program, strategic_context, application_process,
security_bond_required (boolean), location, activity, and optionally "documents" (list of URLs).
Page Content:
{content}
Context: {context}
         """
         iteration = 0
         details_response_text = call_llm(details_prompt, model=LLM_MODELS["extraction"])
         while iteration < max_iterations and (not is_valid_json(details_response_text)):
              details_prompt = optimize_prompt(details_prompt, details_response_text)
              details_response_text = call_llm(details_prompt, model=LLM_MODELS["extraction"])
              iteration += 1
         try:
              details_response = json.loads(details_response_text)
         except Exception as e:
              logging.error(f"Failed to parse details response: {str(e)}")
              details_response = {}
         classification_response["tender_details"] = details_response
    return classification_response

# ----------------------------- FALLBACK LINK EXTRACTION -----------------------------
def extract_links_bs4(content: str, base_url: str) -> list:
    soup = BeautifulSoup(content, 'html.parser')
    links = []
    for a in soup.find_all("a", href=True):
        full_url = urljoin(base_url, a['href'])
        links.append(full_url)
    return links

# ----------------------------- DATA STORAGE -----------------------------
def store_rfp(data: dict):
    try:
        tender = TenderModel(**data)
    except ValidationError as ve:
        logging.error(f"Data validation error: {ve}")
        return
    session = Session()
    try:
        rfp = RFP(
            tender_id=tender.tender_id,
            title=tender.title,
            description=tender.description,
            scope=tender.scope,
            organization=tender.organization,
            contact_info=tender.contact_info,
            eligibility_criteria=tender.eligibility_criteria,
            procurement_method=tender.procurement_method,
            submission_instructions=tender.submission_instructions,
            issue_date=tender.issue_date.date(),
            prebid_date=tender.prebid_date.date() if tender.prebid_date else None,
            evaluation_date=tender.evaluation_date.date() if tender.evaluation_date else None,
            award_date=tender.award_date.date() if tender.award_date else None,
            contract_commencement_date=tender.contract_commencement_date.date() if tender.contract_commencement_date else None,
            contract_duration=tender.contract_duration,
            expiry_date=tender.expiry_date.date(),
            estimated_contract_value=tender.estimated_contract_value,
            legal_details=tender.legal_details,
            sector=tender.sector,
            subnational_location=tender.subnational_location,
            donor_info=tender.donor_info,
            funding_program=tender.funding_program,
            strategic_context=tender.strategic_context,
            application_process=tender.application_process,
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

# ----------------------------- TENDER EVALUATION -----------------------------
def evaluate_tender(tender_data: dict) -> bool:
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

# ----------------------------- DISCOVERY OF TARGET SITES -----------------------------
def discover_target_sites() -> list:
    african_countries = [
        "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cabo Verde",
        "Cameroon", "Central African Republic", "Chad", "Comoros", "Congo", "DR Congo",
        "Côte d'Ivoire", "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini",
        "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Kenya", "Lesotho",
        "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius",
        "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda", "Sao Tome and Principe",
        "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Africa", "South Sudan",
        "Sudan", "Tanzania", "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe"
    ]
    administrative_levels = ["ministry", "state", "county", "municipality", "city"]
    tender_keywords = [
        "tender site", "procurement portal", "government tender", "ministry tender", "RFP", "bid opportunity"
    ]
    international_keywords = [
        "World Bank tender", "UN tender", "UNDP procurement", "WHO tender", "INGO procurement", "NGO tender"
    ]
    discovered_sites = {}
    for country in african_countries:
        for admin in administrative_levels:
            for keyword in tender_keywords:
                query = f"{country} {admin} {keyword}"
                params = {
                    "api_key": SERPAPI_KEY,
                    "engine": "google",
                    "q": query,
                    "google_domain": "google.com",
                    "hl": "en"
                }
                try:
                    response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=30)
                    if response.status_code == 200:
                        results = response.json().get("organic_results", [])
                        for result in results:
                            link = result.get("link")
                            if link:
                                domain = urlparse(link).netloc
                                if domain not in discovered_sites:
                                    discovered_sites[domain] = link
                    else:
                        logging.error(f"Search query '{query}' failed with status {response.status_code}")
                except Exception as e:
                    logging.error(f"Error during search query '{query}': {str(e)}")
                time.sleep(1)
    for keyword in international_keywords:
        params = {
            "api_key": SERPAPI_KEY,
            "engine": "google",
            "q": keyword,
            "google_domain": "google.com",
            "hl": "en"
        }
        try:
            response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=30)
            if response.status_code == 200:
                results = response.json().get("organic_results", [])
                for result in results:
                    link = result.get("link")
                    if link:
                        domain = urlparse(link).netloc
                        if domain not in discovered_sites:
                            discovered_sites[domain] = link
            else:
                logging.error(f"Search query '{keyword}' failed with status {response.status_code}")
        except Exception as e:
            logging.error(f"Error during search query '{keyword}': {str(e)}")
        time.sleep(1)
    targets = []
    for domain, url in discovered_sites.items():
        assigned_country = "Africa"  # heuristic; could be refined based on query context
        targets.append({"base_url": url, "country": assigned_country, "allow_external": True})
    logging.info(f"Discovered {len(targets)} candidate target sites.")
    return targets

# ----------------------------- PREFECT TASKS & FLOW -----------------------------
@task
def process_page(url: str, country: str, allow_external: bool = False):
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
    inference = iterative_infer_page_structure(content, context)
    if inference is None:
        links = extract_links_bs4(content, url)
        inference = {"page_type": "list", "tender_links": links}
    return inference, content_hash, meta, content

@task
def process_inference(url: str, inference: dict, content_hash: str, meta: dict, country: str, domain: str, allow_external: bool = False):
    logger = get_run_logger()
    page_type = inference.get("page_type")
    headers = {'User-Agent': USER_AGENT}
    navigational_types = ["list", "landing", "search", "category", "document_repository", "multimedia", "comparison", "profile", "redirect", "error", "login"]
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
            logger.warning(f"No tender details found for {url}")
            links = extract_links_bs4(inference.get("content", ""), url)
            return {"enqueue": links}
        tender_data['source_url'] = url
        tender_data['content_hash'] = content_hash
        tender_data['documents'] = tender_data.get('documents', [])
        tender_data['metadata'] = meta
        tender_data['country'] = country
        tender_data['is_worth_pursuing'] = evaluate_tender(tender_data)
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
                api_inference = iterative_infer_page_structure(api_response.text, {"url": api_url, "country": country})
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
def scrape_site(config: dict):
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
    logger = get_run_logger()
    targets = discover_target_sites()
    if not targets:
        logger.error("No target sites discovered. Check your search API configuration.")
        return
    with ThreadPoolExecutor(max_workers=len(targets)) as executor:
        futures = [executor.submit(scrape_site, config) for config in targets]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Concurrent execution error: {str(e)}")
    logger.info("Scraping completed. Please review sample records from the database for quality assurance.")

if __name__ == "__main__":
    main_flow()
