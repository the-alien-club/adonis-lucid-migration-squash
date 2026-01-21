"""Data models for representing database schema elements."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Column:
    """Represents a table column."""
    name: str
    pg_type: str
    nullable: bool
    default: Optional[str] = None
    is_primary_key: bool = False
    enum_values: Optional[List[str]] = None  # For ENUM columns extracted from CHECK constraints
    comment: Optional[str] = None  # Column comment/documentation


@dataclass
class Table:
    """Represents a database table."""
    name: str
    columns: List[Column] = field(default_factory=list)
    check_constraints: List[str] = field(default_factory=list)


@dataclass
class Index:
    """Represents a database index."""
    name: str
    table: str
    columns: List[str]
    unique: bool = False


@dataclass
class ForeignKey:
    """Represents a foreign key constraint."""
    table: str
    column: str
    ref_table: str
    ref_column: str
    on_delete: Optional[str] = None


@dataclass
class UniqueConstraint:
    """Represents a UNIQUE constraint."""
    name: str
    table: str
    columns: List[str]
