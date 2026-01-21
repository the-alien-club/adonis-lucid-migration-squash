"""Orchestrates extraction and generation of migration code."""

from typing import List

from .models import Table, Index, ForeignKey, UniqueConstraint
from .extractors import TableExtractor, IndexExtractor, ForeignKeyExtractor, UniqueConstraintExtractor, CommentExtractor
from .generators import TableGenerator, IndexGenerator, ForeignKeyGenerator, UniqueConstraintGenerator, CheckConstraintGenerator


class SchemaParser:
    """Orchestrates extraction and generation of migration code."""

    def __init__(self):
        # Extractors
        self.table_extractor = TableExtractor()
        self.index_extractor = IndexExtractor()
        self.fk_extractor = ForeignKeyExtractor()
        self.unique_extractor = UniqueConstraintExtractor()
        self.comment_extractor = CommentExtractor()

        # Generators
        self.table_generator = TableGenerator()
        self.index_generator = IndexGenerator()
        self.fk_generator = ForeignKeyGenerator()
        self.unique_generator = UniqueConstraintGenerator()
        self.check_generator = CheckConstraintGenerator()

        # Storage
        self.tables: List[Table] = []
        self.indexes: List[Index] = []
        self.foreign_keys: List[ForeignKey] = []
        self.unique_constraints: List[UniqueConstraint] = []

    def parse(self, sql_file_path: str):
        """Parse SQL file and extract all schema elements."""
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()

        # Extract all elements
        self.tables = self.table_extractor.extract(sql_content)
        self.indexes = self.index_extractor.extract(sql_content)
        self.foreign_keys = self.fk_extractor.extract(sql_content)
        self.unique_constraints = self.unique_extractor.extract(sql_content)
        comments = self.comment_extractor.extract(sql_content)

        # Associate comments with columns
        for table in self.tables:
            for column in table.columns:
                comment_key = (table.name, column.name)
                if comment_key in comments:
                    column.comment = comments[comment_key]

    def output(self) -> str:
        """Generate final TypeScript migration file."""
        up_statements = []
        down_statements = []

        # 1. Create tables (includes CHECK constraints inline)
        for table in self.tables:
            up_statements.append(self.table_generator.generate(table))
            down_statements.insert(0, self.table_generator.generate_drop(table))

        # 2. Group alterTable operations by table name for efficiency
        alter_table_ops = self._group_alter_table_operations()

        for table_name, (up_ops, down_ops) in alter_table_ops.items():
            if up_ops:
                # Generate single alterTable with all operations
                up_code = f'this.schema.alterTable("{table_name}", (table) => {{\n'
                up_code += '\n'.join([f'  {op}' for op in up_ops])
                up_code += '\n})'
                up_statements.append(up_code)

            if down_ops:
                # Generate single alterTable for rollback
                down_code = f'this.schema.alterTable("{table_name}", (table) => {{\n'
                down_code += '\n'.join([f'  {op}' for op in down_ops])
                down_code += '\n})'
                down_statements.insert(0, down_code)

        up_code = '\n\n'.join(up_statements)
        down_code = '\n\n'.join(down_statements)

        return f'''import {{ BaseSchema }} from "@adonisjs/lucid/schema"

export default class BaselineMigration extends BaseSchema {{
  async up() {{
{self._indent(up_code, 4)}
  }}

  async down() {{
{self._indent(down_code, 4)}
  }}
}}
'''

    def _group_alter_table_operations(self) -> dict:
        """
        Group all alterTable operations (indexes, unique, FKs) by table name.

        Returns:
            Dict[table_name, (up_operations[], down_operations[])]
        """
        from collections import defaultdict

        grouped = defaultdict(lambda: ([], []))

        # Group indexes by table
        for index in self.indexes:
            up_op, down_op = self._generate_index_inline(index)
            grouped[index.table][0].append(up_op)
            grouped[index.table][1].insert(0, down_op)

        # Group UNIQUE constraints by table
        for unique in self.unique_constraints:
            up_op, down_op = self._generate_unique_inline(unique)
            grouped[unique.table][0].append(up_op)
            grouped[unique.table][1].insert(0, down_op)

        # Group foreign keys by table
        for fk in self.foreign_keys:
            up_op, down_op = self._generate_fk_inline(fk)
            grouped[fk.table][0].append(up_op)
            grouped[fk.table][1].insert(0, down_op)

        return dict(grouped)

    def _generate_index_inline(self, index: Index) -> tuple[str, str]:
        """Generate index operations for inline use in alterTable."""
        columns = ', '.join([f'"{col}"' for col in index.columns])

        if index.unique:
            up = f'table.unique([{columns}], "{index.name}")'
        else:
            up = f'table.index([{columns}], "{index.name}")'

        down = f'table.dropIndex([], "{index.name}")'

        return (up, down)

    def _generate_unique_inline(self, unique: UniqueConstraint) -> tuple[str, str]:
        """Generate UNIQUE operations for inline use in alterTable."""
        columns = ', '.join([f'"{col}"' for col in unique.columns])
        up = f'table.unique([{columns}], "{unique.name}")'
        down = f'table.dropUnique([], "{unique.name}")'
        return (up, down)

    def _generate_fk_inline(self, fk: ForeignKey) -> tuple[str, str]:
        """Generate foreign key operations for inline use in alterTable."""
        up = f'table.foreign("{fk.column}").references("{fk.ref_column}").inTable("{fk.ref_table}")'
        if fk.on_delete:
            up += f'.onDelete("{fk.on_delete}")'

        down = f'table.dropForeign(["{fk.column}"])'
        return (up, down)

    def _indent(self, text: str, spaces: int) -> str:
        """Indent all lines in text."""
        indent = ' ' * spaces
        return '\n'.join(indent + line if line.strip() else '' for line in text.split('\n'))
