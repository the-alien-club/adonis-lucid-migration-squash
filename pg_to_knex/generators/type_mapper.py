"""Maps PostgreSQL types to Knex methods."""


class TypeMapper:
    """Maps PostgreSQL types to Knex methods."""

    @staticmethod
    def map(pg_type: str) -> tuple[str, str]:
        """
        Map PostgreSQL type to Knex method and options.
        Returns: (method_name, method_options)
        """
        # Handle array types (text[], integer[], etc.)
        if pg_type.endswith('[]'):
            # Use specificType for arrays since Knex doesn't have native array() method
            # Convert text[] to TEXT ARRAY format (matches existing migrations)
            base_array_type = pg_type[:-2].strip().upper()
            return ('specificType', f'`{base_array_type} ARRAY`')

        # Extract base type and parameters
        import re

        # Handle character varying(N) and varchar(N) with specific length
        varchar_match = re.match(r'(character varying|varchar)\((\d+)\)', pg_type)
        if varchar_match:
            length = varchar_match.group(2)
            return ('string', length)

        # Handle numeric(precision, scale)
        numeric_match = re.match(r'numeric\((\d+),(\d+)\)', pg_type)
        if numeric_match:
            precision = numeric_match.group(1)
            scale = numeric_match.group(2)
            return ('decimal', f'{precision}, {scale}')

        base_type = pg_type.split('(')[0].strip()

        # Special handling for timestamps
        if base_type == 'timestamp with time zone':
            return ('timestamp', '{ useTz: true }')
        elif base_type in ('timestamp without time zone', 'timestamp'):
            return ('timestamp', '')

        type_map = {
            'integer': 'integer',
            'bigint': 'bigInteger',
            'smallint': 'integer',
            'text': 'text',
            'character varying': 'string',
            'varchar': 'string',
            'boolean': 'boolean',
            'date': 'date',
            'time': 'time',
            'json': 'json',
            'jsonb': 'jsonb',
            'uuid': 'uuid',
            'numeric': 'decimal',
            'real': 'float',
            'double precision': 'double',
        }

        method = type_map.get(base_type, 'text')
        return (method, '')
