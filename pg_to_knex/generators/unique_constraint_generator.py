"""Generates Knex TypeScript code for UNIQUE constraints."""

from ..models import UniqueConstraint


class UniqueConstraintGenerator:
    """Generates Knex TypeScript code for UNIQUE constraints."""

    def generate(self, constraint: UniqueConstraint) -> str:
        """Generate UNIQUE constraint code."""
        columns = ', '.join([f'"{col}"' for col in constraint.columns])

        return f'this.schema.alterTable("{constraint.table}", (table) => {{\n  table.unique([{columns}], "{constraint.name}")\n}})'

    def generate_drop(self, constraint: UniqueConstraint) -> str:
        """Generate drop UNIQUE constraint code."""
        return f'this.schema.alterTable("{constraint.table}", (table) => {{\n  table.dropUnique([], "{constraint.name}")\n}})'
