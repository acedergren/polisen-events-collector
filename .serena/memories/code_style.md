# Code Style and Conventions

## Python Code Style
- **Type Hints**: Used for function parameters and return types
- **Docstrings**: Triple-quoted strings for classes and methods
- **Naming**:
  - Classes: PascalCase (e.g., `PolisenCollector`)
  - Functions/methods: snake_case (e.g., `fetch_events`, `get_last_seen_ids`)
  - Constants: UPPER_SNAKE_CASE (e.g., `API_URL`, `BUCKET_NAME`)
  - Private methods: prefix with underscore if needed
- **Imports**: Standard library first, then third-party (requests, oci)
- **Logging**: Use Python's logging module (configured at module level)
- **Error Handling**: Try-except blocks with specific logging

## Project Conventions
- **Configuration**: All constants at top of file loaded from environment variables
- **Storage Format**: JSONL (newline-delimited JSON)
- **Date Format**: ISO 8601 with timezone
- **Object Names**: `events/YYYY/MM/DD/events-{timestamp}.jsonl`

## No Linting/Testing Setup
This is a simple script project without formal linting or testing infrastructure.
When making changes, manually test by running `python3 collect_events.py`.
