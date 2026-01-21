# AdonisJS/Lucid Migration Squash Tool

**Convert PostgreSQL schema dumps to clean AdonisJS/Knex TypeScript migrations**

Squash 100+ migrations into a single, optimized baseline migration with automatic verification and intelligent enum detection.

---

## ⚠️ Disclaimer

**This tool was tested on a single production project and may not work for all PostgreSQL schemas or Knex configurations.**

- ✅ Tested on: AdonisJS 6, PostgreSQL 16, Knex migrations
- ⚠️ Not extensively tested on edge cases
- ⚠️ Always verify the output before using in production
- ⚠️ No warranty or guarantee provided

**Use at your own risk.** Always test generated migrations on a fresh database before deploying.

---

## 🎯 What It Does

Converts a PostgreSQL schema dump (from `pg_dump`) into clean, optimized AdonisJS/Knex migration code:

**Input:** PostgreSQL schema dump (3000+ lines of SQL)
**Output:** Clean TypeScript migration (1000 lines of Knex code)

### Features

- ✅ **Smart Enum Detection** - Converts `CHECK (column = ANY (ARRAY['val1', 'val2']))` to `table.enum()`
- ✅ **Grouped Operations** - Combines multiple `alterTable` calls per table (50% size reduction)
- ✅ **Complete Type Mapping** - Arrays, UUIDs, numerics, timestamps, varchar lengths, etc.
- ✅ **Built-in Verification** - Ensures 100% conversion accuracy
- ✅ **Clean Code** - Minimal raw SQL, proper Knex methods
- ✅ **Column Comments** - Preserves `.comment()` documentation

---

## 🏗️ Architecture

Clean, maintainable, extensible design:

```
pg_to_knex/
├── models.py                    # Data structures (Column, Table, Index, FK, etc.)
├── extractors/                  # SQL → Data Structures
│   ├── table_extractor.py       # Parse CREATE TABLE
│   ├── index_extractor.py       # Parse CREATE INDEX
│   ├── foreign_key_extractor.py # Parse ALTER TABLE ... FOREIGN KEY
│   ├── unique_constraint_extractor.py
│   └── comment_extractor.py     # Parse COMMENT ON COLUMN
├── generators/                  # Data Structures → Knex Code
│   ├── table_generator.py       # Generate createTable()
│   ├── index_generator.py       # Generate index()/unique()
│   ├── foreign_key_generator.py # Generate foreign()
│   ├── unique_constraint_generator.py
│   ├── check_constraint_generator.py
│   └── type_mapper.py           # PostgreSQL types → Knex types
├── parser.py                    # Orchestrator
└── verifier.py                  # Verification engine
```

**Design Principles:**
- Single Responsibility - Each component does ONE thing
- Easy to extend - Add new feature? Create new extractor/generator
- Testable - Each component can be tested independently
- Maintainable - 50-100 line files instead of 500-line functions

---

## 📦 Installation

### Requirements

- Python 3.10+
- AdonisJS 5+ / Knex.js
- PostgreSQL database

### Setup

```bash
# Clone the repo
git clone <repo-url>
cd adonis-lucid-migration-squash

# No dependencies required - uses Python stdlib only!
```

---

## 🚀 Usage

### Step 1: Run All Existing Migrations

Ensure your database has all migrations applied:

```bash
cd your-adonisjs-project
node ace migration:run
```

### Step 2: Dump PostgreSQL Schema

```bash
# From Docker container
docker exec postgres-container pg_dump -U user -d database -s --no-owner --no-acl > schema.sql

# Or directly
pg_dump -U user -d database -s --no-owner --no-acl > schema.sql
```

### Step 3: Convert to Knex Migration

```bash
cd path/to/adonis-lucid-migration-squash
python -m pg_to_knex schema.sql output_migration.ts
```

**Output:**

```
📖 Reading schema from: schema.sql

✅ Extracted:
   - 31 tables
   - 111 indexes
   - 25 unique constraints
   - 59 foreign keys

🔍 Verifying schema conversion...

======================================================================
SCHEMA VERIFICATION REPORT
======================================================================

📊 Statistics:
   tables              : 31
   columns             : 354
   indexes             : 111
   unique_constraints  : 25
   enum_columns        : 17
   check_constraints   : 1
   foreign_keys        : 59

✅ VERIFICATION PASSED - Schema conversion is complete!
======================================================================

📝 Writing migration to: output_migration.ts
✨ Done!
```

### Step 4: Archive Old Migrations

```bash
cd your-adonisjs-project/database/migrations

# Move old migrations outside the migrations folder
# (AdonisJS scans all .ts files in migrations/)
mkdir -p ../archive
mv *.ts ../archive/

# Copy your new baseline
cp /path/to/output_migration.ts ./0_baseline_migration.ts
```

### Step 5: Test on Fresh Database

```bash
# Create test database
createdb test_baseline

# Run baseline migration
DB_DATABASE=test_baseline node ace migration:run

# Verify it worked
psql -d test_baseline -c "\dt"
```

### Step 6: Verify Schema Match (Recommended)

```bash
# Dump the new schema
pg_dump -d test_baseline -s --no-owner --no-acl > new_schema.sql

# Compare (should only have \restrict token differences)
diff <(grep -v "\\restrict" schema.sql) <(grep -v "\\restrict" new_schema.sql)

# If output is empty: ✅ PERFECT MATCH!
```

---

## 📊 Example Output

### Before (Raw SQL from CHECK constraint):

```sql
CONSTRAINT jobs_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'running'::text, 'completed'::text])))
```

### After (Clean Knex enum):

```typescript
table.enum('status', ['pending', 'running', 'completed']).notNullable()
```

### Before (Multiple alterTable calls):

```typescript
this.schema.alterTable("users", (table) => {
  table.index(["email"], "idx_users_email")
})

this.schema.alterTable("users", (table) => {
  table.index(["org_id"], "idx_users_org")
})

this.schema.alterTable("users", (table) => {
  table.foreign("org_id").references("id").inTable("organizations")
})
```

### After (Grouped operations):

```typescript
this.schema.alterTable("users", (table) => {
  table.index(["email"], "idx_users_email")
  table.index(["org_id"], "idx_users_org")
  table.foreign("org_id").references("id").inTable("organizations")
})
```

---

## 🔬 What Gets Converted

### ✅ Fully Supported

| PostgreSQL Feature | Knex Output | Notes |
|-------------------|-------------|-------|
| **Tables** | `createTable()` | All standard table definitions |
| **Columns** | `table.type()` | All PostgreSQL types mapped |
| **Primary Keys** | `table.increments()` or `table.uuid().primary()` | Integer and UUID PKs |
| **Timestamps** | `table.timestamp({ useTz: true })` | Timezone-aware |
| **Arrays** | `table.specificType('TEXT ARRAY')` | PostgreSQL array types |
| **ENUM CHECKs** | `table.enum(['val1', 'val2'])` | Smart detection from CHECK constraints |
| **Complex CHECKs** | `table.check()` | OR conditions, expressions |
| **Indexes** | `table.index()` | Single and multi-column |
| **UNIQUE** | `table.unique()` | Grouped with indexes |
| **Foreign Keys** | `table.foreign().references()` | With ON DELETE actions |
| **Column Comments** | `table.comment("...")` | Documentation preserved |
| **VARCHAR Lengths** | `table.string(255)` | Preserves specific lengths |
| **Numeric Precision** | `table.decimal(16, 8)` | Preserves precision/scale |

### ⚠️ Not Supported

- Table-level comments (COMMENT ON TABLE)
- Database-level settings
- Extensions (CREATE EXTENSION)
- Views, triggers, functions
- Partitions
- Custom types (ENUM types)

---

## 🧪 Verification

The tool includes automatic verification that checks:

1. **Table count** - All tables extracted
2. **Column count** - Per table and total
3. **Index count** - All indexes present
4. **Foreign key count** - All FKs extracted
5. **UNIQUE constraint count** - All unique constraints
6. **CHECK/ENUM count** - Converted constraints
7. **Primary keys** - All tables have PKs
8. **Type coverage** - All PostgreSQL types mapped

**If verification fails**, the tool reports specific errors before generating output.

---

## 📝 Generated Migration Structure

```typescript
import { BaseSchema } from "@adonisjs/lucid/schema"

export default class BaselineMigration extends BaseSchema {
  async up() {
    // 1. Create all tables with columns, enums, and inline CHECKs
    this.schema.createTable("users", (table) => {
      table.increments("id").primary()
      table.string("email", 255).notNullable()
      table.enum("status", ['active', 'inactive']).notNullable()
      table.timestamp("created_at", { useTz: true }).notNullable()
    })

    // 2. Grouped alterTable operations (indexes, unique, FKs per table)
    this.schema.alterTable("users", (table) => {
      table.index(["email"], "idx_users_email")
      table.unique(["email"], "users_email_unique")
      table.foreign("org_id").references("id").inTable("organizations").onDelete("CASCADE")
    })
  }

  async down() {
    // Reverse order - FKs first, then tables
    this.schema.alterTable("users", (table) => {
      table.dropForeign(["org_id"])
      table.dropUnique([], "users_email_unique")
      table.dropIndex([], "idx_users_email")
    })

    this.schema.dropTableIfExists("users")
  }
}
```

---

## 🤔 When to Squash Migrations

### Good Times to Squash:

- ✅ **100+ migrations** accumulated
- ✅ **Before major version release** (v1.0, v2.0, etc.)
- ✅ **All environments in sync** (dev/staging/prod on same version)
- ✅ **Pre-production** cleanup

### Don't Squash If:

- ❌ **Different environments on different versions**
- ❌ **Production already deployed** with incremental migrations
- ❌ **Active feature branches** with pending migrations

---

## 💡 Benefits

### Before Squashing:
- 📁 65 migration files
- ⏱️ Fresh database setup: ~90 seconds
- 😰 Duplicate migration numbers (merge conflicts)
- 🤯 Hard to understand schema evolution

### After Squashing:
- 📁 1 baseline migration
- ⏱️ Fresh database setup: ~1.5 seconds (60x faster!)
- ✅ Clean foundation for future migrations
- 📖 Easy to understand current schema
- 🚀 Faster CI/CD pipelines
- 🎯 Prevents migration number conflicts

---

## 🛠️ Advanced Usage

### Custom Table Filtering

Edit `extractors/table_extractor.py` to skip specific tables:

```python
if table_name in ['adonis_schema', 'adonis_schema_versions', 'your_custom_table']:
    continue
```

### Adding New Features

Want to support a new PostgreSQL feature? Add:

1. **Data model** in `models.py`
2. **Extractor** in `extractors/your_feature_extractor.py`
3. **Generator** in `generators/your_feature_generator.py`
4. **Integrate** in `parser.py`

Example: Adding sequence support would require `SequenceExtractor` and `SequenceGenerator`.

---

## 🐛 Troubleshooting

### "Type XYZ not mapped"

Add the type to `generators/type_mapper.py`:

```python
type_map = {
    # ... existing types
    'your_type': 'knex_method',
}
```

### Verification Failed

Check the error message - it tells you exactly what's missing:

```
❌ Errors:
   - Table 'users': expected 10 columns, got 9
```

This means one column wasn't extracted. Check `extractors/table_extractor.py` regex patterns.

### Migration Fails to Run

1. Check syntax errors with `tsc --noEmit`
2. Test on fresh database first
3. Check AdonisJS/Knex version compatibility

---

## 📚 How It Works

### Architecture Flow:

```
PostgreSQL Schema Dump
        ↓
   [EXTRACTORS]
   Parse SQL → Data Structures
        ↓
   Column, Table, Index, FK objects
        ↓
   [GENERATORS]
   Data → Knex TypeScript Code
        ↓
   [VERIFIER]
   Verify completeness
        ↓
   Final Migration File
```

### Key Innovation: Enum Detection

The tool analyzes CHECK constraints:

```sql
CONSTRAINT status_check CHECK ((status = ANY (ARRAY['active'::text, 'inactive'::text])))
```

And intelligently converts to:

```typescript
table.enum('status', ['active', 'inactive'])
```

Instead of raw SQL:

```typescript
this.schema.raw(`ALTER TABLE "users" ADD CONSTRAINT ...`)
```

---

## 📖 Real-World Example

**Project:** DataStreaming Platform (6 months development)

**Before:**
- 65 migration files (duplicates, conflicts)
- 2077 lines of generated baseline (with raw SQL)
- 90 seconds for fresh DB setup

**After:**
- 1 baseline migration
- 1093 lines of clean Knex code
- 1.5 seconds for fresh DB setup
- ZERO schema differences (verified with pg_dump diff)

**Conversion Coverage:**
- 31 tables
- 354 columns
- 111 indexes
- 25 unique constraints
- 17 enums (from CHECK constraints)
- 59 foreign keys
- 14 column comments

---

## 🧪 Testing Your Output

Always verify the generated migration works correctly:

```bash
# 1. Create test database
createdb migration_test

# 2. Run baseline migration
DB_DATABASE=migration_test node ace migration:run

# 3. Dump new schema
pg_dump -d migration_test -s --no-owner --no-acl > new_schema.sql

# 4. Compare with original
diff <(grep -v "\\restrict" original_schema.sql) \
     <(grep -v "\\restrict" new_schema.sql)

# 5. If diff is empty: ✅ PERFECT MATCH!
```

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Support for database views
- [ ] Support for custom ENUM types
- [ ] Support for triggers/functions
- [ ] Better handling of complex CHECK constraints
- [ ] CLI with better error messages
- [ ] Unit tests for each extractor/generator
- [ ] Support for other SQL dialects (MySQL, SQLite)

**To contribute:**
1. Fork the repo
2. Create feature branch
3. Add tests
4. Submit PR

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

## 🙏 Credits

Built during migration chaos at DataStreaming Platform.

**Problem:** 65 migrations, duplicates, slow CI/CD
**Solution:** Clean architecture, smart conversion, automatic verification

**Tech Stack:**
- Python 3 (stdlib only - no dependencies!)
- Regular expressions for SQL parsing
- Dataclasses for clean data modeling

---

## 💬 Support

**This is an experimental tool.** No official support provided.

If you find bugs or have suggestions:
- Open an issue
- Submit a PR
- Fork and improve!

**Remember:** Always test on a fresh database before using in production!

---

**Made with ❤️ and lots of regex** 🎯
