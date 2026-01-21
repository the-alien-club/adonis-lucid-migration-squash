"""Extracts UNIQUE constraints from PostgreSQL schema."""

import re
from typing import List

from ..models import UniqueConstraint


class UniqueConstraintExtractor:
    """Extracts UNIQUE constraints from PostgreSQL schema."""

    def extract(self, sql_content: str) -> List[UniqueConstraint]:
        """Parse SQL and extract all UNIQUE constraints."""
        constraints = []

        # Pattern: ALTER TABLE table_name ADD CONSTRAINT constraint_name UNIQUE (columns)
        pattern = r'ALTER TABLE (?:ONLY )?public\.(\w+)\s+ADD CONSTRAINT (\w+)\s+UNIQUE\s+\((.*?)\)'
        matches = re.finditer(pattern, sql_content, re.DOTALL)

        for match in matches:
            table_name = match.group(1)
            constraint_name = match.group(2)
            columns_str = match.group(3)

            # Parse column list
            columns = [col.strip() for col in columns_str.split(',')]

            constraints.append(UniqueConstraint(
                name=constraint_name,
                table=table_name,
                columns=columns
            ))

        return constraints
