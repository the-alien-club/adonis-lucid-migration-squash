"""Generates Knex TypeScript code for CHECK constraints."""

import re
from typing import Optional


class CheckConstraintGenerator:
    """Generates Knex TypeScript code for CHECK constraints."""

    def generate(self, table_name: str, check_constraint: str) -> Optional[str]:
        """
        Generate CHECK constraint code using raw SQL.

        Args:
            table_name: Name of the table
            check_constraint: Raw CHECK constraint from PostgreSQL
                Example: "CONSTRAINT tags_category_check CHECK ((category = ANY (ARRAY[...])))"

        Returns:
            Knex raw SQL code or None if parsing fails
        """
        # Parse constraint name and check condition
        match = re.match(r'CONSTRAINT\s+(\w+)\s+CHECK\s+\((.+)\)', check_constraint, re.DOTALL)
        if not match:
            return None

        constraint_name = match.group(1)
        check_condition = match.group(2).strip()

        # Generate ALTER TABLE with raw SQL
        return f'this.schema.raw(`ALTER TABLE "{table_name}" ADD CONSTRAINT {constraint_name} CHECK ({check_condition})`)'

    def generate_drop(self, table_name: str, check_constraint: str) -> Optional[str]:
        """Generate DROP CHECK constraint code."""
        # Extract constraint name
        match = re.match(r'CONSTRAINT\s+(\w+)', check_constraint)
        if not match:
            return None

        constraint_name = match.group(1)
        return f'this.schema.raw(`ALTER TABLE "{table_name}" DROP CONSTRAINT IF EXISTS {constraint_name}`)'
