"""Verifies that schema conversion is complete and accurate."""

from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
import re


@dataclass
class VerificationResult:
    """Result of schema verification."""
    passed: bool
    errors: List[str]
    warnings: List[str]
    statistics: Dict[str, int]


class SchemaVerifier:
    """Verifies that PostgreSQL schema was completely converted to Knex."""

    def __init__(self, sql_file_path: str):
        """Initialize verifier with PostgreSQL schema."""
        with open(sql_file_path, 'r') as f:
            self.sql_content = f.read()

        # Extract expected counts from SQL
        self.expected_tables = self._count_tables()
        self.expected_columns = self._count_columns_per_table()
        self.expected_indexes = self._count_indexes()
        self.expected_foreign_keys = self._count_foreign_keys()
        self.expected_unique_constraints = self._count_unique_constraints()
        self.expected_check_constraints = self._count_check_constraints()

    def verify(self, parser) -> VerificationResult:
        """
        Verify that parser extracted all schema elements correctly.

        Args:
            parser: SchemaParser instance after parse() was called

        Returns:
            VerificationResult with detailed comparison
        """
        errors = []
        warnings = []

        # 1. Verify table count
        actual_tables = len(parser.tables)
        if actual_tables != self.expected_tables:
            errors.append(
                f"Table count mismatch: expected {self.expected_tables}, got {actual_tables}"
            )

        # 2. Verify columns per table
        for table in parser.tables:
            expected_cols = self.expected_columns.get(table.name, 0)
            actual_cols = len(table.columns)
            if actual_cols != expected_cols:
                errors.append(
                    f"Table '{table.name}': expected {expected_cols} columns, got {actual_cols}"
                )

        # 3. Verify total columns
        total_actual_cols = sum(len(t.columns) for t in parser.tables)
        total_expected_cols = sum(self.expected_columns.values())
        if total_actual_cols != total_expected_cols:
            errors.append(
                f"Total columns: expected {total_expected_cols}, got {total_actual_cols}"
            )

        # 4. Verify indexes
        actual_indexes = len(parser.indexes)
        if actual_indexes != self.expected_indexes:
            errors.append(
                f"Index count mismatch: expected {self.expected_indexes}, got {actual_indexes}"
            )

        # 5. Verify foreign keys
        actual_fks = len(parser.foreign_keys)
        if actual_fks != self.expected_foreign_keys:
            errors.append(
                f"Foreign key count mismatch: expected {self.expected_foreign_keys}, got {actual_fks}"
            )

        # 6. Verify UNIQUE constraints
        actual_unique = len(parser.unique_constraints)
        if actual_unique != self.expected_unique_constraints:
            errors.append(
                f"UNIQUE constraint count mismatch: expected {self.expected_unique_constraints}, got {actual_unique}"
            )

        # 7. Verify CHECK constraints + ENUMs
        # Some CHECK constraints are converted to .enum() columns
        actual_checks = sum(len(t.check_constraints) for t in parser.tables)
        actual_enums = sum(1 for t in parser.tables for c in t.columns if c.enum_values)
        total_constraint_like = actual_checks + actual_enums

        if total_constraint_like != self.expected_check_constraints:
            errors.append(
                f"CHECK/ENUM count mismatch: expected {self.expected_check_constraints}, got {actual_checks} CHECKs + {actual_enums} ENUMs = {total_constraint_like}"
            )

        # 8. Verify primary keys (all tables should have PKs)
        tables_without_pk = [t.name for t in parser.tables if not any(c.is_primary_key for c in t.columns)]
        if tables_without_pk:
            warnings.append(
                f"Tables without primary key: {', '.join(tables_without_pk)}"
            )

        # 9. Verify nullable columns are explicitly marked
        for table in parser.tables:
            for col in table.columns:
                if col.nullable and col.name == 'id':
                    warnings.append(
                        f"Table '{table.name}': 'id' column is nullable (unusual)"
                    )

        # 10. Verify column type coverage
        unmapped_types = self._check_unmapped_types(parser)
        if unmapped_types:
            warnings.append(
                f"Potentially unmapped PostgreSQL types: {', '.join(unmapped_types)}"
            )

        # Statistics
        statistics = {
            'tables': actual_tables,
            'columns': total_actual_cols,
            'indexes': actual_indexes,
            'unique_constraints': actual_unique,
            'enum_columns': actual_enums,
            'check_constraints': actual_checks,
            'foreign_keys': actual_fks,
        }

        passed = len(errors) == 0

        return VerificationResult(
            passed=passed,
            errors=errors,
            warnings=warnings,
            statistics=statistics
        )

    def _count_tables(self) -> int:
        """Count CREATE TABLE statements (excluding internal tables)."""
        pattern = r'CREATE TABLE public\.(\w+)'
        matches = re.findall(pattern, self.sql_content)
        # Exclude AdonisJS internal tables
        return len([t for t in matches if t not in ['adonis_schema', 'adonis_schema_versions']])

    def _count_columns_per_table(self) -> Dict[str, int]:
        """Count columns for each table."""
        columns_per_table = {}
        pattern = r'CREATE TABLE public\.(\w+) \((.*?)\);'
        matches = re.finditer(pattern, self.sql_content, re.DOTALL)

        for match in matches:
            table_name = match.group(1)
            if table_name in ['adonis_schema', 'adonis_schema_versions']:
                continue

            columns_block = match.group(2)
            # Count lines that are column definitions (not CONSTRAINT lines)
            lines = [line.strip() for line in columns_block.split('\n') if line.strip()]
            col_count = sum(1 for line in lines if not line.startswith('CONSTRAINT'))

            columns_per_table[table_name] = col_count

        return columns_per_table

    def _count_indexes(self) -> int:
        """Count CREATE INDEX statements."""
        pattern = r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+\w+\s+ON\s+public\.'
        return len(re.findall(pattern, self.sql_content))

    def _count_foreign_keys(self) -> int:
        """Count foreign key constraints."""
        pattern = r'ADD CONSTRAINT \w+\s+FOREIGN KEY'
        return len(re.findall(pattern, self.sql_content))

    def _count_unique_constraints(self) -> int:
        """Count UNIQUE constraints."""
        pattern = r'ADD CONSTRAINT \w+\s+UNIQUE\s+\('
        return len(re.findall(pattern, self.sql_content))

    def _count_check_constraints(self) -> int:
        """Count CHECK constraints."""
        pattern = r'CONSTRAINT \w+\s+CHECK\s+\('
        return len(re.findall(pattern, self.sql_content))

    def _check_unmapped_types(self, parser) -> Set[str]:
        """Check for PostgreSQL types that might not be mapped."""
        # Extract all types from SQL - ONLY within CREATE TABLE blocks
        sql_types = set()

        # Parse CREATE TABLE blocks
        table_pattern = r'CREATE TABLE public\.(\w+) \((.*?)\);'
        table_matches = re.finditer(table_pattern, self.sql_content, re.DOTALL)

        for table_match in table_matches:
            table_name = table_match.group(1)
            if table_name in ['adonis_schema', 'adonis_schema_versions']:
                continue

            columns_block = table_match.group(2)

            # Parse column definitions (not CONSTRAINT lines)
            lines = [line.strip().rstrip(',') for line in columns_block.split('\n') if line.strip()]
            for line in lines:
                if line.startswith('CONSTRAINT'):
                    continue

                # Extract column type
                col_match = re.match(r'^(\w+)\s+([\w\s\(\),\[\]]+?)(?:\s+(?:NOT\s+NULL|DEFAULT|CONSTRAINT)|$)', line)
                if col_match:
                    type_str = col_match.group(2).strip()
                    base_type = type_str.split('(')[0].strip().rstrip('[]')  # Remove [] for arrays
                    sql_types.add(base_type)

        # Known mapped types (from TypeMapper)
        mapped_types = {
            'integer', 'bigint', 'smallint', 'text', 'character varying',
            'varchar', 'boolean', 'timestamp with time zone',
            'timestamp without time zone', 'timestamp', 'date', 'time',
            'json', 'jsonb', 'uuid', 'numeric', 'real', 'double precision'
        }

        # Find unmapped types
        unmapped = sql_types - mapped_types

        return unmapped

    def print_report(self, result: VerificationResult):
        """Print a formatted verification report."""
        print("\n" + "="*70)
        print("SCHEMA VERIFICATION REPORT")
        print("="*70)

        print("\n📊 Statistics:")
        for key, value in result.statistics.items():
            print(f"   {key:20s}: {value}")

        if result.errors:
            print(f"\n❌ Errors ({len(result.errors)}):")
            for error in result.errors:
                print(f"   - {error}")

        if result.warnings:
            print(f"\n⚠️  Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"   - {warning}")

        if result.passed:
            print("\n✅ VERIFICATION PASSED - Schema conversion is complete!")
        else:
            print("\n❌ VERIFICATION FAILED - Schema conversion has errors!")

        print("="*70 + "\n")
