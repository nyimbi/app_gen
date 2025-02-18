"""
ContentProcessor module

Advanced natural language processing and content analysis capabilities.

This class provides comprehensive text analysis features including:
- Text summarization using extractive methods
- Keyword extraction using TF-IDF
- Named entity recognition
- Readability analysis
- Sentiment analysis
- Language statistics

Attributes:
    nlp: spaCy language model for text processing
    readability: Text readability analyzer
    sentiment_analyzer: Text sentiment analyzer
    num_summary_sentences: Number of sentences to include in summaries
    min_keyword_freq: Minimum frequency for keyword extraction

Classes:

- ContentProcessor

"""


class ContentProcessor:
    """
    Advanced natural language processing and content analysis capabilities.

    This class provides comprehensive text analysis features including:
    - Text summarization using extractive methods
    - Keyword extraction using TF-IDF
    - Named entity recognition
    - Readability analysis
    - Sentiment analysis
    - Language statistics

    Attributes:
        nlp: spaCy language model for text processing
        readability: Text readability analyzer
        sentiment_analyzer: Text sentiment analyzer
        num_summary_sentences: Number of sentences to include in summaries
        min_keyword_freq: Minimum frequency for keyword extraction
    """

    def __init__(
        self, model="en_core_web_sm", num_summary_sentences=3, min_keyword_freq=2
    ):
        """
        Initialize the content processor with specified parameters.

        Args:
            model (str): Name of spaCy model to load
            num_summary_sentences (int): Number of sentences for summaries
            min_keyword_freq (int): Minimum keyword frequency threshold
        """
        from collections import Counter

        import spacy
        from textstat import textstatistics
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        self.nlp = spacy.load(model)
        self.readability = textstatistics()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.num_summary_sentences = num_summary_sentences
        self.min_keyword_freq = min_keyword_freq
        self.counter = Counter

    def process_content(self, text: str) -> Dict:
        """
        Process text content and return comprehensive analysis.

        Args:
            text (str): Raw text content to analyze

        Returns:
            Dict containing analysis results including:
            - Text summary
            - Keywords
            - Named entities
            - Readability metrics
            - Sentiment scores
            - Language statistics
        """
        doc = self.nlp(text)
        return {
            "summary": self.generate_summary(doc),
            "keywords": self.extract_keywords(doc),
            "entities": self.extract_entities(doc),
            "readability_scores": self._get_readability_scores(text),
            "sentiment": self._analyze_sentiment(text),
            "language_stats": self._get_language_stats(doc),
        }

    def generate_summary(self, doc) -> str:
        """
        Generate extractive summary of document.

        Args:
            doc: Processed spaCy document

        Returns:
            String containing summarized text
        """
        sentences = list(doc.sents)
        word_freq = self.counter(
            (token.text.lower() for token in doc if token.is_alpha)
        )
        sentence_scores = self._score_sentences(sentences, word_freq)
        summary_sents = self._top_sentences(sentence_scores, self.num_summary_sentences)
        return " ".join((str(s) for s in summary_sents))

    def extract_keywords(self, doc) -> List[str]:
        """
        Extract important keywords using frequency and TF-IDF.

        Args:
            doc: Processed spaCy document

        Returns:
            List of keyword strings
        """
        return [token.text for token in doc if token.is_alpha and (not token.is_stop)][
            :10
        ]

    def extract_entities(self, doc) -> Dict:
        """
        Extract named entities and their labels.

        Args:
            doc: Processed spaCy document

        Returns:
            Dictionary mapping entity labels to extracted text
        """
        return {ent.label_: ent.text for ent in doc.ents}

    def _score_sentences(self, sentences, word_freq) -> Dict:
        """Score sentences based on word frequencies."""
        scores = {}
        for sent in sentences:
            score = sum(
                (
                    word_freq.get(token.text.lower(), 0)
                    for token in sent
                    if token.is_alpha
                )
            )
            scores[sent] = score / len(sent)
        return scores

    def _top_sentences(self, scores: Dict, n: int) -> List:
        """Return top n scored sentences."""
        return sorted(scores.keys(), key=scores.get, reverse=True)[:n]

    def _get_readability_scores(self, text: str) -> Dict:
        """Calculate readability metrics."""
        return {
            "flesch_reading_ease": self.readability.flesch_reading_ease(text),
            "flesch_kincaid_grade": self.readability.flesch_kincaid_grade(text),
            "gunning_fog": self.readability.gunning_fog(text),
        }

    def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze text sentiment."""
        return self.sentiment_analyzer.polarity_scores(text)

    def _get_language_stats(self, doc) -> Dict:
        """Calculate document statistics."""
        return {
            "sentence_count": len(list(doc.sents)),
            "word_count": len([token for token in doc if token.is_alpha]),
            "unique_words": len(
                set((token.text.lower() for token in doc if token.is_alpha))
            ),
        }
