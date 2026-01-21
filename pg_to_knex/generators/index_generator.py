"""Generates Knex TypeScript code for indexes."""

from ..models import Index


class IndexGenerator:
    """Generates Knex TypeScript code for indexes."""

    def generate(self, index: Index) -> str:
        """Generate createIndex code."""
        columns = ', '.join([f'"{col}"' for col in index.columns])

        if index.unique:
            return f'this.schema.alterTable("{index.table}", (table) => {{\n  table.unique([{columns}], "{index.name}")\n}})'
        else:
            return f'this.schema.alterTable("{index.table}", (table) => {{\n  table.index([{columns}], "{index.name}")\n}})'

    def generate_drop(self, index: Index) -> str:
        """Generate dropIndex code."""
        return f'this.schema.alterTable("{index.table}", (table) => {{\n  table.dropIndex([], "{index.name}")\n}})'
