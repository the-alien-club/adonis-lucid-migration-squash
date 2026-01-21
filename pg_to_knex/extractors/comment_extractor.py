"""Extracts column comments from PostgreSQL schema."""

import re
from typing import Dict, Tuple


class CommentExtractor:
    """Extracts column comments from PostgreSQL schema."""

    def extract(self, sql_content: str) -> Dict[Tuple[str, str], str]:
        """
        Parse SQL and extract all column comments.

        Returns:
            Dict mapping (table_name, column_name) → comment_text
        """
        comments = {}

        # Pattern: COMMENT ON COLUMN public.table_name.column_name IS 'comment text';
        pattern = r"COMMENT ON COLUMN public\.(\w+)\.(\w+) IS '(.+?)';"
        matches = re.finditer(pattern, sql_content, re.DOTALL)

        for match in matches:
            table_name = match.group(1)
            column_name = match.group(2)
            comment_text = match.group(3)

            comments[(table_name, column_name)] = comment_text

        return comments
