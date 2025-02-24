"""
ContentPipeline module

Content processing pipeline

Classes:

- ContentPipeline

"""

from ..content import ContentProcessor, ContentValidator, HTMLCleaner


class ContentPipeline:
    """Content processing pipeline"""

    def __init__(self):
        self.processor = ContentProcessor()
        self.validator = ContentValidator()
        self.html_cleaner = HTMLCleaner()

    async def process(self, content: ScrapedContent) -> Optional[ScrapedContent]:
        try:
            cleaned_html = self.html_cleaner.clean(content.content)
            content.content = cleaned_html
            validated_content = self.validator.validate_and_clean(content)
            if not validated_content:
                return None
            processed_data = self.processor.process_content(validated_content.content)
            validated_content.keywords = processed_data.get("keywords", [])
            validated_content.summary = processed_data.get("summary", "")
            validated_content.entities = processed_data.get("entities", {})
            validated_content.readability_scores = processed_data.get(
                "readability_scores", {}
            )
            return validated_content
        except Exception as e:
            logger.error(f"Content pipeline error: {e}")
            return None
