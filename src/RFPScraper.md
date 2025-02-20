The **RFPscraper** is a comprehensive, adaptive web scraping system designed to autonomously discover, extract, validate, and store rich tender data from a diverse set of sources including government agencies, NGOs, INGOs, and multilateral institutions. At its core, it leverages a robust **breadth-first search (BFS) crawler** to navigate through dynamically discovered websites—using queries that span every African country, multiple administrative levels (from national ministries to local municipalities), and international procurement portals—to build a comprehensive dataset of tender opportunities.

One of the system’s key capabilities is its **iterative LLM extraction pipeline**. Instead of attempting to extract all tender details in a single call, the scraper uses multiple, focused interactions with general-purpose language models. Initially, it determines the overall **page classification** (e.g., whether a page is a list, tender, API, landing, search, or another specialized type) through a dedicated prompt. If a page is classified as tender-like, a subsequent LLM call extracts detailed fields such as **tender_id**, **scope**, **contact_info**, **eligibility criteria**, **procurement method**, key dates (issue, pre-bid, evaluation, award, contract commencement, expiry), **estimated contract value**, **legal details**, and additional context including **sector**, **subnational location**, **donor information**, and **application process**. To ensure accuracy, the system implements a **prompt optimization loop**—using a separate model for optimization—to compare the LLM’s response against the intended output and refine the prompt when necessary. This iterative process minimizes errors and ensures that the output adheres to the expected JSON schema.

In addition, the RFPscraper is engineered for **multi-modal extraction**. While the primary focus is on textual data, the system is also capable of processing non-textual content. For example, it can extract text from downloadable PDF documents using libraries like PyPDF2, and it includes an OCR module (powered by Tesseract via pytesseract) for extracting information from images. This multi-faceted approach allows the scraper to harvest data even from scanned documents or image-based tender announcements, thereby greatly increasing the breadth of data collected.

Data quality and deduplication are critical aspects of the system. Every web page is processed to compute a unique **content hash** and, in conjunction with TF–IDF-based cosine similarity measures, the system detects and eliminates duplicate or near-duplicate entries. This ensures that the database remains clean and that the final dataset contains high–quality, unique records. The extracted tender data is validated using **Pydantic models** before being stored in a PostgreSQL database via SQLAlchemy, which not only enforces schema consistency but also supports extensive metadata such as additional keywords and document attachments.

The scraper’s discovery engine is another standout feature. It employs **SerpApi** to run a series of exhaustive search queries—iterating over combinations of African countries, administrative levels, and relevant tender-related keywords, as well as international queries targeting organizations like the **World Bank**, **UN agencies**, and **NGOs**. The result is a dynamically generated list of target sites that eliminates the need for manual curation, ensuring that the system can adapt to changes in the tender landscape over time.

Workflow orchestration is handled by **Prefect**, which coordinates the concurrent processing of multiple sites. By utilizing a ThreadPoolExecutor, the system can process numerous targets in parallel, significantly speeding up the crawling process and ensuring that the latest tender information is collected promptly. Additionally, the system logs detailed performance metrics and errors, laying the groundwork for future enhancements such as proactive re-crawling, change detection, and even active learning where human feedback is used to further refine the extraction process.

In summary, the **RFPscraper** is a state-of-the-art, end-to-end solution that integrates advanced web crawling, iterative LLM-driven data extraction with prompt optimization, multi-modal document processing, robust deduplication, and dynamic site discovery—all orchestrated within a scalable Prefect workflow. Its design not only maximizes the quantity of tender data collected but also ensures that the quality and comprehensiveness of the dataset meet the rigorous demands of modern procurement analytics and strategic decision–making.

---
The **RFPscraper** is an end‐to‐end system that combines modern natural language processing techniques, robust web crawling algorithms, and rigorous data validation to automatically discover, extract, and store tender-related data. Below is a detailed technical overview of its design, focusing on the algorithms and implementation decisions made throughout the system.

---

### Overall Architecture

At a high level, the system is divided into several modular components:

1. **Target Discovery:**
   Using SerpApi, the system issues a series of search queries that cover every African country, administrative subdivision (e.g., ministry, state, county, municipality, city), and additional international queries for NGO, INGO, and multilateral agency tender sites.
   - **Algorithm:** For each combination of country, administrative level, and tender-related keyword, an HTTP request is sent to SerpApi. The results (organic search results) are parsed to extract links, which are deduplicated by domain using URL parsing.
   - **Technical Decisions:**
     - **Exhaustive Querying:** This ensures comprehensive coverage of tender portals without manual curation.
     - **Deduplication by Domain:** Limits redundancy and ensures that each domain is processed only once.

2. **Breadth-First Search (BFS) Crawler:**
   For each discovered target site, a BFS traversal is used to explore the website.
   - **Algorithm:**
     - A queue (implemented as a Python `deque`) holds URLs to be processed.
     - As each URL is fetched and processed, new links (discovered either via LLM inference or BeautifulSoup fallback) are enqueued, ensuring a systematic exploration of the website.
   - **Technical Decisions:**
     - **BFS over DFS:** A BFS guarantees that the crawler explores pages layer by layer. This is beneficial for large sites, as it helps avoid getting trapped in deep link hierarchies.
     - **Visited Set:** This prevents reprocessing the same URL, thereby saving resources and avoiding infinite loops.

3. **Iterative LLM Extraction & Prompt Optimization:**
   The core innovation is the iterative interaction with a general-purpose LLM to extract structured data from unstructured tender pages.
   - **Two-Step Extraction:**
     - **Classification Step:** The system first calls the LLM with a prompt that asks, "What is the page type?" The response should indicate whether the page is a tender page, a navigational list, an API reference, or another type.
     - **Detailed Extraction Step:** If the page is classified as “tender-like” (e.g., tender, announcement, archived), a second prompt asks for detailed fields (such as tender_id, title, description, key dates, financials, legal details, contact info, etc.).
   - **Iterative Prompt Optimization:**
     - After each LLM call, the system validates the response by checking whether it is valid JSON and whether it contains required keys (for example, a "page_type" key and, for tender pages, "tender_details").
     - If the response does not meet quality criteria, an optimization prompt is sent to the LLM (using a different open–weight model) to compare the original prompt and its response and produce a refined prompt. This loop repeats (up to a maximum of two iterations) until a satisfactory response is obtained.
   - **Technical Decisions:**
     - **Iterative Refinement:** Reduces the chance of receiving incomplete or malformed responses from the LLM.
     - **Multi-Model Usage:** Different open-weight models (e.g., “llama-2-7b-chat” for extraction, “falcon-7b-instruct” for prompt optimization, and “mpt-7b-chat” for quality scoring) are used to leverage their distinct strengths.
     - **Heuristic Quality Checks:** Simple checks (like the presence of required keys) are used to decide if the response is acceptable.

4. **Data Extraction and Multi-Modal Processing:**
   The system extracts text from HTML pages, downloadable PDFs, and can also process images via OCR.
   - **Text Extraction:**
     - HTML pages are processed with BeautifulSoup to extract metadata and fallback links.
     - PDF documents are processed using PyPDF2 to extract textual content.
   - **OCR for Images:**
     - A placeholder function using pytesseract is provided to process images, which is crucial when tenders are published as scanned documents or contain embedded images.
   - **Technical Decisions:**
     - **Library Choices:** Using mature libraries like BeautifulSoup, PyPDF2, and pytesseract ensures reliability and community support.
     - **Modular Design:** Each modality is handled by its own function, making it easier to extend or improve in the future.

5. **Data Validation and Storage:**
   Once extracted, the data is validated and stored.
   - **Validation with Pydantic:**
     - The system defines a comprehensive Pydantic model that represents a tender’s feature vector, including fields like tender_id, title, scope, key dates, estimated contract value, and more.
   - **Storage with SQLAlchemy:**
     - Validated records are stored in a PostgreSQL database using SQLAlchemy ORM.
   - **Technical Decisions:**
     - **Strong Schema Enforcement:** Using Pydantic and SQLAlchemy ensures that the stored data conforms to the expected format and enables rigorous downstream processing.
     - **Deduplication:** A combination of SHA-256 content hashing and TF–IDF cosine similarity is used to avoid storing duplicate or near-duplicate entries.
     - **Graph-based Clustering (Placeholder):** Although not fully implemented, the design notes where graph clustering (e.g., via NetworkX) could further improve duplicate detection.

6. **Error Handling and Retry Logic:**
   Robust error handling is built into each step.
   - **Exponential Backoff with Jitter:**
     - When fetching URLs, the system uses an exponential backoff strategy combined with random jitter to mitigate transient network issues.
   - **Logging:**
     - Detailed logging is integrated throughout the code to capture errors, performance metrics, and duplicate detections. This data can later be used for proactive monitoring and resource adjustment.
   - **Technical Decisions:**
     - **Resilience:** The use of retries and logging ensures that temporary issues do not cause permanent data loss.
     - **Debuggability:** Comprehensive logging aids in troubleshooting and continuous improvement.

7. **Workflow Orchestration with Prefect:**
   The entire process is orchestrated using Prefect.
   - **Concurrent Execution:**
     - A ThreadPoolExecutor is used to process multiple discovered target sites concurrently.
   - **Task-based Design:**
     - Each significant function (page processing, inference processing, site crawling) is wrapped as a Prefect task, making it easier to monitor, schedule, and manage.
   - **Technical Decisions:**
     - **Scalability:** Prefect’s orchestration capabilities ensure that the system can scale to hundreds or thousands of sites.
     - **Extensibility:** Prefect’s task flow makes it straightforward to add additional tasks such as periodic re-crawling or active learning feedback loops.

---

### Key Algorithms and Data Structures

- **Breadth-First Search (BFS):**
  A queue (implemented with Python’s `deque`) is used for BFS. This ensures that pages are processed in layers and prevents the crawler from diving too deep into one branch of the website.

- **Iterative Prompt Optimization Loop:**
  The system uses a loop that:
  1. Sends a prompt to the LLM.
  2. Checks if the response is valid JSON and meets quality criteria (using heuristic checks).
  3. If not, calls an optimization prompt to refine the query.
  4. Repeats up to a maximum number of iterations.

  This is a form of adaptive query refinement that uses feedback to improve output quality.

- **Deduplication using TF–IDF & Cosine Similarity:**
  Texts from tender descriptions are vectorized using TF–IDF, and cosine similarity is computed between new texts and existing ones. If similarity exceeds a threshold, the record is considered a duplicate and is not stored.

- **Modular Function Design:**
  Functions are defined for each major component (LLM calling, prompt optimization, document processing, metadata extraction) so that the system is both maintainable and extensible.

---

### Technical Trade-offs and Decisions

- **Iterative vs. Single-Pass Extraction:**
  The decision to use iterative LLM calls with prompt optimization was made to minimize the risk of overloading the LLM with a single, overly complex prompt. This helps in obtaining higher-quality and more granular data extraction.

- **Multiple LLM Models:**
  By configuring different open–weight models for extraction, optimization, and quality scoring, the system leverages the strengths of each model without overloading a single one. This modularity is key given the general-purpose nature of available LLMs.

- **Comprehensive Site Discovery:**
  Instead of maintaining a static list of target URLs, the system dynamically discovers new tender sites through exhaustive search queries. This design decision ensures that the system remains relevant even as the landscape of tender portals evolves.

- **Robust Error Handling and Logging:**
  Extensive use of exponential backoff, error logging, and duplicate detection helps ensure system resilience. This is critical in real-world web crawling, where network errors, unexpected HTML changes, and duplicate content are common.

- **Prefect for Orchestration:**
  Using Prefect for task management and workflow orchestration allows for easy scaling, scheduling, and monitoring of the scraping process. This decision was made to facilitate not only initial data collection but also future incremental crawling and active learning.

---

### Conclusion

The **RFPscraper** represents a state-of-the-art solution that integrates advanced web crawling, iterative LLM-driven extraction with prompt optimization, multi-modal document processing, robust deduplication, and dynamic site discovery—all orchestrated by Prefect. The technical decisions (from choosing BFS to using multiple LLMs and rigorous error handling) are all designed to maximize both the quantity and quality of tender data collected. This robust, modular, and scalable architecture makes the RFPscraper a powerful tool for procurement analytics and strategic decision-making.
