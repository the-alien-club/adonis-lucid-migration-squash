"""Extractors for parsing PostgreSQL schema into structured data."""

from .table_extractor import TableExtractor
from .index_extractor import IndexExtractor
from .foreign_key_extractor import ForeignKeyExtractor
from .unique_constraint_extractor import UniqueConstraintExtractor
from .comment_extractor import CommentExtractor

__all__ = ['TableExtractor', 'IndexExtractor', 'ForeignKeyExtractor', 'UniqueConstraintExtractor', 'CommentExtractor']
