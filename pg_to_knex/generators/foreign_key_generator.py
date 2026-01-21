"""Generates Knex TypeScript code for foreign keys."""

from ..models import ForeignKey


class ForeignKeyGenerator:
    """Generates Knex TypeScript code for foreign keys."""

    def generate(self, fk: ForeignKey) -> str:
        """Generate foreign key constraint code."""
        code = f'this.schema.alterTable("{fk.table}", (table) => {{\n  table.foreign("{fk.column}").references("{fk.ref_column}").inTable("{fk.ref_table}")'

        if fk.on_delete:
            code += f'.onDelete("{fk.on_delete}")'

        code += '\n})'
        return code

    def generate_drop(self, fk: ForeignKey) -> str:
        """Generate drop foreign key code."""
        return f'this.schema.alterTable("{fk.table}", (table) => {{\n  table.dropForeign(["{fk.column}"])\n}})'
