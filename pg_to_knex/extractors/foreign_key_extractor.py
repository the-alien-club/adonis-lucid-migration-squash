"""Extracts foreign key constraints from PostgreSQL schema."""

import re
from typing import List

from ..models import ForeignKey


class ForeignKeyExtractor:
    """Extracts foreign key constraints from PostgreSQL schema."""

    def extract(self, sql_content: str) -> List[ForeignKey]:
        """Parse SQL and extract all foreign keys."""
        foreign_keys = []
        # Pattern: ALTER TABLE ONLY table_name ADD CONSTRAINT fk_name
        #          FOREIGN KEY (column) REFERENCES ref_table(ref_column) [ON DELETE action]
        # ON DELETE can be: CASCADE, SET NULL, RESTRICT, NO ACTION
        pattern = r'ALTER TABLE ONLY public\.(\w+)\s+ADD CONSTRAINT \w+\s+FOREIGN KEY\s+\((\w+)\)\s+REFERENCES\s+public\.(\w+)\((\w+)\)(?:\s+ON DELETE\s+(SET NULL|CASCADE|RESTRICT|NO ACTION))?'
        matches = re.finditer(pattern, sql_content, re.DOTALL)

        for match in matches:
            foreign_keys.append(ForeignKey(
                table=match.group(1),
                column=match.group(2),
                ref_table=match.group(3),
                ref_column=match.group(4),
                on_delete=match.group(5)
            ))

        return foreign_keys
