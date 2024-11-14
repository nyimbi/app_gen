from io import BytesIO
from typing import List, Optional

from pdfkit import pdfkit
from reflex import markdown
from sqlalchemy import Column, String, Integer, Boolean, Text, FileColumn
from sqlalchemy.orm import validates
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils import TSVectorType
from flask_appbuilder.models.mixins import ImageColumn
from sqlalchemy.sql import text, func
from sqlalchemy.dialects.postgresql import ARRAY
import os
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, Text, FileColumn, LargeBinary
from sqlalchemy.orm import validates
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils import TSVectorType
from flask_appbuilder.models.mixins import ImageColumn
from sqlalchemy.sql import text, func
from sqlalchemy.dialects.postgresql import ARRAY
from cryptography.fernet import Fernet
import PyPDF2
import pypandoc
import magic
import docx
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from transformers import pipeline
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from transformers import pipeline
import markdown
import pdfkit
from io import BytesIO
import mimetypes

from base_mixin import BaseModelMixin

from base_mixin import BaseModelMixin

class DocMixin(BaseModelMixin):
    mime_type: str = Column(String(60), default="application/pdf")
    doc: ImageColumn = Column(ImageColumn(thumbnail_size=(30, 30, True), size=(300, 300, True)))
    doc_text: str = Column(Text)
    doc_binary: FileColumn = Column(FileColumn)
    doc_title: str = Column(String(200))
    subject: str = Column(String(100))
    author: str = Column(String(100))
    keywords: str = Column(String(200))
    comments: str = Column(Text)

    # fields for chapter structure
    chapter_number: int = Column(Integer)
    chapter_title: str = Column(String(200))
    section_number: int = Column(Integer)
    section_title: str =Column(String(200))
    sub_section_number: int = Column(Integer)
    sub_section_title:str = Column(String(200))

    # fields for LLM-based text generation
    doc_context: str = Column(Text)
    doc_prompt: str = Column(Text)

    # Metadata
    doc_type: str = Column(String(5), default="pdf")
    char_count: int = Column(Integer)
    word_count: int = Column(Integer)
    lines: int = Column(Integer)
    paragraphs: int = Column(Integer)
    gpt_token_count: int = Column(Integer)
    grammar_checked: bool = Column(Boolean)
    doc_summary: str = Column(Text)
    doc_spell_checked: bool = Column(Boolean)
    doc_gpt_ver: str = Column(String(40))
    doc_format: str = Column(String(40))
    doc_downloadable: bool = Column(Boolean)
    doc_template: str = Column(Text)
    doc_rendered: bool = Column(Boolean)
    doc_render: FileColumn = Column(FileColumn)

    file_size_bytes: int = Column(Integer)
    producer_prog: str = Column(String(40))
    immutable: bool = Column(Boolean, default=False)

    page_size: str = Column(String(40))
    page_count: int = Column(Integer)
    hashx: str = Column(String(40))

    # if is Audio
    is_audio: bool = Column(Boolean)
    audio_duration_secs: int = Column(Integer)
    audio_frame_rate: int = Column(Integer)
    audio_channels: int = Column(Integer)

    # Encryption
    is_encrypted: bool = Column(Boolean, default=False)
    encryption_key: str = Column(String(100))

    @declared_attr
    def search_vector(cls):
        return Column(
            TSVectorType("doc_title", "doc_text", "comments", weights={"doc_title": "A", "doc_text": "B", "comments": "C"}),
            nullable=False,
            index=True,
        )

    @validates('doc_text')
    def update_doc_info(self, key: str, value: str) -> str:
        self.char_count = len(value)
        self.word_count = len(value.split())
        return value

    def extract_metadata(self) -> Dict[str, Any]:
        """
        Extract metadata from the document and populate relevant fields.

        :return: A dictionary containing the extracted metadata.
        """
        metadata = {}

        if self.mime_type == "application/pdf":
            try:
                with BytesIO(self.doc_binary) as file:
                    pdf = PyPDF2.PdfReader(file)
                    info = pdf.metadata
                    if info:
                        metadata['author'] = info.get('/Author', '')
                        metadata['subject'] = info.get('/Subject', '')
                        metadata['title'] = info.get('/Title', '')
                        metadata['creator'] = info.get('/Creator', '')
                        metadata['producer'] = info.get('/Producer', '')
                        metadata['creation_date'] = info.get('/CreationDate', '')
                        metadata['modification_date'] = info.get('/ModDate', '')
                        metadata['keywords'] = info.get('/Keywords', '')

                    # Extract additional information
                    metadata['page_count'] = len(pdf.pages)

                    # Extract text from the first page for summary
                    first_page = pdf.pages[0]
                    metadata['first_page_text'] = first_page.extract_text()[:1000]  # First 1000 characters
            except Exception as e:
                metadata['extraction_error'] = str(e)

        elif self.mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                "application/msword"]:
            # For .docx and .doc files
            # Note: Proper extraction would require additional libraries like python-docx for .docx
            # or a combination of libraries for .doc files
            metadata['extraction_note'] = "Metadata extraction for Word documents requires additional processing."

        elif self.mime_type == "text/plain":
            # For plain text files, we can provide basic information
            metadata['file_size'] = len(self.doc_binary)
            metadata['first_line'] = self.doc_binary.decode('utf-8', errors='ignore').split('\n')[0][
                                     :100]  # First 100 chars of first line

        elif self.mime_type == "text/markdown":
            # For markdown files
            content = self.doc_binary.decode('utf-8', errors='ignore')
            metadata['file_size'] = len(content)
            metadata['first_heading'] = next((line for line in content.split('\n') if line.strip().startswith('#')),
                                             '')[:100]

        else:
            metadata['extraction_note'] = f"Metadata extraction not supported for MIME type: {self.mime_type}"

        # Update object attributes with extracted metadata
        self.author = metadata.get('author', self.author)
        self.subject = metadata.get('subject', self.subject)
        self.doc_title = metadata.get('title', self.doc_title)
        self.keywords = metadata.get('keywords', self.keywords)
        self.page_count = metadata.get('page_count', self.page_count)
        self.file_size_bytes = metadata.get('file_size', self.file_size_bytes)
        self.producer_prog = metadata.get('producer', self.producer_prog)

        return metadata

    def generate_summary(self, max_length: int = 200) -> None:
        """
        Generate a summary of the document content using NLP techniques.

        :param max_length: Maximum length of the summary in words
        """
        nltk.download('punkt')
        nltk.download('stopwords')

        # Tokenize the text into sentences
        sentences = sent_tokenize(self.doc_text)

        # Calculate word frequencies
        stop_words = set(stopwords.words('english'))
        word_frequencies = {}
        for word in word_tokenize(self.doc_text):
            if word not in stop_words:
                if word not in word_frequencies:
                    word_frequencies[word] = 1
                else:
                    word_frequencies[word] += 1

        # Calculate sentence scores
        sentence_scores = {}
        for sentence in sentences:
            for word in word_tokenize(sentence.lower()):
                if word in word_frequencies:
                    if len(sentence.split(' ')) < 30:
                        if sentence not in sentence_scores:
                            sentence_scores[sentence] = word_frequencies[word]
                        else:
                            sentence_scores[sentence] += word_frequencies[word]

        # Get the summary
        summary_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:3]
        summary = ' '.join(summary_sentences)

        # Use a pre-trained model for more advanced summarization
        summarizer = pipeline("summarization")
        advanced_summary = summarizer(summary, max_length=max_length, min_length=50, do_sample=False)

        self.doc_summary = advanced_summary[0]['summary_text']

    @classmethod
    def search(cls, session, query: str, *, limit: Optional[int] = None, offset: Optional[int] = None) -> List['DocMixin']:
        """
        Perform a full-text search on the doc_title, doc_text and comments fields.

        :param session: A SQLAlchemy session object.
        :param query: The search query.
        :param limit: The maximum number of results to return.
        :param offset: The starting index of the results.
        :return: A list of matching objects with relevance score and highlighted terms.
        """
        search_query = func.plainto_tsquery('english', query)
        rank_function = func.ts_rank(cls.search_vector, search_query)

        results = (
            session.query(cls, rank_function.label('relevance'))
            .filter(cls.search_vector.match(search_query))
            .order_by(func.ts_rank(cls.search_vector, search_query).desc())
        )

        if limit is not None:
            results = results.limit(limit)
        if offset is not None:
            results = results.offset(offset)

        results = results.all()

        highlighted_results = []
        for doc, relevance in results:
            doc.relevance_score = relevance
            doc.highlighted_title = cls.highlight_matched_terms(doc.doc_title, query)
            doc.highlighted_text = cls.highlight_matched_terms(doc.doc_text, query)
            highlighted_results.append(doc)

        return highlighted_results

    @staticmethod
    def highlight_matched_terms(text: str, query: str) -> str:
        """
        Highlight the matched terms in the given text.

        :param text: The original text.
        :param query: The search query.
        :return: Text with matched terms highlighted.
        """
        words = query.split()
        highlighted_text = text

        for word in words:
            highlighted_text = highlighted_text.replace(
                word, f'<span class="highlight">{word}</span>'
            )

        return highlighted_text

    def encrypt_document(self, key: Optional[str] = None) -> None:
        """
        Encrypt the document using Fernet symmetric encryption.

        :param key: Optional encryption key. If not provided, a new one will be generated.
        """
        if not key:
            key = Fernet.generate_key()
        fernet = Fernet(key)
        self.doc_binary = fernet.encrypt(self.doc_binary)
        self.encryption_key = key.decode()
        self.is_encrypted = True

    def decrypt_document(self) -> None:
        """
        Decrypt the document using the stored encryption key.
        """
        if not self.is_encrypted:
            raise ValueError("Document is not encrypted")
        fernet = Fernet(self.encryption_key.encode())
        self.doc_binary = fernet.decrypt(self.doc_binary)
        self.is_encrypted = False
        self.encryption_key = None


    def convert_format(self, target_format: str) -> None:
        """
        Convert the document to a different format using Pandoc.

        :param target_format: The format to convert to (e.g., 'pdf', 'docx', 'md', 'html')
        """
        if self.doc_type == target_format:
            return

        # Mapping of doc_type to Pandoc format strings
        format_mapping = {
            'pdf': 'pdf',
            'docx': 'docx',
            'md': 'markdown',
            'html': 'html',
            'txt': 'plain',
            # Add more mappings as needed
        }

        source_format = format_mapping.get(self.doc_type)
        target_pandoc_format = format_mapping.get(target_format)

        if not source_format or not target_pandoc_format:
            raise ValueError(f"Conversion from {self.doc_type} to {target_format} is not supported")

        try:
            # Write the current document to a temporary file
            with BytesIO(self.doc_binary) as input_file:
                # Convert the document
                output = pypandoc.convert_file(
                    input_file.name,
                    target_pandoc_format,
                    format=source_format,
                    outputfile=None  # Return the result as a string
                )

            # Update the document properties
            self.doc_binary = output.encode('utf-8') if isinstance(output, str) else output
            self.doc_type = target_format
            self.mime_type = mimetypes.guess_type(f"dummy.{target_format}")[0]

            # Update metadata
            self.extract_metadata()
        except Exception as e:
            raise RuntimeError(f"Conversion failed: {str(e)}")

    def to_markdown(self) -> str:
        """
        Convert the document to markdown format.

        :return: The document content in markdown format.
        """
        return self.convert_format('md')

    def from_markdown(self, markdown_text: str, target_format: str) -> None:
        """
        Convert markdown text to the specified format and update the document.

        :param markdown_text: The markdown text to convert.
        :param target_format: The format to convert to ('pdf', 'docx', etc.).
        """
        # First, save the markdown text to a temporary file
        with BytesIO(markdown_text.encode('utf-8')) as input_file:
            # Convert the markdown to the target format
            output = pypandoc.convert_file(
                input_file.name,
                target_format,
                format='markdown',
                outputfile=None
            )

        # Update the document properties
        self.doc_binary = output.encode('utf-8') if isinstance(output, str) else output
        self.doc_type = target_format
        self.mime_type = mimetypes.guess_type(f"dummy.{target_format}")[0]

        # Update metadata
        self.extract_metadata()





    def generate_text_with_llm(self, llm_function):
        """
        Generate doc_text using an LLM based on doc_context and doc_prompt.

        :param llm_function: A function that takes context and prompt and returns generated text.
        """
        self.doc_text = llm_function(self.doc_context, self.doc_prompt)
        self.update_doc_info('doc_text', self.doc_text)

    def detect_mime_type(self, filename: Optional[str] = None) -> str:
        """
        Detect and set the MIME type of the document.

        :param filename: Optional filename to use for extension-based detection.
        :return: Detected MIME type.
        """
        if self.doc_binary:
            # Use python-magic for content-based detection
            mime = magic.Magic(mime=True)
            detected_mime_type = mime.from_buffer(self.doc_binary)
        elif filename:
            # Fallback to extension-based detection
            detected_mime_type, _ = mimetypes.guess_type(filename)
        else:
            raise ValueError("Either doc_binary or filename must be provided")

        if not detected_mime_type:
            detected_mime_type = "application/octet-stream"

        self.mime_type = detected_mime_type
        return detected_mime_type

    def set_doc_type_from_mime_type(self) -> None:
        """
        Set the doc_type based on the detected MIME type.
        """
        mime_to_doc_type = {
            "application/pdf": "pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            "application/msword": "doc",
            "text/plain": "txt",
            "text/markdown": "md",
            # Add more mappings as needed
        }
        self.doc_type = mime_to_doc_type.get(self.mime_type, "unknown")

    def update_document(self, file_content: bytes, filename: Optional[str] = None) -> None:
        """
        Update the document content, detect MIME type, and set doc_type.

        :param file_content: The binary content of the file.
        :param filename: Optional filename to use for extension-based detection.
        """
        self.doc_binary = file_content
        self.detect_mime_type(filename)
        self.set_doc_type_from_mime_type()
        self.file_size_bytes = len(file_content)