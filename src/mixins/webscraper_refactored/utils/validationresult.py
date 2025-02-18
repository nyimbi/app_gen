"""
ValidationResult module

Container for content validation results

Classes:

- ValidationResult

"""

from typing import Any, Dict, List, Optional, Set


@dataclass
class ValidationResult:
    """Container for content validation results"""

    is_valid: bool
    score: float
    message: str
    metrics: Dict[str, Any]
