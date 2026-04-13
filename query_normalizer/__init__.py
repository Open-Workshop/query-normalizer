"""Query normalizer library for search queries.

Supports Russian and English languages with mixed script detection,
keyboard layout fixing, lemmatization, and stopword removal.
"""

from query_normalizer.core import NormalizationResult, QueryNormalizer

__version__ = "0.2.1"
__all__ = ["QueryNormalizer", "NormalizationResult", "__version__"]