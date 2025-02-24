import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import hashlib
import json
from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import urljoin
from collections import deque

# Configuration
DATABASE_URL = "postgresql://user:password@localhost/rfp_database"  # Replace with your PostgreSQL credentials
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
REQUEST_DELAY = 2  # Seconds between requests
MAX_RETRIES = 3
OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Ollama API endpoint
BASE_URL = "https://example-tenders-website.com"  # Replace with the base URL of the tenders website

# Initialize SQLAlchemy
Base = declarative_base()

# Define RFP table
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
    activity = Column(String)  # Classification/tag for the RFP
    source_url = Column(String, unique=True)
    content_hash = Column(String, unique=True)
    is_worth_pursuing = Column(Boolean)  # Evaluation status

# Initialize database
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Check if URL/content already exists
def check_existing(source_url, content):
    session = Session()
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    
    exists = session.query(RFP).filter(
        (RFP.source_url == source_url) | (RFP.content_hash == content_hash)
    ).first()
    session.close()
    return exists is not None, content_hash

# Store RFP in database
def store_rfp(data):
    session = Session()
    try:
        rfp = RFP(
            title=data['title'],
            description=data['description'],
            organization=data['organization'],
            issue_date=data['issue_date'],
            expiry_date=data['expiry_date'],
            security_bond_required=data['security_bond_required'],
            country=data['country'],
            location=data['location'],
            activity=data['activity'],
            source_url=data['source_url'],
            content_hash=data['content_hash'],
            is_worth_pursuing=data['is_worth_pursuing']
        )
        session.add(rfp)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error storing RFP: {str(e)}")
    finally:
        session.close()

# Use Ollama with Qwen2.5 to analyze and process content
def analyze_with_ollama(content, context=None):
    prompt = f"""
    Analyze the following content and provide instructions in JSON format:
    - type: The type of content (e.g., "list_of_tenders", "single_tender", "api_reference")
    - actions: A list of actions to take (e.g., "extract_links", "parse_tender_details", "call_api")
    - data: Any relevant data (e.g., tender links, API endpoint, tender details)

    Context: {context}
    Content:
    {content}
    """

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "qwen2.5",  # Use the Qwen2.5 model
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
            print(f"Ollama API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error analyzing with Ollama: {str(e)}")
        return None

# Extract tender details using Ollama
def parse_tender_details(content, country):
    prompt = f"""
    Extract the following information from the text below in JSON format:
    - title: The title of the RFP
    - description: A detailed description of the RFP
    - organization: The organization issuing the RFP
    - issue_date: The date the RFP was issued (in YYYY-MM-DD format)
    - expiry_date: The deadline for submissions (in YYYY-MM-DD format)
    - security_bond_required: Whether a security bond is required (true/false)
    - country: The country where the RFP is issued (already provided: {country})
    - location: The location where the work will be performed
    - activity: The type of activity required (e.g., software development, construction, consulting)

    Text:
    {content}
    """

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "qwen2.5",  # Use the Qwen2.5 model
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
            print(f"Ollama API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error parsing tender details with Ollama: {str(e)}")
        return None

# Evaluate whether the tender is worth pursuing
def evaluate_tender(tender_data):
    # Example evaluation logic
    if tender_data['expiry_date'] < datetime.now().date():
        return False  # Tender has expired
    if tender_data['location'] not in ["Country A", "Country B"]:
        return False  # Not in target locations
    if tender_data['activity'] not in ["Software Development", "IT Consulting"]:
        return False  # Not in target activities
    return True

# Main scraping function
def scrape_site(start_url, country):
    visited = set()
    queue = deque([start_url])

    while queue:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            headers = {'User-Agent': USER_AGENT}
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                # Check for existing content
                content = response.text
                exists, content_hash = check_existing(url, content)
                if exists:
                    continue

                # Analyze the page content using Ollama
                analysis = analyze_with_ollama(content, context={"url": url, "country": country})
                if not analysis:
                    continue

                # Handle the page based on the analysis
                if analysis['type'] == "list_of_tenders":
                    # Extract tender links and add them to the queue
                    for link in analysis['data'].get('links', []):
                        full_url = urljoin(url, link)
                        if BASE_URL in full_url:  # Ensure links are within the same domain
                            queue.append(full_url)
                elif analysis['type'] == "single_tender":
                    # Parse tender details and store in the database
                    tender_data = parse_tender_details(content, country)
                    if tender_data:
                        tender_data['source_url'] = url
                        tender_data['content_hash'] = content_hash
                        tender_data['is_worth_pursuing'] = evaluate_tender(tender_data)
                        store_rfp(tender_data)
                elif analysis['type'] == "api_reference":
                    # Call the API and process the response
                    api_url = analysis['data'].get('api_endpoint')
                    if api_url:
                        api_response = requests.get(api_url, headers=headers, timeout=30)
                        if api_response.status_code == 200:
                            api_data = analyze_with_ollama(api_response.text, context={"type": "api_response"})
                            if api_data and api_data['type'] == "single_tender":
                                tender_data = parse_tender_details(api_response.text, country)
                                if tender_data:
                                    tender_data['source_url'] = api_url
                                    tender_data['content_hash'] = hashlib.sha256(api_response.text.encode()).hexdigest()
                                    tender_data['is_worth_pursuing'] = evaluate_tender(tender_data)
                                    store_rfp(tender_data)

                time.sleep(REQUEST_DELAY)
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")

# Load target websites (example format)
def load_targets():
    return [
        # Format: (url, country)
        ('https://example-tenders-website.com/tenders', 'Country A'),
        # Add more websites here...
    ]

# Main execution
if __name__ == "__main__":
    targets = load_targets()
    
    for url, country in targets:
        scrape_site(url, country)