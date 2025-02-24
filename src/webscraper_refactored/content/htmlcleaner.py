"""
HTMLCleaner module

Advanced HTML cleaning and sanitization with support for multiple cleaning strategies,
custom tag handling, and content preservation options.

This class provides comprehensive HTML cleaning capabilities including:
- Tag and attribute filtering
- JavaScript and style removal
- Comment and metadata stripping
- Structural element preservation
- Custom tag handling
- Content sanitization
- Encoding normalization

Attributes:
    allowed_tags (Set[str]): Set of HTML tags to preserve
    allowed_attributes (Set[str]): Set of allowed HTML attributes
    preserve_structure (bool): Whether to maintain document structure
    encoding (str): Input/output encoding
    remove_empty (bool): Whether to remove empty elements
    normalize_whitespace (bool): Whether to normalize whitespace
    url_schemes (Set[str]): Allowed URL schemes
    max_length (int): Maximum length for attribute values

Classes:

- HTMLCleaner

"""


class HTMLCleaner:
    """
    Advanced HTML cleaning and sanitization with support for multiple cleaning strategies,
    custom tag handling, and content preservation options.

    This class provides comprehensive HTML cleaning capabilities including:
    - Tag and attribute filtering
    - JavaScript and style removal
    - Comment and metadata stripping
    - Structural element preservation
    - Custom tag handling
    - Content sanitization
    - Encoding normalization

    Attributes:
        allowed_tags (Set[str]): Set of HTML tags to preserve
        allowed_attributes (Set[str]): Set of allowed HTML attributes
        preserve_structure (bool): Whether to maintain document structure
        encoding (str): Input/output encoding
        remove_empty (bool): Whether to remove empty elements
        normalize_whitespace (bool): Whether to normalize whitespace
        url_schemes (Set[str]): Allowed URL schemes
        max_length (int): Maximum length for attribute values
    """

    def __init__(
        self,
        preserve_structure: bool = True,
        remove_empty: bool = True,
        normalize_whitespace: bool = True,
        encoding: str = "utf-8",
    ):
        """
        Initialize HTMLCleaner with specified configuration.

        Args:
            preserve_structure: Whether to maintain document structure
            remove_empty: Remove empty elements
            normalize_whitespace: Normalize whitespace
            encoding: Input/output encoding
        """
        from bs4 import BeautifulSoup
        from lxml import etree
        from lxml.html.clean import Cleaner

        self.preserve_structure = preserve_structure
        self.remove_empty = remove_empty
        self.normalize_whitespace = normalize_whitespace
        self.encoding = encoding
        self.allowed_tags = {
            "div",
            "p",
            "br",
            "span",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "ul",
            "ol",
            "li",
            "a",
            "img",
            "table",
            "tr",
            "td",
            "th",
            "thead",
            "tbody",
            "article",
            "section",
            "main",
            "aside",
            "blockquote",
        }
        self.allowed_attributes = {
            "href",
            "src",
            "alt",
            "title",
            "class",
            "id",
            "name",
            "width",
            "height",
            "target",
        }
        self.url_schemes = {"http", "https", "mailto", "tel"}
        self.max_length = 1024
        self.cleaner = Cleaner(
            scripts=True,
            javascript=True,
            comments=True,
            style=True,
            links=True,
            meta=True,
            processing_instructions=True,
            embedded=True,
            frames=True,
            forms=True,
            annoying_tags=True,
            remove_unknown_tags=True,
            safe_attrs_only=True,
            safe_attrs=self.allowed_attributes,
            remove_tags=set(),
            allow_tags=self.allowed_tags,
        )
        self.parser = etree.HTMLParser(remove_blank_text=True)
        self.beautifier = BeautifulSoup

    def clean(self, html: str) -> str:
        """
        Clean and sanitize HTML content.

        Args:
            html: Raw HTML content to clean

        Returns:
            Cleaned HTML string

        Raises:
            ValueError: If HTML is malformed
            UnicodeError: If encoding fails
        """
        try:
            cleaned_html = self.cleaner.clean_html(html)
            if self.preserve_structure:
                cleaned_html = self._preserve_document_structure(cleaned_html)
            if self.remove_empty:
                cleaned_html = self._remove_empty_elements(cleaned_html)
            if self.normalize_whitespace:
                cleaned_html = self._normalize_whitespace(cleaned_html)
            return self._post_process(cleaned_html)
        except Exception as e:
            logger.error(f"HTML cleaning failed: {str(e)}")
            return self._fallback_clean(html)

    def _preserve_document_structure(self, html: str) -> str:
        """Preserve important document structure elements"""
        soup = self.beautifier(html, "lxml")
        for tag in soup.find_all(True):
            if tag.name in self.allowed_tags:
                continue
            if any((c.name in self.allowed_tags for c in tag.children)):
                tag.unwrap()
            else:
                tag.decompose()
        return str(soup)

    def _remove_empty_elements(self, html: str) -> str:
        """Remove elements with no content"""
        soup = self.beautifier(html, "lxml")
        for tag in soup.find_all(True):
            if not tag.get_text(strip=True) and tag.name not in {"img", "br"}:
                tag.decompose()
        return str(soup)

    def _normalize_whitespace(self, html: str) -> str:
        """Normalize whitespace in text nodes"""
        soup = self.beautifier(html, "lxml")
        for text in soup.find_all(text=True):
            if text.parent.name not in {"pre", "code"}:
                text.replace_with(" ".join(text.strip().split()))
        return str(soup)

    def _post_process(self, html: str) -> str:
        """Final processing and cleanup"""
        soup = self.beautifier(html, "lxml")
        for tag in soup.find_all(["a", "img"]):
            if "href" in tag.attrs:
                tag["href"] = self._clean_url(tag["href"])
            if "src" in tag.attrs:
                tag["src"] = self._clean_url(tag["src"])
        for tag in soup.find_all(True):
            for attr in list(tag.attrs):
                if len(str(tag[attr])) > self.max_length:
                    tag[attr] = str(tag[attr])[: self.max_length] + "..."
        return str(soup)

    def _clean_url(self, url: str) -> str:
        """Clean and validate URLs"""
        try:
            parsed = urlparse(url)
            if parsed.scheme and parsed.scheme not in self.url_schemes:
                return ""
            return url
        except Exception:
            return ""

    def _fallback_clean(self, html: str) -> str:
        """Fallback cleaning method for malformed HTML"""
        try:
            html = re.sub("<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
            html = re.sub("<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
            html = re.sub("<!--.*?-->", "", html, flags=re.DOTALL)
            return html
        except Exception:
            return re.sub("<[^>]+>", "", html)
