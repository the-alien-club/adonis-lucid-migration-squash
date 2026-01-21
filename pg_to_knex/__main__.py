"""Main entry point for the converter."""

import sys
from .parser import SchemaParser
from .verifier import SchemaVerifier


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: python -m pg_to_knex <input.sql> <output.ts>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    print(f"📖 Reading schema from: {input_file}")
    parser = SchemaParser()
    parser.parse(input_file)

    print(f"\n✅ Extracted:")
    print(f"   - {len(parser.tables)} tables")
    print(f"   - {len(parser.indexes)} indexes")
    print(f"   - {len(parser.unique_constraints)} unique constraints")
    print(f"   - {len(parser.foreign_keys)} foreign keys")

    # Verify extraction completeness
    print(f"\n🔍 Verifying schema conversion...")
    verifier = SchemaVerifier(input_file)
    result = verifier.verify(parser)
    verifier.print_report(result)

    if not result.passed:
        print("⚠️  Verification failed! Review errors above before using the migration.")
        print("    Continuing anyway, but please check the generated file carefully.")

    print(f"\n📝 Writing migration to: {output_file}")
    migration_code = parser.output()

    with open(output_file, 'w') as f:
        f.write(migration_code)

    print(f"✨ Done!")


if __name__ == '__main__':
    main()
