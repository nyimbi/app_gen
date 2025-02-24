import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import time
from urllib.parse import urljoin
import re

class RFPScraper:
    def __init__(self):
        # Initialize database and create table if it doesn't exist
        self.conn = sqlite3.connect('rfp_database.db')
        self.create_table()
        
        # List of websites to scrape (you can expand this list)
        self.sources = [
            {"url": "https://www.fbo.gov", "base": "https://www.fbo.gov"},
            {"url": "https://www.merx.com", "base": "https://www.merx.com"},
            {"url": "https://www.gov.uk/contracts-finder", "base": "https://www.gov.uk"}
            # Add more sources as needed
        ]

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rfps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT UNIQUE NOT NULL,
                source_website TEXT NOT NULL,
                category TEXT,
                publication_date TEXT,
                last_checked TEXT,
                status TEXT DEFAULT 'new'
            )
        ''')
        self.conn.commit()

    def check_existing_rfp(self, url):
        cursor = self.conn.cursor()
        cursor.execute("SELECT url FROM rfps WHERE url = ?", (url,))
        return cursor.fetchone() is not None

    def save_rfp(self, title, description, url, source, category, pub_date):
        if not self.check_existing_rfp(url):
            cursor = self.conn.cursor()
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO rfps (title, description, url, source_website, category, publication_date, last_checked)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, url, source, category, pub_date, current_date))
            self.conn.commit()
            print(f"New RFP saved: {title}")

    def scrape_website(self, url, base_url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for RFP listings (adjust selectors based on website structure)
            # This is a generic approach; specific websites may need custom parsing
            rfp_elements = soup.find_all('div', class_=re.compile('listing|opportunity|notice', re.I))
            # or 'a', class_=re.compile('title|link', re.I) depending on structure

            for element in rfp_elements:
                # Extract title
                title_elem = element.find('h2') or element.find('a')
                title = title_elem.text.strip() if title_elem else 'No title'

                # Check if it's software related
                if not re.search(r'software|development|IT|technology|digital', title, re.I):
                    continue

                # Extract URL
                link = title_elem.get('href', '') if title_elem else ''
                full_url = urljoin(base_url, link) if link else ''

                if not full_url or self.check_existing_rfp(full_url):
                    continue

                # Extract description and publication date
                description = (element.find('p', class_=re.compile('description|details', re.I)) or 
                             element.find('div', class_=re.compile('description|details', re.I)))
                description = description.text.strip() if description else 'No description'

                date_elem = element.find('span', class_=re.compile('date|published', re.I)) or \
                           element.find('time')
                pub_date = date_elem.text.strip() if date_elem else datetime.now().strftime("%Y-%m-%d")

                # Save to database
                self.save_rfp(title, description, full_url, base_url, 'Software Development', pub_date)

        except requests.RequestException as e:
            print(f"Error scraping {url}: {e}")

    def run(self):
        for source in self.sources:
            self.scrape_website(source['url'], source['base'])
            # Be polite to websites, add delay between requests
            time.sleep(2)

    def close(self):
        self.conn.close()

def main():
    scraper = RFPScraper()
    try:
        scraper.run()
    finally:
        scraper.close()

if __name__ == "__main__":
    # This script can be scheduled to run daily using a scheduler like cron or Windows Task Scheduler
    main()