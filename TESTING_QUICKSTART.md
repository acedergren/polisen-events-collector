# Testing Quick Start Guide

This guide will help you quickly set up and run the test suite for the Polisen Events Collector.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

## Installation

### 1. Install Development Dependencies

```bash
cd /home/alex/projects/polisen-events-collector
pip install -r requirements-dev.txt
```

### 2. Verify Installation

```bash
pytest --version
# Should output: pytest 7.4.3
```

## Running Tests

### Run All Tests

```bash
# Run all unit tests with coverage
pytest tests/unit -v

# Run with coverage report
pytest tests/unit -v --cov=. --cov-report=term-missing
```

### Run Specific Test Files

```bash
# Test datetime normalization
pytest tests/unit/test_normalize_datetime.py -v

# Test collector initialization
pytest tests/unit/test_collector_init.py -v

# Test API fetching
pytest tests/unit/test_fetch_events.py -v
```

### Run Tests by Marker

```bash
# Run only security tests
pytest -v -m security

# Run only unit tests
pytest -v -m unit

# Run integration tests (when available)
pytest -v -m integration
```

### Generate Coverage Reports

```bash
# HTML coverage report
pytest tests/unit --cov=. --cov-report=html
# Open htmlcov/index.html in browser

# Terminal coverage report
pytest tests/unit --cov=. --cov-report=term-missing

# XML coverage report (for CI/CD)
pytest tests/unit --cov=. --cov-report=xml
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_collector_init.py
│   ├── test_fetch_events.py
│   └── test_normalize_datetime.py
├── integration/             # Integration tests (slower)
│   └── (to be implemented)
└── fixtures/                # Test data
    └── (to be implemented)
```

## Writing Tests

### Example Test Structure

```python
import pytest
from collect_events import PolisenCollector

class TestMyFeature:
    """Test suite for a specific feature"""

    def test_success_case(self, mocker):
        """Test successful execution"""
        # Arrange
        collector = self._create_collector(mocker)

        # Act
        result = collector.my_method()

        # Assert
        assert result == expected_value

    def test_error_case(self, mocker):
        """Test error handling"""
        # Arrange
        collector = self._create_collector(mocker)

        # Act & Assert
        with pytest.raises(ExpectedException):
            collector.my_method()

    @staticmethod
    def _create_collector(mocker):
        """Helper to create test collector"""
        mocker.patch('collect_events.get_oci_config_from_vault')
        mocker.patch('oci.object_storage.ObjectStorageClient')
        return PolisenCollector(use_vault=True)
```

### Using Fixtures

```python
def test_with_sample_data(sample_events):
    """Use predefined sample data from conftest.py"""
    assert len(sample_events) == 2
    assert sample_events[0]['id'] == 620014
```

## Common Testing Patterns

### Mocking External Dependencies

```python
def test_api_call(mocker, sample_events):
    """Mock external API calls"""
    mock_response = Mock()
    mock_response.json.return_value = sample_events
    mocker.patch('requests.get', return_value=mock_response)

    # Your test code here
```

### Testing Logging

```python
def test_logging(caplog):
    """Verify log messages"""
    with caplog.at_level('INFO'):
        # Code that logs
        pass

    assert "Expected log message" in caplog.text
```

### Testing Exceptions

```python
def test_exception_handling(mocker):
    """Test exception scenarios"""
    mocker.patch('some_function', side_effect=Exception("Error"))

    with pytest.raises(Exception, match="Error"):
        # Code that should raise exception
        pass
```

## Coverage Targets

- **Overall Project:** 80%+
- **collect_events.py:** 85%+
- **secrets_manager.py:** 90%+

## Current Test Status

As of 2026-01-02:

| Test File | Tests | Status |
|-----------|-------|--------|
| test_normalize_datetime.py | 8 | ✅ Implemented |
| test_collector_init.py | 10 | ✅ Implemented |
| test_fetch_events.py | 16 | ✅ Implemented |
| **Total** | **34** | **34 passing** |

## Next Steps

1. **Complete Unit Tests** (Week 2-3)
   - test_get_last_seen_ids.py
   - test_update_last_seen_ids.py
   - test_save_events.py
   - test_secrets_manager.py

2. **Add Integration Tests** (Week 4)
   - OCI Object Storage integration
   - Vault integration
   - API contract tests

3. **Set Up CI/CD** (Week 5)
   - Enable GitHub Actions
   - Configure coverage reporting
   - Add pre-commit hooks

## Troubleshooting

### Import Errors

If you get import errors:
```bash
# Add project root to PYTHONPATH
export PYTHONPATH=/home/alex/projects/polisen-events-collector:$PYTHONPATH
pytest tests/unit -v
```

### Fixture Not Found

Ensure fixtures are defined in `tests/conftest.py` or the test file itself.

### Coverage Too Low

Check which lines are not covered:
```bash
pytest tests/unit --cov=. --cov-report=term-missing
```

Look for lines marked with `!` in the output.

## Useful Commands

```bash
# Run tests in parallel (faster)
pytest tests/unit -v -n auto

# Run tests with verbose output
pytest tests/unit -vv

# Run only failed tests from last run
pytest tests/unit --lf

# Run tests matching pattern
pytest tests/unit -k "test_init"

# Show slowest tests
pytest tests/unit --durations=10

# Run with debugging on first failure
pytest tests/unit -x --pdb
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-mock Documentation](https://pytest-mock.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Analysis](TESTING_ANALYSIS.md) - Comprehensive testing strategy

## Getting Help

- Review [TESTING_ANALYSIS.md](TESTING_ANALYSIS.md) for detailed testing strategy
- Check existing tests for examples
- Refer to pytest documentation for advanced features
