"""Generates Knex TypeScript code for tables."""

from typing import Optional
from ..models import Table, Column
from .type_mapper import TypeMapper


class TableGenerator:
    """Generates Knex TypeScript code for tables."""

    def __init__(self):
        self.type_mapper = TypeMapper()

    def generate(self, table: Table) -> str:
        """Generate createTable code for a table."""
        lines = [f'this.schema.createTable("{table.name}", (table) => {{']

        # Add columns
        for column in table.columns:
            col_code = self._generate_column(column)
            lines.append(f'  {col_code}')

        # Add complex CHECK constraints (those not converted to enums)
        for check_constraint in table.check_constraints:
            check_code = self._generate_check_constraint(check_constraint)
            if check_code:
                lines.append(f'  {check_code}')

        lines.append('})')
        return '\n'.join(lines)

    def _generate_check_constraint(self, check_constraint: str) -> Optional[str]:
        """Generate table.check() code for complex CHECK constraints."""
        import re

        # Parse: CONSTRAINT name CHECK (condition)
        match = re.match(r'CONSTRAINT\s+(\w+)\s+CHECK\s+\((.+)\)', check_constraint, re.DOTALL)
        if not match:
            return None

        constraint_name = match.group(1)
        condition = match.group(2).strip()

        # Remove outer parentheses if they exist
        if condition.startswith('(') and condition.endswith(')'):
            condition = condition[1:-1]

        # Generate table.check() call
        return f'table.check("{condition}", undefined, "{constraint_name}")'

    def _generate_column(self, column: Column) -> str:
        """Generate Knex code for a single column."""
        # Handle primary keys
        if column.is_primary_key:
            if column.pg_type == 'integer':
                # Auto-increment integer PK
                return f'table.increments("{column.name}").primary()'
            elif column.pg_type == 'uuid':
                # UUID PK with gen_random_uuid()
                code = f'table.uuid("{column.name}").primary()'
                if column.default:
                    code += f'.defaultTo(this.raw({column.default}))'
                return code

        # Handle ENUM columns (from CHECK constraints)
        if column.enum_values:
            enum_values_str = ', '.join([f"'{v}'" for v in column.enum_values])
            code = f'table.enum("{column.name}", [{enum_values_str}])'

            # Nullable/Not Nullable
            if column.nullable:
                code += '.nullable()'
            else:
                code += '.notNullable()'

            # Default value
            if column.default:
                code += f'.defaultTo({column.default})'

            # Comment
            if column.comment:
                escaped_comment = column.comment.replace('"', '\\"')
                code += f'.comment("{escaped_comment}")'

            return code

        # Map type
        method, options = self.type_mapper.map(column.pg_type)

        if options:
            code = f'table.{method}("{column.name}", {options})'
        else:
            code = f'table.{method}("{column.name}")'

        # Nullable/Not Nullable
        if column.nullable:
            code += '.nullable()'
        else:
            code += '.notNullable()'

        # Default value
        if column.default:
            code += f'.defaultTo({column.default})'

        # Comment
        if column.comment:
            # Escape quotes in comment
            escaped_comment = column.comment.replace('"', '\\"')
            code += f'.comment("{escaped_comment}")'

        return code

    def generate_drop(self, table: Table) -> str:
        """Generate dropTable code."""
        return f'this.schema.dropTableIfExists("{table.name}")'
