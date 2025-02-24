"""
ContentValidator module

Advanced content validation and cleaning system.

This class provides comprehensive content validation and cleaning capabilities,
including:
- HTML cleaning and normalization
- Minimum length requirements
- Language detection and filtering
- Quality metrics evaluation
- Content structure analysis
- Readability assessment

Attributes:
    html_cleaner: HTML cleaning component
    content_filters: List of content validation filters
    validation_threshold: Minimum validation score required
    validation_results: Dictionary storing validation results

Classes:

- ContentValidator

"""

from typing import Any, Dict, List, Optional, Set

from ..content import HTMLCleaner


class ContentValidator:
    """
    Advanced content validation and cleaning system.

    This class provides comprehensive content validation and cleaning capabilities,
    including:
    - HTML cleaning and normalization
    - Minimum length requirements
    - Language detection and filtering
    - Quality metrics evaluation
    - Content structure analysis
    - Readability assessment

    Attributes:
        html_cleaner: HTML cleaning component
        content_filters: List of content validation filters
        validation_threshold: Minimum validation score required
        validation_results: Dictionary storing validation results
    """

    def __init__(self, validation_threshold: float = 0.7):
        """
        Initialize ContentValidator with specified parameters.

        Args:
            validation_threshold: Minimum score for content to be considered valid
        """
        self.html_cleaner = HTMLCleaner()
        self.content_filters = [
            MinLengthFilter(min_length=100, min_words=20),
            LanguageFilter(allowed_languages=["en"]),
            QualityFilter(min_score=validation_threshold),
        ]
        self.validation_threshold = validation_threshold
        self.validation_results: Dict[str, List[ValidationResult]] = {}

    def validate_and_clean(self, content: ScrapedContent) -> Optional[ScrapedContent]:
        """
        Validate and clean scraped content.

        Args:
            content: ScrapedContent object to validate and clean

        Returns:
            Cleaned ScrapedContent object if valid, None otherwise

        Raises:
            ValueError: If content is malformed or cleaning fails
        """
        try:
            cleaned_content = self.html_cleaner.clean(content.content)
            results = []
            for filter_obj in self.content_filters:
                result = filter_obj.validate(cleaned_content)
                results.append(result)
                if not result.is_valid:
                    self._store_validation_results(content.url, results)
                    return None
                cleaned_content = filter_obj.clean(cleaned_content)
            self._store_validation_results(content.url, results)
            content.content = cleaned_content
            content.word_count = len(cleaned_content.split())
            return content
        except Exception as e:
            logger.error(f"Content validation failed: {str(e)}")
            return None

    def _store_validation_results(self, url: str, results: List[ValidationResult]):
        """Store validation results for analysis"""
        self.validation_results[url] = results

    def get_validation_metrics(self, url: str) -> Dict[str, Any]:
        """
        Get validation metrics for a specific URL.

        Args:
            url: URL to get metrics for

        Returns:
            Dictionary containing validation metrics
        """
        if url not in self.validation_results:
            return {}
        results = self.validation_results[url]
        return {
            "overall_score": mean((r.score for r in results)),
            "passed_filters": sum((1 for r in results if r.is_valid)),
            "total_filters": len(results),
            "messages": [r.message for r in results],
            "metrics": {i: r.metrics for i, r in enumerate(results)},
        }

    def clear_validation_results(self):
        """Clear stored validation results"""
        self.validation_results.clear()
