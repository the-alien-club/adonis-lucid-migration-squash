"""Extracts index definitions from PostgreSQL schema."""

import re
from typing import List

from ..models import Index


class IndexExtractor:
    """Extracts index definitions from PostgreSQL schema."""

    def extract(self, sql_content: str) -> List[Index]:
        """Parse SQL and extract all indexes."""
        indexes = []
        # Pattern: CREATE [UNIQUE] INDEX index_name ON table_name USING method (columns)
        pattern = r'CREATE\s+(UNIQUE\s+)?INDEX\s+(\w+)\s+ON\s+public\.(\w+)\s+USING\s+\w+\s+\((.*?)\)'
        matches = re.finditer(pattern, sql_content, re.DOTALL)

        for match in matches:
            unique = bool(match.group(1))
            index_name = match.group(2)
            table_name = match.group(3)
            columns_str = match.group(4)

            # Parse column list
            columns = [col.strip() for col in columns_str.split(',')]

            indexes.append(Index(
                name=index_name,
                table=table_name,
                columns=columns,
                unique=unique
            ))

        return indexes
