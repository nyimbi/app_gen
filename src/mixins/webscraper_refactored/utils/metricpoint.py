"""
MetricPoint module

Data class for storing individual metric measurements

Classes:

- MetricPoint

"""

from typing import Any, Dict, List, Optional, Set


@dataclass
class MetricPoint:
    """Data class for storing individual metric measurements"""

    value: float
    timestamp: float
    labels: Dict[str, str] = None
