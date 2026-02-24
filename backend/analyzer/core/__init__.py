"""
core/__init__.py
~~~~~~~~~~~~~~~~
Re-exports for convenient top-level access.
"""

from .clustering import TopicClusteredService
from .summary import SummaryService
from . import s3_sync
from .services import get_topic_service, get_summary_service

__all__ = [
    "TopicClusteredService",
    "SummaryService",
    "s3_sync",
    "get_topic_service",
    "get_summary_service",
]
