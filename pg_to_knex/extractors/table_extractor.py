"""Extracts table definitions from PostgreSQL schema."""

import re
from typing import List, Optional

from ..models import Table, Column


class TableExtractor:
    """Extracts table definitions from PostgreSQL schema."""

    def extract(self, sql_content: str) -> List[Table]:
        """Parse SQL and extract all tables."""
        tables = []
        pattern = r'CREATE TABLE public\.(\w+) \((.*?)\);'
        matches = re.finditer(pattern, sql_content, re.DOTALL)

        for match in matches:
            table_name = match.group(1)
            columns_block = match.group(2)

            # Skip internal AdonisJS tables
            if table_name in ['adonis_schema', 'adonis_schema_versions']:
                continue

            table = self._parse_table(table_name, columns_block)
            tables.append(table)

        return tables

    def _parse_table(self, table_name: str, columns_block: str) -> Table:
        """Parse a single table definition."""
        table = Table(name=table_name)

        # Split into lines and process each
        lines = [line.strip().rstrip(',') for line in columns_block.split('\n') if line.strip()]

        # First pass: Extract CHECK constraints and identify enum-style ones
        enum_constraints = {}  # column_name → [enum_values]

        for line in lines:
            if line.startswith('CONSTRAINT') and 'CHECK' in line:
                # Try to parse as enum-style CHECK
                enum_data = self._parse_enum_check(line)
                if enum_data:
                    column_name, values = enum_data
                    enum_constraints[column_name] = values
                else:
                    # Not an enum - keep as regular CHECK constraint
                    table.check_constraints.append(line)

        # Second pass: Parse columns and associate enum values
        for line in lines:
            if not line.startswith('CONSTRAINT'):
                column = self._parse_column(line)
                if column:
                    # Check if this column has enum values
                    if column.name in enum_constraints:
                        column.enum_values = enum_constraints[column.name]
                    table.columns.append(column)

        return table

    def _parse_enum_check(self, check_constraint: str) -> Optional[tuple[str, List[str]]]:
        """
        Parse enum-style CHECK constraint and extract column name + values.

        Pattern: CONSTRAINT table_column_check CHECK ((column = ANY (ARRAY['val1'::text, 'val2'::text])))

        Returns: (column_name, [values]) or None if not an enum-style check
        """
        # Match the pattern: CONSTRAINT ... CHECK ((column = ANY (ARRAY['val1', 'val2'])))
        # We only care about the column name from the CHECK condition, not the constraint name
        match = re.match(
            r'CONSTRAINT\s+\w+\s+CHECK\s+\(\((\w+)\s+=\s+ANY\s+\(ARRAY\[(.+?)\]\)\)\)',
            check_constraint,
            re.DOTALL
        )

        if not match:
            return None

        column_name = match.group(1)  # Column name from CHECK condition
        values_str = match.group(2)    # The ARRAY contents

        # Parse enum values from ARRAY['val1'::text, 'val2'::text]
        # Extract quoted strings
        value_pattern = r"'([^']+)'"
        enum_values = re.findall(value_pattern, values_str)

        if not enum_values:
            return None

        return (column_name, enum_values)

    def _parse_column(self, col_definition: str) -> Optional[Column]:
        """Parse a single column definition."""
        # Match: "column_name type [constraints]"
        match = re.match(r'^(\w+)\s+(.+)$', col_definition)
        if not match:
            return None

        col_name = match.group(1)
        rest = match.group(2)

        # Extract type (everything before keywords or end)
        # Includes: word chars, spaces, parentheses, commas (for numeric(16,8)), brackets (for text[])
        type_match = re.match(r'^([\w\s\(\),\[\]]+?)(?:\s+(NOT\s+NULL|DEFAULT|CONSTRAINT)|$)', rest)
        if not type_match:
            return None

        col_type = type_match.group(1).strip()
        constraints = rest[len(col_type):].strip() if len(rest) > len(col_type) else ""

        # Parse constraints
        nullable = 'NOT NULL' not in constraints
        default = self._extract_default(constraints)
        # Detect primary key: id column that's NOT NULL (integer or uuid)
        is_pk = (col_name == 'id' and col_type in ('integer', 'uuid') and not nullable)

        return Column(
            name=col_name,
            pg_type=col_type,
            nullable=nullable,
            default=default,
            is_primary_key=is_pk
        )

    def _extract_default(self, constraints: str) -> Optional[str]:
        """Extract DEFAULT value from constraints."""
        # Match DEFAULT followed by value, stopping at keywords or end
        match = re.search(r'DEFAULT\s+(.+?)(?:\s+(?:NOT\s+NULL|CONSTRAINT)|$)', constraints)
        if not match:
            return None

        default_val = match.group(1).strip()

        # Remove PostgreSQL type casts (::type)
        # Examples: '0'::numeric, 'text'::character varying, 1::integer
        default_val = re.sub(r'::\w+(?:\s+\w+)*', '', default_val)

        # Strip quotes if present
        default_val = default_val.strip("'\"")

        # Wrap string values in quotes for TypeScript
        # Numbers and booleans should not be quoted
        if not default_val.replace('.', '').replace('-', '').isdigit() and default_val.lower() not in ['true', 'false', 'null']:
            return f"'{default_val}'"

        return default_val
