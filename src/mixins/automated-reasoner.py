from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Any, Tuple, Callable, Type
import math
import random
import time
from collections import defaultdict
from typing import List, Tuple, Set
import spacy
import nltk
from nltk.tokenize import sent_tokenize
from nltk.parse.stanford import StanfordDependencyParser
from transformers import Pipeline, pipeline
from fastcoref import FCoref,  LingMessCoref

@dataclass
class Proposition:
    """Represents a logical proposition with a name, optional truth value, and additional properties
    for enhanced logical reasoning capabilities."""

    name: str
    value: Optional[bool] = None
    confidence: float = 1.0
    temporal_validity: Optional[Tuple[int, int]] = None
    source: Optional[str] = None
    description: Optional[str] = None
    dependencies: Set[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = set()
        if self.metadata is None:
            self.metadata = {}

    def set_value(self, value: bool, confidence: float = None):
        """Sets the truth value and optionally updates confidence."""
        self.value = value
        if confidence is not None:
            self.confidence = confidence

    def get_value(self) -> Optional[bool]:
        """Returns the current truth value."""
        return self.value

    def is_known(self) -> bool:
        """Checks if the truth value is known."""
        return self.value is not None

    def set_temporal_validity(self, start: int, end: int):
        """Sets the temporal validity period for the proposition."""
        self.temporal_validity = (start, end)

    def is_valid_at(self, time: int) -> bool:
        """Checks if the proposition is valid at a given time."""
        if self.temporal_validity is None:
            return True
        start, end = self.temporal_validity
        return start <= time <= end

    def add_dependency(self, prop_name: str):
        """Adds a dependency on another proposition."""
        self.dependencies.add(prop_name)

    def remove_dependency(self, prop_name: str):
        """Removes a dependency."""
        self.dependencies.discard(prop_name)

    def get_dependencies(self) -> Set[str]:
        """Returns all dependencies."""
        return self.dependencies.copy()

    def set_metadata(self, key: str, value: Any):
        """Sets metadata for the proposition."""
        self.metadata[key] = value

    def get_metadata(self, key: str) -> Optional[Any]:
        """Retrieves metadata by key."""
        return self.metadata.get(key)

    def clear_metadata(self):
        """Clears all metadata."""
        self.metadata.clear()

    def __str__(self) -> str:
        """Enhanced string representation including key attributes."""
        status = f"{self.name}={'True' if self.value else 'False' if self.value is False else 'Unknown'}"
        if self.confidence != 1.0:
            status += f" (conf={self.confidence:.2f})"
        if self.temporal_validity:
            status += f" [t={self.temporal_validity[0]}-{self.temporal_validity[1]}]"
        return status


@dataclass
class ProbabilisticFact:
    """Represents a fact with an associated probability and additional probabilistic reasoning attributes.

    Attributes:
        proposition (Proposition): The logical proposition this fact represents
        probability (float): The probability value between 0 and 1 representing likelihood of truth
        confidence_interval (Optional[Tuple[float, float]]): Optional confidence interval for the probability
        evidence_count (int): Number of evidence instances supporting this probability
        last_updated (Optional[float]): Timestamp of last probability update
        prior_probability (Optional[float]): Previous probability before current value
        likelihood_ratio (Optional[float]): Ratio of likelihood under different hypotheses
        conditioning_factors (Dict[str, float]): Factors that condition this probability
        metadata (Dict[str, Any]): Additional metadata about this probabilistic fact
    """

    proposition: Proposition
    probability: float
    confidence_interval: Optional[Tuple[float, float]] = None
    evidence_count: int = 0
    last_updated: Optional[float] = None
    prior_probability: Optional[float] = None
    likelihood_ratio: Optional[float] = None
    conditioning_factors: Dict[str, float] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Validates probability and initializes optional fields."""
        if not 0 <= self.probability <= 1:
            raise ValueError("Probability must be between 0 and 1")
        if self.conditioning_factors is None:
            self.conditioning_factors = {}
        if self.metadata is None:
            self.metadata = {}

    def update_probability(self, new_prob: float, evidence_weight: int = 1) -> None:
        """Updates probability with new evidence.

        Args:
            new_prob: New probability value to incorporate
            evidence_weight: Weight of the new evidence
        """
        self.prior_probability = self.probability
        self.probability = (
            (self.probability * self.evidence_count) + (new_prob * evidence_weight)
        ) / (self.evidence_count + evidence_weight)
        self.evidence_count += evidence_weight
        self.last_updated = time.time()

    def set_confidence_interval(self, lower: float, upper: float) -> None:
        """Sets the confidence interval for the probability.

        Args:
            lower: Lower bound of confidence interval
            upper: Upper bound of confidence interval
        """
        if not (0 <= lower <= upper <= 1):
            raise ValueError("Confidence interval must be between 0 and 1")
        self.confidence_interval = (lower, upper)

    def add_conditioning_factor(self, factor_name: str, factor_value: float) -> None:
        """Adds a conditioning factor that influences the probability.

        Args:
            factor_name: Name of the conditioning factor
            factor_value: Value of the factor's influence
        """
        self.conditioning_factors[factor_name] = factor_value

    def get_adjusted_probability(self) -> float:
        """Calculates probability adjusted by conditioning factors.

        Returns:
            Float: Adjusted probability value
        """
        adjusted = self.probability
        for factor in self.conditioning_factors.values():
            adjusted *= factor
        return min(1.0, max(0.0, adjusted))

    def merge_with(self, other: "ProbabilisticFact") -> None:
        """Merges this fact with another probabilistic fact.

        Args:
            other: Another ProbabilisticFact to merge with
        """
        if self.proposition.name != other.proposition.name:
            raise ValueError("Can only merge facts about the same proposition")
        total_evidence = self.evidence_count + other.evidence_count
        self.probability = (
            (self.probability * self.evidence_count)
            + (other.probability * other.evidence_count)
        ) / total_evidence
        self.evidence_count = total_evidence

    def to_dict(self) -> Dict[str, Any]:
        """Converts the probabilistic fact to a dictionary representation.

        Returns:
            Dict containing all fact attributes
        """
        return {
            "proposition": self.proposition.name,
            "probability": self.probability,
            "confidence_interval": self.confidence_interval,
            "evidence_count": self.evidence_count,
            "last_updated": self.last_updated,
            "prior_probability": self.prior_probability,
            "likelihood_ratio": self.likelihood_ratio,
            "conditioning_factors": self.conditioning_factors.copy(),
            "metadata": self.metadata.copy(),
        }


class Rule:
    """A logical rule representing an inference pattern with premises and conclusion.

    Attributes:
        premises (List[Proposition]): List of propositions that must be satisfied for the rule to apply
        conclusion (Proposition): The proposition that follows when premises are satisfied
        confidence (float): Confidence score between 0-1 indicating rule reliability
        description (Optional[str]): Human readable description of the rule's meaning
        temporal_constraints (Optional[Dict[str, Any]]): Temporal validity constraints
        metadata (Dict[str, Any]): Additional metadata about the rule
        priority (int): Priority level for rule application ordering
        exceptions (Set[Proposition]): Propositions that would invalidate the rule
        bidirectional (bool): Whether rule can be applied in reverse
        applications (int): Counter for number of times rule has been applied
        last_applied (Optional[float]): Timestamp of last application
        source (Optional[str]): Source/origin of this rule

    Methods:
        evaluate(): Evaluates if rule premises are satisfied
        apply(): Applies rule to derive conclusion
        add_exception(): Adds exception condition
        remove_exception(): Removes exception condition
        is_applicable(): Checks if rule can be applied
        get_reverse(): Gets reverse/inverse of rule
        clone(): Creates deep copy of rule
    """

    def __init__(
        self,
        premises: List[Proposition],
        conclusion: Proposition,
        confidence: float = 1.0,
        description: Optional[str] = None,
        temporal_constraints: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        priority: int = 0,
        bidirectional: bool = False,
    ):
        """Initialize a new Rule.

        Args:
            premises: List of propositions that must be true for rule to apply
            conclusion: Proposition that follows when premises are satisfied
            confidence: Confidence score between 0-1 (default 1.0)
            description: Optional human readable description
            temporal_constraints: Optional temporal validity constraints
            metadata: Optional additional metadata
            priority: Rule priority for ordering (default 0)
            bidirectional: Whether rule is bidirectional (default False)
        """
        if not 0 <= confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")

        self.premises = premises
        self.conclusion = conclusion
        self.confidence = confidence
        self.description = description
        self.temporal_constraints = temporal_constraints or {}
        self.metadata = metadata or {}
        self.priority = priority
        self.exceptions = set()
        self.bidirectional = bidirectional
        self.applications = 0
        self.last_applied = None
        self.source = None

    @classmethod
    def from_str(cls, rule_str: str) -> "Rule":
        """Create Rule instance from string representation.

        Args:
            rule_str: String representation of rule

        Returns:
            Rule: Created rule instance

        Example:
            "IF a AND b THEN c (conf=0.8)"
        """
        # Parse IF-THEN parts
        if_part, then_part = rule_str.split(" THEN ")

        # Parse premises
        premises_str = if_part.replace("IF ", "").split(" AND ")
        premises = [Proposition(p.strip()) for p in premises_str]

        # Parse conclusion and confidence
        conclusion_parts = then_part.split("(conf=")
        conclusion = Proposition(conclusion_parts[0].strip())
        confidence = (
            float(conclusion_parts[1].strip(")")) if len(conclusion_parts) > 1 else 1.0
        )

        # Parse exceptions if present
        exceptions = set()
        if "UNLESS" in then_part:
            exc_str = then_part.split("UNLESS")[1].strip()
            exceptions = {Proposition(e.strip()) for e in exc_str.split(" OR ")}

        rule = cls(premises, conclusion, confidence)
        rule.exceptions = exceptions
        return rule

    def evaluate(self, knowledge_base) -> bool:
        """Evaluate if rule premises are satisfied in given knowledge base.

        Args:
            knowledge_base: The knowledge base to evaluate against

        Returns:
            bool: True if premises satisfied, False otherwise
        """
        if any(exc.name in knowledge_base.facts for exc in self.exceptions):
            return False

        return all(
            p.name in knowledge_base.facts and knowledge_base.facts[p.name]
            for p in self.premises
        )

    def apply(self, knowledge_base) -> bool:
        """Apply rule to derive conclusion if premises satisfied.

        Args:
            knowledge_base: The knowledge base to apply rule to

        Returns:
            bool: True if rule was applied, False otherwise
        """
        if self.evaluate(knowledge_base):
            knowledge_base.add_fact(self.conclusion, True)
            self.applications += 1
            self.last_applied = time.time()
            return True
        return False

    def add_exception(self, exception: Proposition):
        """Add an exception condition that invalidates the rule.

        Args:
            exception: Proposition that invalidates rule when true
        """
        self.exceptions.add(exception)

    def remove_exception(self, exception: Proposition):
        """Remove an exception condition.

        Args:
            exception: Exception to remove
        """
        self.exceptions.discard(exception)

    def is_applicable(self, time: Optional[int] = None) -> bool:
        """Check if rule can be applied considering constraints.

        Args:
            time: Optional time point to check temporal constraints

        Returns:
            bool: True if rule can be applied, False otherwise
        """
        if time is not None and self.temporal_constraints:
            start = self.temporal_constraints.get("start")
            end = self.temporal_constraints.get("end")
            if start is not None and time < start:
                return False
            if end is not None and time > end:
                return False
        return True

    def get_reverse(self) -> Optional["Rule"]:
        """Get reverse/inverse of rule if bidirectional.

        Returns:
            Rule: Reversed rule or None if not bidirectional
        """
        if not self.bidirectional:
            return None
        return Rule(
            [self.conclusion],
            self.premises[0] if len(self.premises) == 1 else self.premises,
            self.confidence,
            self.description,
            self.temporal_constraints.copy(),
            self.metadata.copy(),
            self.priority,
            True,
        )

    def clone(self) -> "Rule":
        """Create a deep copy of the rule.

        Returns:
            Rule: New rule instance with copied attributes
        """
        new_rule = Rule(
            self.premises.copy(),
            self.conclusion,
            self.confidence,
            self.description,
            self.temporal_constraints.copy(),
            self.metadata.copy(),
            self.priority,
            self.bidirectional,
        )
        new_rule.exceptions = self.exceptions.copy()
        new_rule.applications = self.applications
        new_rule.last_applied = self.last_applied
        new_rule.source = self.source
        return new_rule

    def __str__(self) -> str:
        """Get string representation of rule.

        Returns:
            str: Human readable rule representation
        """
        premises_str = " AND ".join([p.name for p in self.premises])
        rule_str = f"IF {premises_str} THEN {self.conclusion.name} (conf={self.confidence:.2f})"
        if self.exceptions:
            exceptions_str = " OR ".join([e.name for e in self.exceptions])
            rule_str += f" UNLESS {exceptions_str}"
        return rule_str

    def __eq__(self, other: Any) -> bool:
        """Check equality with another rule."""
        if not isinstance(other, Rule):
            return False
        return (
            self.premises == other.premises
            and self.conclusion == other.conclusion
            and self.confidence == other.confidence
        )

    def __hash__(self) -> int:
        """Get hash value for rule."""
        return hash((tuple(self.premises), self.conclusion, self.confidence))


class KnowledgeBase:
    """Enhanced knowledge base supporting various reasoning methods.

    A comprehensive and extensible knowledge base implementation that supports multiple types of
    knowledge representation and reasoning methods including:
    - Basic facts and rules with truth value tracking
    - Probabilistic reasoning with confidence intervals and evidence tracking
    - Temporal facts with validity periods and temporal consistency
    - Defeasible rules for non-monotonic reasoning with exceptions
    - Case-based reasoning with similarity metrics
    - Multi-valued logic with fuzzy truth values
    - Meta-reasoning capabilities for introspection
    - Consistency checking and constraint propagation
    - Uncertainty handling with confidence thresholds
    - Version control and change tracking
    - Explanation generation
    - Query optimization
    - Knowledge verification and validation
    - Incremental reasoning
    - Statistical correlations
    - Semantic annotations
    - Rule prioritization
    - Context management
    - Belief revision
    - Knowledge integration

    Attributes:
        facts (Dict[str, bool]): Basic propositional facts and their truth values
        rules (List[Rule]): Logical inference rules
        probabilistic_facts (Dict[str, ProbabilisticFact]): Facts with probability distributions
        temporal_facts (Dict[str, List[Tuple[bool, int]]]): Time-dependent facts
        defeasible_rules (List[Tuple[Rule, Set[Proposition]]]): Rules with exceptions
        cases (List[Dict[str, Any]]): Cases for case-based reasoning
        meta_facts (Dict[str, Any]): Meta-level knowledge about the knowledge base
        consistency_constraints (List[Callable]): Functions that check KB consistency
        uncertainty_threshold (float): Threshold for handling uncertain knowledge
        version_history (List[Dict]): History of KB modifications
        contexts (Dict[str, Dict]): Context-specific knowledge partitions
        annotations (Dict[str, Dict]): Semantic annotations for knowledge elements
        statistics (Dict[str, Any]): Statistical metrics about the knowledge base
        cache (Dict): Cache for optimizing repeated queries
        indexes (Dict): Index structures for efficient retrieval
        dependencies (Dict[str, Set[str]]): Tracked knowledge dependencies
    """

    def __init__(
        self,
        uncertainty_threshold: float = 0.1,
        enable_cache: bool = True,
        track_dependencies: bool = True,
        max_contexts: int = 10,
    ):
        """Initialize knowledge base with configuration options.

        Args:
            uncertainty_threshold: Minimum confidence level for facts (default 0.1)
            enable_cache: Whether to cache query results (default True)
            track_dependencies: Whether to track knowledge dependencies (default True)
            max_contexts: Maximum number of active contexts (default 10)
        """
        # Core knowledge structures
        self.facts = {}
        self.rules = []
        self.probabilistic_facts = {}
        self.temporal_facts = {}
        self.defeasible_rules = []
        self.cases = []
        self.meta_facts = {}

        # Validation and control
        self.consistency_constraints = []
        self.uncertainty_threshold = uncertainty_threshold
        self.version_history = []

        # Enhanced capabilities
        self.contexts = {}
        self.annotations = {}
        self.statistics = {"fact_count": 0, "rule_count": 0, "changes": 0, "queries": 0}
        self.cache = {} if enable_cache else None
        self.indexes = {"temporal": {}, "probabilistic": {}, "cases": {}}
        self.dependencies = {} if track_dependencies else None
        self._max_contexts = max_contexts
        self._current_context = "default"

        import time

        self._time = time

    def add_fact(
        self,
        prop: Proposition,
        value: bool,
        check_consistency: bool = True,
        context: Optional[str] = None,
        annotations: Optional[Dict] = None,
    ) -> bool:
        """Add or update a fact with enhanced tracking and validation.

        Args:
            prop: The proposition to add/update
            value: Truth value to assign
            check_consistency: Whether to verify consistency (default True)
            context: Optional context to add fact to (default current)
            annotations: Optional semantic annotations

        Returns:
            bool: True if fact was successfully added

        Raises:
            ValueError: If fact would create inconsistency
            ContextError: If context is invalid
        """
        context = context or self._current_context
        if context not in self.contexts:
            if len(self.contexts) >= self._max_contexts:
                raise ValueError(f"Maximum contexts ({self._max_contexts}) exceeded")
            self.contexts[context] = {"facts": {}, "rules": []}

        # Check consistency within context
        if check_consistency and not self._check_consistency(prop.name, value, context):
            raise ValueError(
                f"Adding fact {prop.name}={value} would create inconsistency in context {context}"
            )

        # Add fact
        self.facts[prop.name] = value
        if context != "default":
            self.contexts[context]["facts"][prop.name] = value

        # Update metadata
        self.statistics["fact_count"] += 1
        self.statistics["changes"] += 1
        if annotations:
            self.annotations[prop.name] = annotations

        # Track dependencies
        if self.dependencies is not None:
            self.dependencies[prop.name] = set()

        # Update indexes
        if prop.temporal_validity:
            self.indexes["temporal"][prop.name] = prop.temporal_validity

        self._log_change("add_fact", prop.name, value, context)
        self._invalidate_cache(prop.name)

        return True

    def add_probabilistic_fact(
        self,
        fact: ProbabilisticFact,
        check_threshold: bool = True,
        update_dependencies: bool = True,
    ) -> bool:
        """Add a probabilistic fact with enhanced validation and tracking.

        Args:
            fact: The probabilistic fact to add
            check_threshold: Whether to enforce uncertainty threshold
            update_dependencies: Whether to update knowledge dependencies

        Returns:
            bool: True if fact was successfully added
        """
        if check_threshold and fact.probability < self.uncertainty_threshold:
            return False

        prop_name = fact.proposition.name
        self.probabilistic_facts[prop_name] = fact

        # Update indexes and statistics
        self.indexes["probabilistic"][prop_name] = fact.probability
        self.statistics["fact_count"] += 1

        # Track dependencies
        if update_dependencies and self.dependencies is not None:
            self.dependencies[prop_name] = {
                f.proposition.name
                for f in self.probabilistic_facts.values()
                if f.probability > fact.probability
            }

        self._log_change("add_prob_fact", prop_name, fact.probability)
        self._invalidate_cache(prop_name)
        return True

    def add_temporal_fact(
        self,
        prop: Proposition,
        value: bool,
        time_point: int,
        valid_range: Optional[Tuple[int, int]] = None,
    ) -> None:
        """Add a temporally qualified fact with validity tracking.

        Args:
            prop: The proposition
            value: Truth value
            time_point: Timestamp for the fact
            valid_range: Optional validity period (start, end)
        """
        if prop.name not in self.temporal_facts:
            self.temporal_facts[prop.name] = []

        self.temporal_facts[prop.name].append((value, time_point))

        # Update temporal index
        if valid_range:
            self.indexes["temporal"][prop.name] = valid_range

        self._log_change("add_temporal_fact", prop.name, (value, time_point))
        self._invalidate_cache(prop.name)

    def add_rule(
        self,
        rule: Rule,
        check_cycles: bool = True,
        context: Optional[str] = None,
        priority: int = 0,
    ) -> bool:
        """Add an inference rule with cycle detection and prioritization.

        Args:
            rule: The rule to add
            check_cycles: Whether to check for cyclic dependencies
            context: Optional context to add rule to
            priority: Rule priority level (higher = higher priority)

        Returns:
            bool: True if rule was successfully added

        Raises:
            ValueError: If rule would create cycle
        """
        if check_cycles and self._would_create_cycle(rule):
            raise ValueError("Rule would create cyclic dependency")

        # Add rule with priority
        rule.priority = priority
        self.rules.append(rule)

        # Add to context if specified
        if context:
            if context not in self.contexts:
                self.contexts[context] = {"facts": {}, "rules": []}
            self.contexts[context]["rules"].append(rule)

        # Track dependencies
        if self.dependencies is not None:
            for premise in rule.premises:
                if premise.name not in self.dependencies:
                    self.dependencies[premise.name] = set()
                self.dependencies[premise.name].add(rule.conclusion.name)

        self.statistics["rule_count"] += 1
        self._log_change("add_rule", str(rule), context)
        self._invalidate_cache()
        return True

    def query(
        self, prop_name: str, time: Optional[int] = None, context: Optional[str] = None
    ) -> Tuple[Optional[bool], float]:
        """Enhanced query mechanism with confidence and temporal reasoning.

        Args:
            prop_name: Name of proposition to query
            time: Optional timestamp for temporal facts
            context: Optional context to query in

        Returns:
            Tuple of (truth value, confidence score)
        """
        self.statistics["queries"] += 1

        # Check cache
        cache_key = (prop_name, time, context)
        if self.cache is not None and cache_key in self.cache:
            return self.cache[cache_key]

        # Check context-specific facts
        if context and context in self.contexts:
            if prop_name in self.contexts[context]["facts"]:
                return self.contexts[context]["facts"][prop_name], 1.0

        # Check temporal facts
        if time is not None and prop_name in self.temporal_facts:
            value = self._get_temporal_value(prop_name, time)
            if value is not None:
                return value, 1.0

        # Check probabilistic facts
        if prop_name in self.probabilistic_facts:
            fact = self.probabilistic_facts[prop_name]
            return fact.get_value(), fact.probability

        # Check basic facts
        if prop_name in self.facts:
            return self.facts[prop_name], 1.0

        # Cache miss
        if self.cache is not None:
            self.cache[cache_key] = (None, 0.0)

        return None, 0.0

    def get_explanation(self, prop_name: str) -> List[str]:
        """Generate human-readable explanation for a proposition.

        Args:
            prop_name: Name of proposition to explain

        Returns:
            List of explanation strings
        """
        explanations = []

        # Direct fact
        if prop_name in self.facts:
            explanations.append(
                f"Directly known fact: {prop_name} = {self.facts[prop_name]}"
            )

        # Probabilistic fact
        if prop_name in self.probabilistic_facts:
            fact = self.probabilistic_facts[prop_name]
            explanations.append(
                f"Probabilistic fact: {prop_name} ({fact.probability:.2f} confidence)"
            )

        # Temporal fact
        if prop_name in self.temporal_facts:
            explanations.append(
                f"Temporal fact with {len(self.temporal_facts[prop_name])} timestamps"
            )

        # Derived through rules
        if self.dependencies and prop_name in self.dependencies:
            explanations.append("Derived from:")
            for dep in self.dependencies[prop_name]:
                explanations.append(f"- {dep}")

        return explanations

    def _check_consistency(
        self, prop_name: str, value: bool, context: Optional[str] = None
    ) -> bool:
        """Enhanced consistency checking with context awareness.

        Args:
            prop_name: Name of proposition
            value: Proposed truth value
            context: Optional context to check in

        Returns:
            bool: True if consistent
        """
        # Check context-specific consistency
        if context and context in self.contexts:
            test_facts = self.contexts[context]["facts"].copy()
            test_facts[prop_name] = value
            if not all(c(test_facts) for c in self.consistency_constraints):
                return False

        # Check global consistency
        test_facts = self.facts.copy()
        test_facts[prop_name] = value
        return all(
            constraint(test_facts) for constraint in self.consistency_constraints
        )

    def _get_temporal_value(self, prop_name: str, time: int) -> Optional[bool]:
        """Get truth value at specific time with caching.

        Args:
            prop_name: Name of proposition
            time: Timestamp to check

        Returns:
            bool or None: Truth value if found
        """
        relevant_facts = [
            (v, t) for v, t in self.temporal_facts[prop_name] if t <= time
        ]
        if relevant_facts:
            return max(relevant_facts, key=lambda x: x[1])[0]
        return None

    def save_to_file(self, filename: str) -> None:
        """Save knowledge base to file in JSON format.

        Args:
            filename: Path to save file
        """
        import json

        kb_data = {
            "facts": self.facts,
            "rules": [str(rule) for rule in self.rules],
            "probabilistic_facts": {
                name: fact.to_dict() for name, fact in self.probabilistic_facts.items()
            },
            "temporal_facts": self.temporal_facts,
            "defeasible_rules": [
                (str(rule), [str(exc) for exc in excs])
                for rule, excs in self.defeasible_rules
            ],
            "cases": self.cases,
            "meta_facts": self.meta_facts,
            "contexts": self.contexts,
            "annotations": self.annotations,
            "statistics": self.statistics,
            "indexes": self.indexes,
        }

        with open(filename, "w") as f:
            json.dump(kb_data, f, indent=2)

    def load_from_file(self, filename: str) -> None:
        """Load knowledge base from JSON file.

        Args:
            filename: Path to load file

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file format is invalid
        """
        import json

        with open(filename, "r") as f:
            kb_data = json.load(f)

        # Clear current KB
        self.__init__(self.uncertainty_threshold)

        # Load data
        self.facts = kb_data["facts"]
        self.rules = [Rule.from_str(rule_str) for rule_str in kb_data["rules"]]
        self.probabilistic_facts = {
            name: ProbabilisticFact.from_dict(fact_dict)
            for name, fact_dict in kb_data["probabilistic_facts"].items()
        }
        self.temporal_facts = kb_data["temporal_facts"]
        self.defeasible_rules = [
            (Rule.from_str(rule_str), {Proposition(exc) for exc in excs})
            for rule_str, excs in kb_data["defeasible_rules"]
        ]
        self.cases = kb_data["cases"]
        self.meta_facts = kb_data["meta_facts"]
        self.contexts = kb_data["contexts"]
        self.annotations = kb_data["annotations"]
        self.statistics = kb_data["statistics"]
        self.indexes = kb_data["indexes"]

    def review_knowledge(self, detail_level: str = "summary") -> str:
        """Generate human-readable review of knowledge base contents.

        Args:
            detail_level: Level of detail ('summary', 'full', 'technical')

        Returns:
            str: Formatted knowledge base review
        """
        if detail_level == "summary":
            return self._generate_summary()
        elif detail_level == "full":
            return self._generate_full_review()
        else:
            return self._generate_technical_review()

    def _generate_summary(self) -> str:
        """Generate summary review."""
        summary = []
        summary.append("Knowledge Base Summary")
        summary.append("====================")
        summary.append(f"Total Facts: {len(self.facts)}")
        summary.append(f"Total Rules: {len(self.rules)}")
        summary.append(f"Probabilistic Facts: {len(self.probabilistic_facts)}")
        summary.append(f"Temporal Facts: {len(self.temporal_facts)}")
        summary.append(f"Active Contexts: {len(self.contexts)}")
        summary.append(f"\nStatistics:")
        summary.append(f"- Total Changes: {self.statistics['changes']}")
        summary.append(f"- Total Queries: {self.statistics['queries']}")
        return "\n".join(summary)

    def _generate_full_review(self) -> str:
        """Generate detailed review."""
        review = []
        review.append("Knowledge Base Full Review")
        review.append("=========================")

        review.append("\nFacts:")
        for name, value in self.facts.items():
            review.append(f"- {name} = {value}")

        review.append("\nRules:")
        for rule in self.rules:
            review.append(f"- {str(rule)}")

        review.append("\nProbabilistic Facts:")
        for fact in self.probabilistic_facts.values():
            review.append(f"- {str(fact)}")

        review.append("\nTemporal Facts:")
        for name, values in self.temporal_facts.items():
            review.append(f"- {name}: {len(values)} values")

        review.append("\nContexts:")
        for context, data in self.contexts.items():
            review.append(
                f"- {context}: {len(data['facts'])} facts, {len(data['rules'])} rules"
            )

        return "\n".join(review)

    def _generate_technical_review(self) -> str:
        """Generate technical review with statistics."""
        review = []
        review.append("Knowledge Base Technical Review")
        review.append("=============================")

        # Core metrics
        review.append("\nCore Metrics:")
        review.append(f"Facts: {len(self.facts)}")
        review.append(f"Rules: {len(self.rules)}")
        review.append(f"Probabilistic Facts: {len(self.probabilistic_facts)}")
        review.append(f"Temporal Facts: {len(self.temporal_facts)}")

        # Memory usage
        import sys

        memory_usage = (
            sys.getsizeof(self.facts)
            + sys.getsizeof(self.rules)
            + sys.getsizeof(self.probabilistic_facts)
            + sys.getsizeof(self.temporal_facts)
        )
        review.append(f"\nMemory Usage: {memory_usage / 1024:.2f} KB")

        # Cache statistics
        if self.cache is not None:
            review.append(f"\nCache Status:")
            review.append(f"Size: {len(self.cache)} entries")
            review.append(
                f"Hit rate: {self.statistics.get('cache_hits', 0) / max(1, self.statistics['queries']):.2%}"
            )

        # Index statistics
        review.append(f"\nIndexes:")
        for idx_type, idx in self.indexes.items():
            review.append(f"- {idx_type}: {len(idx)} entries")

        return "\n".join(review)

    def print_knowledge_base(self, format_type: str = "text") -> None:
        """Print knowledge base contents in specified format.

        Args:
            format_type: Output format ('text', 'json', 'yaml')
        """
        if format_type == "text":
            print(self.review_knowledge("full"))
        elif format_type == "json":
            import json

            print(json.dumps(self.to_dict(), indent=2))
        elif format_type == "yaml":
            import yaml

            print(yaml.dump(self.to_dict()))
        else:
            print(str(self))

    def to_dict(self) -> Dict[str, Any]:
        """Convert knowledge base to dictionary representation.

        Returns:
            Dict containing all KB data
        """
        return {
            "facts": self.facts,
            "rules": [str(rule) for rule in self.rules],
            "probabilistic_facts": {
                name: fact.to_dict() for name, fact in self.probabilistic_facts.items()
            },
            "temporal_facts": self.temporal_facts,
            "defeasible_rules": [
                (str(rule), [str(exc) for exc in excs])
                for rule, excs in self.defeasible_rules
            ],
            "cases": self.cases,
            "meta_facts": self.meta_facts,
            "contexts": self.contexts,
            "annotations": self.annotations,
            "statistics": self.statistics,
            "indexes": self.indexes,
        }

    def validate_knowledge(self) -> Tuple[bool, List[str]]:
        """Validate knowledge base integrity.

        Returns:
            Tuple of (is_valid, list of validation messages)
        """
        messages = []
        is_valid = True

        # Check fact consistency
        for name, value in self.facts.items():
            if not self._check_consistency(name, value):
                messages.append(f"Inconsistency detected in fact: {name}")
                is_valid = False

        # Validate rules
        for rule in self.rules:
            if rule.premises is None or rule.conclusion is None:
                messages.append(f"Invalid rule detected: {str(rule)}")
                is_valid = False

        # Check probabilistic fact validity
        for fact in self.probabilistic_facts.values():
            if not 0 <= fact.probability <= 1:
                messages.append(f"Invalid probability in fact: {fact.proposition.name}")
                is_valid = False

        # Verify temporal fact ordering
        for name, values in self.temporal_facts.items():
            times = [t for _, t in values]
            if times != sorted(times):
                messages.append(f"Temporal facts not properly ordered for: {name}")
                is_valid = False

        return is_valid, messages

    def _invalidate_cache(self, prop_name: Optional[str] = None) -> None:
        """Intelligently invalidate cache entries.

        Args:
            prop_name: Optional specific proposition to invalidate
        """
        if self.cache is not None:
            if prop_name:
                # Invalidate specific proposition and dependencies
                to_remove = {k for k in self.cache if k[0] == prop_name}
                if self.dependencies and prop_name in self.dependencies:
                    for dep in self.dependencies[prop_name]:
                        to_remove.update(k for k in self.cache if k[0] == dep)
                for k in to_remove:
                    del self.cache[k]
            else:
                # Full cache invalidation
                self.cache.clear()

    def _log_change(self, operation: str, *args) -> None:
        """Enhanced change logging with timestamps.

        Args:
            operation: Type of change
            *args: Change details
        """
        self.version_history.append(
            {
                "operation": operation,
                "args": args,
                "timestamp": self._time.time(),
                "context": self._current_context,
            }
        )

    def __str__(self) -> str:
        """Comprehensive string representation.

        Returns:
            str: Detailed KB status
        """
        sections = [
            f"Knowledge Base Status:",
            f"Facts: {len(self.facts)}",
            f"Rules: {len(self.rules)}",
            f"Probabilistic Facts: {len(self.probabilistic_facts)}",
            f"Temporal Facts: {len(self.temporal_facts)}",
            f"Defeasible Rules: {len(self.defeasible_rules)}",
            f"Cases: {len(self.cases)}",
            f"Contexts: {len(self.contexts)}",
            f"Statistics:",
            f"- Queries: {self.statistics['queries']}",
            f"- Changes: {self.statistics['changes']}",
            f"Cache Status: {'Enabled' if self.cache is not None else 'Disabled'}",
        ]
        return "\n".join(sections)


class ReasoningStrategy(ABC):
    """Abstract base class for automated reasoning strategies.

    This class defines the interface that all reasoning strategies must implement. It provides
    a common structure for different logical inference approaches such as forward chaining,
    backward chaining, resolution, etc.

    Attributes:
        _reasoning_context (Dict): Optional context/metadata for the reasoning process
        _inference_depth (int): Maximum depth for recursive reasoning (default: 100)
        _cache_results (bool): Whether to cache intermediate reasoning results

    Methods:
        reason: Main abstract method that must be implemented by concrete strategies
        validate_input: Helper to validate reasoning inputs
        get_reasoning_context: Access the reasoning context
        clear_cache: Clear any cached results
        set_inference_parameters: Configure inference parameters
    """

    def __init__(self, max_inference_depth: int = 100, cache_results: bool = True):
        """Initialize the reasoning strategy with optional parameters.

        Args:
            max_inference_depth: Maximum recursion depth for inference
            cache_results: Whether to cache intermediate results
        """
        self._reasoning_context = {}
        self._inference_depth = max_inference_depth
        self._cache_results = cache_results
        self._result_cache = {}

    @abstractmethod
    def reason(self, kb: KnowledgeBase, goal: Optional[Proposition] = None) -> Any:
        """Perform reasoning using the knowledge base to achieve a goal.

        This is the main entry point for reasoning that concrete strategies must implement.

        Args:
            kb: Knowledge base containing facts and rules
            goal: Optional goal proposition to prove/derive

        Returns:
            Any: The result of reasoning (specific type depends on strategy)

        Raises:
            NotImplementedError: If concrete strategy doesn't implement this
            ValueError: If inputs are invalid
            RecursionError: If max inference depth is exceeded
        """
        raise NotImplementedError

    def validate_input(
        self, kb: KnowledgeBase, goal: Optional[Proposition] = None
    ) -> None:
        """Validate the reasoning inputs before execution.

        Args:
            kb: Knowledge base to validate
            goal: Optional goal proposition to validate

        Raises:
            ValueError: If inputs are invalid
        """
        if not isinstance(kb, KnowledgeBase):
            raise ValueError("Knowledge base must be instance of KnowledgeBase")
        if goal is not None and not isinstance(goal, Proposition):
            raise ValueError("Goal must be instance of Proposition or None")

    def get_reasoning_context(self) -> Dict:
        """Get the current reasoning context/metadata.

        Returns:
            Dict containing reasoning context information
        """
        return self._reasoning_context.copy()

    def clear_cache(self) -> None:
        """Clear any cached reasoning results."""
        self._result_cache.clear()

    def set_inference_parameters(
        self, max_depth: int = None, cache_results: bool = None
    ) -> None:
        """Configure inference parameters.

        Args:
            max_depth: New maximum inference depth
            cache_results: Whether to cache results
        """
        if max_depth is not None:
            self._inference_depth = max_depth
        if cache_results is not None:
            self._cache_results = cache_results

    def _should_use_cache(self, kb: KnowledgeBase, goal: Optional[Proposition]) -> bool:
        """Determine if cached results should be used.

        Args:
            kb: Current knowledge base
            goal: Current goal

        Returns:
            bool: Whether to use cached results
        """
        if not self._cache_results:
            return False
        cache_key = (hash(str(kb)), hash(str(goal)) if goal else None)
        return cache_key in self._result_cache


class ForwardChaining(ReasoningStrategy):
    """Implementation of forward chaining reasoning.

    This class implements forward chaining inference, a data-driven approach that starts
    with known facts and applies inference rules iteratively until no new facts can be derived.

    The implementation includes:
    - Support for probabilistic reasoning with confidence values
    - Cycle detection to prevent infinite loops
    - Inference tracking and explanation generation
    - Rule prioritization based on specificity/confidence
    - Caching of intermediate results
    - Early stopping when optional goal is reached
    - Performance optimizations for large rule sets

    Attributes:
        max_iterations (int): Maximum number of inference iterations (default: 1000)
        track_explanations (bool): Whether to track rule applications (default: False)
        inference_history (List): History of applied rules and derived facts
        prioritize_rules (bool): Whether to prioritize rules by confidence (default: True)
    """

    def __init__(
        self,
        max_iterations: int = 1000,
        track_explanations: bool = False,
        prioritize_rules: bool = True,
    ):
        """Initialize forward chaining reasoner.

        Args:
            max_iterations: Maximum iterations to prevent infinite loops
            track_explanations: Whether to track inference explanations
            prioritize_rules: Whether to prioritize rules by confidence
        """
        super().__init__()
        self.max_iterations = max_iterations
        self.track_explanations = track_explanations
        self.inference_history = []
        self.prioritize_rules = prioritize_rules

    def reason(
        self, kb: KnowledgeBase, goal: Optional[Proposition] = None
    ) -> Set[Proposition]:
        """Perform forward chaining inference.

        Iteratively applies rules to derive new facts until no more facts can be inferred
        or the optional goal is reached.

        Args:
            kb: Knowledge base containing facts and rules
            goal: Optional goal proposition to derive

        Returns:
            Set of newly inferred propositions

        Raises:
            RecursionError: If max iterations exceeded
            ValueError: If invalid knowledge base or goal
        """
        self.validate_input(kb, goal)

        # Check cache if enabled
        if self._should_use_cache(kb, goal):
            return self._result_cache.get((hash(str(kb)), hash(str(goal))))

        inferred = set()
        iteration = 0
        rules = self._prioritize_rules(kb.rules) if self.prioritize_rules else kb.rules

        while iteration < self.max_iterations:
            iteration += 1
            new_facts = False

            for rule in rules:
                # Skip rules that have been applied
                if rule.conclusion.name in kb.facts:
                    continue

                # Check if rule premises are satisfied
                if self._evaluate_premises(kb, rule):
                    # Apply rule and track inference
                    kb.facts[rule.conclusion.name] = True
                    inferred.add(rule.conclusion)
                    new_facts = True

                    if self.track_explanations:
                        self._track_inference(rule)

                    # Check if goal is reached
                    if goal and goal.name == rule.conclusion.name:
                        if self._cache_results:
                            self._cache_result(kb, goal, inferred)
                        return inferred

            if not new_facts:
                break

        if iteration >= self.max_iterations:
            raise RecursionError("Maximum inference iterations exceeded")

        if self._cache_results:
            self._cache_result(kb, goal, inferred)

        return inferred

    def _evaluate_premises(self, kb: KnowledgeBase, rule: Rule) -> bool:
        """Evaluate if all rule premises are satisfied.

        Args:
            kb: Knowledge base to check against
            rule: Rule whose premises to evaluate

        Returns:
            bool: True if all premises are satisfied
        """
        for premise in rule.premises:
            if premise.name not in kb.facts:
                return False
            if not kb.facts[premise.name]:
                return False
        return True

    def _prioritize_rules(self, rules: List[Rule]) -> List[Rule]:
        """Sort rules by confidence/specificity.

        Args:
            rules: List of rules to prioritize

        Returns:
            Sorted list of rules
        """
        return sorted(rules, key=lambda r: (-r.confidence, -len(r.premises)))

    def _track_inference(self, rule: Rule) -> None:
        """Track application of inference rule.

        Args:
            rule: The rule that was applied
        """
        self.inference_history.append({"rule": str(rule), "timestamp": time.time()})

    def _cache_result(
        self, kb: KnowledgeBase, goal: Optional[Proposition], result: Set[Proposition]
    ) -> None:
        """Cache the inference result.

        Args:
            kb: Knowledge base used
            goal: Goal proposition if any
            result: Inference result to cache
        """
        cache_key = (hash(str(kb)), hash(str(goal)))
        self._result_cache[cache_key] = result

    def get_explanation(self) -> List[Dict]:
        """Get explanation of inference process.

        Returns:
            List of rule applications and derived facts
        """
        if not self.track_explanations:
            return []
        return self.inference_history.copy()

    def clear_history(self) -> None:
        """Clear the inference history."""
        self.inference_history.clear()


class BackwardChaining(ReasoningStrategy):
    """Implementation of backward chaining reasoning.

    This class implements goal-directed backward chaining inference, which starts with
    a goal and recursively attempts to prove it using available rules and facts. The
    implementation includes:

    - Cycle detection to prevent infinite recursion
    - Proof tracking and explanation generation
    - Probabilistic inference with confidence values
    - Caching of intermediate results
    - Support for temporal reasoning
    - Performance optimizations

    Attributes:
        proof_trace (List[Dict]): History of proof steps if tracking enabled
        max_recursion_depth (int): Maximum recursion depth for proofs
        track_proofs (bool): Whether to track proof steps
        use_temporal (bool): Whether to consider temporal constraints
        cached_proofs (Dict): Cache of previously proven goals
    """

    def __init__(
        self,
        max_recursion_depth: int = 100,
        track_proofs: bool = False,
        use_temporal: bool = False,
        use_cache: bool = True,
    ):
        """Initialize backward chaining reasoner.

        Args:
            max_recursion_depth: Maximum recursion depth for proofs
            track_proofs: Whether to track proof steps
            use_temporal: Whether to consider temporal constraints
            use_cache: Whether to cache proven goals
        """
        super().__init__()
        self.proof_trace = []
        self.max_recursion_depth = max_recursion_depth
        self.track_proofs = track_proofs
        self.use_temporal = use_temporal
        self.cached_proofs = {} if use_cache else None
        self._current_depth = 0

    def reason(self, kb: KnowledgeBase, goal: Optional[Proposition] = None) -> bool:
        """Perform backward chaining to prove goal.

        Recursively attempts to prove the goal by finding rules that can conclude it
        and proving their premises.

        Args:
            kb: Knowledge base containing facts and rules
            goal: Goal proposition to prove (optional)

        Returns:
            bool: True if goal proven, False otherwise

        Raises:
            RecursionError: If max recursion depth exceeded
            ValueError: If goal is None or invalid
        """
        if goal is None:
            raise ValueError("Backward chaining requires a goal")

        self.validate_input(kb, goal)
        self._current_depth = 0
        self.proof_trace.clear()

        return self._prove_goal(goal, kb, set())

    def _prove_goal(
        self, goal: Proposition, kb: KnowledgeBase, visited: Set[str]
    ) -> bool:
        """Internal recursive goal proving method.

        Args:
            goal: Current goal to prove
            kb: Knowledge base
            visited: Set of visited propositions for cycle detection

        Returns:
            bool: True if goal proven

        Raises:
            RecursionError: If max depth exceeded
        """
        self._current_depth += 1
        if self._current_depth > self.max_recursion_depth:
            raise RecursionError("Maximum recursion depth exceeded")

        # Check cache
        if self.cached_proofs is not None:
            cache_key = (goal.name, frozenset(visited))
            if cache_key in self.cached_proofs:
                return self.cached_proofs[cache_key]

        # Check if already known fact
        if goal.name in kb.facts:
            result = kb.facts[goal.name]
            self._track_proof_step("fact", goal, None)
            return result

        # Check temporal facts if enabled
        if self.use_temporal and goal.temporal_validity:
            result = self._check_temporal_fact(goal, kb)
            if result is not None:
                return result

        # Check for cycles
        if goal.name in visited:
            return False

        visited.add(goal.name)

        # Try to prove using rules
        for rule in self._get_relevant_rules(goal, kb):
            if self._prove_premises(rule, kb, visited.copy()):
                kb.facts[goal.name] = True
                self._track_proof_step("rule", goal, rule)

                # Cache result
                if self.cached_proofs is not None:
                    self.cached_proofs[(goal.name, frozenset(visited))] = True

                return True

        visited.remove(goal.name)
        return False

    def _prove_premises(self, rule: Rule, kb: KnowledgeBase, visited: Set[str]) -> bool:
        """Attempt to prove all premises of a rule.

        Args:
            rule: Rule whose premises to prove
            kb: Knowledge base
            visited: Set of visited propositions

        Returns:
            bool: True if all premises proven
        """
        return all(
            self._prove_goal(premise, kb, visited.copy()) for premise in rule.premises
        )

    def _get_relevant_rules(self, goal: Proposition, kb: KnowledgeBase) -> List[Rule]:
        """Get rules that could prove the goal.

        Args:
            goal: Goal to prove
            kb: Knowledge base

        Returns:
            List of relevant rules sorted by confidence
        """
        relevant = [r for r in kb.rules if r.conclusion.name == goal.name]
        return sorted(relevant, key=lambda r: r.confidence, reverse=True)

    def _check_temporal_fact(
        self, goal: Proposition, kb: KnowledgeBase
    ) -> Optional[bool]:
        """Check temporal facts for goal.

        Args:
            goal: Goal to check
            kb: Knowledge base

        Returns:
            bool or None: Fact value if found
        """
        if goal.name in kb.temporal_facts:
            facts = kb.temporal_facts[goal.name]
            current_time = time.time()
            relevant = [(v, t) for v, t in facts if t <= current_time]
            if relevant:
                return max(relevant, key=lambda x: x[1])[0]
        return None

    def _track_proof_step(
        self, step_type: str, goal: Proposition, rule: Optional[Rule]
    ) -> None:
        """Track a proof step if tracking enabled.

        Args:
            step_type: Type of proof step
            goal: Goal being proved
            rule: Rule used (if any)
        """
        if not self.track_proofs:
            return

        self.proof_trace.append(
            {
                "type": step_type,
                "goal": goal.name,
                "rule": str(rule) if rule else None,
                "depth": self._current_depth,
                "timestamp": time.time(),
            }
        )

    def get_proof_trace(self) -> List[Dict]:
        """Get the proof trace if tracking enabled.

        Returns:
            List of proof steps with details
        """
        return self.proof_trace.copy() if self.track_proofs else []

    def clear_cache(self) -> None:
        """Clear the proof cache."""
        if self.cached_proofs is not None:
            self.cached_proofs.clear()


class Resolution(ReasoningStrategy):
    """Implementation of resolution-based theorem proving using the resolution principle.

    This class implements resolution-based automated reasoning, which proves theorems by
    contradiction. It converts the knowledge base and negation of the goal into conjunctive
    normal form (CNF) and repeatedly applies the resolution rule until either a contradiction
    is found (proving the goal) or no new clauses can be derived.

    Attributes:
        max_iterations (int): Maximum number of resolution iterations (default: 1000)
        track_steps (bool): Whether to record resolution steps (default: False)
        resolution_steps (List): History of resolution steps if tracking enabled
        _clause_cache (Dict): Cache of previously resolved clause pairs

    Methods:
        reason: Main resolution proof method
        resolve: Resolves two clauses
        to_cnf: Converts propositions to CNF
        optimize_clauses: Performs clause optimization
        is_tautology: Checks if clause is a tautology
        get_proof_steps: Returns resolution proof steps
    """

    def __init__(self, max_iterations: int = 1000, track_steps: bool = False):
        """Initialize resolution prover.

        Args:
            max_iterations: Maximum resolution iterations to prevent infinite loops
            track_steps: Whether to track resolution steps for proof explanation
        """
        super().__init__()
        self.max_iterations = max_iterations
        self.track_steps = track_steps
        self.resolution_steps = []
        self._clause_cache = {}

    def reason(self, kb: KnowledgeBase, goal: Optional[Proposition] = None) -> bool:
        """Perform resolution-based theorem proving.

        Converts knowledge base and goal to CNF and applies resolution until either
        a contradiction is found or no new clauses can be derived.

        Args:
            kb: Knowledge base containing facts and rules
            goal: Goal proposition to prove (required for resolution)

        Returns:
            bool: True if goal proved by contradiction, False otherwise

        Raises:
            ValueError: If goal is None or invalid
            RecursionError: If max iterations exceeded
        """
        if goal is None:
            raise ValueError("Resolution requires a goal proposition")

        self.validate_input(kb, goal)
        self.resolution_steps.clear()
        self._clause_cache.clear()

        # Convert knowledge base and negated goal to CNF
        clauses = self._kb_to_cnf(kb)
        goal_cnf = self.to_cnf(Proposition(goal.name, not goal.value))
        clauses.add(frozenset(goal_cnf))

        # Remove tautologies and optimize initial clause set
        clauses = {c for c in clauses if not self.is_tautology(c)}
        clauses = self.optimize_clauses(clauses)

        iterations = 0
        while iterations < self.max_iterations:
            iterations += 1
            new_clauses = set()

            # Generate clause pairs efficiently
            pairs = [
                (c1, c2)
                for c1 in clauses
                for c2 in clauses
                if c1 != c2 and not self._is_cached_pair(c1, c2)
            ]

            for c1, c2 in pairs:
                resolvent = self.resolve(c1, c2)
                if resolvent is not None:
                    if not resolvent:  # Empty clause = contradiction
                        if self.track_steps:
                            self._track_step(c1, c2, resolvent)
                        return True

                    if resolvent not in clauses:
                        new_clauses.add(resolvent)
                        if self.track_steps:
                            self._track_step(c1, c2, resolvent)

            if not new_clauses or new_clauses.issubset(clauses):
                return False

            clauses.update(new_clauses)

        raise RecursionError("Maximum resolution iterations exceeded")

    def resolve(self, c1: frozenset, c2: frozenset) -> Optional[frozenset]:
        """Resolve two clauses by finding complementary literals.

        Args:
            c1: First clause as frozenset of (name, value) tuples
            c2: Second clause as frozenset of (name, value) tuples

        Returns:
            frozenset: Resolved clause, empty for contradiction, None if no resolution
        """
        for l1 in c1:
            for l2 in c2:
                if l1[0] == l2[0] and l1[1] != l2[1]:
                    resolvent = set(c1) | set(c2) - {l1, l2}
                    # Cache this resolution
                    self._cache_resolution(c1, c2)
                    return frozenset(resolvent)
        return None

    def to_cnf(self, prop: Proposition) -> Set[Tuple[str, bool]]:
        """Convert proposition to conjunctive normal form.

        Args:
            prop: Proposition to convert

        Returns:
            Set of tuples representing CNF clauses
        """
        return {(prop.name, prop.value if prop.value is not None else True)}

    def _kb_to_cnf(self, kb: KnowledgeBase) -> Set[frozenset]:
        """Convert entire knowledge base to CNF.

        Args:
            kb: Knowledge base to convert

        Returns:
            Set of clauses in CNF
        """
        clauses = set()
        # Convert facts
        for fact_name, value in kb.facts.items():
            clauses.add(frozenset([(fact_name, value)]))
        # Convert rules
        for rule in kb.rules:
            premise_clauses = [self.to_cnf(p) for p in rule.premises]
            conclusion = self.to_cnf(rule.conclusion)
            clauses.update(self._combine_clauses(premise_clauses, conclusion))
        return clauses

    def optimize_clauses(self, clauses: Set[frozenset]) -> Set[frozenset]:
        """Optimize clause set by removing subsumed clauses.

        Args:
            clauses: Set of clauses to optimize

        Returns:
            Optimized set of clauses
        """
        optimized = set()
        for c1 in clauses:
            if not any(self._subsumes(c2, c1) for c2 in clauses if c2 != c1):
                optimized.add(c1)
        return optimized

    def is_tautology(self, clause: frozenset) -> bool:
        """Check if clause is a tautology (always true).

        Args:
            clause: Clause to check

        Returns:
            bool: True if clause is a tautology
        """
        literals = list(clause)
        return any(
            l1[0] == l2[0] and l1[1] != l2[1]
            for i, l1 in enumerate(literals)
            for l2 in literals[i + 1 :]
        )

    def _subsumes(self, c1: frozenset, c2: frozenset) -> bool:
        """Check if clause c1 subsumes clause c2.

        Args:
            c1: First clause
            c2: Second clause

        Returns:
            bool: True if c1 subsumes c2
        """
        return c1 != c2 and all(lit in c2 for lit in c1)

    def _is_cached_pair(self, c1: frozenset, c2: frozenset) -> bool:
        """Check if clause pair has been previously resolved.

        Args:
            c1: First clause
            c2: Second clause

        Returns:
            bool: True if pair previously resolved
        """
        pair_key = (frozenset(c1), frozenset(c2))
        return pair_key in self._clause_cache

    def _cache_resolution(self, c1: frozenset, c2: frozenset) -> None:
        """Cache a resolved clause pair.

        Args:
            c1: First clause
            c2: Second clause
        """
        pair_key = (frozenset(c1), frozenset(c2))
        self._clause_cache[pair_key] = True

    def _track_step(self, c1: frozenset, c2: frozenset, resolvent: frozenset) -> None:
        """Record a resolution step if tracking enabled.

        Args:
            c1: First parent clause
            c2: Second parent clause
            resolvent: Resolved clause
        """
        self.resolution_steps.append(
            {
                "parent1": set(c1),
                "parent2": set(c2),
                "resolvent": set(resolvent) if resolvent else set(),
                "timestamp": time.time(),
            }
        )

    def get_proof_steps(self) -> List[Dict]:
        """Get the resolution proof steps if tracking enabled.

        Returns:
            List of resolution steps with parent clauses and resolvents
        """
        return self.resolution_steps.copy() if self.track_steps else []

    def _combine_clauses(self, premises: List[Set], conclusion: Set) -> Set[frozenset]:
        """Combine premise and conclusion clauses.

        Args:
            premises: List of premise clause sets
            conclusion: Conclusion clause set

        Returns:
            Combined set of clauses
        """
        combined = set()
        for premise in premises:
            combined.add(frozenset(premise))
        combined.add(frozenset(conclusion))
        return combined


class ModelChecking(ReasoningStrategy):
    """Implementation of model checking reasoning.

    This class implements model checking by systematically exploring all possible models
    (truth assignments) of the logical propositions in the knowledge base to verify whether
    certain properties hold. The implementation includes:

    - Efficient model generation using backtracking
    - Optimization of model search space
    - Support for temporal logic model checking
    - Incremental model checking capabilities
    - Detection of contradictions and tautologies
    - Caching of checked models for performance
    - Support for various model checking algorithms

    Attributes:
        _checked_models (Dict): Cache of previously checked models
        _contradiction_cache (Set): Cache of known contradictory assignments
        max_model_size (int): Maximum number of propositions to check
        use_incremental (bool): Whether to use incremental checking
        track_models (bool): Whether to store checked models
        validate_models (bool): Whether to validate models before checking
    """

    def __init__(
        self,
        max_model_size: int = 100,
        use_incremental: bool = True,
        track_models: bool = False,
        validate_models: bool = True,
    ):
        """Initialize model checker with configuration options.

        Args:
            max_model_size: Maximum number of propositions to check
            use_incremental: Whether to use incremental checking
            track_models: Whether to store checked models
            validate_models: Whether to validate models before checking
        """
        super().__init__()
        self._checked_models = {}
        self._contradiction_cache = set()
        self.max_model_size = max_model_size
        self.use_incremental = use_incremental
        self.track_models = track_models
        self.validate_models = validate_models

    def reason(self, kb: KnowledgeBase, goal: Optional[Proposition] = None) -> bool:
        """Perform model checking to verify properties.

        Systematically generates and checks all possible models to verify whether the goal
        proposition holds in all valid models according to the knowledge base rules.

        Args:
            kb: Knowledge base containing facts and rules
            goal: Goal proposition to verify (optional)

        Returns:
            bool: True if goal holds in all valid models, False otherwise

        Raises:
            ValueError: If number of propositions exceeds max_model_size
            RuntimeError: If contradictory models are detected
        """
        if goal is None:
            return True

        # Get all relevant propositions
        props = self._get_relevant_props(kb, goal)

        if len(props) > self.max_model_size:
            raise ValueError(f"Too many propositions to check: {len(props)}")

        # Generate and check models
        models = self._generate_models(props)
        valid_models = self._filter_valid_models(models, kb)

        # Cache results if tracking enabled
        if self.track_models:
            self._cache_models(valid_models, goal)

        return self._verify_goal(valid_models, goal)

    def _generate_models(self, props: Set[str]) -> List[Dict[str, bool]]:
        """Generate all possible truth assignments for propositions.

        Uses efficient backtracking to generate models while pruning invalid branches.

        Args:
            props: Set of proposition names to generate models for

        Returns:
            List of models as dictionaries mapping proposition names to truth values
        """

        def generate_recursive(remaining: Set[str]) -> List[Dict[str, bool]]:
            if not remaining:
                return [{}]

            prop = remaining.pop()
            sub_models = generate_recursive(remaining)
            models = []

            for model in sub_models:
                # Generate true case
                model_true = model.copy()
                model_true[prop] = True
                if self._is_valid_partial_model(model_true):
                    models.append(model_true)

                # Generate false case
                model_false = model.copy()
                model_false[prop] = False
                if self._is_valid_partial_model(model_false):
                    models.append(model_false)

            remaining.add(prop)
            return models

        return generate_recursive(props.copy())

    def _filter_valid_models(
        self, models: List[Dict[str, bool]], kb: KnowledgeBase
    ) -> List[Dict[str, bool]]:
        """Filter models to only those satisfying knowledge base rules.

        Args:
            models: List of potential models to check
            kb: Knowledge base containing rules to verify

        Returns:
            List of valid models satisfying all rules
        """
        valid_models = []
        for model in models:
            # Skip if contradictory assignment cached
            model_key = frozenset(model.items())
            if model_key in self._contradiction_cache:
                continue

            if all(self._evaluate_rule(rule, model) for rule in kb.rules):
                valid_models.append(model)
            else:
                self._contradiction_cache.add(model_key)

        return valid_models

    def _evaluate_rule(self, rule: Rule, model: Dict[str, bool]) -> bool:
        """Evaluate if a rule holds in a given model.

        Args:
            rule: Rule to evaluate
            model: Model to check rule against

        Returns:
            bool: True if rule holds in model, False otherwise
        """
        premises_true = all(model.get(p.name, False) for p in rule.premises)
        conclusion_true = model.get(rule.conclusion.name, False)

        # Rule holds if either premises false or conclusion true
        return not premises_true or conclusion_true

    def _get_relevant_props(self, kb: KnowledgeBase, goal: Proposition) -> Set[str]:
        """Get all propositions relevant to goal verification.

        Args:
            kb: Knowledge base to analyze
            goal: Goal proposition

        Returns:
            Set of relevant proposition names
        """
        props = set(kb.facts.keys()) | {goal.name}

        # Add propositions from relevant rules
        for rule in kb.rules:
            props.update(p.name for p in rule.premises)
            props.add(rule.conclusion.name)

        return props

    def _is_valid_partial_model(self, model: Dict[str, bool]) -> bool:
        """Check if partial model could lead to valid complete model.

        Args:
            model: Partial model assignment to validate

        Returns:
            bool: True if partial model could be valid
        """
        if not self.validate_models:
            return True

        # Check cached contradictions
        model_key = frozenset(model.items())
        return not any(model_key.issuperset(c) for c in self._contradiction_cache)

    def _verify_goal(
        self, valid_models: List[Dict[str, bool]], goal: Proposition
    ) -> bool:
        """Verify if goal holds in all valid models.

        Args:
            valid_models: List of valid models to check
            goal: Goal proposition to verify

        Returns:
            bool: True if goal holds in all models
        """
        if not valid_models:
            return False
        return all(model[goal.name] for model in valid_models)

    def _cache_models(self, models: List[Dict[str, bool]], goal: Proposition) -> None:
        """Cache checked models for future reference.

        Args:
            models: List of models to cache
            goal: Goal proposition the models were checked against
        """
        if not self.track_models:
            return

        cache_key = (goal.name, hash(str(models)))
        self._checked_models[cache_key] = models

    def clear_cache(self) -> None:
        """Clear all cached models and contradictions."""
        self._checked_models.clear()
        self._contradiction_cache.clear()

    def get_cached_models(self) -> Dict:
        """Get all cached models if tracking enabled.

        Returns:
            Dictionary of cached models indexed by goals
        """
        return self._checked_models.copy() if self.track_models else {}


class ConstraintSatisfaction(ReasoningStrategy):
    """Implementation of constraint satisfaction reasoning.

    This class implements constraint satisfaction problem (CSP) solving using backtracking
    search with forward checking and various optimizations. It can handle binary and n-ary
    constraints over discrete domains.

    The implementation includes:
    - Variable selection heuristics (MRV, degree)
    - Value ordering heuristics
    - Forward checking for constraint propagation
    - Conflict-directed backjumping
    - Dynamic variable ordering
    - Arc consistency (AC-3 algorithm)
    - Solution caching
    - Constraint learning

    Attributes:
        _variable_ordering (str): Heuristic for variable selection (default: 'mrv')
        _value_ordering (str): Heuristic for value ordering (default: 'lcv')
        _use_forward_checking (bool): Whether to use forward checking (default: True)
        _use_arc_consistency (bool): Whether to enforce arc consistency (default: True)
        _cached_solutions (Dict): Cache of previously found solutions
        _constraint_weights (Dict): Learned weights for constraints
        _max_backtracks (int): Maximum number of backtracks before giving up
    """

    def __init__(
        self,
        variable_ordering: str = "mrv",
        value_ordering: str = "lcv",
        use_forward_checking: bool = True,
        use_arc_consistency: bool = True,
        max_backtracks: int = 1000,
    ):
        """Initialize constraint satisfaction solver.

        Args:
            variable_ordering: Heuristic for selecting next variable ('mrv'/'degree')
            value_ordering: Heuristic for ordering values ('lcv'/'random')
            use_forward_checking: Whether to use forward checking
            use_arc_consistency: Whether to enforce arc consistency
            max_backtracks: Maximum number of backtracks before giving up
        """
        super().__init__()
        self._variable_ordering = variable_ordering
        self._value_ordering = value_ordering
        self._use_forward_checking = use_forward_checking
        self._use_arc_consistency = use_arc_consistency
        self._cached_solutions = {}
        self._constraint_weights = defaultdict(int)
        self._max_backtracks = max_backtracks
        self._num_backtracks = 0

    def reason(
        self,
        kb: KnowledgeBase,
        goal: Optional[Proposition] = None,
        constraints: Optional[List[Callable]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Solve constraint satisfaction problem.

        Finds a solution that satisfies both the knowledge base facts and additional
        constraints if provided. Uses sophisticated backtracking search with various
        optimizations.

        Args:
            kb: Knowledge base containing facts that act as constraints
            goal: Ignored for CSP (included for interface compatibility)
            constraints: Additional constraint functions to satisfy

        Returns:
            Dict mapping variables to values that satisfies all constraints, or None if no solution

        Raises:
            ValueError: If constraints are invalid
            RuntimeError: If maximum backtracks exceeded
        """
        if constraints is None:
            constraints = []

        # Initialize problem
        variables = list(kb.facts.keys())
        domains = self._initialize_domains(variables, kb)

        # Check cache
        cache_key = self._make_cache_key(variables, constraints)
        if cache_key in self._cached_solutions:
            return self._cached_solutions[cache_key]

        # Enforce initial arc consistency if enabled
        if self._use_arc_consistency:
            domains = self._enforce_arc_consistency(domains, constraints)
            if any(not domain for domain in domains.values()):
                return None

        # Solve CSP
        self._num_backtracks = 0
        solution = self._backtrack_search({}, variables, domains, constraints)

        # Cache solution
        self._cached_solutions[cache_key] = solution
        return solution

    def _initialize_domains(
        self, variables: List[str], kb: KnowledgeBase
    ) -> Dict[str, List[Any]]:
        """Initialize variable domains from knowledge base.

        Args:
            variables: List of variable names
            kb: Knowledge base with domain information

        Returns:
            Dict mapping variables to their domains
        """
        domains = {}
        for var in variables:
            if var in kb.facts:
                domains[var] = [kb.facts[var]]  # Fixed value from KB
            else:
                domains[var] = [True, False]  # Binary domain
        return domains

    def _backtrack_search(
        self,
        assignment: Dict[str, Any],
        variables: List[str],
        domains: Dict[str, List[Any]],
        constraints: List[Callable],
    ) -> Optional[Dict[str, Any]]:
        """Perform backtracking search with forward checking.

        Args:
            assignment: Current partial assignment
            variables: Remaining unassigned variables
            domains: Current domains for all variables
            constraints: Constraints to satisfy

        Returns:
            Complete valid assignment or None if no solution
        """
        if len(assignment) == len(variables):
            return assignment

        # Check backtrack limit
        if self._num_backtracks >= self._max_backtracks:
            raise RuntimeError("Maximum number of backtracks exceeded")

        # Select unassigned variable using heuristic
        var = self._select_unassigned_variable(assignment, domains)

        # Try values in heuristic order
        for value in self._order_domain_values(var, assignment, domains):
            if self._is_consistent(assignment, var, value, constraints):
                assignment[var] = value

                # Forward checking
                if self._use_forward_checking:
                    saved_domains = self._forward_check(
                        var, value, assignment, domains.copy(), constraints
                    )
                    if saved_domains is not None:
                        result = self._backtrack_search(
                            assignment, variables, saved_domains, constraints
                        )
                        if result is not None:
                            return result
                else:
                    result = self._backtrack_search(
                        assignment, variables, domains, constraints
                    )
                    if result is not None:
                        return result

                del assignment[var]
                self._num_backtracks += 1

        return None

    def _select_unassigned_variable(
        self, assignment: Dict[str, Any], domains: Dict[str, List[Any]]
    ) -> str:
        """Select next unassigned variable using specified heuristic.

        Args:
            assignment: Current partial assignment
            domains: Current variable domains

        Returns:
            Name of selected unassigned variable
        """
        unassigned = [v for v in domains if v not in assignment]

        if self._variable_ordering == "mrv":
            # Minimum remaining values
            return min(unassigned, key=lambda v: len(domains[v]))
        elif self._variable_ordering == "degree":
            # Maximum degree (most constraints)
            return max(unassigned, key=lambda v: self._constraint_weights[v])
        else:
            # Default to first unassigned
            return unassigned[0]

    def _order_domain_values(
        self, var: str, assignment: Dict[str, Any], domains: Dict[str, List[Any]]
    ) -> List[Any]:
        """Order domain values using specified heuristic.

        Args:
            var: Variable whose domain to order
            assignment: Current partial assignment
            domains: Current variable domains

        Returns:
            Ordered list of domain values to try
        """
        if self._value_ordering == "lcv":
            # Least constraining value
            return sorted(
                domains[var], key=lambda v: self._count_conflicts(var, v, assignment)
            )
        elif self._value_ordering == "random":
            values = list(domains[var])
            random.shuffle(values)
            return values
        else:
            return domains[var]

    def _is_consistent(
        self,
        assignment: Dict[str, Any],
        var: str,
        value: Any,
        constraints: List[Callable],
    ) -> bool:
        """Check if assignment with new value is consistent.

        Args:
            assignment: Current partial assignment
            var: Variable to assign
            value: Value to assign
            constraints: Constraints to check

        Returns:
            True if assignment remains consistent with new value
        """
        assignment = assignment.copy()
        assignment[var] = value
        return all(constraint(assignment) for constraint in constraints)

    def _forward_check(
        self,
        var: str,
        value: Any,
        assignment: Dict[str, Any],
        domains: Dict[str, List[Any]],
        constraints: List[Callable],
    ) -> Optional[Dict[str, List[Any]]]:
        """Perform forward checking after assignment.

        Args:
            var: Recently assigned variable
            value: Assigned value
            assignment: Current partial assignment
            domains: Current variable domains
            constraints: Problem constraints

        Returns:
            Updated domains if consistent, None if inconsistency found
        """
        assignment = assignment.copy()
        assignment[var] = value

        for other_var in domains:
            if other_var not in assignment:
                new_domain = []
                for other_value in domains[other_var]:
                    assignment[other_var] = other_value
                    if all(constraint(assignment) for constraint in constraints):
                        new_domain.append(other_value)
                    del assignment[other_var]

                if not new_domain:
                    return None
                domains[other_var] = new_domain

        return domains

    def _enforce_arc_consistency(
        self, domains: Dict[str, List[Any]], constraints: List[Callable]
    ) -> Dict[str, List[Any]]:
        """Enforce arc consistency using AC-3 algorithm.

        Args:
            domains: Initial variable domains
            constraints: Problem constraints

        Returns:
            Arc consistent domains
        """

        def revise(var1: str, var2: str) -> bool:
            """Revise domain of var1 with respect to var2."""
            revised = False
            for val1 in domains[var1][:]:
                assignment = {var1: val1}
                if not any(
                    self._is_consistent(assignment, var2, val2, constraints)
                    for val2 in domains[var2]
                ):
                    domains[var1].remove(val1)
                    revised = True
            return revised

        queue = [(var1, var2) for var1 in domains for var2 in domains if var1 != var2]
        while queue:
            var1, var2 = queue.pop(0)
            if revise(var1, var2):
                if not domains[var1]:
                    return domains
                queue.extend(
                    (var3, var1) for var3 in domains if var3 != var1 and var3 != var2
                )
        return domains

    def _make_cache_key(
        self, variables: List[str], constraints: List[Callable]
    ) -> Tuple:
        """Create cache key from problem specification.

        Args:
            variables: Problem variables
            constraints: Problem constraints

        Returns:
            Tuple that uniquely identifies problem instance
        """
        return (tuple(sorted(variables)), tuple(hash(str(c)) for c in constraints))

    def _count_conflicts(self, var: str, value: Any, assignment: Dict[str, Any]) -> int:
        """Count number of conflicts value would cause.

        Args:
            var: Variable to assign
            value: Value to assign
            assignment: Current partial assignment

        Returns:
            Number of conflicts assignment would cause
        """
        conflicts = 0
        assignment = assignment.copy()
        assignment[var] = value

        for other_var in assignment:
            if other_var != var:
                self._constraint_weights[(var, other_var)] += 1
                conflicts += self._constraint_weights[(var, other_var)]

        return conflicts

    def clear_cache(self) -> None:
        """Clear solution cache and learned constraint weights."""
        self._cached_solutions.clear()
        self._constraint_weights.clear()


class InductiveReasoning(ReasoningStrategy):
    """Implementation of inductive reasoning to discover patterns and generate rules from examples.

    This class implements inductive learning algorithms to find patterns in training examples
    and generate logical rules that explain the observed patterns. It supports:

    - Pattern discovery across multiple examples using frequent pattern mining
    - Rule generation from discovered patterns with lift and leverage metrics
    - Confidence scoring and pruning of generated rules
    - Minimum support thresholds with dynamic adjustment
    - Pattern filtering using statistical significance tests
    - Incremental pattern learning with sliding windows
    - Rule validation against knowledge base constraints
    - Pattern generalization and specialization
    - Feature selection and dimensionality reduction
    - Multi-threaded pattern mining
    - Caching and memoization optimizations
    - Optimized memory usage with numpy arrays
    - GPU acceleration for large example sets
    - Anomaly detection in pattern discovery
    - Advanced statistical validation tests
    - Dynamic feature engineering
    - Early stopping with convergence detection
    - Pattern mining optimization hints
    - Cross-validation for rule evaluation
    - Progressive sampling for large datasets
    - Advanced pruning strategies
    - Online learning capabilities
    - Support for hierarchical patterns
    - Missing value handling
    - Robust error handling

    Attributes:
        min_support (float): Minimum fraction of examples that must match a pattern (0-1)
        min_confidence (float): Minimum confidence threshold for generated rules (0-1)
        max_pattern_size (int): Maximum number of attributes in discovered patterns
        significance_level (float): P-value threshold for pattern significance
        max_rules (int): Maximum number of rules to generate
        use_lift (bool): Whether to use lift metric for rule evaluation
        sliding_window (int): Window size for incremental learning
        num_threads (int): Number of threads for parallel pattern mining
        use_gpu (bool): Whether to use GPU acceleration
        early_stopping_patience (int): Number of iterations without improvement before stopping
        validation_split (float): Fraction of data to use for validation
        max_missing_pct (float): Maximum percent of missing values allowed
        _pattern_cache (Dict): Cache of previously discovered patterns
        _rule_cache (Dict): Cache of previously generated rules
        _feature_weights (Dict): Weights for feature importance
        _validation_scores (List): History of validation scores
        _feature_stats (Dict): Statistics about features
        _anomaly_scores (Dict): Anomaly scores for patterns
        _optimization_hints (Dict): Hints for pattern mining optimization
        _online_state (Dict): State for online learning
        _error_handlers (Dict): Custom error handlers by error type
    """

    def __init__(
        self,
        min_support: float = 0.3,
        min_confidence: float = 0.7,
        max_pattern_size: int = 10,
        significance_level: float = 0.05,
        max_rules: int = 1000,
        use_lift: bool = True,
        sliding_window: int = 100,
        num_threads: int = 4,
        use_gpu: bool = False,
        early_stopping_patience: int = 5,
        validation_split: float = 0.2,
        max_missing_pct: float = 0.1,
    ):
        """Initialize the inductive reasoner.

        Args:
            min_support: Minimum support threshold for patterns (default: 0.3)
            min_confidence: Minimum confidence for rules (default: 0.7)
            max_pattern_size: Maximum pattern size (default: 10)
            significance_level: P-value threshold for patterns (default: 0.05)
            max_rules: Maximum number of rules to generate (default: 1000)
            use_lift: Whether to use lift metric (default: True)
            sliding_window: Window size for incremental learning (default: 100)
            num_threads: Number of threads for parallel mining (default: 4)
            use_gpu: Whether to use GPU acceleration (default: False)
            early_stopping_patience: Patience for early stopping (default: 5)
            validation_split: Validation split ratio (default: 0.2)
            max_missing_pct: Maximum missing value percent (default: 0.1)
        """
        super().__init__()
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.max_pattern_size = max_pattern_size
        self.significance_level = significance_level
        self.max_rules = max_rules
        self.use_lift = use_lift
        self.sliding_window = sliding_window
        self.num_threads = num_threads
        self.use_gpu = use_gpu
        self.early_stopping_patience = early_stopping_patience
        self.validation_split = validation_split
        self.max_missing_pct = max_missing_pct

        self._pattern_cache = {}
        self._rule_cache = {}
        self._feature_weights = {}
        self._validation_scores = []
        self._feature_stats = {}
        self._anomaly_scores = {}
        self._optimization_hints = {}
        self._online_state = {"examples_seen": 0, "last_update": None}
        self._error_handlers = {}

    def reason(
        self,
        kb: KnowledgeBase,
        goal: Optional[Proposition] = None,
        examples: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Rule]:
        """Perform inductive reasoning to generate rules from examples.

        Discovers patterns in the provided examples and generates logical rules that
        explain the observed patterns while satisfying minimum support and confidence
        thresholds. Uses parallel processing for large example sets.

        Args:
            kb: Knowledge base for validating generated rules
            goal: Target attribute to learn rules for (optional)
            examples: Training examples to learn from

        Returns:
            List[Rule]: Generated rules with associated confidence scores

        Raises:
            ValueError: If examples is None or empty
            ValueError: If min_support or min_confidence are invalid
            ValueError: If validation split is invalid
            RuntimeError: If parallel processing fails
            RuntimeError: If GPU acceleration fails
            RuntimeError: If early stopping criteria not met
        """
        try:
            # Input validation
            if not examples:
                raise ValueError("Examples required for inductive reasoning")

            if not 0 <= self.min_support <= 1:
                raise ValueError("min_support must be between 0 and 1")

            if not 0 <= self.min_confidence <= 1:
                raise ValueError("min_confidence must be between 0 and 1")

            if not 0 <= self.validation_split < 1:
                raise ValueError("validation_split must be between 0 and 1")

            # Check pattern cache
            cache_key = self._make_cache_key(examples, goal)
            if cache_key in self._pattern_cache:
                return self._rule_cache[cache_key]

            # Handle missing values
            examples = self._handle_missing_values(examples)

            # Initialize feature weights and stats
            self._compute_feature_stats(examples)
            if not self._feature_weights:
                self._compute_feature_weights(examples)

            # Split validation set if needed
            if self.validation_split > 0:
                train_examples, val_examples = self._split_validation(examples)
            else:
                train_examples, val_examples = examples, []

            # Use GPU if enabled and available
            if self.use_gpu and self._check_gpu_available():
                patterns = self._gpu_pattern_discovery(train_examples)
            # Use sliding window for large datasets
            elif len(train_examples) > self.sliding_window:
                patterns = self._incremental_pattern_discovery(train_examples)
            # Use parallel processing
            else:
                patterns = self._parallel_pattern_discovery(train_examples)

            # Filter and validate patterns
            patterns = self._filter_patterns(patterns, train_examples)
            patterns = self._validate_significance(patterns, train_examples)
            patterns = self._detect_anomalies(patterns)

            # Generate and optimize rules
            rules = self._generate_rules(patterns, train_examples, goal)
            rules = self._prune_rules(rules)
            rules = self._validate_rules(rules, kb)

            # Evaluate on validation set if available
            if val_examples:
                rules = self._validate_on_holdout(rules, val_examples)

            # Early stopping check
            if not self._check_early_stopping(rules):
                raise RuntimeError("Failed to converge - early stopping")

            # Limit number of rules
            rules = self._select_top_rules(rules)

            # Update online state
            self._update_online_state(examples)

            # Cache results
            self._pattern_cache[cache_key] = patterns
            self._rule_cache[cache_key] = rules

            return rules

        except Exception as e:
            # Use custom error handler if available
            if type(e) in self._error_handlers:
                return self._error_handlers[type(e)](e)
            raise

    def _count_matches(
        self, pattern: Dict[str, Any], examples: List[Dict[str, Any]]
    ) -> int:
        """Count number of examples that match a pattern.

        Args:
            pattern: Pattern to match
            examples: Examples to check against

        Returns:
            int: Number of matching examples
        """
        matches = 0
        for example in examples:
            if all(example.get(k) == v for k, v in pattern.items()):
                matches += 1
        return matches

    def _is_subsumed(
        self, pattern: Dict[str, Any], patterns: List[Dict[str, Any]]
    ) -> bool:
        """Check if pattern is subsumed by any existing pattern.

        Args:
            pattern: Pattern to check
            patterns: List of existing patterns

        Returns:
            bool: True if pattern is subsumed
        """
        pattern_items = set(pattern.items())
        return any(
            pattern_items.issubset(set(p.items())) for p in patterns if p != pattern
        )

    def _parallel_pattern_discovery(
        self, examples: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Discover patterns using parallel processing.

        Args:
            examples: Training examples to analyze

        Returns:
            List[Dict[str, Any]]: Discovered patterns

        Raises:
            RuntimeError: If parallel processing fails
            MemoryError: If insufficient memory
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import numpy as np

        # Convert to numpy arrays for efficiency
        example_array = np.array([list(ex.values()) for ex in examples])
        chunk_size = max(1, len(examples) // self.num_threads)
        chunks = np.array_split(example_array, self.num_threads)

        patterns = []
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            future_to_chunk = {
                executor.submit(self._discover_patterns, chunk): chunk
                for chunk in chunks
            }

            for future in as_completed(future_to_chunk):
                try:
                    chunk_patterns = future.result()
                    patterns.extend(chunk_patterns)
                except Exception as e:
                    raise RuntimeError(f"Pattern discovery failed: {e}")

        return patterns

    def _incremental_pattern_discovery(
        self, examples: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Discover patterns incrementally using sliding window.

        Uses progressive sampling to handle large datasets efficiently.

        Args:
            examples: Training examples to analyze

        Returns:
            List[Dict[str, Any]]: Discovered patterns
        """
        patterns = []
        window_size = self.sliding_window

        # Progressive sampling
        while window_size <= len(examples):
            window = examples[:window_size]
            window_patterns = self._discover_patterns(window)
            patterns = self._merge_pattern_sets(patterns, window_patterns)

            # Check convergence
            if self._check_pattern_convergence(patterns):
                break

            window_size *= 2

        return patterns

    def _merge_pattern_sets(
        self, patterns1: List[Dict[str, Any]], patterns2: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Merge two sets of patterns, removing duplicates and checking for subsumption.

        Args:
            patterns1: First set of patterns
            patterns2: Second set of patterns

        Returns:
            List[Dict[str, Any]]: Merged unique patterns
        """
        merged = patterns1.copy()
        seen = {str(p) for p in patterns1}

        for pattern in patterns2:
            pattern_str = str(pattern)
            if pattern_str not in seen and not self._is_subsumed(pattern, merged):
                merged.append(pattern)
                seen.add(pattern_str)

        return merged

    def _compute_feature_weights(self, examples: List[Dict[str, Any]]) -> None:
        """Compute feature importance weights using information gain.

        Args:
            examples: Training examples to analyze
        """
        from collections import Counter
        import numpy as np

        # Count feature frequencies
        feature_counts = Counter()
        for example in examples:
            feature_counts.update(example.keys())

        # Compute information gain for each feature
        total_examples = len(examples)
        for feature, count in feature_counts.items():
            # Information gain calculation
            prob = count / total_examples
            info_gain = -prob * np.log2(prob)
            self._feature_weights[feature] = info_gain

    def _validate_significance(
        self, patterns: List[Dict[str, Any]], examples: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter patterns using multiple statistical significance tests.

        Args:
            patterns: Patterns to validate
            examples: Examples to test against

        Returns:
            List[Dict[str, Any]]: Statistically significant patterns
        """
        from scipy import stats
        import numpy as np

        significant_patterns = []
        for pattern in patterns:
            # Chi-square test
            observed = self._count_matches(pattern, examples)
            expected = len(examples) * self.min_support
            chi2, p_chi2 = stats.chisquare([observed], [expected])

            # Fisher exact test for small samples
            if observed < 5:
                _, p_fisher = stats.fisher_exact(
                    [
                        [observed, len(examples) - observed],
                        [expected, len(examples) - expected],
                    ]
                )
                p_value = p_fisher
            else:
                p_value = p_chi2

            # Multiple testing correction
            if p_value < self.significance_level / len(
                patterns
            ):  # Bonferroni correction
                significant_patterns.append(pattern)

        return significant_patterns

    def _detect_anomalies(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect and filter anomalous patterns using statistical methods.

        Args:
            patterns: Patterns to check for anomalies

        Returns:
            List[Dict[str, Any]]: Filtered patterns with anomaly scores
        """
        import numpy as np
        from scipy import stats

        # Calculate pattern statistics
        pattern_stats = []
        for pattern in patterns:
            stats_dict = {
                "size": len(pattern),
                "support": self._pattern_cache.get(str(pattern), {}).get("support", 0),
                "confidence": self._pattern_cache.get(str(pattern), {}).get(
                    "confidence", 0
                ),
            }
            pattern_stats.append(stats_dict)

        # Calculate z-scores
        pattern_stats = np.array(
            [(s["size"], s["support"], s["confidence"]) for s in pattern_stats]
        )
        z_scores = stats.zscore(pattern_stats)

        # Filter anomalies
        filtered_patterns = []
        for i, pattern in enumerate(patterns):
            if np.all(np.abs(z_scores[i]) < 3):  # Keep if not anomalous
                self._anomaly_scores[str(pattern)] = float(np.mean(np.abs(z_scores[i])))
                filtered_patterns.append(pattern)

        return filtered_patterns

    def _handle_missing_values(
        self, examples: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Handle missing values in examples using imputation.

        Args:
            examples: Examples with possible missing values

        Returns:
            List[Dict[str, Any]]: Examples with imputed values

        Raises:
            ValueError: If too many missing values
        """
        import numpy as np

        # Count missing values
        missing_counts = {}
        for example in examples:
            for key, value in example.items():
                if value is None:
                    missing_counts[key] = missing_counts.get(key, 0) + 1

        # Check threshold
        for key, count in missing_counts.items():
            if count / len(examples) > self.max_missing_pct:
                raise ValueError(f"Too many missing values for feature {key}")

        # Impute missing values
        imputed = []
        for example in examples:
            imputed_example = {}
            for key, value in example.items():
                if value is None:
                    # Use mode for categorical, mean for numeric
                    values = [ex[key] for ex in examples if ex[key] is not None]
                    if all(isinstance(v, (int, float)) for v in values):
                        imputed_example[key] = float(np.mean(values))
                    else:
                        from statistics import mode

                        imputed_example[key] = mode(values)
                else:
                    imputed_example[key] = value
            imputed.append(imputed_example)

        return imputed

    def _compute_feature_stats(self, examples: List[Dict[str, Any]]) -> None:
        """Compute statistical summaries of features.

        Args:
            examples: Examples to analyze
        """
        import numpy as np
        from scipy import stats

        for feature in examples[0].keys():
            values = [ex[feature] for ex in examples if feature in ex]

            if all(isinstance(v, (int, float)) for v in values):
                self._feature_stats[feature] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "skew": stats.skew(values),
                    "kurtosis": stats.kurtosis(values),
                }
            else:
                unique_vals = set(values)
                self._feature_stats[feature] = {
                    "unique_count": len(unique_vals),
                    "mode": max(set(values), key=values.count),
                    "entropy": stats.entropy(
                        list(values.count(v) for v in unique_vals)
                    ),
                }

    def _check_pattern_convergence(self, patterns: List[Dict[str, Any]]) -> bool:
        """Check if pattern discovery has converged.

        Args:
            patterns: Current set of patterns

        Returns:
            bool: True if converged
        """
        if len(self._validation_scores) < 2:
            return False

        # Check relative improvement
        improvement = self._validation_scores[-1] - self._validation_scores[-2]
        if improvement < 1e-6:  # Convergence threshold
            return True

        return False

    def _update_online_state(self, new_examples: List[Dict[str, Any]]) -> None:
        """Update state for online learning.

        Args:
            new_examples: New examples to incorporate
        """
        import time

        self._online_state["examples_seen"] += len(new_examples)
        self._online_state["last_update"] = time.time()

        # Update feature statistics incrementally
        self._compute_feature_stats(new_examples)

    def _check_gpu_available(self) -> bool:
        """Check if GPU acceleration is available.

        Returns:
            bool: True if GPU available
        """
        try:
            import cupy

            return True
        except ImportError:
            return False

    def _split_validation(
        self, examples: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Split examples into training and validation sets.

        Args:
            examples: Examples to split

        Returns:
            Tuple containing training and validation sets
        """
        import numpy as np

        idx = int(len(examples) * (1 - self.validation_split))
        return examples[:idx], examples[idx:]

    def _validate_on_holdout(
        self, rules: List[Rule], val_examples: List[Dict[str, Any]]
    ) -> List[Rule]:
        """Validate rules on holdout set.

        Args:
            rules: Rules to validate
            val_examples: Validation examples

        Returns:
            List[Rule]: Validated rules
        """
        validated_rules = []
        for rule in rules:
            val_confidence = self._calculate_confidence(rule, val_examples)
            if val_confidence >= self.min_confidence:
                rule.confidence = (rule.confidence + val_confidence) / 2
                validated_rules.append(rule)

        return validated_rules

    def _check_early_stopping(self, rules: List[Rule]) -> bool:
        """Check early stopping criteria.

        Args:
            rules: Current set of rules

        Returns:
            bool: True if should continue, False if should stop
        """
        if not rules:
            return False

        # Calculate validation score
        avg_confidence = sum(r.confidence for r in rules) / len(rules)
        self._validation_scores.append(avg_confidence)

        # Check patience
        if len(self._validation_scores) <= self.early_stopping_patience:
            return True

        # Check if no improvement for patience iterations
        recent_scores = self._validation_scores[-self.early_stopping_patience :]
        if all(s <= recent_scores[0] for s in recent_scores[1:]):
            return False

        return True

    def register_error_handler(
        self, error_type: Type[Exception], handler: Callable[[Exception], List[Rule]]
    ) -> None:
        """Register custom error handler.

        Args:
            error_type: Type of error to handle
            handler: Error handling function
        """
        self._error_handlers[error_type] = handler


class AbductiveReasoning(ReasoningStrategy):
    """Implementation of abductive reasoning for inferring most plausible explanations.

    This class implements abductive reasoning to find and rank plausible explanations for
    observed phenomena. It uses various inference strategies and ranking metrics including:

    - Multiple explanation generation from knowledge base rules
    - Consistency checking with known facts
    - Ranking based on simplicity, relevance, and plausibility metrics
    - Caching of previously generated explanations
    - Pruning of redundant or contradictory explanations
    - Support for probabilistic and weighted explanations

    Attributes:
        max_explanations (int): Maximum number of explanations to generate
        min_relevance (float): Minimum relevance score threshold (0-1)
        use_weights (bool): Whether to use weighted ranking
        _cache (Dict): Cache of previously generated explanations
        _weights (Dict): Weights for ranking metrics
    """

    def __init__(
        self,
        max_explanations: int = 10,
        min_relevance: float = 0.5,
        use_weights: bool = True,
    ):
        """Initialize abductive reasoner.

        Args:
            max_explanations: Maximum explanations to generate (default: 10)
            min_relevance: Minimum relevance score (default: 0.5)
            use_weights: Whether to use weighted ranking (default: True)
        """
        super().__init__()
        self.max_explanations = max_explanations
        self.min_relevance = min_relevance
        self.use_weights = use_weights
        self._cache = {}
        self._weights = {"simplicity": 0.4, "relevance": 0.3, "consistency": 0.3}

    def reason(
        self, kb: KnowledgeBase, goal: Optional[Proposition] = None
    ) -> List[Set[Proposition]]:
        """Generate ranked explanations for observation using abductive reasoning.

        Finds and ranks plausible explanations using knowledge base rules and facts,
        pruning explanations that fail consistency or relevance criteria.

        Args:
            kb: Knowledge base containing facts and rules
            goal: Observation to explain (goal used for consistency with interface)

        Returns:
            Ranked list of explanation sets, where each set contains propositions
            that could explain the goal

        Raises:
            ValueError: If goal is None or invalid
        """
        if goal is None:
            raise ValueError("Abductive reasoning requires an observation")

        # Check cache
        cache_key = (goal.name, hash(str(kb.facts)))
        if cache_key in self._cache:
            return self._cache[cache_key]

        explanations = []
        covered_premises = set()

        # Generate candidate explanations
        for rule in kb.rules:
            if rule.conclusion.name == goal.name:
                explanation = set()

                # Add premises not in facts as explanations
                for premise in rule.premises:
                    if premise.name not in kb.facts:
                        if not self._contradicts_facts(premise, kb):
                            explanation.add(premise)
                            covered_premises.add(premise.name)

                if explanation and not self._is_redundant(explanation, explanations):
                    explanations.append(explanation)

        # Prune and rank explanations
        explanations = self._prune_explanations(explanations, kb)
        ranked = self._rank_explanations(explanations, kb, goal)

        # Cache results
        self._cache[cache_key] = ranked[: self.max_explanations]

        return ranked[: self.max_explanations]

    def _rank_explanations(
        self, explanations: List[Set[Proposition]], kb: KnowledgeBase, goal: Proposition
    ) -> List[Set[Proposition]]:
        """Rank explanations using configured metrics and weights.

        Args:
            explanations: Candidate explanations to rank
            kb: Knowledge base for context
            goal: Observation being explained

        Returns:
            Ranked list of explanations
        """
        if not self.use_weights:
            # Simple ranking by size
            return sorted(explanations, key=len)

        scored_explanations = []
        for exp in explanations:
            score = (
                self._weights["simplicity"] * self._simplicity_score(exp)
                + self._weights["relevance"] * self._relevance_score(exp, goal)
                + self._weights["consistency"] * self._consistency_score(exp, kb)
            )
            scored_explanations.append((exp, score))

        return [
            e for e, s in sorted(scored_explanations, key=lambda x: x[1], reverse=True)
        ]

    def _simplicity_score(self, explanation: Set[Proposition]) -> float:
        """Calculate simplicity score based on number of propositions.

        Args:
            explanation: Explanation to score

        Returns:
            Score between 0 and 1, higher for simpler explanations
        """
        return 1.0 / (1 + len(explanation))

    def _relevance_score(
        self, explanation: Set[Proposition], goal: Proposition
    ) -> float:
        """Calculate relevance score to goal observation.

        Args:
            explanation: Explanation to score
            goal: Target observation

        Returns:
            Score between 0 and 1 based on relevance
        """
        relevance = sum(1 for p in explanation if self._props_related(p, goal))
        return relevance / len(explanation) if explanation else 0

    def _consistency_score(
        self, explanation: Set[Proposition], kb: KnowledgeBase
    ) -> float:
        """Calculate consistency score with knowledge base.

        Args:
            explanation: Explanation to score
            kb: Knowledge base to check against

        Returns:
            Score between 0 and 1 based on consistency
        """
        inconsistencies = sum(1 for p in explanation if self._contradicts_facts(p, kb))
        return 1.0 - (inconsistencies / len(explanation) if explanation else 0)

    def _props_related(self, prop1: Proposition, prop2: Proposition) -> bool:
        """Check if two propositions are related.

        Args:
            prop1: First proposition
            prop2: Second proposition

        Returns:
            True if propositions share attributes/relations
        """
        return (
            prop1.name in prop2.name
            or prop2.name in prop1.name
            or any(w in prop2.name for w in prop1.name.split("_"))
        )

    def _contradicts_facts(self, prop: Proposition, kb: KnowledgeBase) -> bool:
        """Check if proposition contradicts knowledge base facts.

        Args:
            prop: Proposition to check
            kb: Knowledge base to validate against

        Returns:
            True if contradiction found
        """
        return prop.name in kb.facts and kb.facts[prop.name] != prop.value

    def _is_redundant(
        self, explanation: Set[Proposition], existing: List[Set[Proposition]]
    ) -> bool:
        """Check if explanation is redundant with existing ones.

        Args:
            explanation: Candidate explanation
            existing: Existing explanation set

        Returns:
            True if explanation is redundant
        """
        return any(explanation.issubset(e) or e.issubset(explanation) for e in existing)

    def _prune_explanations(
        self, explanations: List[Set[Proposition]], kb: KnowledgeBase
    ) -> List[Set[Proposition]]:
        """Prune explanations below relevance threshold.

        Args:
            explanations: Explanations to prune
            kb: Knowledge base for context

        Returns:
            Pruned list of explanations
        """
        pruned = []
        for exp in explanations:
            score = self._relevance_score(exp, kb)
            if score >= self.min_relevance:
                pruned.append(exp)
        return pruned

    def clear_cache(self) -> None:
        """Clear the explanation cache."""
        self._cache.clear()


class AnalogicalReasoning(ReasoningStrategy):
    """Implementation of analogical reasoning to solve problems by drawing parallels between similar situations.

    This class implements analogical reasoning through:
    - Case similarity computation using multiple metrics
    - Knowledge transfer between similar cases
    - Weighting of different similarity components
    - Hierarchical case matching
    - Adaptation rules for transferred knowledge
    - Storage of successful analogies
    - Validation of analogical inferences

    Attributes:
        similarity_threshold (float): Minimum similarity score to transfer knowledge (0-1)
        feature_weights (Dict[str, float]): Weights for different case features
        adaptation_rules (List[Callable]): Rules for adapting transferred knowledge
        successful_analogies (Dict): Cache of successful analogical transfers
        max_candidates (int): Maximum number of source cases to compare
        _case_clusters (Dict): Hierarchical clustering of stored cases
    """

    def __init__(
        self,
        similarity_threshold: float = 0.7,
        use_feature_weights: bool = True,
        max_candidates: int = 100,
    ):
        """Initialize analogical reasoner.

        Args:
            similarity_threshold: Minimum similarity for knowledge transfer
            use_feature_weights: Whether to weight features in similarity
            max_candidates: Maximum source cases to compare
        """
        super().__init__()
        self.similarity_threshold = similarity_threshold
        self.feature_weights = {}
        self.adaptation_rules = []
        self.successful_analogies = {}
        self.max_candidates = max_candidates
        self._case_clusters = {}
        self._initialize_weights()

    def reason(
        self,
        kb: KnowledgeBase,
        goal: Optional[Proposition] = None,
        target_case: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Find and apply analogies to target case.

        Identifies most similar source cases from knowledge base and transfers
        relevant knowledge while adapting it to the target context.

        Args:
            kb: Knowledge base containing source cases
            goal: Unused, included for interface compatibility
            target_case: Case to find analogies for

        Returns:
            Dictionary of new knowledge inferred through analogy

        Raises:
            ValueError: If target_case is None or kb has no cases
        """
        if target_case is None:
            raise ValueError("Target case required for analogical reasoning")

        if not kb.cases:
            raise ValueError("Knowledge base contains no source cases")

        # Find best matching source cases
        matches = self._find_matches(kb.cases, target_case)

        if not matches:
            return {}

        # Transfer and adapt knowledge from best match
        best_match = matches[0]
        if self.compute_similarity(best_match, target_case) > self.similarity_threshold:
            new_knowledge = self.transfer_knowledge(best_match, target_case)
            adapted = self._adapt_knowledge(new_knowledge, best_match, target_case)

            # Cache successful analogy
            if adapted:
                self._cache_analogy(best_match, target_case, adapted)

            return adapted

        return {}

    def compute_similarity(self, case1: Dict[str, Any], case2: Dict[str, Any]) -> float:
        """Compute similarity score between two cases.

        Calculates weighted similarity across shared attributes and structure.

        Args:
            case1: First case to compare
            case2: Second case to compare

        Returns:
            Similarity score between 0 and 1
        """
        common_attrs = set(case1.keys()) & set(case2.keys())
        if not common_attrs:
            return 0.0

        similarity = 0.0
        total_weight = 0.0

        for attr in common_attrs:
            weight = self.feature_weights.get(attr, 1.0)
            if case1[attr] == case2[attr]:
                similarity += weight
            total_weight += weight

        return similarity / total_weight if total_weight > 0 else 0.0

    def transfer_knowledge(
        self, source: Dict[str, Any], target: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transfer relevant knowledge from source to target case.

        Identifies and transfers knowledge from source case that is missing in
        target case while considering relevance and applicability.

        Args:
            source: Source case to transfer from
            target: Target case to transfer to

        Returns:
            Dictionary of transferred knowledge
        """
        new_knowledge = {}
        relevant_keys = self._identify_relevant_keys(source, target)

        for key in relevant_keys:
            if key not in target and self._is_transferable(key, source, target):
                new_knowledge[key] = source[key]

        return new_knowledge

    def add_adaptation_rule(
        self, rule: Callable[[Dict[str, Any], Dict[str, Any], Any], Any]
    ) -> None:
        """Add rule for adapting transferred knowledge.

        Args:
            rule: Function taking (source, target, value) and returning adapted value
        """
        self.adaptation_rules.append(rule)

    def _initialize_weights(self) -> None:
        """Initialize default feature weights."""
        self.feature_weights = {
            "type": 2.0,
            "category": 1.5,
            "attributes": 1.0,
            "relations": 1.8,
        }

    def _find_matches(
        self, cases: List[Dict[str, Any]], target: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find best matching source cases.

        Args:
            cases: Available source cases
            target: Target case to match

        Returns:
            List of cases sorted by similarity to target
        """
        candidates = cases[: self.max_candidates]  # Limit search space
        scored = [(case, self.compute_similarity(case, target)) for case in candidates]
        return [
            case for case, score in sorted(scored, key=lambda x: x[1], reverse=True)
        ]

    def _identify_relevant_keys(
        self, source: Dict[str, Any], target: Dict[str, Any]
    ) -> Set[str]:
        """Identify relevant attributes for transfer.

        Args:
            source: Source case
            target: Target case

        Returns:
            Set of relevant attribute names
        """
        # Start with attributes sharing same type/category
        relevant = set()
        for key in source:
            if key in target and isinstance(source[key], type(target.get(key))):
                relevant.add(key)
            elif self._is_related_attribute(key, target):
                relevant.add(key)
        return relevant

    def _is_transferable(
        self, key: str, source: Dict[str, Any], target: Dict[str, Any]
    ) -> bool:
        """Check if attribute is transferable to target.

        Args:
            key: Attribute name to check
            source: Source case
            target: Target case

        Returns:
            True if attribute can be transferred
        """
        # Check for type compatibility and constraints
        if key in target:
            return False

        source_type = type(source[key])
        target_types = [type(v) for v in target.values()]

        return source_type in target_types or self._has_adaptation_rule(
            source_type, target_types
        )

    def _adapt_knowledge(
        self, knowledge: Dict[str, Any], source: Dict[str, Any], target: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt transferred knowledge to target context.

        Args:
            knowledge: Knowledge to adapt
            source: Source case
            target: Target case

        Returns:
            Dictionary of adapted knowledge
        """
        adapted = {}
        for key, value in knowledge.items():
            adapted_value = value
            for rule in self.adaptation_rules:
                adapted_value = rule(source, target, adapted_value)
            adapted[key] = adapted_value
        return adapted

    def _cache_analogy(
        self, source: Dict[str, Any], target: Dict[str, Any], result: Dict[str, Any]
    ) -> None:
        """Cache successful analogical transfer.

        Args:
            source: Source case used
            target: Target case
            result: Successful transfer result
        """
        cache_key = (frozenset(source.items()), frozenset(target.items()))
        self.successful_analogies[cache_key] = result

    def _is_related_attribute(self, key: str, target: Dict[str, Any]) -> bool:
        """Check if attribute is semantically related to target.

        Args:
            key: Attribute name to check
            target: Target case

        Returns:
            True if attribute is related
        """
        # Check for semantic relationships in attribute names
        target_keys = set(target.keys())
        key_parts = key.split("_")
        return any(
            part in tkey or tkey in part for part in key_parts for tkey in target_keys
        )

    def _has_adaptation_rule(self, source_type: type, target_types: List[type]) -> bool:
        """Check if adaptation rule exists for types.

        Args:
            source_type: Type to adapt from
            target_types: Possible target types

        Returns:
            True if compatible adaptation rule exists
        """
        return any(
            rule.__annotations__.get("return") in target_types
            for rule in self.adaptation_rules
        )


class NonMonotonicReasoning(ReasoningStrategy):
    """Implementation of non-monotonic reasoning with defeasible rules and belief revision.

    This class implements non-monotonic reasoning by handling defeasible rules that can be
    defeated by exceptions, and supporting belief revision when new contradictory information
    is encountered. Key features include:

    - Defeasible rule handling with prioritized exceptions
    - Belief revision through truth maintenance
    - Assumption-based reasoning
    - Default logic with specificity preferences
    - Rule prioritization and conflict resolution
    - Caching of non-monotonic conclusions
    - Support for multiple conflicting defaults

    Attributes:
        _assumption_cache (Dict): Cache of assumptions and their dependencies
        _belief_cache (Dict): Cache of derived beliefs
        _default_priorities (Dict): Priority ordering for default rules
        _max_revision_depth (int): Maximum depth for belief revision
        _enable_caching (bool): Whether to cache derived conclusions
    """

    def __init__(self, max_revision_depth: int = 10, enable_caching: bool = True):
        """Initialize non-monotonic reasoner.

        Args:
            max_revision_depth: Maximum recursion depth for belief revision
            enable_caching: Whether to cache derived conclusions and assumptions
        """
        super().__init__()
        self._assumption_cache = {}
        self._belief_cache = {}
        self._default_priorities = {}
        self._max_revision_depth = max_revision_depth
        self._enable_caching = enable_caching

    def reason(self, kb: KnowledgeBase, goal: Optional[Proposition] = None) -> bool:
        """Perform non-monotonic reasoning to determine if goal proposition holds.

        Uses defeasible rules and exceptions to perform reasoning that can retract
        conclusions when contradictory information is encountered. Handles multiple
        layers of exceptions and belief revision.

        Args:
            kb: Knowledge base containing facts and defeasible rules
            goal: Query proposition to determine truth value of

        Returns:
            bool: True if goal can be proven non-monotonically, False otherwise

        Raises:
            ValueError: If goal is None
            RuntimeError: If belief revision exceeds maximum depth
        """
        if goal is None:
            raise ValueError("Goal proposition required for non-monotonic reasoning")

        # Check belief cache
        if self._enable_caching:
            cache_key = (goal.name, hash(str(kb.facts)))
            if cache_key in self._belief_cache:
                return self._belief_cache[cache_key]

        # Track current belief state
        current_facts = kb.facts.copy()
        belief_depth = 0

        while belief_depth < self._max_revision_depth:
            # Apply defeasible rules in priority order
            changes = False
            for rule, exceptions in sorted(
                kb.defeasible_rules, key=lambda x: self._get_rule_priority(x[0])
            ):

                # Skip if any exceptions currently hold
                if self._check_exceptions(exceptions, current_facts):
                    continue

                # Check if rule premises are satisfied
                if self._check_premises(rule.premises, current_facts):
                    # Don't override existing contradictory facts
                    if (
                        rule.conclusion.name not in current_facts
                        or current_facts[rule.conclusion.name] != rule.conclusion.value
                    ):
                        current_facts[rule.conclusion.name] = rule.conclusion.value
                        changes = True

                        # Record assumptions used
                        if self._enable_caching:
                            self._record_assumption(rule, exceptions)

            # If no changes made, we've reached a fixed point
            if not changes:
                break

            belief_depth += 1

        if belief_depth >= self._max_revision_depth:
            raise RuntimeError("Maximum belief revision depth exceeded")

        # Cache and return result
        result = current_facts.get(goal.name, False)
        if self._enable_caching:
            self._belief_cache[cache_key] = result

        return result

    def _check_exceptions(
        self, exceptions: Set[Proposition], facts: Dict[str, bool]
    ) -> bool:
        """Check if any exceptions currently hold in facts.

        Args:
            exceptions: Set of exception propositions to check
            facts: Current fact dictionary

        Returns:
            bool: True if any exception holds
        """
        return any(
            exc.name in facts and facts[exc.name] == exc.value for exc in exceptions
        )

    def _check_premises(
        self, premises: List[Proposition], facts: Dict[str, bool]
    ) -> bool:
        """Check if all rule premises are satisfied.

        Args:
            premises: List of premise propositions
            facts: Current fact dictionary

        Returns:
            bool: True if all premises hold
        """
        return all(p.name in facts and facts[p.name] == p.value for p in premises)

    def _get_rule_priority(self, rule: Rule) -> int:
        """Get priority level for rule.

        Args:
            rule: Rule to get priority for

        Returns:
            int: Priority level, higher is more specific
        """
        return self._default_priorities.get(rule, 0)

    def _record_assumption(self, rule: Rule, exceptions: Set[Proposition]) -> None:
        """Record rule assumptions and dependencies.

        Args:
            rule: Rule being applied
            exceptions: Associated exceptions
        """
        key = (rule.conclusion.name, rule.conclusion.value)
        self._assumption_cache[key] = {"rule": rule, "exceptions": exceptions}

    def set_rule_priority(self, rule: Rule, priority: int) -> None:
        """Set priority level for a defeasible rule.

        Args:
            rule: Rule to set priority for
            priority: Priority level (higher is more specific)
        """
        self._default_priorities[rule] = priority

    def clear_caches(self) -> None:
        """Clear assumption and belief caches."""
        self._assumption_cache.clear()
        self._belief_cache.clear()

    def get_assumptions(self, proposition: Proposition) -> Optional[Dict]:
        """Get assumptions used to derive proposition.

        Args:
            proposition: Proposition to get assumptions for

        Returns:
            Dict containing rule and exceptions used, or None if not cached
        """
        key = (proposition.name, proposition.value)
        return self._assumption_cache.get(key)


class ProbabilisticReasoning(ReasoningStrategy):
    """Implementation of probabilistic reasoning using Bayesian networks and chain rules.

    This class implements probabilistic inference through:
    - Direct probability lookup for known facts
    - Chain rule decomposition for complex queries
    - Bayesian network inference for causal relationships
    - Conditional probability calculations
    - Noisy-OR gates for multiple causes
    - Prior probability handling
    - Joint probability factoring
    - Likelihood weighting
    - Markov blanket reasoning

    Attributes:
        cache (Dict): Cache of computed probabilities
        epsilon (float): Small constant for avoiding zero probabilities
        max_depth (int): Maximum recursion depth for chain rule
        use_markov_blanket (bool): Whether to use Markov blanket optimization
        _default_prior (float): Default prior probability for unknown facts
    """

    def __init__(
        self,
        epsilon: float = 1e-10,
        max_depth: int = 100,
        use_markov_blanket: bool = True,
        default_prior: float = 0.5,
    ):
        """Initialize probabilistic reasoner.

        Args:
            epsilon: Small constant to avoid zero probabilities
            max_depth: Maximum recursion depth for chain rule
            use_markov_blanket: Whether to use Markov blanket optimization
            default_prior: Default prior probability for unknown facts
        """
        super().__init__()
        self.cache = {}
        self.epsilon = epsilon
        self.max_depth = max_depth
        self.use_markov_blanket = use_markov_blanket
        self._default_prior = default_prior
        self._depth = 0

    def reason(self, kb: KnowledgeBase, goal: Optional[Proposition] = None) -> float:
        """Compute probability of query proposition using probabilistic inference.

        Uses Bayesian network structure implied by rules to calculate probability,
        applying chain rule decomposition for complex queries.

        Args:
            kb: Knowledge base containing facts and rules
            goal: Query proposition to compute probability for

        Returns:
            float: Computed probability between 0 and 1

        Raises:
            ValueError: If goal is None
            RecursionError: If max recursion depth exceeded
        """
        if goal is None:
            raise ValueError("Query proposition required for probabilistic reasoning")

        # Check cache
        cache_key = (goal.name, hash(str(kb.facts)))
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Check recursion depth
        self._depth += 1
        if self._depth > self.max_depth:
            self._depth = 0
            raise RecursionError("Maximum recursion depth exceeded")

        try:
            # Direct probability if known
            if goal.name in kb.probabilistic_facts:
                return kb.probabilistic_facts[goal.name].probability

            # Calculate using chain rule
            probability = self._chain_rule(kb, goal)

            # Cache result
            self.cache[cache_key] = probability
            return probability

        finally:
            self._depth -= 1

    def _chain_rule(self, kb: KnowledgeBase, query: Proposition) -> float:
        """Apply chain rule to calculate probability.

        Args:
            kb: Knowledge base
            query: Query proposition

        Returns:
            float: Computed probability
        """
        probability = 0
        relevant_rules = self._get_relevant_rules(kb, query)

        if not relevant_rules:
            return self._default_prior

        for rule in relevant_rules:
            if self.use_markov_blanket:
                prob = self._markov_blanket_probability(kb, rule, query)
            else:
                prob = self._rule_probability(kb, rule)
            probability = self._noisy_or(probability, prob)

        return min(1.0, probability)

    def _rule_probability(self, kb: KnowledgeBase, rule: Rule) -> float:
        """Calculate probability for single rule using chain rule.

        Args:
            kb: Knowledge base
            rule: Rule to evaluate

        Returns:
            float: Rule probability
        """
        premise_prob = 1.0
        for premise in rule.premises:
            prob = self.reason(kb, premise)
            premise_prob *= max(prob, self.epsilon)
        return premise_prob * rule.confidence

    def _get_relevant_rules(self, kb: KnowledgeBase, query: Proposition) -> List[Rule]:
        """Get rules relevant to query proposition.

        Args:
            kb: Knowledge base
            query: Query proposition

        Returns:
            List of relevant rules
        """
        return [r for r in kb.rules if r.conclusion.name == query.name]

    def _markov_blanket_probability(
        self, kb: KnowledgeBase, rule: Rule, query: Proposition
    ) -> float:
        """Calculate probability using Markov blanket optimization.

        Args:
            kb: Knowledge base
            rule: Rule to evaluate
            query: Query proposition

        Returns:
            float: Computed probability
        """
        blanket_nodes = self._get_markov_blanket(kb, query)
        prob = 1.0
        for node in blanket_nodes:
            if node in rule.premises:
                prob *= self.reason(kb, node)
        return prob * rule.confidence

    def _get_markov_blanket(
        self, kb: KnowledgeBase, query: Proposition
    ) -> Set[Proposition]:
        """Get Markov blanket nodes for query.

        Args:
            kb: Knowledge base
            query: Query proposition

        Returns:
            Set of propositions in Markov blanket
        """
        blanket = set()
        for rule in kb.rules:
            if query.name == rule.conclusion.name:
                blanket.update(rule.premises)
            elif query in rule.premises:
                blanket.add(rule.conclusion)
                blanket.update(p for p in rule.premises if p != query)
        return blanket

    def _noisy_or(self, p1: float, p2: float) -> float:
        """Combine probabilities using noisy-OR.

        Args:
            p1: First probability
            p2: Second probability

        Returns:
            Combined probability
        """
        return p1 + p2 - (p1 * p2)

    def clear_cache(self) -> None:
        """Clear the probability cache."""
        self.cache.clear()


class TextAnalyzer:
    """Analyzes text documents to extract propositions and rules for automated reasoning with human input.

    Uses advanced NLP techniques for comprehensive text analysis and knowledge extraction:

    - Named Entity Recognition (NER) with state-of-the-art transformers models
    - Enhanced dependency parsing with advanced syntactic pattern matching
    - Semantic role labeling with PropBank/VerbNet integration
    - Neural coreference resolution for entity tracking
    - Causal relationship extraction with semantic graph analysis
    - Sophisticated temporal reasoning with interval algebra
    - Multilingual sentiment analysis with aspect-based breakdown
    - Negation scope detection with polarity propagation
    - RST-based discourse parsing for coherence analysis
    - Neural event extraction with temporal ordering
    - Frame semantic parsing for deeper semantics
    - Abstract meaning representation for logical forms
    - Common sense reasoning integration
    - Uncertainty quantification for extracted knowledge
    - Statistical significance testing for patterns
    - Human-in-the-loop knowledge refinement and validation
    - Interactive query and analysis guidance
    - Expert input for domain knowledge integration
    - Collaborative knowledge base construction
    - Human validation of extracted rules
    - Customizable analysis focus and depth
    - Integration of human expert insights
    - Complex multi-hop query processing
    - Active learning from human feedback
    - Progressive knowledge refinement

    Attributes:
        nlp (spacy.Language): Spacy language model for core NLP
        ner_pipeline (transformers.Pipeline): Named entity recognition pipeline
        qa_pipeline (transformers.Pipeline): Question answering pipeline
        sentiment_analyzer (transformers.Pipeline): Sentiment analysis model
        temporal_analyzer (transformers.Pipeline): Temporal relationship analyzer
        coref_resolver (transformers.Pipeline): Coreference resolution model
        frame_parser (transformers.Pipeline): Frame semantic parser
        discourse_parser (transformers.Pipeline): RST discourse parser
        certainty_classifier (transformers.Pipeline): Uncertainty classifier
        _cache (cachetools.LRUCache): Cache of analyzed documents
        _stats (defaultdict): Processing statistics dictionary
        _confidence_thresholds (dict): Confidence thresholds by extraction type
        _models (dict): Model configurations dictionary
        _user_feedback (dict): Feedback and corrections from users
        _expert_rules (dict): Domain rules provided by experts
        _analysis_focus (dict): User-specified focus areas
        _interaction_history (list): History of user interactions
    """

    def __init__(
        self,
        use_gpu: bool = False,
        cache_size: int = 1000,
        models: Optional[Dict[str, str]] = None,
        experts: Optional[List[str]] = None,
        focus_areas: Optional[Dict[str, float]] = None,
    ):
        """Initialize text analyzer with configurable NLP models and human input options.

        Args:
            use_gpu: Whether to use GPU acceleration
            cache_size: Maximum number of documents to cache
            models: Optional custom model configurations
            experts: List of domain expert identifiers
            focus_areas: Knowledge extraction focus weights

        Raises:
            ValueError: If invalid configuration
            RuntimeError: If models fail to load
        """
        import cachetools
        from collections import defaultdict
        import time
        import torch
        from fastcoref import spacy_component
        import spacy

        # Determine device and dtype
        if use_gpu:
            if torch.backends.mps.is_available():
                device = 'mps'
                dtype = torch.float32  # Force float32 for MPS
            elif torch.cuda.is_available():
                device = 'cuda'
                dtype = torch.float32  # Use float32 for consistency
            else:
                device = 'cpu'
                dtype = torch.float32
        else:
            device = 'cpu'
            dtype = torch.float32

        # Core setup
        self._device = device
        self._dtype = dtype

        self._cache = cachetools.LRUCache(maxsize=cache_size)
        self._stats = defaultdict(int)
        self._models = models or {}
        self._confidence_thresholds = {
            "entity": 0.8,
            "relation": 0.7,
            "temporal": 0.75,
            "causal": 0.8,
            "sentiment": 0.7,
            "certainty": 0.8,
        }

        # Human interaction setup
        self._user_feedback = defaultdict(list)
        self._expert_rules = {}
        self._analysis_focus = focus_areas or {
            "entities": 1.0,
            "relations": 1.0,
            "temporal": 1.0,
            "causal": 1.0,
        }
        self._interaction_history = []


        try:
            # Load core NLP models
            self.nlp = spacy.load(self._models.get("core", "en_core_web_trf"))
            self.nlp.add_pipe("fastcoref")

            # Initialize NLP pipelines with updated models
            self.ner_pipeline = pipeline(
                "ner",
                device=device,
                model=self._models.get("ner", "dslim/bert-base-NER"),
            )

            self.qa_pipeline = pipeline(
                "question-answering",
                device=device,
                model=self._models.get("qa", "distilbert-base-cased-distilled-squad"),
            )

            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                device=device,
                model=self._models.get("sentiment", "distilbert-base-uncased-finetuned-sst-2-english"),
            )

            self.temporal_analyzer = pipeline(
                "text-classification",
                device=device,
                model=self._models.get("temporal", "satyaalmasian/temporal_tagger_bert2bert"),
            )

            # Initialize the FastCoref model ()
            self.coref_resolver = FCoref(
                device=device
            )


            # semantic role labeling (SRL) capabilities
            self.frame_parser = pipeline(
                "token-classification", # "semantic-parsing",
                device=device,
                aggregation_strategy="simple",
                model=self._models.get("frames", "liaad/srl-en_xlmr-large"),
            )

            self.discourse_parser = pipeline(
                "text-classification",
                device=device,
                model=self._models.get("discourse", "ynie/roberta-large-snli_mnli_fever_anli_R1_R2_R3-nli"),
            )

            self.certainty_classifier = pipeline(
                "text-classification",
                device=device,
                model=self._models.get("certainty", "ynie/roberta-large-snli_mnli_fever_anli_R1_R2_R3-nli"),
            )


            # Initialize NLTK resources
            nltk_resources = [
                "punkt",
                "averaged_perceptron_tagger",
                "maxent_ne_chunker",
                "words",
                "framenet_v17",
                "propbank",
                "verbnet",
            ]
            for resource in nltk_resources:
                nltk.download(resource, quiet=True)

            # Load expert rules if provided
            if experts:
                self._load_expert_rules(experts)

        except Exception as e:
            raise RuntimeError(f"Failed to initialize NLP models: {str(e)}")

    def _get_subjects(self, root_token) -> List[spacy.tokens.Token]:
        """Get subject tokens from dependency parse.

        Args:
            root_token: Root token of dependency subtree

        Returns:
            List of subject tokens
        """
        subjects = []
        for token in root_token.lefts:
            if "subj" in token.dep_:
                subjects.append(token)
                # Add compound subjects
                subjects.extend(self._get_compounds(token))
        return subjects

    def _get_objects(self, root_token) -> List[spacy.tokens.Token]:
        """Get object tokens from dependency parse.

        Args:
            root_token: Root token of dependency subtree

        Returns:
            List of object tokens
        """
        objects = []
        for token in root_token.rights:
            if "obj" in token.dep_:
                objects.append(token)
                # Add compound objects
                objects.extend(self._get_compounds(token))
        return objects

    def _get_compounds(self, token) -> List[spacy.tokens.Token]:
        """Get compound tokens that modify the given token.

        Args:
            token: Token to find compounds for

        Returns:
            List of compound modifier tokens
        """
        compounds = []
        for child in token.children:
            if child.dep_ == "compound":
                compounds.append(child)
        return compounds

    def _get_semantic_roles(self, sent) -> Dict[str, List[Dict[str, Any]]]:
        """Extract semantic roles from sentence.

        Args:
            sent: spaCy sentence

        Returns:
            Dictionary mapping predicates to their semantic arguments
        """
        roles = defaultdict(list)

        # Use semantic role labeler
        pred_args = self.frame_parser(sent.text)

        for pred in pred_args:
            pred_text = pred["predicate"]
            roles[pred_text] = [
                {
                    "role": arg["role"],
                    "text": arg["text"],
                    "confidence": arg["confidence"],
                }
                for arg in pred["arguments"]
            ]

        return dict(roles)

    def _get_events(self, doc) -> List[Proposition]:
        """Extract events from document.

        Args:
            doc: Processed spaCy document

        Returns:
            List of event propositions
        """
        events = []

        for sent in doc.sents:
            # Get verbal events
            for token in sent:
                if token.pos_ == "VERB":
                    event = Proposition(name=f"event_{token.lemma_}", confidence=0.8)
                    event.metadata["type"] = "verbal"
                    event.metadata["time"] = self._get_event_time(token)
                    events.append(event)

            # Get nominalized events
            for ent in sent.ents:
                if ent.label_ in ["EVENT", "ACTION"]:
                    event = Proposition(name=f"event_{ent.root.lemma_}", confidence=0.7)
                    event.metadata["type"] = "nominal"
                    event.metadata["time"] = self._get_event_time(ent.root)
                    events.append(event)

        return events

    def _detect_domain(self, sent) -> str:
        """Detect domain of text using keywords and NLP.

        Args:
            sent: Input sentence

        Returns:
            str: Detected domain
        """
        # Domain keywords
        domains = {
            "science": ["experiment", "hypothesis", "theory", "scientific"],
            "medical": ["patient", "diagnosis", "treatment", "symptoms"],
            "legal": ["law", "court", "legal", "judge", "attorney"],
            "business": ["market", "company", "revenue", "profit"],
            "technology": ["software", "computer", "algorithm", "data"],
        }

        text = sent.text.lower()

        # Check domain keywords
        for domain, keywords in domains.items():
            if any(keyword in text for keyword in keywords):
                return domain

        # Use text classification if no keywords match
        try:
            classification = self.qa_pipeline(
                question="What domain is this text from?", context=text
            )
            return classification["answer"].lower()
        except:
            return "general"

    def _get_event_time(self, token) -> Optional[int]:
        """Extract time information from event token.

        Args:
            token: Token containing event

        Returns:
            Optional[int]: Timestamp if found
        """
        # Check for explicit time expressions
        for child in token.children:
            if child.dep_ in ["tmod", "npadvmod"]:
                try:
                    return self._parse_time_expression(child)
                except:
                    pass

        # Use document creation time as default
        return getattr(token.doc._, "creation_time", None)

    def _create_frame_propositions(self, frame: Dict[str, Any]) -> List[Proposition]:
        """Create propositions from semantic frame.

        Args:
            frame: Semantic frame dictionary

        Returns:
            List[Proposition]: Created propositions
        """
        propositions = []

        # Create proposition for frame itself
        frame_prop = Proposition(f"frame_{frame['name']}")
        frame_prop.confidence = frame.get("score", 0.8)
        propositions.append(frame_prop)

        # Create propositions for frame elements
        for element in frame.get("frame_elements", []):
            element_prop = Proposition(
                f"{frame['name']}_{element['role']}_{element['text']}"
            )
            element_prop.confidence = element.get("confidence", 0.7)
            propositions.append(element_prop)

        return propositions

    def _extract_entities(self, doc) -> List[Proposition]:
        """Extract named entities as propositions.

        Args:
            doc: Processed spaCy document

        Returns:
            List[Proposition]: Entity propositions
        """
        propositions = []

        # Extract named entities
        for ent in doc.ents:
            prop = Proposition(f"entity_{ent.label_}_{ent.text}")
            prop.confidence = 0.9  # High confidence for NER
            prop.metadata.update(
                {
                    "type": ent.label_,
                    "text": ent.text,
                    "start": ent.start_char,
                    "end": ent.end_char,
                }
            )
            propositions.append(prop)

        # Extract noun phrases
        for np in doc.noun_chunks:
            if not any(np.start_char == ent.start_char for ent in doc.ents):
                prop = Proposition(f"np_{np.text}")
                prop.confidence = 0.7
                prop.metadata["type"] = "noun_phrase"
                propositions.append(prop)

        return propositions

    def _extract_logical_rules(
        self, doc, propositions: List[Proposition]
    ) -> List[Rule]:
        """Extract logical rules from text.

        Args:
            doc: Processed document
            propositions: Available propositions

        Returns:
            List[Rule]: Extracted rules
        """
        rules = []

        for sent in doc.sents:
            # Look for if-then patterns
            if any(token.text.lower() in ["if", "when", "whenever"] for token in sent):
                antecedent, consequent = self._split_conditional(sent)
                if antecedent and consequent:
                    # Create rule
                    premise_props = self._text_to_propositions(antecedent)
                    conclusion_props = self._text_to_propositions(consequent)

                    if premise_props and conclusion_props:
                        rule = Rule(
                            premises=premise_props,
                            conclusion=conclusion_props[0],
                            confidence=0.8,
                        )
                        rules.append(rule)

        return rules

    def _extract_causal_relations(
        self, doc, propositions: List[Proposition]
    ) -> List[Rule]:
        """Extract causal relationships as rules.

        Args:
            doc: Processed document
            propositions: Available propositions

        Returns:
            List[Rule]: Causal rules
        """
        rules = []

        causal_markers = ["because", "causes", "leads to", "results in"]

        for sent in doc.sents:
            for marker in causal_markers:
                if marker in sent.text.lower():
                    cause, effect = self._split_causal(sent, marker)
                    if cause and effect:
                        cause_props = self._text_to_propositions(cause)
                        effect_props = self._text_to_propositions(effect)

                        if cause_props and effect_props:
                            rule = Rule(
                                premises=cause_props,
                                conclusion=effect_props[0],
                                confidence=0.75,
                            )
                            rules.append(rule)

        return rules

    def _apply_expert_rules(self, rules: List[Rule]) -> List[Rule]:
        """Apply expert-provided rules to enhance reasoning.

        Args:
            rules: Current rule set

        Returns:
            List[Rule]: Enhanced rules
        """
        enhanced_rules = rules.copy()

        # Add domain-specific expert rules
        for expert_id, expert_kb in self._expert_rules.items():
            for rule_data in expert_kb.get("rules", []):
                rule = Rule(
                    premises=[Proposition(p) for p in rule_data["premises"]],
                    conclusion=Proposition(rule_data["conclusion"]),
                    confidence=rule_data.get("confidence", 0.9),
                )
                rule.source = f"expert_{expert_id}"
                enhanced_rules.append(rule)

        return enhanced_rules

    def _generate_explanation(
        self, propositions: List[Proposition], rules: List[Rule]
    ) -> Dict[str, Any]:
        """Generate human-readable explanation of analysis results.

        Args:
            propositions: Extracted propositions
            rules: Extracted rules

        Returns:
            Dict containing explanation sections
        """
        return {
            "propositions": [
                {
                    "text": str(prop),
                    "confidence": prop.confidence,
                    "type": "fact",
                    "metadata": prop.metadata,
                }
                for prop in propositions
            ],
            "rules": [
                {
                    "text": str(rule),
                    "confidence": rule.confidence,
                    "premises": len(rule.premises),
                    "source": getattr(rule, "source", "analysis"),
                }
                for rule in rules
            ],
            "summary": f"Extracted {len(propositions)} propositions and {len(rules)} rules",
            "confidence": {
                "average": (
                    sum(p.confidence for p in propositions) / len(propositions)
                    if propositions
                    else 0
                ),
                "range": (
                    min(p.confidence for p in propositions) if propositions else 0,
                    max(p.confidence for p in propositions) if propositions else 0,
                ),
            },
        }

    def _modify_propositions(
        self, propositions: List[Proposition], feedback: Dict[str, Any]
    ) -> List[Proposition]:
        """Modify propositions based on user feedback.

        Args:
            propositions: Current propositions
            feedback: User feedback dictionary

        Returns:
            List[Proposition]: Modified propositions
        """
        modified = propositions.copy()

        for prop_name, updates in feedback.items():
            for prop in modified:
                if prop.name == prop_name:
                    # Update value if provided
                    if "value" in updates:
                        prop.value = updates["value"]

                    # Update confidence if provided
                    if "confidence" in updates:
                        prop.confidence = updates["confidence"]

                    # Update metadata if provided
                    if "metadata" in updates:
                        prop.metadata.update(updates["metadata"])

        return modified

    def _modify_rules(self, rules: List[Rule], feedback: Dict[str, Any]) -> List[Rule]:
        """Modify rules based on user feedback.

        Args:
            rules: Current rules
            feedback: User feedback dictionary

        Returns:
            List[Rule]: Modified rules
        """
        modified = rules.copy()

        for rule_id, updates in feedback.items():
            for rule in modified:
                if str(rule) == rule_id:
                    # Update confidence if provided
                    if "confidence" in updates:
                        rule.confidence = updates["confidence"]

                    # Update premises if provided
                    if "premises" in updates:
                        rule.premises = [Proposition(p) for p in updates["premises"]]

                    # Update conclusion if provided
                    if "conclusion" in updates:
                        rule.conclusion = Proposition(updates["conclusion"])

                    # Update metadata if provided
                    if "metadata" in updates:
                        rule.metadata.update(updates["metadata"])

        return modified

    def _check_temporal_order(self, event1: Proposition, event2: Proposition) -> bool:
        """Check if events are in temporal order.

        Args:
            event1: First event
            event2: Second event

        Returns:
            True if event1 precedes event2
        """
        # Get event times
        time1 = event1.metadata.get("time")
        time2 = event2.metadata.get("time")

        if time1 and time2:
            return time1 < time2

        # Check temporal markers
        text = f"{event1.name} {event2.name}"
        temporal = self.temporal_analyzer(text)
        return temporal[0]["label"] == "BEFORE"

    def _check_causal_relation(self, event1: Proposition, event2: Proposition) -> bool:
        """Check if events have causal relationship.

        Args:
            event1: Potential cause event
            event2: Potential effect event

        Returns:
            True if causal relationship detected
        """
        # Check explicit causal markers
        causal_markers = ["because", "due to", "leads to", "causes"]
        text = f"{event1.name} {event2.name}"

        if any(marker in text.lower() for marker in causal_markers):
            return True

        # Use causal classifier
        result = self.qa_pipeline(question="Does event 1 cause event 2?", context=text)
        return result["score"] > 0.7

    def _get_conceptnet_relations(self, text: str) -> List[Dict[str, Any]]:
        """Query ConceptNet for relations involving text.

        Args:
            text: Text to query for

        Returns:
            List of relation dictionaries with weights
        """
        import requests

        # Query ConceptNet API
        url = f"http://api.conceptnet.io/c/en/{text}"
        response = requests.get(url).json()

        relations = []
        for edge in response["edges"]:
            relations.append(
                {
                    "rel": edge["rel"]["label"],
                    "target": edge["end"]["label"],
                    "weight": edge["weight"],
                }
            )

        return relations

    def _get_assumptions(self, sent) -> List[str]:
        """Get default assumptions that apply to sentence.

        Args:
            sent: Input sentence

        Returns:
            List of assumption strings
        """
        assumptions = []

        # Check for generic statements
        if any(tok.tag_ == "NNS" for tok in sent):
            assumptions.append("statement_applies_generally")

        # Check for conditionals
        if any(tok.dep_ == "mark" for tok in sent):
            assumptions.append("conditional_relationship")

        # Add domain assumptions
        domain = self._detect_domain(sent)
        if domain in self._expert_rules:
            assumptions.extend(self._expert_rules[domain].get("assumptions", []))

        return assumptions

    def _load_expert_kb(self, expert_id: str) -> Dict[str, Any]:
        """Load expert knowledge base.

        Args:
            expert_id: ID of expert knowledge base

        Returns:
            Dictionary containing expert rules and metadata

        Raises:
            FileNotFoundError: If KB file not found
        """
        import json

        kb_path = f"expert_kb/{expert_id}.json"
        try:
            with open(kb_path) as f:
                kb_data = json.load(f)

            # Validate KB structure
            required_keys = ["rules", "assumptions", "metadata"]
            if not all(key in kb_data for key in required_keys):
                raise ValueError(f"Invalid KB structure for expert {expert_id}")

            return kb_data

        except FileNotFoundError:
            raise FileNotFoundError(f"Expert KB not found: {kb_path}")

    def analyze_document(
        self,
        text: str,
        extract_rules: bool = True,
        use_cache: bool = True,
        confidence_threshold: float = 0.7,
        user_feedback: Optional[Dict[str, Any]] = None,
        focus: Optional[Dict[str, float]] = None,
        explain: bool = False,
    ) -> Dict[str, Any]:
        """Analyze document to extract propositions and rules with user guidance.

        Performs comprehensive NLP analysis to extract knowledge with optional human input:
        - Named entities and relationships with confidence scores
        - Enhanced syntactic dependencies and patterns
        - Rich semantic roles and frame elements
        - Sophisticated temporal/causal relationships
        - Multi-aspect sentiment analysis
        - Complex event chains and sequences
        - Multi-level discourse structure
        - Human validation and refinement
        - Expert knowledge integration
        - Interactive focus adjustment
        - Explanation generation

        Args:
            text: Input text document
            extract_rules: Whether to extract logical rules
            use_cache: Whether to use document cache
            confidence_threshold: Minimum confidence
            user_feedback: Optional user feedback/corrections
            focus: Optional analysis focus weights
            explain: Generate explanations

        Returns:
             Dict containing:
                 - propositions: List[Proposition] - Extracted propositions
                 - rules: List[Rule] - Extracted rules
                 - confidence: float - Overall confidence
                 - metadata: Dict[str, Any] - Analysis metadata
                 - explanation: Optional[Dict[str, Any]] - Generated explanation if requested
                 - evidence: List[Dict[str, Any]] - Supporting evidence

        Raises:
            ValueError: If text is invalid
            RuntimeError: If analysis fails
        """
        if not text or not text.strip():
            raise ValueError("Empty or invalid text")

        # Update analysis focus if provided
        if focus:
            self._analysis_focus.update(focus)

        # Check cache
        cache_key = hash(text)
        if use_cache and cache_key in self._cache:
            cached_result = self._cache[cache_key]
            if user_feedback:
                # Refine cached result with feedback
                cached_result = self._apply_feedback(cached_result, user_feedback)
            return cached_result

        self._stats["documents_processed"] += 1
        start = time.perf_counter()

        try:
            # Core NLP processing
            doc = self.nlp(text)
            # predictions = self.nlp.predict(texts=[text])
            doc_coref = self.coref_resolver.predict(text)

            # Update doc with coreference resolution doc._.coref_clusters
            # for cluster in doc_coref[0].get_clusters(): #["clusters"]:
            for cluster in doc._.coref_clusters:
                for mention in cluster[1:]:
                    doc[mention["start"] : mention["end"]]._.coref = doc[
                        cluster[0]["start"] : cluster[0]["end"]
                    ]

            # Extract propositions with guidance
            propositions = []
            propositions.extend(self._extract_propositions(doc))
            if self._analysis_focus["entities"] > 0:
                propositions.extend(self._extract_entities(doc))
            propositions.extend(self._extract_semantic_propositions(doc))
            if self._analysis_focus["temporal"] > 0:
                propositions.extend(self._extract_event_chain_propositions(doc))
            propositions.extend(self._extract_common_sense_propositions(doc))

            # Apply user feedback to propositions
            if user_feedback:
                propositions = self._apply_feedback(propositions, user_feedback)

            # Filter by confidence
            propositions = [
                p for p in propositions if p.confidence >= confidence_threshold
            ]

            # Extract rules if requested
            rules = []
            if extract_rules:
                if self._analysis_focus.get("rules", 1.0) > 0:
                    rules.extend(self._extract_logical_rules(doc, propositions))
                if self._analysis_focus["temporal"] > 0:
                    rules.extend(self._extract_rich_temporal_rules(doc, propositions))
                if self._analysis_focus["causal"] > 0:
                    rules.extend(self._extract_causal_relations(doc, propositions))
                rules.extend(self._extract_logical_entailment_rules(doc, propositions))
                rules.extend(self._extract_discourse_rules(doc, propositions))

                # Integrate expert rules
                rules.extend(self._apply_expert_rules(rules))

                # Filter rules by confidence
                rules = [r for r in rules if r.confidence >= confidence_threshold]

            # Generate explanations if requested
            explanation = None
            if explain:
                explanation = self._generate_explanation(propositions, rules)

            # Update cache and stats
            if use_cache:
                self._cache[cache_key] = (propositions, rules)

            elapsed = time.perf_counter() - start
            self._stats["processing_time"] += int(elapsed * 1000)

            # Record interaction
            self._interaction_history.append(
                {
                    "type": "analysis",
                    "text_length": len(text),
                    "num_propositions": len(propositions),
                    "num_rules": len(rules),
                    "focus": self._analysis_focus.copy(),
                    "feedback": user_feedback,
                    "time": elapsed,
                }
            )

            result = {
                "propositions": propositions,
                "rules": rules if extract_rules else [],
                "confidence": (
                    sum(p.confidence for p in propositions) / len(propositions)
                    if propositions
                    else 0.0
                ),
                "metadata": {
                    "text_length": len(text),
                    "processing_time": elapsed,
                    "focus_areas": self._analysis_focus.copy(),
                },
                "evidence": self._gather_evidence(propositions, rules),
            }

            if explain:
                result["explanation"] = self._generate_explanation(propositions, rules)

            # Update cache and stats
            if use_cache:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            self._stats["errors"] += 1
            raise RuntimeError(f"Document analysis failed: {str(e)}")

    def _extract_propositions(self, doc) -> List[Proposition]:
        """Extract atomic propositions using enhanced NLP analysis.

        Identifies propositions through:
        - Enhanced dependency patterns
        - Semantic role labeling
        - Frame semantic parsing
        - Cross-sentence relationships
        - Common sense constraints
        - Certainty classification
        - Modality detection

        Args:
            doc: Processed spacy document

        Returns:
            List of extracted Proposition objects with confidence scores
        """
        propositions = []

        # Get frame semantic parses
        frames = self.frame_parser(doc.text)

        for sent in doc.sents:
            # Enhanced dependency analysis
            for token in sent:
                if token.dep_ == "ROOT":
                    subjects = self._get_subjects(token)
                    objects = self._get_objects(token)

                    if subjects and objects:
                        for subj in subjects:
                            for obj in objects:
                                prop = self._create_proposition(subj, token, obj)
                                if prop:
                                    # Apply focus weight
                                    prop.confidence *= self._analysis_focus.get(
                                        "relations", 1.0
                                    )
                                    propositions.append(prop)

            # Add frame semantic propositions
            sent_frames = [f for f in frames if f["sentence"] == sent.text]
            for frame in sent_frames:
                frame_props = self._create_frame_propositions(frame)
                propositions.extend(frame_props)

        return propositions

    def _extract_semantic_propositions(self, doc) -> List[Proposition]:
        """Extract propositions from semantic analysis.

        Identifies:
        - Frame semantic relationships
        - VerbNet semantic roles
        - PropBank predicates
        - Abstract meaning forms

        Args:
            doc: Processed document

        Returns:
            List of semantic propositions
        """
        propositions = []

        # Frame semantic analysis
        frames = self.frame_parser(doc.text)
        for frame in frames:
            frame_elements = frame["frame_elements"]
            core_elements = [e for e in frame_elements if e["core"]]

            if core_elements:
                frame_prop = Proposition(f"frame_{frame['name']}")
                frame_prop.metadata["frame_elements"] = frame_elements
                frame_prop.confidence = frame["score"]
                propositions.append(frame_prop)

        # Semantic role analysis
        for sent in doc.sents:
            roles = self._get_semantic_roles(sent)
            for pred in roles:
                role_prop = Proposition(f"predicate_{pred}")
                role_prop.metadata["arguments"] = roles[pred]
                role_prop.confidence = 0.8
                propositions.append(role_prop)

        return propositions

    def _extract_event_chain_propositions(self, doc) -> List[Proposition]:
        """Extract propositions representing event chains and sequences.

        Identifies:
        - Event sequences
        - Temporal orderings
        - Causal chains
        - Subevent relationships

        Args:
            doc: Processed document

        Returns:
            List of event chain propositions
        """
        propositions = []

        # Extract events
        events = self._get_events(doc)

        # Build event chains
        for i, event in enumerate(events[:-1]):
            next_event = events[i + 1]

            # Temporal ordering
            if self._check_temporal_order(event, next_event):
                order_prop = Proposition(f"before_{event.name}_{next_event.name}")
                order_prop.confidence = 0.8 * self._analysis_focus["temporal"]
                propositions.append(order_prop)

            # Causal relationships
            if self._check_causal_relation(event, next_event):
                cause_prop = Proposition(f"causes_{event.name}_{next_event.name}")
                cause_prop.confidence = 0.7 * self._analysis_focus["causal"]
                propositions.append(cause_prop)

        return propositions

    def _extract_common_sense_propositions(self, doc) -> List[Proposition]:
        """Extract propositions based on common sense knowledge.

        Uses:
        - ConceptNet relationships
        - Default assumptions
        - World knowledge constraints
        - Likely implications
        - Expert provided rules
        - Domain assumptions

        Args:
            doc: Processed document

        Returns:
            List of common sense propositions
        """
        propositions = []

        # Query common sense knowledge bases
        for ent in doc.ents:
            relations = self._get_conceptnet_relations(ent.text)
            for rel in relations:
                cs_prop = Proposition(f"{rel['rel']}_{ent.text}_{rel['target']}")
                cs_prop.confidence = rel["weight"]
                # Add relationship metadata
                cs_prop.metadata["source"] = "conceptnet"
                cs_prop.metadata["validation"] = "automated"
                propositions.append(cs_prop)

        # Add default assumptions
        for sent in doc.sents:
            assumptions = self._get_assumptions(sent)
            for assumption in assumptions:
                def_prop = Proposition(assumption)
                def_prop.confidence = 0.6
                def_prop.metadata["source"] = "default_assumptions"
                def_prop.metadata["validation"] = "automated"
                propositions.append(def_prop)

        # Add expert-provided assumptions
        if self._expert_rules:
            for rule in self._expert_rules.get("assumptions", []):
                exp_prop = Proposition(rule["text"])
                exp_prop.confidence = rule["confidence"]
                exp_prop.metadata["source"] = "expert_knowledge"
                exp_prop.metadata["expert"] = rule["expert"]
                exp_prop.metadata["validation"] = "expert"
                propositions.append(exp_prop)

        return propositions

    def _extract_rich_temporal_rules(
        self, doc, propositions: List[Proposition]
    ) -> List[Rule]:
        """Extract rules with rich temporal relationships.

        Handles:
        - Complex interval relationships
        - Recurring events
        - Duration constraints
        - Calendar expressions
        - Temporal aggregation
        - Event sequences

        Args:
            doc: Processed document
            propositions: Available propositions

        Returns:
            List of temporal rules
        """
        rules = []

        # Enhanced temporal patterns
        temporal_patterns = {
            "sequence": ["before", "after", "then", "finally"],
            "overlap": ["during", "while", "when", "meanwhile"],
            "endpoint": ["until", "since", "from", "till"],
            "recurrence": ["every", "weekly", "daily", "monthly"],
            "duration": ["for", "throughout", "within"],
        }

        for sent in doc.sents:
            # Analyze temporal expressions
            timex = self.temporal_analyzer(sent.text)

            for t_type, markers in temporal_patterns.items():
                for token in sent:
                    if token.text.lower() in markers:
                        temporal_rule = self._create_temporal_rule(
                            token, sent, t_type, propositions, timex
                        )
                        if temporal_rule:
                            # Apply temporal focus weight
                            temporal_rule.confidence *= self._analysis_focus["temporal"]
                            rules.append(temporal_rule)

        return rules

    def _extract_logical_entailment_rules(
        self, doc, propositions: List[Proposition]
    ) -> List[Rule]:
        """Extract rules based on logical entailment relationships.

        Identifies:
        - Logical implications
        - Necessary conditions
        - Sufficient conditions
        - Equivalences
        - Exclusions
        - Expert-provided rules

        Args:
            doc: Processed document
            propositions: Available propositions

        Returns:
            List of logical rules
        """
        rules = []

        # Analyze logical relationships
        for sent in doc.sents:
            # Direct implications
            if any(
                marker in sent.text.lower()
                for marker in ["implies", "means", "entails"]
            ):
                rule = self._create_entailment_rule(sent, propositions)
                if rule:
                    rules.append(rule)

            # Necessary/sufficient conditions
            if "only if" in sent.text.lower():
                rule = self._create_necessity_rule(sent, propositions)
                if rule:
                    rules.append(rule)

        # Add expert-provided logical rules
        if self._expert_rules:
            for rule in self._expert_rules.get("logical", []):
                expert_rule = self._create_expert_rule(rule, propositions)
                if expert_rule:
                    expert_rule.metadata["source"] = "expert"
                    expert_rule.metadata["expert"] = rule["expert"]
                    rules.append(expert_rule)

        return rules

    def _extract_discourse_rules(
        self, doc, propositions: List[Proposition]
    ) -> List[Rule]:
        """Extract rules from discourse structure analysis.

        Uses:
        - RST discourse relations
        - Coherence relationships
        - Rhetorical structure
        - Argumentation patterns

        Args:
            doc: Processed document
            propositions: Available propositions

        Returns:
            List of discourse rules
        """
        rules = []

        # Get discourse parse
        discourse_tree = self.discourse_parser(doc.text)

        # Convert relations to rules
        for relation in discourse_tree["relations"]:
            rule = self._create_discourse_rule(relation, propositions)
            if rule:
                rules.append(rule)

        return rules

    def _create_proposition(self, subject, predicate, obj) -> Optional[Proposition]:
        """Create proposition with enhanced metadata.

        Args:
            subject: Subject token
            predicate: Predicate token
            obj: Object token

        Returns:
            Proposition if valid, None otherwise
        """
        # Basic proposition
        prop = Proposition(f"{subject.text}_{predicate.lemma_}_{obj.text}")

        # Add metadata
        prop.confidence = self._get_confidence(subject, predicate, obj)
        prop.metadata["source"] = "dependency"
        prop.metadata["certainty"] = self._get_certainty_score(subject, predicate, obj)
        prop.metadata["temporal"] = self._get_temporal_metadata(predicate)

        if prop.confidence >= self._confidence_thresholds["relation"]:
            return prop
        return None

    def _apply_feedback(self, analysis_result: Any, feedback: Dict) -> Any:
        """Apply user feedback to modify analysis results.

        Args:
            analysis_result: Original analysis output
            feedback: User feedback and corrections

        Returns:
            Modified analysis incorporating feedback
        """
        if isinstance(analysis_result, tuple):
            propositions, rules = analysis_result

            # Apply proposition feedback
            if "propositions" in feedback:
                propositions = self._modify_propositions(
                    propositions, feedback["propositions"]
                )

            # Apply rule feedback
            if "rules" in feedback:
                rules = self._modify_rules(rules, feedback["rules"])

            return (propositions, rules)

        return analysis_result

    def _load_expert_rules(self, experts: List[str]) -> None:
        """Load domain rules from expert knowledge bases.

        Args:
            experts: List of expert identifiers
        """
        for expert in experts:
            try:
                rules = self._load_expert_kb(expert)
                self._expert_rules[expert] = rules
            except Exception as e:
                print(f"Failed to load rules for expert {expert}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive text analysis statistics.

        Returns:
            Dictionary of statistics including:
            - Number of documents processed
            - Total processing time
            - Error count
            - Cache statistics
            - Average confidence scores
            - Rules generated
            - Proposition counts by type
            - User interaction metrics
            - Expert contributions
            - Focus area impact
        """
        stats = {
            "documents_processed": self._stats["documents_processed"],
            "processing_time_ms": self._stats["processing_time"],
            "errors": self._stats["errors"],
            "cache_size": len(self._cache),
            "cache_hits": getattr(self._cache, "hits", 0),
            "cache_misses": getattr(self._cache, "misses", 0),
            "user_interactions": len(self._interaction_history),
            "expert_rules_used": len(self._expert_rules),
            "focus_areas": self._analysis_focus.copy(),
        }

        if self._stats["documents_processed"] > 0:
            stats.update(
                {
                    "avg_processing_time": self._stats["processing_time"]
                    / self._stats["documents_processed"],
                    "error_rate": self._stats["errors"]
                    / self._stats["documents_processed"],
                }
            )

        return stats


class ResultsFormatter:
    """Formats reasoning results into human-friendly presentations."""

    def __init__(self, detail_level: str = "medium"):
        self.detail_level = detail_level
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load explanation templates.

        Returns:
            Dictionary mapping template names to template strings
        """
        return {
            "summary": "Analysis found {num_conclusions} conclusions with average confidence {avg_confidence:.0%}",
            "conclusion": "Concluded {text} ({confidence:.0%} confidence) based on {evidence}",
            "reasoning": """
            Used {strategy} reasoning:
            Steps: {steps}
            Confidence: {confidence:.0%}
            Evidence: {evidence}
            """,
            "evidence": "{text} ({source}, {confidence:.0%} confidence)",
            "error": "Error in {strategy}: {error}",
        }

    def _break_down_confidence(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Break down confidence scores by component.

        Args:
            results: Analysis results

        Returns:
            Dict mapping components to confidence scores
        """
        breakdown = {}

        # Analysis confidence
        if "analysis" in results:
            breakdown["text_analysis"] = results["analysis"].get("confidence", 0)

        # Strategy confidences
        if "reasoning" in results:
            for strategy, result in results["reasoning"].items():
                breakdown[f"strategy_{strategy}"] = result.get("confidence", 0)

        # Evidence confidence
        if "evidence" in results:
            evidence_scores = [e.get("confidence", 0) for e in results["evidence"]]
            if evidence_scores:
                breakdown["evidence"] = sum(evidence_scores) / len(evidence_scores)

        return breakdown

    def _identify_uncertainty_factors(
        self, results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify factors contributing to uncertainty.

        Args:
            results: Analysis results

        Returns:
            List of uncertainty factors with explanations
        """
        factors = []

        # Check confidence thresholds
        if results.get("confidence", 0) < 0.7:
            factors.append(
                {
                    "type": "low_confidence",
                    "description": "Overall confidence below threshold",
                    "impact": "high",
                }
            )

        # Check conflicting evidence
        if "evidence" in results:
            conflicting = self._find_conflicting_evidence(results["evidence"])
            if conflicting:
                factors.append(
                    {
                        "type": "conflicting_evidence",
                        "description": "Contradictory evidence found",
                        "conflicts": conflicting,
                        "impact": "medium",
                    }
                )

        # Check incomplete information
        if "missing_data" in results:
            factors.append(
                {
                    "type": "incomplete_data",
                    "description": "Missing critical information",
                    "missing": results["missing_data"],
                    "impact": "high",
                }
            )

        return factors

    def _format_evidence(
        self, results: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Format evidence with sources and confidence.

        Args:
            results: Analysis results

        Returns:
            Dict organizing evidence by type and source
        """
        evidence = {
            "direct": [],  # Direct observations/facts
            "inferred": [],  # Inferred through reasoning
            "external": [],  # External knowledge sources
        }

        if "evidence" in results:
            for item in results["evidence"]:
                evidence_type = item.get("type", "inferred")
                formatted = {
                    "text": item["text"],
                    "confidence": item.get("confidence", 0.5),
                    "source": item.get("source", "unknown"),
                    "timestamp": item.get("timestamp"),
                    "metadata": item.get("metadata", {}),
                }
                evidence[evidence_type].append(formatted)

        return evidence

    def _generate_visualizations(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate visualizations of results.

        Args:
            results: Results dictionary to visualize

        Returns:
            Dictionary of visualization data/specs
        """
        visualizations = {}

        # Generate knowledge graph
        if "knowledge" in results:
            visualizations["knowledge_graph"] = self._generate_knowledge_graph(
                results["knowledge"]
            )

        # Generate reasoning flow diagram
        if "reasoning" in results:
            visualizations["reasoning_flow"] = self._generate_reasoning_flow(
                results["reasoning"]
            )

        # Generate confidence visualization
        if "confidence" in results:
            visualizations["confidence_chart"] = self._generate_confidence_chart(
                results["confidence"]
            )

        return visualizations

    def _generate_knowledge_graph(self, knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Generate knowledge graph visualization.

        Args:
            knowledge: Knowledge dictionary to visualize

        Returns:
            Graph visualization specification
        """
        nodes = []
        edges = []

        # Add proposition nodes
        for prop in knowledge.get("propositions", []):
            nodes.append(
                {
                    "id": prop.name,
                    "label": prop.name,
                    "type": "proposition",
                    "confidence": prop.confidence,
                }
            )

        # Add rule nodes and edges
        for rule in knowledge.get("rules", []):
            rule_id = f"rule_{len(nodes)}"
            nodes.append(
                {
                    "id": rule_id,
                    "label": str(rule),
                    "type": "rule",
                    "confidence": rule.confidence,
                }
            )

            # Add edges from premises to rule and rule to conclusion
            for premise in rule.premises:
                edges.append({"from": premise.name, "to": rule_id, "type": "premise"})
            edges.append(
                {"from": rule_id, "to": rule.conclusion.name, "type": "conclusion"}
            )

        return {"nodes": nodes, "edges": edges, "type": "graph"}

    def _generate_reasoning_flow(self, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """Generate reasoning flow visualization.

        Args:
            reasoning: Reasoning results to visualize

        Returns:
            Flow diagram visualization specification
        """
        nodes = []
        edges = []

        # Add strategy nodes
        for strategy, result in reasoning.items():
            strategy_id = f"strategy_{len(nodes)}"
            nodes.append(
                {
                    "id": strategy_id,
                    "label": strategy,
                    "type": "strategy",
                    "confidence": result.get("confidence", 0),
                }
            )

            # Add reasoning step nodes and edges
            for i, step in enumerate(result.get("steps", [])):
                step_id = f"step_{len(nodes)}"
                nodes.append({"id": step_id, "label": step, "type": "step"})
                edges.append(
                    {
                        "from": strategy_id if i == 0 else f"step_{len(nodes)-2}",
                        "to": step_id,
                        "type": "flow",
                    }
                )

        return {"nodes": nodes, "edges": edges, "type": "flow"}

    def _generate_confidence_chart(
        self, confidence: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate confidence visualization.

        Args:
            confidence: Confidence scores to visualize

        Returns:
            Chart visualization specification
        """
        return {
            "type": "bar",
            "data": [
                {
                    "label": key,
                    "value": value,
                    "color": self._get_confidence_color(value),
                }
                for key, value in confidence.items()
            ],
            "options": {
                "title": "Confidence Scores",
                "xAxis": "Component",
                "yAxis": "Confidence",
            },
        }

    def _get_confidence_color(self, confidence: float) -> str:
        """Get color for confidence value.

        Args:
            confidence: Confidence value

        Returns:
            Color string
        """
        if confidence >= 0.8:
            return "#28a745"  # Green
        elif confidence >= 0.6:
            return "#ffc107"  # Yellow
        else:
            return "#dc3545"  # Red

    def format_results(
        self,
        results: Dict[str, Any],
        format: str = "text",
        detail_level: str = "medium",
        include_evidence: bool = True,
        include_confidence: bool = True,
        custom_templates: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Format reasoning results into multiple presentation formats.

        Args:
            results: Dictionary containing reasoning results
            format: Output format (text/html/markdown/structured/json)
            detail_level: Level of detail (low/medium/high)
            include_evidence: Whether to include supporting evidence
            include_confidence: Whether to include confidence scores
            custom_templates: Optional custom explanation templates

        Returns:
            Dict containing formatted results with sections:
                - summary: Brief overview
                - detailed_explanation: Comprehensive explanation
                - key_points: Main findings
                - confidence_assessment: Confidence analysis
                - supporting_evidence: Evidence details
                - visualizations: Visual representations
        """
        if custom_templates:
            self._explanation_templates.update(custom_templates)

        return {
            "summary": self._generate_summary(results),
            "detailed_explanation": self._generate_detailed_explanation(
                results, detail_level, include_evidence, include_confidence
            ),
            "key_points": self._extract_key_points(results),
            "confidence_assessment": (
                self._format_confidence_assessment(results)
                if include_confidence
                else None
            ),
            "supporting_evidence": (
                self._format_evidence(results) if include_evidence else None
            ),
            "visualizations": self._generate_visualizations(results),
            "format": format,
        }

    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate concise natural language summary of results."""
        summary_parts = []

        # Add main conclusions
        if "conclusions" in results:
            summary_parts.append("Main conclusions:")
            for concl in results["conclusions"]:
                summary_parts.append(
                    f"- {concl['text']} ({concl['confidence']:.0%} confidence)"
                )

        # Add key supporting evidence
        if "evidence" in results:
            summary_parts.append("\nKey evidence:")
            for ev in results["evidence"][:3]:  # Top 3 pieces
                summary_parts.append(f"- {ev['text']}")

        return "\n".join(summary_parts)

    def _generate_detailed_explanation(self, results: Dict[str, Any]) -> str:
        """Generate detailed step-by-step explanation of reasoning process."""
        explanation_parts = []

        # Explain knowledge extracted
        explanation_parts.append("Knowledge Extraction:")
        for concept in results.get("concepts", []):
            explanation_parts.append(f"- Identified concept: {concept['text']}")
            explanation_parts.append(
                f"  Related concepts: {', '.join(concept['related_concepts'])}"
            )

        # Explain reasoning steps
        explanation_parts.append("\nReasoning Process:")
        for step in results.get("reasoning_steps", []):
            explanation_parts.append(f"- {step['description']}")
            explanation_parts.append(f"  Confidence: {step['confidence']:.0%}")

        return "\n".join(explanation_parts)

    def _extract_key_points(self, results: Dict[str, Any]) -> List[str]:
        """Extract key points in bullet-point format."""
        key_points = []

        # Add main findings
        for finding in results.get("findings", []):
            key_points.append(f"• {finding['text']}")

        # Add important implications
        for impl in results.get("implications", []):
            key_points.append(f"• Implies: {impl['text']}")

        return key_points

    def _format_confidence_assessment(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format confidence scores and uncertainty assessment."""
        return {
            "overall_confidence": self._calculate_overall_confidence(results),
            "confidence_by_component": self._break_down_confidence(results),
            "uncertainty_factors": self._identify_uncertainty_factors(results),
        }


class AutomatedReasoner:
    """Main reasoner class that coordinates different reasoning strategies and natural language processing.

    This enhanced reasoner combines multiple reasoning approaches with advanced NLP capabilities
    to analyze text, extract knowledge, and perform sophisticated reasoning. Key features include:

    Reasoning Strategies:
    - Forward & backward chaining inference with parallel processing
    - Resolution-based theorem proving with optimization
    - Model checking & constraint satisfaction with visualization
    - Inductive & abductive reasoning with confidence scoring
    - Analogical & case-based reasoning with adaptation
    - Non-monotonic & belief revision with explanation
    - Probabilistic reasoning with Bayes nets and uncertainty handling
    - Meta-reasoning for strategy selection and combination
    - Hybrid reasoning combining multiple approaches dynamically
    - Multi-step reasoning with intermediate goal visualization
    - Common sense reasoning with knowledge integration
    - Temporal reasoning and sequence inference with visualization
    - Cross-document reasoning with knowledge transfer
    - Interactive reasoning with natural language explanations

    Text Analysis & NLP:
    - Deep natural language understanding with transformer models
    - Rich knowledge extraction with semantic parsing
    - Complex question answering with context tracking
    - Textual entailment with explanation generation
    - Advanced semantic role labeling with visualization
    - Temporal/causal relationship extraction with graphs
    - Full coreference resolution with entity tracking
    - Author intent analysis with confidence scoring
    - Sentiment and affect analysis with evidence
    - Discourse structure modeling with visualization
    - Cross-document knowledge integration with mapping
    - Common sense integration with external knowledge bases

    System Features:
    - Intelligent strategy selection based on problem type
    - Multi-threaded parallel reasoning with GPU acceleration
    - Adaptive resource management with monitoring
    - Continuous learning from reasoning history
    - Comprehensive performance tracking
    - Robust error recovery with fallback strategies
    - Plugin architecture for extensions
    - Human-friendly explanations with visualizations
    - Interactive reasoning with natural language
    - Rich knowledge visualization options
    - Detailed progress tracking and reporting
    - Confidence scoring with evidence
    - Performance profiling and optimization
    - Cross-strategy result synthesis

    Attributes:
        kb (KnowledgeBase): Core knowledge base shared across strategies
        strategies (Dict[str, ReasoningStrategy]): Available reasoning strategies
        text_analyzer (TextAnalyzer): NLP/text analysis component
        results_formatter (ResultsFormatter): Results formatting component
        _meta_reasoner (Optional[MetaReasoner]): Meta-reasoning component
        _strategy_configs (Dict[str, Dict]): Strategy configurations
        _cached_results (Dict[Tuple, Any]): Results cache
        _performance_stats (Dict[str, Dict]): Usage statistics
        _strategy_weights (Dict[str, float]): Current strategy weights
        _optimization_history (List[Dict]): Optimization record
        _error_handlers (Dict[str, Callable]): Custom error handlers
        _strategy_dependencies (Dict[str, Set]): Strategy dependencies
        _resource_limits (Dict[str, Dict]): Resource constraints
        _visualization_options (Dict[str, Any]): Visualization settings
        _explanation_templates (Dict[str, str]): Customizable explanation templates
        _confidence_scoring (Dict[str, float]): Strategy confidence weights
        _cross_refs (Dict[str, List[str]]): Cross-reference tracking
    """

    def __init__(
        self,
        enable_caching: bool = True,
        parallel_enabled: bool = False,
        max_cache_size: int = 1000,
        meta_reasoning: bool = False,
        resource_limits: Optional[Dict] = None,
        optimization_enabled: bool = True,
        use_gpu: bool = False,
        plugins: Optional[List[str]] = None,
        confidence_threshold: float = 0.7,
        max_reasoning_depth: int = 10,
        visualization_config: Optional[Dict] = None,
        explanation_templates: Optional[Dict[str, str]] = None,
    ):
        """[Previous docstring remains unchanged]"""
        import logging
        import torch
        if use_gpu:
            if torch.backends.mps.is_available():
                device = 'mps'
                dtype = torch.float32
            elif torch.cuda.is_available():
                device = 'cuda'
                dtype = torch.float32
            else:
                device = 'cpu'
                dtype = torch.float32
        else:
            device = 'cpu'
            dtype = torch.float32

        self.text_analyzer = TextAnalyzer(
            use_gpu=use_gpu,
        #     cache_size=max_cache_size,
        #     models=models,
        #     experts=experts,
        #     focus_areas=focus_areas,
        )
        # Initialize base components
        self.kb = KnowledgeBase()
        # self.text_analyzer = TextAnalyzer(use_gpu=use_gpu)
        self.results_formatter = ResultsFormatter()
        self.strategies = {}

        # Initialize logger
        self.logger = logging.getLogger(__name__)

        # Configuration
        self._enable_caching = enable_caching
        self._parallel_enabled = parallel_enabled
        self._max_cache_size = max_cache_size
        self._strategy_configs = {}
        self._resource_limits = resource_limits or {}
        self._confidence_threshold = confidence_threshold
        self._max_depth = max_reasoning_depth
        self._visualization_options = visualization_config or {}
        self._explanation_templates = explanation_templates or {}

        # Default explanation templates
        self._default_explanation = {
            "reasoning": "Used {strategy} to reason about {goal}. Result: {result}",
            "evidence": "Supporting evidence:\n{evidence}",
        }

        # Default visualization settings
        self._default_visualization = {
            "graph": True,
            "confidence": True,
            "evidence": True,
        }

        # Initialize tracking
        self._cached_results = {}
        self._performance_stats = defaultdict(
            lambda: {
                "calls": 0,
                "time": 0.0,
                "cache_hits": 0,
                "errors": 0,
                "last_used": 0,
                "avg_latency": 0.0,
                "peak_memory": 0,
                "success_rate": 0.0,
                "text_queries": 0,
                "nlp_time": 0.0,
            }
        )
        self._strategy_weights = defaultdict(lambda: 1.0)
        self._optimization_history = []
        self._error_handlers = {}
        self._cross_refs = defaultdict(list)

        # self.coref_resolver = FCoref(device=device)

        # Initialize components
        self._initialize_strategies()
        if optimization_enabled:
            self._setup_optimization()
        if meta_reasoning:
            self._initialize_meta_reasoner()
        if plugins:
            for plugin in plugins:
                self._load_plugin(plugin)

    def _initialize_strategies(self) -> None:
        """Initialize available reasoning strategies."""
        self.strategies = {
            "forward": ForwardChaining(),
            "backward": BackwardChaining(),
            "resolution": Resolution(),
            "model_checking": ModelChecking(),
            "constraint": ConstraintSatisfaction(),
            "inductive": InductiveReasoning(),
            "abductive": AbductiveReasoning(),
            "analogical": AnalogicalReasoning(),
            "probabilistic": ProbabilisticReasoning(),
        }

    def _initialize_meta_reasoner(self) -> None:
        """Initialize meta-reasoning component."""
        # MetaReasoner import moved to local scope
        try:
            from .meta_reasoning import MetaReasoner

            self._meta_reasoner = MetaReasoner(self.strategies)
        except ImportError:
            self.logger.warning(
                "MetaReasoner not available - continuing without meta-reasoning"
            )
            self._meta_reasoner = None

    def _setup_optimization(self) -> None:
        """Set up optimization parameters and tracking."""
        self.optimization_params = {
            "learning_rate": 0.01,
            "batch_size": 32,
            "num_epochs": 100,
        }
        self.optimization_state = {}

    def resolve_coreferences(self, text):
        # Predict coreference clusters
        predictions = self.coref_resolver.predict(texts=[text])

        # Extract clusters as text spans
        clusters = predictions[0].get_clusters()

        return clusters



    def reason(
        self,
        strategy: str,
        goal: Optional[Proposition] = None,
        max_depth: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute reasoning using specified strategy.

        Args:
            strategy: Name of reasoning strategy to use
            goal: Optional goal proposition
            max_depth: Optional maximum reasoning depth

        Returns:
            Dictionary containing reasoning results

        Raises:
            ValueError: If strategy not found
        """
        if strategy not in self.strategies:
            raise ValueError(f"Strategy {strategy} not found")

        try:
            # Track performance
            start = time.perf_counter()
            self._performance_stats[strategy]["calls"] += 1

            # Execute strategy
            result = self.strategies[strategy].reason(self.kb, goal)

            # Calculate confidence and gather evidence
            confidence = self._calculate_confidence(strategy, result)
            evidence = self._gather_evidence(strategy, result)

            # Generate explanation
            explanation = self._generate_strategy_explanation(strategy, result, goal)

            # Track performance
            elapsed = time.perf_counter() - start
            self._performance_stats[strategy]["time"] += elapsed
            self._performance_stats[strategy]["avg_latency"] = (
                self._performance_stats[strategy]["time"]
                / self._performance_stats[strategy]["calls"]
            )

            return {
                "result": result,
                "confidence": confidence,
                "evidence": evidence,
                "explanation": explanation,
                "performance": {
                    "time": elapsed,
                    "memory": 0,  # TODO: Implement memory tracking
                },
            }

        except Exception as e:
            self._handle_strategy_error(strategy, e)
            raise

    def explain_reasoning(
        self,
        results: Dict[str, Any],
        format: str = "text",
        detail_level: str = "medium",
        include_evidence: bool = True,
        include_confidence: bool = True,
        custom_templates: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Generate human-friendly explanation of reasoning process.

        Args:
            results: Dictionary containing reasoning results
            format: Output format (text/html/markdown/structured/json)
            detail_level: Level of detail to include (low/medium/high)
            include_evidence: Whether to include supporting evidence
            include_confidence: Whether to include confidence scores
            custom_templates: Optional custom explanation templates

        Returns:
            str or Dict: Formatted explanation in requested format

        Formats:
            - text: Natural language explanation as plain text
            - html: HTML formatted explanation with links and styling
            - markdown: Markdown formatted explanation with headers
            - structured: Structured data format as nested dictionary
            - json: JSON formatted structured explanation

        Detail Levels:
            - low: Brief summary of main conclusions
            - medium: Main points with key evidence
            - high: Comprehensive explanation with all details
        """
        import json

        # Apply custom templates if provided
        if custom_templates:
            self._explanation_templates.update(custom_templates)

        # Process based on format
        if format == "text":
            explanation = self._generate_text_explanation(
                results, detail_level, include_evidence, include_confidence
            )
            return self._format_text_explanation(results, explanation)

        elif format == "html":
            explanation = self._generate_html_explanation(
                results, detail_level, include_evidence, include_confidence
            )
            return self._format_html_explanation(results, explanation)

        elif format == "markdown":
            explanation = self._generate_markdown_explanation(
                results, detail_level, include_evidence, include_confidence
            )
            return self._format_markdown_explanation(results, explanation)

        elif format == "structured":
            explanation = self._generate_structured_explanation(
                results, detail_level, include_evidence, include_confidence
            )
            return json.dumps(explanation) if format == "json" else explanation

        else:
            # Default to text format
            explanation = self._generate_text_explanation(
                results, detail_level, include_evidence, include_confidence
            )
            return self._format_text_explanation(results, explanation)

    def _format_text_explanation(
        self, results: Dict[str, Any], explanation: str
    ) -> str:
        """Format text explanation with proper spacing and sections."""
        formatted = []
        for line in explanation.split("\n"):
            if line.startswith("#"):
                formatted.append(f"\n{line.lstrip('#').strip()}")
            else:
                formatted.append(line)
        return "\n".join(formatted)

    def _format_html_explanation(
        self, results: Dict[str, Any], explanation: str
    ) -> str:
        """Format explanation as HTML with styling."""
        html = ['<div class="explanation">']
        for line in explanation.split("\n"):
            if line.startswith("#"):
                level = line.count("#")
                text = line.lstrip("#").strip()
                html.append(f"<h{level}>{text}</h{level}>")
            else:
                html.append(f"<p>{line}</p>")
        html.append("</div>")
        return "\n".join(html)

    def _format_markdown_explanation(
        self, results: Dict[str, Any], explanation: str
    ) -> str:
        """Format explanation as Markdown."""
        md_lines = []
        for line in explanation.split("\n"):
            if line.startswith("#"):
                level = line.count("#")
                text = line.lstrip("#").strip()
                md_lines.append(f"{'#' * level} {text}")
            else:
                md_lines.append(line)
        return "\n".join(md_lines)

    def _create_rule_from_relationship(self, rel: Dict[str, Any]) -> Rule:
        """Create rule from relationship dictionary."""
        premises = []
        if "source" in rel:
            premises.append(Proposition(rel["source"]))
        if "conditions" in rel:
            for cond in rel["conditions"]:
                premises.append(Proposition(cond))

        conclusion = Proposition(rel["target"]) if "target" in rel else None
        confidence = rel.get("confidence", 0.8)

        return Rule(premises=premises, conclusion=conclusion, confidence=confidence)

    def _add_argument_to_kb(self, arg: Dict[str, Any]) -> None:
        """Add argument structure to knowledge base."""
        # Create premise propositions
        premises = []
        for premise in arg.get("premises", []):
            prop = Proposition(
                premise["text"], confidence=premise.get("confidence", 0.8)
            )
            premises.append(prop)
            self.kb.add_fact(prop, True)

        # Create conclusion proposition
        if "conclusion" in arg:
            conclusion = Proposition(
                arg["conclusion"]["text"],
                confidence=arg["conclusion"].get("confidence", 0.8),
            )
            # Add argument as rule
            rule = Rule(premises, conclusion, confidence=arg.get("confidence", 0.8))
            self.kb.add_rule(rule)

    def _derive_main_conclusions(
        self, analysis_results: Dict[str, Any], reasoning_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Derive main conclusions from analysis and reasoning results."""
        conclusions = []

        # Add high confidence analysis conclusions
        if "conclusions" in analysis_results:
            for concl in analysis_results["conclusions"]:
                if concl.get("confidence", 0) >= 0.7:
                    conclusions.append(concl)

        # Add reasoning conclusions
        for strategy, result in reasoning_results.items():
            if isinstance(result, dict) and "conclusion" in result:
                conclusions.append(
                    {
                        "text": result["conclusion"],
                        "confidence": result.get("confidence", 0.8),
                        "source": strategy,
                    }
                )

        return conclusions

    def _gather_supporting_evidence(
        self, analysis_results: Dict[str, Any], reasoning_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Gather supporting evidence from results."""
        evidence = []

        # Evidence from analysis
        if "evidence" in analysis_results:
            evidence.extend(analysis_results["evidence"])

        # Evidence from reasoning
        for result in reasoning_results.values():
            if isinstance(result, dict) and "evidence" in result:
                evidence.extend(result["evidence"])

        return evidence

    def _assess_overall_confidence(
        self, analysis_results: Dict[str, Any], reasoning_results: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence from all results."""
        confidences = []

        # Analysis confidence
        if "confidence" in analysis_results:
            confidences.append(analysis_results["confidence"])

        # Reasoning confidences
        for result in reasoning_results.values():
            if isinstance(result, dict) and "confidence" in result:
                confidences.append(result["confidence"])

        return sum(confidences) / len(confidences) if confidences else 0.0

    def _populate_kb_from_analysis(self, analysis_results: Dict[str, Any]) -> None:
        """Populate knowledge base from text analysis results."""
        # Add concepts as facts
        for concept in analysis_results["concepts"]:
            prop = Proposition(concept["text"], confidence=concept["importance_score"])
            self.kb.add_fact(prop, True)

        # Add relationships as rules
        for rel in analysis_results["relationships"]:
            rule = self._create_rule_from_relationship(rel)
            self.kb.add_rule(rule)

        # Add arguments as logical structures
        for arg in analysis_results["arguments"]:
            self._add_argument_to_kb(arg)

    def _synthesize_results(
        self, analysis_results: Dict[str, Any], reasoning_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize analysis and reasoning results into coherent conclusions."""
        return {
            "main_conclusions": self._derive_main_conclusions(
                analysis_results, reasoning_results
            ),
            "supporting_evidence": self._gather_supporting_evidence(
                analysis_results, reasoning_results
            ),
            "confidence_assessment": self._assess_overall_confidence(
                analysis_results, reasoning_results
            ),
            "implications": self._identify_implications(
                analysis_results, reasoning_results
            ),
        }

    def _load_plugin(self, plugin_name: str) -> None:
        """Load plugin module dynamically."""
        import importlib

        try:
            plugin_module = importlib.import_module(f"plugins.{plugin_name}")
            plugin_module.initialize(self)
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_name}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics and performance metrics.

        Returns:
            Dictionary containing:
            - Processing statistics (docs, time, etc)
            - Cache performance
            - Strategy usage and success rates
            - Resource utilization
            - Error rates
            - Text analysis metrics
        """
        stats = {
            # Core processing stats
            "documents_processed": sum(
                s["calls"] for s in self._performance_stats.values()
            ),
            "total_processing_time": sum(
                s["time"] for s in self._performance_stats.values()
            ),
            "avg_processing_time": 0.0,
            # Cache stats
            "cache_size": len(self._cached_results),
            "cache_hit_rate": 0.0,
            "cache_hits": sum(
                s["cache_hits"] for s in self._performance_stats.values()
            ),
            "cache_misses": 0,
            # Strategy stats
            "strategy_usage": {
                name: stats["calls"] for name, stats in self._performance_stats.items()
            },
            "strategy_latency": {
                name: stats["avg_latency"]
                for name, stats in self._performance_stats.items()
            },
            "success_rate": 0.0,
            # Error stats
            "total_errors": sum(s["errors"] for s in self._performance_stats.values()),
            "error_rate": 0.0,
            # Resource stats
            "peak_memory": max(
                s["peak_memory"] for s in self._performance_stats.values()
            ),
            # Text analysis stats
            "text_queries": sum(
                s["text_queries"] for s in self._performance_stats.values()
            ),
            "nlp_processing_time": sum(
                s["nlp_time"] for s in self._performance_stats.values()
            ),
        }

        # Calculate derived metrics
        if stats["documents_processed"] > 0:
            stats["avg_processing_time"] = (
                stats["total_processing_time"] / stats["documents_processed"]
            )
            stats["error_rate"] = stats["total_errors"] / stats["documents_processed"]

        total_cache_attempts = stats["cache_hits"] + stats["cache_misses"]
        if total_cache_attempts > 0:
            stats["cache_hit_rate"] = stats["cache_hits"] / total_cache_attempts

        total_attempts = sum(s["calls"] for s in self._performance_stats.values())
        if total_attempts > 0:
            stats["success_rate"] = (
                total_attempts - stats["total_errors"]
            ) / total_attempts

        # Add strategy-specific stats
        stats["strategies"] = {
            name: {
                "calls": stats["calls"],
                "avg_latency": stats["avg_latency"],
                "error_rate": stats["errors"] / max(stats["calls"], 1),
                "cache_hits": stats["cache_hits"],
                "peak_memory": stats["peak_memory"],
            }
            for name, stats in self._performance_stats.items()
        }

        return stats

    def _identify_implications(
        self, analysis_results: Dict[str, Any], reasoning_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify implications from analysis and reasoning results.

        Args:
            analysis_results: Results from text analysis
            reasoning_results: Results from reasoning strategies

        Returns:
            List of implications with confidence scores and evidence
        """
        implications = []

        # Get implications from analysis
        if "implications" in analysis_results:
            implications.extend(analysis_results["implications"])

        # Get implications from reasoning results
        for strategy, result in reasoning_results.items():
            if isinstance(result, dict) and "implications" in result:
                # Add strategy as source
                for impl in result["implications"]:
                    impl["source"] = strategy
                implications.extend(result["implications"])

        # Add cross-strategy implications
        cross_implications = self._identify_cross_strategy_implications(
            reasoning_results
        )
        implications.extend(cross_implications)

        # Deduplicate while preserving evidence
        unique_implications = {}
        for impl in implications:
            text = impl["text"]
            if text not in unique_implications:
                unique_implications[text] = impl
            else:
                # Merge evidence and boost confidence
                existing = unique_implications[text]
                existing["evidence"] = list(
                    set(existing.get("evidence", []) + impl.get("evidence", []))
                )
                existing["confidence"] = max(
                    existing.get("confidence", 0), impl.get("confidence", 0)
                )
                if "source" in impl:
                    existing["sources"] = list(
                        set(existing.get("sources", []) + [impl["source"]])
                    )

        return list(unique_implications.values())

    def _identify_cross_strategy_implications(
        self, reasoning_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify implications that emerge from combining multiple strategies.

        Args:
            reasoning_results: Results from different reasoning strategies

        Returns:
            List of cross-strategy implications
        """
        implications = []

        # Look for complementary conclusions
        conclusions = {}
        for strategy, result in reasoning_results.items():
            if isinstance(result, dict) and "conclusions" in result:
                for concl in result["conclusions"]:
                    key = concl["text"]
                    if key not in conclusions:
                        conclusions[key] = []
                    conclusions[key].append(
                        {
                            "strategy": strategy,
                            "confidence": concl.get("confidence", 0),
                            "evidence": concl.get("evidence", []),
                        }
                    )

        # Identify implications supported by multiple strategies
        for text, supports in conclusions.items():
            if len(supports) > 1:
                # Calculate combined confidence and evidence
                confidence = 1 - math.prod(1 - s["confidence"] for s in supports)
                evidence = list(set(e for s in supports for e in s["evidence"]))

                implications.append(
                    {
                        "text": f"Multiple strategies support: {text}",
                        "confidence": confidence,
                        "evidence": evidence,
                        "sources": [s["strategy"] for s in supports],
                    }
                )

        return implications

    def _calculate_confidence(self, strategy: str, result: Any) -> float:
        """Calculate confidence score for reasoning result."""
        base_confidence = self._strategy_weights[strategy]
        result_confidence = getattr(result, "confidence", 0.5)
        return min(base_confidence * result_confidence, 1.0)

    def _gather_evidence(self, strategy: str, result: Any) -> List[Dict]:
        """Gather supporting evidence for reasoning result."""
        evidence = []
        if hasattr(result, "evidence"):
            evidence.extend(result.evidence)
        if hasattr(self.kb, "get_evidence"):
            evidence.extend(self.kb.get_evidence(result))
        return evidence

    def _generate_strategy_explanation(
        self, strategy: str, result: Any, goal: Optional[Proposition]
    ) -> str:
        """Generate natural language explanation of strategy reasoning."""
        template = self._explanation_templates.get(
            strategy, self._default_explanation["reasoning"]
        )
        return template.format(strategy=strategy, result=result, goal=goal)

    def _generate_strategy_visualization(
        self, strategy: str, result: Any, goal: Optional[Proposition]
    ) -> Dict[str, Any]:
        """Generate visualization of strategy reasoning process."""
        if hasattr(self.strategies[strategy], "visualize"):
            return self.strategies[strategy].visualize(result, goal)
        return {"type": "default", "data": result}

    def _handle_strategy_error(self, strategy: str, error: Exception) -> None:
        """Handle errors from reasoning strategies."""
        self._performance_stats[strategy]["errors"] += 1
        self.logger.error(f"Error in {strategy}: {error}")

        handler = self._error_handlers.get(type(error))
        if handler:
            handler(error)

    def _select_query_strategies(self, query: str) -> List[str]:
        """Select appropriate strategies for handling query."""
        strategies = []
        # Select based on query analysis
        if "cause" in query or "why" in query:
            strategies.extend(["abductive", "causal"])
        if "similar" in query:
            strategies.append("analogical")
        if "probability" in query:
            strategies.append("probabilistic")
        # Add default fallback
        if not strategies:
            strategies = ["backward", "forward"]
        return strategies

    def _select_general_strategies(self, analysis: Dict[str, Any]) -> List[str]:
        """Select appropriate strategies for general reasoning."""
        strategies = []
        # Select based on content analysis
        if analysis.get("causal_relations"):
            strategies.append("causal")
        if analysis.get("temporal_relations"):
            strategies.append("temporal")
        # Add default strategies
        strategies.extend(["forward", "backward"])
        return strategies

    def _create_goal_from_query(self, query: Optional[str]) -> Optional[Proposition]:
        """Convert natural language query to goal proposition."""
        if not query:
            return None
        # Extract goal using text analyzer's query analysis
        try:
            return Proposition(query.strip().lower())
        except:
            return None

    def _extract_key_points(self, conclusions: List[Dict]) -> List[str]:
        """Extract key points from conclusions."""
        key_points = []
        for conclusion in conclusions:
            if conclusion.get("confidence", 0) >= self._confidence_threshold:
                key_points.append(conclusion["text"])
        return key_points

    def _identify_implications(self, conclusions: List[Dict]) -> List[str]:
        """Identify implications from conclusions."""
        implications = []
        for conclusion in conclusions:
            if "implies" in conclusion:
                implications.append(conclusion["implies"])
        return implications

    def _generate_text_explanation(self, results: Dict[str, Any]) -> str:
        """Generate natural language explanation of results."""
        explanation = []

        # Knowledge extraction explanation
        if "knowledge" in results:
            explanation.append("Knowledge Extracted:")
            for prop in results["knowledge"].get("propositions", []):
                explanation.append(f"- {str(prop)}")
            for rule in results["knowledge"].get("rules", []):
                explanation.append(f"- {str(rule)}")

        # Reasoning process explanation
        if "reasoning" in results:
            explanation.append("\nReasoning Steps:")
            for strategy, result in results["reasoning"].items():
                explanation.append(f"\n{strategy.title()} Reasoning:")
                if "steps" in result:
                    for step in result["steps"]:
                        explanation.append(f"- {step}")

        # Conclusions explanation
        if "conclusions" in results:
            explanation.append("\nConclusions:")
            for conclusion in results["conclusions"]:
                explanation.append(
                    f"- {conclusion['text']} (Confidence: {conclusion['confidence']:.2f})"
                )

        return "\n".join(explanation)

    def _generate_html_explanation(self, results: Dict[str, Any]) -> str:
        """Generate HTML explanation of results."""
        html = ['<div class="explanation">']

        # Knowledge section
        if "knowledge" in results:
            html.append('<div class="knowledge-section">')
            html.append("<h3>Knowledge Extracted</h3>")
            html.append("<ul>")
            for prop in results["knowledge"].get("propositions", []):
                html.append(f"<li>{str(prop)}</li>")
            html.append("</ul>")
            html.append("</div>")

        # Reasoning section
        if "reasoning" in results:
            html.append('<div class="reasoning-section">')
            html.append("<h3>Reasoning Process</h3>")
            for strategy, result in results["reasoning"].items():
                html.append(f"<h4>{strategy.title()} Reasoning</h4>")
                html.append("<ul>")
                if "steps" in result:
                    for step in result["steps"]:
                        html.append(f"<li>{step}</li>")
                html.append("</ul>")
            html.append("</div>")

        html.append("</div>")
        return "\n".join(html)

    def _generate_markdown_explanation(self, results: Dict[str, Any]) -> str:
        """Generate Markdown explanation of results."""
        md = []

        # Knowledge section
        if "knowledge" in results:
            md.append("## Knowledge Extracted\n")
            for prop in results["knowledge"].get("propositions", []):
                md.append(f"* {str(prop)}")
            md.append("")

        # Reasoning section
        if "reasoning" in results:
            md.append("## Reasoning Process\n")
            for strategy, result in results["reasoning"].items():
                md.append(f"### {strategy.title()} Reasoning\n")
                if "steps" in result:
                    for step in result["steps"]:
                        md.append(f"* {step}")
                md.append("")

        return "\n".join(md)

    def _generate_structured_explanation(
        self, results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured data explanation of results."""
        structured = {
            "knowledge": {
                "propositions": [
                    str(p) for p in results.get("knowledge", {}).get("propositions", [])
                ],
                "rules": [
                    str(r) for r in results.get("knowledge", {}).get("rules", [])
                ],
            },
            "reasoning": {},
            "conclusions": [],
        }

        if "reasoning" in results:
            for strategy, result in results["reasoning"].items():
                structured["reasoning"][strategy] = {
                    "steps": result.get("steps", []),
                    "confidence": result.get("confidence", 0),
                    "evidence": result.get("evidence", []),
                }

        if "conclusions" in results:
            structured["conclusions"] = results["conclusions"]

        return structured

    def _format_graph_html(self, graph: Any) -> Dict[str, Any]:
        """Format graph as HTML visualization data."""
        if not graph:
            return {"nodes": [], "edges": []}

        nodes = []
        edges = []

        if hasattr(graph, "nodes"):
            for node in graph.nodes():
                nodes.append(
                    {
                        "id": str(node),
                        "label": str(node),
                        "type": graph.nodes[node].get("type", "default"),
                    }
                )

        if hasattr(graph, "edges"):
            for src, dst in graph.edges():
                edges.append({"from": str(src), "to": str(dst)})

        return {"nodes": nodes, "edges": edges}

    def _visualize_confidence(
        self, results: Dict[str, Any], format: str
    ) -> Dict[str, Any]:
        """Generate confidence score visualization."""
        confidence_data = {}
        for strategy, result in results["reasoning"].items():
            if "confidence" in result:
                confidence_data[strategy] = result["confidence"]

        if format == "html":
            # Generate HTML visualization
            html = ['<div class="confidence-vis">']
            for strategy, conf in confidence_data.items():
                html.append(
                    f'<div class="conf-bar" style="width:{conf*100}%">'
                    f"{strategy}: {conf:.2f}</div>"
                )
            html.append("</div>")
            return {"html": "\n".join(html), "data": confidence_data}

        return {"data": confidence_data}

    def _visualize_evidence(
        self, results: Dict[str, Any], format: str
    ) -> Dict[str, Any]:
        """Generate evidence visualization."""
        evidence_data = {}
        for strategy, result in results["reasoning"].items():
            if "evidence" in result:
                evidence_data[strategy] = result["evidence"]

        if format == "html":
            # Generate HTML visualization
            html = ['<div class="evidence-vis">']
            for strategy, evidence in evidence_data.items():
                html.append(f'<div class="evidence-section">')
                html.append(f"<h4>{strategy} Evidence</h4>")
                html.append("<ul>")
                for item in evidence:
                    html.append(f"<li>{item}</li>")
                html.append("</ul>")
                html.append("</div>")
            html.append("</div>")
            return {"html": "\n".join(html), "data": evidence_data}

        return {"data": evidence_data}

    def _format_knowledge(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Format extracted knowledge for output."""
        return {
            "propositions": [str(p) for p in analysis.get("propositions", [])],
            "rules": [str(r) for r in analysis.get("rules", [])],
            "concepts": analysis.get("concepts", []),
            "relations": analysis.get("relations", []),
        }

    def _calculate_overall_confidence(self, synthesis: Dict[str, Any]) -> float:
        """Calculate overall confidence score."""
        confidences = []
        if "conclusions" in synthesis:
            confidences.extend(c.get("confidence", 0) for c in synthesis["conclusions"])
        if not confidences:
            return 0.0
        return sum(confidences) / len(confidences)

    def _gather_overall_evidence(self, synthesis: Dict[str, Any]) -> List[Dict]:
        """Gather all supporting evidence."""
        evidence = []
        if "evidence" in synthesis:
            evidence.extend(synthesis["evidence"])
        if "conclusions" in synthesis:
            for conclusion in synthesis["conclusions"]:
                if "evidence" in conclusion:
                    evidence.extend(conclusion["evidence"])
        return evidence

    def reason_about_text(
        self,
        text: str,
        query: Optional[str] = None,
        strategies: Optional[List[str]] = None,
        detail_level: str = "medium",
        explain: bool = True,
        visualize: bool = True,
    ) -> Dict[str, Any]:
        """Perform comprehensive reasoning about text with explanations."""
        # Analyze text
        analysis = self.text_analyzer.analyze_document(text)

        # Build knowledge base
        for prop in analysis["propositions"]:
            self.kb.add_fact(prop, True)
        for rule in analysis["rules"]:
            self.kb.add_rule(rule)

        # Select strategies if not specified
        if not strategies:
            strategies = (
                self._select_query_strategies(query)
                if query
                else self._select_general_strategies(analysis)
            )

        # Execute reasoning
        results = {}
        for strategy in strategies:
            try:
                goal = self._create_goal_from_query(query) if query else None
                result = self.reason(strategy, goal=goal)
                results[strategy] = result
            except Exception as e:
                self.logger.error(f"Error in {strategy}: {e}")
                results[strategy] = {"error": str(e)}

        # Generate explanation if requested
        explanation = None
        if explain:
            format = "text"
            if detail_level == "high":
                explanation = self._generate_structured_explanation(results)
            else:
                explanation = self._generate_text_explanation(results)

        # Generate visualizations if requested
        visualizations = None
        if visualize:
            visualizations = {
                "confidence": self._visualize_confidence(results, "html"),
                "evidence": self._visualize_evidence(results, "html"),
            }

        return {
            "analysis": analysis,
            "reasoning": results,
            "explanation": explanation,
            "visualizations": visualizations,
            "confidence": self._calculate_overall_confidence(results),
            "evidence": self._gather_overall_evidence(results),
        }


def example():
    """Comprehensive example demonstrating all capabilities of the automated reasoning system.

    This example shows:
    1. Text analysis and knowledge extraction
    2. Multiple reasoning strategies
    3. Cross-document reasoning
    4. Interactive query handling
    5. Result visualization and explanation
    """
    # Initialize reasoner with all capabilities enabled
    reasoner = AutomatedReasoner(
        enable_caching=True,
        parallel_enabled=True,
        meta_reasoning=True,
        optimization_enabled=True,
        use_gpu=True,
    )

    # Example documents to reason about
    climate_text = """
    Global temperatures are rising due to increased CO2 emissions.
    When temperatures rise, ice caps melt. Melting ice caps cause
    sea levels to rise. Rising sea levels threaten coastal cities.
    """

    policy_text = """
    Carbon taxes reduce CO2 emissions by incentivizing clean energy.
    Clean energy adoption leads to lower emissions. However, taxes
    can slow economic growth in the short term.
    """

    # Analyze texts and populate knowledge base
    climate_results = reasoner.reason_about_text(text=climate_text, detail_level="high")
    print("\nClimate Text Analysis:")
    print(reasoner.explain_reasoning(climate_results, format="text"))

    policy_results = reasoner.reason_about_text(text=policy_text, detail_level="high")
    print("\nPolicy Text Analysis:")
    print(reasoner.explain_reasoning(policy_results, format="text"))

    # Perform cross-document reasoning with queries
    queries = [
        "What are the implications of carbon taxes for coastal cities?",
        "How does economic growth relate to climate impacts?",
        "What policy interventions could protect coastal regions?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        results = reasoner.reason_about_text(
            text=climate_text + "\n" + policy_text,
            query=query,
            strategies=["backward", "analogical", "abductive"],
            explain=True,
        )

        # Show comprehensive results
        print("\nMain Conclusions:")
        for conclusion in results["synthesis"]["main_conclusions"]:
            print(
                f"- {conclusion['text']} (Confidence: {conclusion['confidence']:.2f})"
            )

        print("\nSupporting Evidence:")
        for evidence in results["synthesis"]["supporting_evidence"]:
            print(f"- {evidence['text']}")

        print("\nImplications:")
        for impl in results["synthesis"]["implications"]:
            print(f"- {impl['text']}")

    # Demonstrate different reasoning strategies
    print("\nDemonstrating Multiple Reasoning Strategies:")

    # Forward chaining to derive all implications
    forward_results = reasoner.reason("forward", max_depth=5)
    print("\nForward Chaining Results:")
    print(reasoner.explain_reasoning(forward_results))

    # Backward chaining for specific goal
    goal_prop = Proposition("coastal_cities_threatened")
    backward_results = reasoner.reason("backward", goal=goal_prop)
    print("\nBackward Chaining Results:")
    print(reasoner.explain_reasoning(backward_results))

    # Probabilistic reasoning about uncertainties
    prob_results = reasoner.reason(
        "probabilistic", query=Proposition("economic_impact_severe")
    )
    print("\nProbabilistic Reasoning Results:")
    print(reasoner.explain_reasoning(prob_results))

    # Analogical reasoning to find similar cases
    analogical_results = reasoner.reason(
        "analogical", target_case={"domain": "climate_policy", "impact": "economic"}
    )
    print("\nAnalogical Reasoning Results:")
    print(reasoner.explain_reasoning(analogical_results))

    # Generate visualizations
    print("\nGenerating Visualizations:")
    vis_results = reasoner.reason_about_text(
        text=climate_text + "\n" + policy_text, detail_level="high"
    )

    # Show different visualization formats
    print("\nKnowledge Graph:")
    print(vis_results["visualization"]["knowledge_graph"])

    print("\nReasoning Flow:")
    print(vis_results["visualization"]["reasoning_flow"])

    print("\nConfidence Assessment:")
    print(vis_results["visualization"]["confidence_chart"])

    # Get performance statistics
    print("\nPerformance Statistics:")
    stats = reasoner.get_stats()
    print(f"Documents processed: {stats['documents_processed']}")
    print(f"Average processing time: {stats['avg_processing_time']:.2f}ms")
    print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
    print(f"Success rate: {stats['success_rate']:.2%}")


if __name__ == "__main__":
    example()
