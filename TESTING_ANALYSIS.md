# Testing Strategy Analysis - Polisen Events Collector

**Analysis Date:** 2026-01-02
**Project:** Swedish Police Events Collector
**Assessment Type:** Comprehensive Testing Gap Analysis

---

## Executive Summary

**CRITICAL FINDING:** The project currently has **ZERO test coverage** - no test files, no test infrastructure, and no testing dependencies.

**Risk Level:** 🔴 HIGH - Production code handling sensitive credentials and automated data collection with no automated quality gates.

**Immediate Actions Required:**
1. Create comprehensive test suite (Unit + Integration)
2. Add test dependencies (pytest, pytest-mock, responses)
3. Implement CI/CD testing pipeline
4. Add pre-commit hooks for test execution
5. Establish test coverage baseline (target: 80%+)

---

## 1. Current Test Coverage Analysis

### 1.1 Existing Tests: NONE ❌

**Search Results:**
- No `tests/` directory
- No `test_*.py` files
- No `*_test.py` files
- No test configuration files (pytest.ini, tox.ini, etc.)
- No testing dependencies in requirements.txt

### 1.2 Coverage Gaps - collect_events.py

#### PolisenCollector Class (100% untested)

**Untested Methods:**
| Method | Complexity | Risk Level | Coverage Status |
|--------|-----------|-----------|----------------|
| `__init__()` | Medium | HIGH | ❌ 0% |
| `fetch_events()` | Low | MEDIUM | ❌ 0% |
| `get_last_seen_ids()` | Medium | HIGH | ❌ 0% |
| `update_last_seen_ids()` | Medium | HIGH | ❌ 0% |
| `normalize_datetime()` | Medium | MEDIUM | ❌ 0% |
| `save_events()` | High | CRITICAL | ❌ 0% |
| `run()` | High | CRITICAL | ❌ 0% |

**Critical Untested Paths:**
- ✗ Vault authentication success/failure
- ✗ OCI client initialization errors
- ✗ API network failures (timeout, connection errors)
- ✗ Malformed API responses
- ✗ Object storage read/write failures
- ✗ Metadata file corruption handling
- ✗ Date parsing edge cases (single-digit hours)
- ✗ Event deduplication logic
- ✗ Empty event list handling
- ✗ Partitioning logic for different timezones

### 1.3 Coverage Gaps - secrets_manager.py

#### SecretsManager Class (100% untested)

**Untested Methods:**
| Method | Complexity | Risk Level | Coverage Status |
|--------|-----------|-----------|----------------|
| `__init__()` | Medium | CRITICAL | ❌ 0% |
| `get_vault_id()` | Medium | HIGH | ❌ 0% |
| `get_secret()` | High | CRITICAL | ❌ 0% |
| `get_oci_config()` | Medium | CRITICAL | ❌ 0% |
| `get_secret_optional()` | Low | MEDIUM | ❌ 0% |
| `get_oci_config_from_vault()` | Low | HIGH | ❌ 0% |

**Security-Critical Untested Paths:**
- ✗ Instance principal authentication failure
- ✗ Config file authentication failure
- ✗ Vault not found scenario
- ✗ Secret not found scenario
- ✗ Secret in non-ACTIVE state
- ✗ Base64 decoding errors
- ✗ Invalid PEM key format
- ✗ Network timeouts during vault access
- ✗ Missing required secrets
- ✗ Malformed vault responses

---

## 2. Unit Test Requirements

### 2.1 PolisenCollector Tests (Priority: CRITICAL)

#### Test Suite Structure
```
tests/
├── unit/
│   ├── __init__.py
│   ├── test_polisen_collector.py
│   └── test_secrets_manager.py
├── integration/
│   ├── __init__.py
│   ├── test_oci_integration.py
│   └── test_api_integration.py
├── fixtures/
│   ├── __init__.py
│   ├── api_responses.py
│   └── vault_responses.py
└── conftest.py
```

#### Required Test Cases - PolisenCollector

**Test: `__init__()` Method**
```python
class TestPolisenCollectorInit:
    def test_init_with_vault_success(self, mock_vault)
    def test_init_with_vault_failure(self, mock_vault_error)
    def test_init_with_local_config(self, mock_oci_config)
    def test_init_with_invalid_config(self, mock_invalid_config)
    def test_init_sets_correct_region(self, mock_vault)
    def test_init_creates_object_storage_client(self, mock_vault)
    def test_init_logs_authentication_mode(self, mock_vault, caplog)
```

**Test: `fetch_events()` Method**
```python
class TestFetchEvents:
    def test_fetch_events_success(self, mock_api_response)
    def test_fetch_events_includes_user_agent(self, mock_requests)
    def test_fetch_events_timeout(self, mock_timeout)
    def test_fetch_events_connection_error(self, mock_connection_error)
    def test_fetch_events_http_404(self, mock_404_response)
    def test_fetch_events_http_500(self, mock_500_response)
    def test_fetch_events_malformed_json(self, mock_invalid_json)
    def test_fetch_events_empty_response(self, mock_empty_response)
    def test_fetch_events_logs_count(self, mock_api_response, caplog)
```

**Test: `get_last_seen_ids()` Method**
```python
class TestGetLastSeenIds:
    def test_get_last_seen_ids_success(self, mock_metadata_file)
    def test_get_last_seen_ids_file_not_found(self, mock_404_error)
    def test_get_last_seen_ids_malformed_json(self, mock_invalid_metadata)
    def test_get_last_seen_ids_empty_file(self, mock_empty_metadata)
    def test_get_last_seen_ids_missing_seen_ids_key(self, mock_partial_metadata)
    def test_get_last_seen_ids_service_error(self, mock_oci_error)
    def test_get_last_seen_ids_returns_set(self, mock_metadata_file)
    def test_get_last_seen_ids_handles_duplicates(self, mock_metadata_with_dupes)
```

**Test: `update_last_seen_ids()` Method**
```python
class TestUpdateLastSeenIds:
    def test_update_last_seen_ids_success(self, mock_object_storage)
    def test_update_last_seen_ids_limits_to_1000(self, mock_large_id_set)
    def test_update_last_seen_ids_keeps_most_recent(self, mock_id_set)
    def test_update_last_seen_ids_includes_metadata(self, mock_object_storage)
    def test_update_last_seen_ids_handles_empty_set(self, mock_object_storage)
    def test_update_last_seen_ids_upload_failure(self, mock_upload_error)
    def test_update_last_seen_ids_json_format(self, mock_object_storage)
```

**Test: `normalize_datetime()` Static Method**
```python
class TestNormalizeDatetime:
    def test_normalize_single_digit_hour(self):
        # "2026-01-02 9:38:09 +01:00" -> "2026-01-02 09:38:09 +01:00"
    def test_normalize_double_digit_hour(self):
        # "2026-01-02 19:38:09 +01:00" -> "2026-01-02 19:38:09 +01:00" (unchanged)
    def test_normalize_midnight_hour(self):
        # "2026-01-02 0:00:00 +01:00" -> "2026-01-02 00:00:00 +01:00"
    def test_normalize_invalid_format(self):
        # Invalid input should return unchanged
    def test_normalize_edge_cases(self):
        # Edge cases: "2026-01-02 1:00:00 +00:00", negative timezone, etc.
```

**Test: `save_events()` Method**
```python
class TestSaveEvents:
    def test_save_events_success(self, mock_object_storage, sample_events)
    def test_save_events_partitions_by_date(self, mock_object_storage, multi_date_events)
    def test_save_events_creates_correct_path(self, mock_object_storage, sample_events)
    def test_save_events_jsonl_format(self, mock_object_storage, sample_events)
    def test_save_events_handles_empty_list(self, mock_object_storage)
    def test_save_events_skips_invalid_datetime(self, mock_object_storage, invalid_event)
    def test_save_events_normalizes_datetime(self, mock_object_storage, single_digit_hour_event)
    def test_save_events_upload_failure(self, mock_upload_error, sample_events)
    def test_save_events_multiple_partitions(self, mock_object_storage, cross_month_events)
    def test_save_events_preserves_unicode(self, mock_object_storage, unicode_events)
    def test_save_events_timestamp_uniqueness(self, mock_object_storage, sample_events)
```

**Test: `run()` Method**
```python
class TestRun:
    def test_run_success_with_new_events(self, mock_full_workflow)
    def test_run_success_no_new_events(self, mock_no_new_events)
    def test_run_handles_fetch_failure(self, mock_api_error)
    def test_run_handles_save_failure(self, mock_save_error)
    def test_run_updates_metadata_after_save(self, mock_full_workflow)
    def test_run_deduplicates_correctly(self, mock_duplicate_events)
    def test_run_logs_event_counts(self, mock_full_workflow, caplog)
    def test_run_exits_on_error(self, mock_fatal_error)
```

### 2.2 SecretsManager Tests (Priority: CRITICAL)

#### Required Test Cases - SecretsManager

**Test: `__init__()` Method**
```python
class TestSecretsManagerInit:
    def test_init_instance_principal_mode(self, mock_instance_principal)
    def test_init_config_file_mode(self, mock_config_file)
    def test_init_sets_correct_region(self, mock_config_file)
    def test_init_creates_clients(self, mock_config_file)
    def test_init_instance_principal_failure(self, mock_ip_error)
    def test_init_config_file_not_found(self, mock_missing_config)
    def test_init_uses_environment_profile(self, mock_custom_profile)
```

**Test: `get_vault_id()` Method**
```python
class TestGetVaultId:
    def test_get_vault_id_success(self, mock_vault_list)
    def test_get_vault_id_not_found(self, mock_empty_vault_list)
    def test_get_vault_id_inactive_vault(self, mock_inactive_vault)
    def test_get_vault_id_multiple_vaults(self, mock_multiple_vaults)
    def test_get_vault_id_api_error(self, mock_list_vaults_error)
```

**Test: `get_secret()` Method**
```python
class TestGetSecret:
    def test_get_secret_success(self, mock_secret_bundle)
    def test_get_secret_not_found(self, mock_empty_secret_list)
    def test_get_secret_inactive_state(self, mock_inactive_secret)
    def test_get_secret_base64_decode_error(self, mock_invalid_base64)
    def test_get_secret_utf8_decode_error(self, mock_invalid_utf8)
    def test_get_secret_api_error(self, mock_get_bundle_error)
    def test_get_secret_caches_vault_id(self, mock_secret_bundle)
```

**Test: `get_oci_config()` Method**
```python
class TestGetOciConfig:
    def test_get_oci_config_success(self, mock_all_secrets)
    def test_get_oci_config_missing_user_ocid(self, mock_partial_secrets)
    def test_get_oci_config_missing_tenancy(self, mock_partial_secrets)
    def test_get_oci_config_missing_fingerprint(self, mock_partial_secrets)
    def test_get_oci_config_missing_private_key(self, mock_partial_secrets)
    def test_get_oci_config_uses_optional_region(self, mock_secrets_with_region)
    def test_get_oci_config_defaults_region(self, mock_secrets_without_region)
    def test_get_oci_config_structure(self, mock_all_secrets)
```

**Test: `get_secret_optional()` Method**
```python
class TestGetSecretOptional:
    def test_get_secret_optional_found(self, mock_secret)
    def test_get_secret_optional_not_found_uses_default(self, mock_secret_not_found)
    def test_get_secret_optional_error_uses_default(self, mock_secret_error)
    def test_get_secret_optional_none_default(self, mock_secret_not_found)
```

---

## 3. Integration Test Needs

### 3.1 OCI Object Storage Integration (Priority: HIGH)

**Test Scenarios:**
```python
class TestOCIIntegration:
    """Integration tests with actual OCI services (requires test environment)"""

    @pytest.mark.integration
    def test_upload_and_retrieve_metadata(self, test_bucket)

    @pytest.mark.integration
    def test_upload_events_file(self, test_bucket)

    @pytest.mark.integration
    def test_handle_large_file_upload(self, test_bucket, large_events)

    @pytest.mark.integration
    def test_concurrent_uploads(self, test_bucket)

    @pytest.mark.integration
    def test_network_retry_logic(self, test_bucket, flaky_connection)
```

### 3.2 Polisen API Integration (Priority: MEDIUM)

**Test Scenarios:**
```python
class TestPolisenAPIIntegration:
    """Integration tests with actual Polisen API (rate-limited)"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_fetch_real_events(self):
        """Verify API contract hasn't changed"""

    @pytest.mark.integration
    def test_api_rate_limiting_compliance(self):
        """Ensure we respect rate limits"""

    @pytest.mark.integration
    def test_user_agent_header_accepted(self):
        """Verify our User-Agent is accepted"""
```

### 3.3 Vault Secret Retrieval Integration (Priority: CRITICAL)

**Test Scenarios:**
```python
class TestVaultIntegration:
    """Integration tests with OCI Vault"""

    @pytest.mark.integration
    @pytest.mark.security
    def test_retrieve_all_required_secrets(self, test_vault)

    @pytest.mark.integration
    def test_instance_principal_authentication(self, compute_instance)

    @pytest.mark.integration
    def test_config_file_authentication(self, local_config)

    @pytest.mark.integration
    def test_vault_failover_handling(self, test_vault)
```

### 3.4 End-to-End Workflow (Priority: HIGH)

**Test Scenarios:**
```python
class TestEndToEndWorkflow:
    """Complete workflow integration tests"""

    @pytest.mark.e2e
    def test_complete_collection_cycle(self, test_environment):
        """
        Test complete workflow:
        1. Authenticate with vault
        2. Fetch events from API
        3. Check existing metadata
        4. Save new events
        5. Update metadata
        """

    @pytest.mark.e2e
    def test_subsequent_runs_deduplicate(self, test_environment):
        """Verify deduplication across multiple runs"""

    @pytest.mark.e2e
    def test_recovery_from_partial_failure(self, test_environment):
        """Verify system recovers from mid-process failures"""
```

---

## 4. Test Quality Metrics

### 4.1 Mock Usage Appropriateness

**RECOMMENDATIONS:**

| Component | Mocking Strategy | Rationale |
|-----------|-----------------|-----------|
| OCI SDK | Mock in unit tests, real in integration | Avoid slow/costly API calls in unit tests |
| Polisen API | Use `responses` library | Avoid rate limiting and ensure deterministic tests |
| Vault Client | Mock in unit tests, real in security tests | Sensitive operations need both mocked and real validation |
| Filesystem/Logging | Use pytest fixtures | Isolate side effects |
| datetime.now() | Mock with freezegun | Ensure deterministic timestamps |

**Anti-patterns to avoid:**
- ❌ Over-mocking (testing mocks instead of logic)
- ❌ Under-mocking (slow tests, external dependencies)
- ❌ Mocking in integration tests (defeats the purpose)
- ❌ Not verifying mock calls (missing interaction validation)

### 4.2 Test Isolation and Independence

**REQUIRED PRACTICES:**

1. **No Shared State Between Tests**
   ```python
   # Good: Each test gets fresh fixtures
   @pytest.fixture
   def collector(mocker):
       with mocker.patch('collect_events.get_oci_config_from_vault'):
           return PolisenCollector()
   ```

2. **Cleanup After Tests**
   ```python
   @pytest.fixture
   def temp_metadata_file():
       file = create_temp_file()
       yield file
       file.cleanup()  # Always cleanup
   ```

3. **Test Execution Order Independence**
   - Tests must pass in any order
   - Use `pytest-randomly` to verify

4. **Isolated Logging**
   ```python
   def test_logging(caplog):
       with caplog.at_level(logging.INFO):
           # Test logging without affecting other tests
   ```

### 4.3 Assertion Completeness

**ASSERTION CHECKLIST:**

Every test should verify:
- ✓ Return value correctness
- ✓ Side effects (file writes, API calls)
- ✓ Exception types and messages
- ✓ Logging messages (using caplog)
- ✓ Mock call counts and arguments
- ✓ State changes in objects

**Example of Complete Assertion:**
```python
def test_update_last_seen_ids_complete(mock_storage, caplog):
    collector = PolisenCollector()
    test_ids = {1, 2, 3}

    # Execute
    collector.update_last_seen_ids(test_ids)

    # Assert return value (if any)
    # Assert side effects
    assert mock_storage.put_object.call_count == 1
    call_args = mock_storage.put_object.call_args
    assert call_args[0][0] == NAMESPACE
    assert call_args[0][1] == BUCKET_NAME
    assert call_args[0][2] == METADATA_FILE

    # Assert data format
    uploaded_data = json.loads(call_args[0][3].decode('utf-8'))
    assert set(uploaded_data['seen_ids']) == test_ids
    assert 'last_updated' in uploaded_data
    assert uploaded_data['total_tracked'] == 3

    # Assert logging
    assert "Updated metadata with 3 tracked IDs" in caplog.text
```

### 4.4 Edge Case Coverage

**CRITICAL EDGE CASES:**

1. **Empty Collections**
   - Empty event list from API
   - Empty metadata file
   - Empty seen_ids set

2. **Boundary Values**
   - Exactly 500 events (API limit)
   - Exactly 1000 tracked IDs (metadata limit)
   - 1001 IDs (should truncate to 1000)

3. **Invalid Data**
   - Malformed JSON
   - Missing required fields
   - Invalid datetime formats
   - Non-UTF8 characters

4. **Network Issues**
   - Timeouts
   - Connection errors
   - Partial responses
   - Retries and backoff

5. **Datetime Edge Cases**
   - Single-digit hours (0-9)
   - Timezone variations (+/- offsets)
   - Daylight saving time transitions
   - Year boundaries

---

## 5. Testing Gaps - Prioritized

### 5.1 CRITICAL Gaps (Fix Immediately)

| Gap | Risk | Test Type | Priority |
|-----|------|-----------|----------|
| No vault authentication tests | Security breach | Unit + Integration | P0 |
| No API failure handling tests | Data loss | Unit | P0 |
| No deduplication logic tests | Duplicate data | Unit | P0 |
| No secret retrieval error tests | Service outage | Unit | P0 |
| No OCI client init failure tests | Service failure | Unit | P0 |

### 5.2 HIGH Priority Gaps

| Gap | Risk | Test Type | Priority |
|-----|------|-----------|----------|
| No datetime normalization tests | Data corruption | Unit | P1 |
| No metadata corruption handling | State loss | Unit + Integration | P1 |
| No object storage write failure tests | Data loss | Unit + Integration | P1 |
| No event partitioning tests | Incorrect storage structure | Unit | P1 |
| No JSONL format validation | Parsing errors downstream | Unit | P1 |

### 5.3 MEDIUM Priority Gaps

| Gap | Risk | Test Type | Priority |
|-----|------|-----------|----------|
| No unicode handling tests | Character encoding issues | Unit | P2 |
| No configuration variation tests | Runtime errors | Integration | P2 |
| No concurrent execution tests | Race conditions | Integration | P2 |
| No API rate limit compliance tests | API ban | Integration | P2 |

### 5.4 Security-Critical Test Gaps

**IMMEDIATE REQUIREMENTS:**

1. **Credential Leakage Prevention**
   ```python
   def test_no_secrets_in_logs(caplog, mock_vault):
       """Ensure private keys/secrets never appear in logs"""
       collector = PolisenCollector()
       assert "BEGIN PRIVATE KEY" not in caplog.text
       assert "fingerprint" not in caplog.text.lower()
   ```

2. **Authentication Failure Handling**
   ```python
   def test_vault_auth_failure_exits_cleanly(mock_vault_error):
       """System must fail safely on auth errors"""
       with pytest.raises(Exception):
           PolisenCollector(use_vault=True)
       # Verify no partial operations occurred
   ```

3. **Vault Unavailability**
   ```python
   def test_vault_service_unavailable(mock_vault_503):
       """Handle vault service outages gracefully"""
       with pytest.raises(VaultUnavailableError):
           SecretsManager().get_secret("oci-user-ocid")
   ```

---

## 6. Test Pyramid Adherence

### 6.1 Current State: ❌ NO PYRAMID

**Ideal Distribution:**
```
    E2E Tests (5%)        <-- 0 tests
   ────────────
  Integration (15%)      <-- 0 tests
 ──────────────────
Unit Tests (80%)         <-- 0 tests
```

### 6.2 Recommended Test Distribution

**Target Test Count: ~120 tests**

| Test Type | Count | Percentage | Purpose |
|-----------|-------|------------|---------|
| Unit Tests | 95 | 79% | Fast feedback, code coverage |
| Integration Tests | 20 | 17% | Component interaction validation |
| E2E Tests | 5 | 4% | Critical path validation |

**Test Execution Time Targets:**
- Unit tests: < 5 seconds total
- Integration tests: < 30 seconds total
- E2E tests: < 2 minutes total
- **Total test suite: < 3 minutes**

### 6.3 Contract Testing Needs

**External API Contracts to Validate:**

1. **Polisen API Contract**
   ```python
   def test_polisen_api_response_schema():
       """Validate API response structure hasn't changed"""
       expected_schema = {
           "id": int,
           "datetime": str,
           "name": str,
           "summary": str,
           "url": str,
           "type": str,
           "location": {"name": str, "gps": str}
       }
       # Validate against real API response
   ```

2. **OCI SDK Contract**
   ```python
   def test_oci_object_storage_interface():
       """Ensure OCI SDK interface matches expectations"""
       # Validate method signatures, return types
   ```

3. **OCI Vault Contract**
   ```python
   def test_vault_secret_bundle_structure():
       """Validate vault response structure"""
       # Ensure secret bundle format is correct
   ```

---

## 7. Framework Recommendations

### 7.1 Testing Framework: **pytest** ✅

**Rationale:**
- Modern, Pythonic syntax
- Rich plugin ecosystem
- Excellent fixture system
- Better parametrization than unittest
- Community standard for new Python projects

**vs unittest:**
| Feature | pytest | unittest |
|---------|--------|----------|
| Syntax | Simple asserts | self.assertEqual() |
| Fixtures | Powerful, reusable | setUp/tearDown only |
| Parametrization | Built-in, elegant | Requires external libs |
| Plugins | Extensive | Limited |
| **Recommendation** | ✅ Use this | ❌ Avoid |

### 7.2 Mocking Strategy

**Primary Tools:**

1. **pytest-mock** (wrapper around unittest.mock)
   ```python
   def test_fetch_events(mocker):
       mock_get = mocker.patch('requests.get')
       mock_get.return_value.json.return_value = [...]
   ```

2. **responses** (for HTTP mocking)
   ```python
   @responses.activate
   def test_api_call():
       responses.add(
           responses.GET,
           'https://polisen.se/api/events',
           json=[...],
           status=200
       )
   ```

3. **freezegun** (for datetime mocking)
   ```python
   @freeze_time("2026-01-02 12:00:00")
   def test_timestamp_generation():
       # datetime.now() returns frozen time
   ```

### 7.3 Fixture Design Strategy

**Recommended Fixture Organization:**

**File: `tests/conftest.py`**
```python
import pytest
from unittest.mock import Mock, MagicMock
import responses

# ============================================================================
# SHARED FIXTURES
# ============================================================================

@pytest.fixture
def sample_events():
    """Sample Polisen API events for testing"""
    return [
        {
            "id": 620014,
            "datetime": "2026-01-02 19:56:53 +01:00",
            "name": "02 januari 18.30, Misshandel, Linköping",
            "summary": "Bråk på buss i Linköping.",
            "url": "/aktuellt/handelser/2026/januari/2/02-januari-18.30-misshandel-linkoping/",
            "type": "Misshandel",
            "location": {"name": "Linköping", "gps": "58.410807,15.621373"}
        },
        {
            "id": 620015,
            "datetime": "2026-01-02 9:15:00 +01:00",  # Single-digit hour test
            "name": "Trafikolycka",
            "summary": "Singelolycka på E4",
            "url": "/aktuellt/handelser/2026/januari/2/...",
            "type": "Trafikolycka",
            "location": {"name": "Stockholm", "gps": "59.329323,18.068581"}
        }
    ]

@pytest.fixture
def mock_oci_config():
    """Mock OCI configuration"""
    return {
        "user": "ocid1.user.oc1..test",
        "tenancy": "ocid1.tenancy.oc1..test",
        "fingerprint": "aa:bb:cc:dd:ee:ff",
        "key_content": "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----",
        "region": "eu-stockholm-1"
    }

@pytest.fixture
def mock_object_storage_client(mocker):
    """Mock OCI ObjectStorageClient"""
    mock_client = MagicMock()
    mock_client.get_object.return_value = Mock(
        data=Mock(content=b'{"seen_ids": [1, 2, 3]}')
    )
    mocker.patch(
        'oci.object_storage.ObjectStorageClient',
        return_value=mock_client
    )
    return mock_client

@pytest.fixture
def mock_vault_config(mocker):
    """Mock vault configuration retrieval"""
    mock_config = {
        "user": "ocid1.user.oc1..vaulttest",
        "tenancy": "ocid1.tenancy.oc1..vaulttest",
        "fingerprint": "11:22:33:44:55:66",
        "key_content": "-----BEGIN PRIVATE KEY-----\nVAULT_KEY\n-----END PRIVATE KEY-----",
        "region": "eu-stockholm-1"
    }
    mocker.patch(
        'secrets_manager.get_oci_config_from_vault',
        return_value=mock_config
    )
    return mock_config

@pytest.fixture
def mock_polisen_api(mocker, sample_events):
    """Mock Polisen API responses"""
    mock_response = Mock()
    mock_response.json.return_value = sample_events
    mock_response.status_code = 200
    mock_get = mocker.patch('requests.get', return_value=mock_response)
    return mock_get
```

**File: `tests/fixtures/api_responses.py`**
```python
"""Fixture data for Polisen API responses"""

VALID_EVENT = {
    "id": 620014,
    "datetime": "2026-01-02 19:56:53 +01:00",
    "name": "02 januari 18.30, Misshandel, Linköping",
    "summary": "Bråk på buss i Linköping.",
    "url": "/aktuellt/handelser/2026/januari/2/02-januari-18.30-misshandel-linkoping/",
    "type": "Misshandel",
    "location": {"name": "Linköping", "gps": "58.410807,15.621373"}
}

SINGLE_DIGIT_HOUR_EVENT = {
    "id": 620015,
    "datetime": "2026-01-02 9:15:00 +01:00",
    "name": "Event at 9 AM",
    "summary": "Test",
    "url": "/test/",
    "type": "Test",
    "location": {"name": "Stockholm", "gps": "59.329323,18.068581"}
}

MALFORMED_EVENT_MISSING_DATETIME = {
    "id": 620016,
    # Missing datetime field
    "name": "Invalid Event",
    "summary": "Test",
    "url": "/test/",
    "type": "Test",
    "location": {"name": "Stockholm", "gps": "59.329323,18.068581"}
}

UNICODE_EVENT = {
    "id": 620017,
    "datetime": "2026-01-02 14:30:00 +01:00",
    "name": "Händelse med åäö ÅÄÖ",
    "summary": "Test med svenska tecken och émojis 🚓",
    "url": "/test/",
    "type": "Test",
    "location": {"name": "Göteborg", "gps": "57.708870,11.974560"}
}
```

### 7.4 Test Data Management Strategy

**Recommended Approaches:**

1. **Fixture Files for Complex Data**
   ```
   tests/
   └── fixtures/
       ├── api_responses.py      # Polisen API responses
       ├── vault_responses.py    # Vault API responses
       ├── metadata_samples.py   # Metadata file variations
       └── events_data.json      # Large event datasets
   ```

2. **Factory Functions for Variations**
   ```python
   def create_event(event_id=1, datetime_str=None, **kwargs):
       """Factory for creating test events with variations"""
       event = {
           "id": event_id,
           "datetime": datetime_str or "2026-01-02 12:00:00 +01:00",
           "name": "Test Event",
           "summary": "Test",
           "url": "/test/",
           "type": "Test",
           "location": {"name": "Stockholm", "gps": "59.329323,18.068581"}
       }
       event.update(kwargs)
       return event
   ```

3. **Parameterized Tests for Edge Cases**
   ```python
   @pytest.mark.parametrize("datetime_str,expected", [
       ("2026-01-02 9:00:00 +01:00", "2026-01-02 09:00:00 +01:00"),
       ("2026-01-02 0:30:00 +01:00", "2026-01-02 00:30:00 +01:00"),
       ("2026-01-02 10:00:00 +01:00", "2026-01-02 10:00:00 +01:00"),
   ])
   def test_normalize_datetime_variations(datetime_str, expected):
       assert PolisenCollector.normalize_datetime(datetime_str) == expected
   ```

### 7.5 Required Test Dependencies

**File: `requirements-dev.txt`** (to be created)
```txt
# Testing Framework
pytest==7.4.3
pytest-cov==4.1.0           # Coverage reporting
pytest-mock==3.12.0         # Mocking utilities
pytest-asyncio==0.23.2      # Async test support
pytest-xdist==3.5.0         # Parallel test execution
pytest-randomly==3.15.0     # Randomized test order
pytest-timeout==2.2.0       # Test timeout enforcement

# Mocking Libraries
responses==0.24.1           # HTTP mocking
freezegun==1.4.0            # Datetime mocking

# Code Quality
black==23.12.1              # Code formatting
flake8==7.0.0               # Linting
mypy==1.7.1                 # Type checking
pylint==3.0.3               # Static analysis

# Coverage
coverage[toml]==7.3.4       # Coverage configuration

# Security Testing
bandit==1.7.6               # Security vulnerability scanner
safety==3.0.1               # Dependency vulnerability checker
```

### 7.6 pytest Configuration

**File: `pytest.ini`** (to be created)
```ini
[pytest]
# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Output
addopts =
    -v                      # Verbose output
    --strict-markers        # Enforce marker registration
    --tb=short              # Shorter traceback format
    --cov=.                 # Coverage for all Python files
    --cov-report=html       # HTML coverage report
    --cov-report=term-missing  # Show missing lines in terminal
    --cov-fail-under=80     # Fail if coverage < 80%
    --maxfail=5             # Stop after 5 failures
    --timeout=30            # 30 second timeout per test

# Markers
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (require test environment)
    e2e: End-to-end tests (full workflow)
    slow: Tests that take > 1 second
    security: Security-related tests

# Logging
log_cli = true
log_cli_level = INFO
log_file = tests/logs/test_output.log
log_file_level = DEBUG

# Warnings
filterwarnings =
    error                   # Treat warnings as errors
    ignore::DeprecationWarning
```

**File: `pyproject.toml`** (coverage configuration)
```toml
[tool.coverage.run]
source = ["."]
omit = [
    "*/tests/*",
    "*/venv/*",
    "*/__pycache__/*",
    "setup.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "if sys.version_info",
]
precision = 2
show_missing = true

[tool.coverage.html]
directory = "htmlcov"
```

---

## 8. Example Test Implementation

### 8.1 Complete Test File Example

**File: `tests/unit/test_polisen_collector.py`**

```python
"""
Unit tests for PolisenCollector class
"""
import json
import pytest
from unittest.mock import Mock, MagicMock, call, patch
from datetime import datetime, timezone
import requests
import oci.exceptions

from collect_events import PolisenCollector, API_URL, NAMESPACE, BUCKET_NAME, METADATA_FILE


class TestPolisenCollectorInit:
    """Test PolisenCollector initialization"""

    def test_init_with_vault_success(self, mocker, mock_oci_config):
        """Successfully initialize with vault authentication"""
        # Arrange
        mock_vault = mocker.patch(
            'collect_events.get_oci_config_from_vault',
            return_value=mock_oci_config
        )
        mock_client = mocker.patch('oci.object_storage.ObjectStorageClient')

        # Act
        collector = PolisenCollector(use_vault=True)

        # Assert
        mock_vault.assert_called_once()
        assert collector.config["region"] == "eu-stockholm-1"
        mock_client.assert_called_once_with(collector.config)

    def test_init_with_vault_failure_raises_exception(self, mocker):
        """Initialization fails gracefully when vault auth fails"""
        # Arrange
        mocker.patch(
            'collect_events.get_oci_config_from_vault',
            side_effect=Exception("Vault authentication failed")
        )

        # Act & Assert
        with pytest.raises(Exception, match="Vault authentication failed"):
            PolisenCollector(use_vault=True)

    def test_init_with_local_config(self, mocker, mock_oci_config):
        """Initialize with local config file (testing mode)"""
        # Arrange
        mock_config = mocker.patch('oci.config.from_file', return_value=mock_oci_config)
        mocker.patch('oci.object_storage.ObjectStorageClient')

        # Act
        collector = PolisenCollector(use_vault=False)

        # Assert
        mock_config.assert_called_once()
        assert collector.config["region"] == "eu-stockholm-1"

    def test_init_sets_stockholm_region(self, mocker, mock_oci_config):
        """Verify Stockholm region is set for data residency"""
        # Arrange
        mocker.patch('collect_events.get_oci_config_from_vault', return_value=mock_oci_config)
        mocker.patch('oci.object_storage.ObjectStorageClient')

        # Act
        collector = PolisenCollector(use_vault=True)

        # Assert
        assert collector.config["region"] == "eu-stockholm-1"

    def test_init_logs_authentication_mode(self, mocker, mock_oci_config, caplog):
        """Verify appropriate logging for authentication mode"""
        # Arrange
        mocker.patch('collect_events.get_oci_config_from_vault', return_value=mock_oci_config)
        mocker.patch('oci.object_storage.ObjectStorageClient')

        # Act - Vault mode
        with caplog.at_level('INFO'):
            PolisenCollector(use_vault=True)

        # Assert
        assert "Loading OCI credentials from vault (secure mode)" in caplog.text

        # Act - Local config mode
        caplog.clear()
        mocker.patch('oci.config.from_file', return_value=mock_oci_config)
        with caplog.at_level('WARNING'):
            PolisenCollector(use_vault=False)

        # Assert
        assert "Using local config file (INSECURE - only for testing!)" in caplog.text


class TestFetchEvents:
    """Test API event fetching"""

    def test_fetch_events_success(self, mocker, sample_events):
        """Successfully fetch events from API"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = sample_events
        mock_get = mocker.patch('requests.get', return_value=mock_response)

        collector = self._create_collector(mocker)

        # Act
        events = collector.fetch_events()

        # Assert
        assert events == sample_events
        assert len(events) == 2
        mock_get.assert_called_once_with(
            API_URL,
            headers={'User-Agent': collector.USER_AGENT},
            timeout=30
        )

    def test_fetch_events_includes_user_agent(self, mocker, sample_events):
        """Verify User-Agent header is included (API requirement)"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = sample_events
        mock_get = mocker.patch('requests.get', return_value=mock_response)

        collector = self._create_collector(mocker)

        # Act
        collector.fetch_events()

        # Assert
        call_kwargs = mock_get.call_args[1]
        assert 'User-Agent' in call_kwargs['headers']
        assert 'PolisEnEventsCollector' in call_kwargs['headers']['User-Agent']

    def test_fetch_events_timeout_raises_exception(self, mocker):
        """Handle timeout errors appropriately"""
        # Arrange
        mocker.patch('requests.get', side_effect=requests.Timeout("Connection timeout"))
        collector = self._create_collector(mocker)

        # Act & Assert
        with pytest.raises(requests.Timeout):
            collector.fetch_events()

    def test_fetch_events_connection_error(self, mocker):
        """Handle connection errors appropriately"""
        # Arrange
        mocker.patch(
            'requests.get',
            side_effect=requests.ConnectionError("Failed to connect")
        )
        collector = self._create_collector(mocker)

        # Act & Assert
        with pytest.raises(requests.ConnectionError):
            collector.fetch_events()

    def test_fetch_events_http_500_error(self, mocker):
        """Handle HTTP 500 errors"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mocker.patch('requests.get', return_value=mock_response)
        collector = self._create_collector(mocker)

        # Act & Assert
        with pytest.raises(requests.HTTPError):
            collector.fetch_events()

    def test_fetch_events_malformed_json(self, mocker):
        """Handle malformed JSON responses"""
        # Arrange
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mocker.patch('requests.get', return_value=mock_response)
        collector = self._create_collector(mocker)

        # Act & Assert
        with pytest.raises(json.JSONDecodeError):
            collector.fetch_events()

    def test_fetch_events_logs_count(self, mocker, sample_events, caplog):
        """Verify event count is logged"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = sample_events
        mocker.patch('requests.get', return_value=mock_response)
        collector = self._create_collector(mocker)

        # Act
        with caplog.at_level('INFO'):
            collector.fetch_events()

        # Assert
        assert "Fetched 2 events from API" in caplog.text

    @staticmethod
    def _create_collector(mocker):
        """Helper to create collector with mocked dependencies"""
        mocker.patch('collect_events.get_oci_config_from_vault')
        mocker.patch('oci.object_storage.ObjectStorageClient')
        return PolisenCollector(use_vault=True)


class TestNormalizeDatetime:
    """Test datetime normalization logic"""

    @pytest.mark.parametrize("input_dt,expected", [
        # Single-digit hours (0-9)
        ("2026-01-02 0:00:00 +01:00", "2026-01-02 00:00:00 +01:00"),
        ("2026-01-02 1:15:30 +01:00", "2026-01-02 01:15:30 +01:00"),
        ("2026-01-02 9:59:59 +01:00", "2026-01-02 09:59:59 +01:00"),

        # Double-digit hours (should not change)
        ("2026-01-02 10:00:00 +01:00", "2026-01-02 10:00:00 +01:00"),
        ("2026-01-02 19:56:53 +01:00", "2026-01-02 19:56:53 +01:00"),
        ("2026-01-02 23:59:59 +01:00", "2026-01-02 23:59:59 +01:00"),

        # Different timezones
        ("2026-01-02 5:30:00 +00:00", "2026-01-02 05:30:00 +00:00"),
        ("2026-01-02 8:45:12 -05:00", "2026-01-02 08:45:12 -05:00"),

        # Already normalized (no change)
        ("2026-01-02 09:38:09 +01:00", "2026-01-02 09:38:09 +01:00"),
    ])
    def test_normalize_datetime_variations(self, input_dt, expected):
        """Test datetime normalization with various inputs"""
        result = PolisenCollector.normalize_datetime(input_dt)
        assert result == expected

    def test_normalize_datetime_invalid_format_unchanged(self):
        """Invalid datetime formats should return unchanged"""
        invalid_inputs = [
            "invalid-date",
            "2026-01-02",  # Missing time
            "12:00:00",    # Missing date
            "",            # Empty string
        ]
        for invalid in invalid_inputs:
            result = PolisenCollector.normalize_datetime(invalid)
            assert result == invalid


class TestGetLastSeenIds:
    """Test metadata retrieval"""

    def test_get_last_seen_ids_success(self, mocker):
        """Successfully retrieve seen IDs from metadata"""
        # Arrange
        collector = self._create_collector(mocker)
        metadata = {"seen_ids": [1, 2, 3, 4, 5]}
        mock_obj = Mock()
        mock_obj.data.content = json.dumps(metadata).encode('utf-8')
        collector.object_storage.get_object.return_value = mock_obj

        # Act
        seen_ids = collector.get_last_seen_ids()

        # Assert
        assert seen_ids == {1, 2, 3, 4, 5}
        collector.object_storage.get_object.assert_called_once_with(
            NAMESPACE,
            BUCKET_NAME,
            METADATA_FILE
        )

    def test_get_last_seen_ids_file_not_found(self, mocker, caplog):
        """Handle metadata file not found (first run)"""
        # Arrange
        collector = self._create_collector(mocker)
        error = oci.exceptions.ServiceError(
            status=404,
            code="ObjectNotFound",
            headers={},
            message="Object not found"
        )
        collector.object_storage.get_object.side_effect = error

        # Act
        with caplog.at_level('INFO'):
            seen_ids = collector.get_last_seen_ids()

        # Assert
        assert seen_ids == set()
        assert "No previous metadata found, starting fresh" in caplog.text

    def test_get_last_seen_ids_service_error(self, mocker):
        """Handle OCI service errors (not 404)"""
        # Arrange
        collector = self._create_collector(mocker)
        error = oci.exceptions.ServiceError(
            status=500,
            code="InternalError",
            headers={},
            message="Internal server error"
        )
        collector.object_storage.get_object.side_effect = error

        # Act & Assert
        with pytest.raises(oci.exceptions.ServiceError):
            collector.get_last_seen_ids()

    def test_get_last_seen_ids_malformed_json(self, mocker):
        """Handle malformed metadata JSON"""
        # Arrange
        collector = self._create_collector(mocker)
        mock_obj = Mock()
        mock_obj.data.content = b"invalid json {"
        collector.object_storage.get_object.return_value = mock_obj

        # Act & Assert
        with pytest.raises(json.JSONDecodeError):
            collector.get_last_seen_ids()

    def test_get_last_seen_ids_empty_metadata(self, mocker):
        """Handle empty seen_ids in metadata"""
        # Arrange
        collector = self._create_collector(mocker)
        metadata = {"seen_ids": []}
        mock_obj = Mock()
        mock_obj.data.content = json.dumps(metadata).encode('utf-8')
        collector.object_storage.get_object.return_value = mock_obj

        # Act
        seen_ids = collector.get_last_seen_ids()

        # Assert
        assert seen_ids == set()

    def test_get_last_seen_ids_missing_key(self, mocker):
        """Handle missing seen_ids key in metadata"""
        # Arrange
        collector = self._create_collector(mocker)
        metadata = {"other_key": "value"}
        mock_obj = Mock()
        mock_obj.data.content = json.dumps(metadata).encode('utf-8')
        collector.object_storage.get_object.return_value = mock_obj

        # Act
        seen_ids = collector.get_last_seen_ids()

        # Assert
        assert seen_ids == set()

    @staticmethod
    def _create_collector(mocker):
        """Helper to create collector with mocked dependencies"""
        mocker.patch('collect_events.get_oci_config_from_vault')
        mock_client = MagicMock()
        mocker.patch('oci.object_storage.ObjectStorageClient', return_value=mock_client)
        collector = PolisenCollector(use_vault=True)
        return collector


class TestUpdateLastSeenIds:
    """Test metadata update logic"""

    def test_update_last_seen_ids_success(self, mocker, caplog):
        """Successfully update metadata"""
        # Arrange
        collector = self._create_collector(mocker)
        test_ids = {1, 2, 3, 4, 5}

        # Act
        with caplog.at_level('INFO'):
            collector.update_last_seen_ids(test_ids)

        # Assert
        collector.object_storage.put_object.assert_called_once()
        call_args = collector.object_storage.put_object.call_args[0]
        assert call_args[0] == NAMESPACE
        assert call_args[1] == BUCKET_NAME
        assert call_args[2] == METADATA_FILE

        # Verify JSON structure
        uploaded_data = json.loads(call_args[3].decode('utf-8'))
        assert set(uploaded_data['seen_ids']) == test_ids
        assert 'last_updated' in uploaded_data
        assert uploaded_data['total_tracked'] == 5
        assert "Updated metadata with 5 tracked IDs" in caplog.text

    def test_update_last_seen_ids_limits_to_1000(self, mocker):
        """Verify metadata limits to 1000 most recent IDs"""
        # Arrange
        collector = self._create_collector(mocker)
        # Create 1500 IDs (should truncate to 1000)
        test_ids = set(range(1, 1501))

        # Act
        collector.update_last_seen_ids(test_ids)

        # Assert
        call_args = collector.object_storage.put_object.call_args[0]
        uploaded_data = json.loads(call_args[3].decode('utf-8'))
        assert len(uploaded_data['seen_ids']) == 1000
        assert uploaded_data['total_tracked'] == 1000

    def test_update_last_seen_ids_keeps_most_recent(self, mocker):
        """Verify truncation keeps most recent (highest) IDs"""
        # Arrange
        collector = self._create_collector(mocker)
        test_ids = set(range(1, 1501))

        # Act
        collector.update_last_seen_ids(test_ids)

        # Assert
        call_args = collector.object_storage.put_object.call_args[0]
        uploaded_data = json.loads(call_args[3].decode('utf-8'))
        seen_ids = uploaded_data['seen_ids']

        # Should keep IDs 501-1500 (1000 highest IDs)
        assert min(seen_ids) >= 501
        assert max(seen_ids) == 1500

    def test_update_last_seen_ids_handles_empty_set(self, mocker):
        """Handle empty ID set"""
        # Arrange
        collector = self._create_collector(mocker)

        # Act
        collector.update_last_seen_ids(set())

        # Assert
        call_args = collector.object_storage.put_object.call_args[0]
        uploaded_data = json.loads(call_args[3].decode('utf-8'))
        assert uploaded_data['seen_ids'] == []
        assert uploaded_data['total_tracked'] == 0

    def test_update_last_seen_ids_upload_failure(self, mocker):
        """Handle upload failures"""
        # Arrange
        collector = self._create_collector(mocker)
        collector.object_storage.put_object.side_effect = Exception("Upload failed")

        # Act & Assert
        with pytest.raises(Exception, match="Upload failed"):
            collector.update_last_seen_ids({1, 2, 3})

    @staticmethod
    def _create_collector(mocker):
        """Helper to create collector with mocked dependencies"""
        mocker.patch('collect_events.get_oci_config_from_vault')
        mock_client = MagicMock()
        mocker.patch('oci.object_storage.ObjectStorageClient', return_value=mock_client)
        return PolisenCollector(use_vault=True)


class TestSaveEvents:
    """Test event storage logic"""

    def test_save_events_success(self, mocker, sample_events, caplog):
        """Successfully save events to storage"""
        # Arrange
        collector = self._create_collector(mocker)

        # Act
        with caplog.at_level('INFO'):
            collector.save_events(sample_events)

        # Assert
        # Should call put_object twice (two different dates)
        assert collector.object_storage.put_object.call_count == 2
        assert "Saved" in caplog.text

    def test_save_events_partitions_by_date(self, mocker, sample_events):
        """Verify events are partitioned by date"""
        # Arrange
        collector = self._create_collector(mocker)

        # Act
        collector.save_events(sample_events)

        # Assert
        calls = collector.object_storage.put_object.call_args_list

        # Extract object names from calls
        object_names = [call[0][2] for call in calls]

        # Both should start with events/2026/01/02/ (same date)
        for name in object_names:
            assert name.startswith("events/2026/01/02/")
            assert name.endswith(".jsonl")

    def test_save_events_creates_correct_path_format(self, mocker, sample_events):
        """Verify object path format: events/YYYY/MM/DD/events-{timestamp}.jsonl"""
        # Arrange
        collector = self._create_collector(mocker)

        # Act
        with patch('collect_events.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.fromisoformat = datetime.fromisoformat
            collector.save_events(sample_events[:1])

        # Assert
        call_args = collector.object_storage.put_object.call_args[0]
        object_name = call_args[2]

        # Should match: events/2026/01/02/events-{timestamp}.jsonl
        assert object_name.startswith("events/2026/01/02/events-")
        assert object_name.endswith(".jsonl")

    def test_save_events_jsonl_format(self, mocker, sample_events):
        """Verify JSONL format (one JSON object per line)"""
        # Arrange
        collector = self._create_collector(mocker)

        # Act
        collector.save_events(sample_events)

        # Assert
        call_args = collector.object_storage.put_object.call_args[0]
        content = call_args[3].decode('utf-8')

        # Should be valid JSONL
        lines = content.strip().split('\n')
        for line in lines:
            event = json.loads(line)  # Should not raise
            assert 'id' in event
            assert 'datetime' in event

    def test_save_events_handles_empty_list(self, mocker, caplog):
        """Handle empty event list gracefully"""
        # Arrange
        collector = self._create_collector(mocker)

        # Act
        with caplog.at_level('INFO'):
            collector.save_events([])

        # Assert
        collector.object_storage.put_object.assert_not_called()
        assert "No new events to save" in caplog.text

    def test_save_events_skips_invalid_datetime(self, mocker, caplog):
        """Skip events with unparseable datetime"""
        # Arrange
        collector = self._create_collector(mocker)
        invalid_event = {
            "id": 999,
            "datetime": "invalid-datetime-format",
            "name": "Test",
            "summary": "Test",
            "url": "/test/",
            "type": "Test",
            "location": {"name": "Stockholm", "gps": "59.329323,18.068581"}
        }

        # Act
        with caplog.at_level('WARNING'):
            collector.save_events([invalid_event])

        # Assert
        assert "Failed to parse datetime" in caplog.text
        collector.object_storage.put_object.assert_not_called()

    def test_save_events_normalizes_datetime(self, mocker):
        """Verify datetime normalization is applied before parsing"""
        # Arrange
        collector = self._create_collector(mocker)
        event_with_single_digit = {
            "id": 1,
            "datetime": "2026-01-02 9:30:00 +01:00",  # Single-digit hour
            "name": "Test",
            "summary": "Test",
            "url": "/test/",
            "type": "Test",
            "location": {"name": "Stockholm", "gps": "59.329323,18.068581"}
        }

        # Act
        collector.save_events([event_with_single_digit])

        # Assert - Should not raise parsing error
        collector.object_storage.put_object.assert_called_once()

    def test_save_events_preserves_unicode(self, mocker):
        """Verify unicode characters are preserved"""
        # Arrange
        collector = self._create_collector(mocker)
        unicode_event = {
            "id": 1,
            "datetime": "2026-01-02 14:30:00 +01:00",
            "name": "Händelse med åäö ÅÄÖ",
            "summary": "Test med svenska tecken 🚓",
            "url": "/test/",
            "type": "Test",
            "location": {"name": "Göteborg", "gps": "57.708870,11.974560"}
        }

        # Act
        collector.save_events([unicode_event])

        # Assert
        call_args = collector.object_storage.put_object.call_args[0]
        content = call_args[3].decode('utf-8')

        # Verify unicode is preserved
        assert "Händelse med åäö ÅÄÖ" in content
        assert "🚓" in content

    @staticmethod
    def _create_collector(mocker):
        """Helper to create collector with mocked dependencies"""
        mocker.patch('collect_events.get_oci_config_from_vault')
        mock_client = MagicMock()
        mocker.patch('oci.object_storage.ObjectStorageClient', return_value=mock_client)
        return PolisenCollector(use_vault=True)


# ============================================================================
# FIXTURES (would normally be in conftest.py)
# ============================================================================

@pytest.fixture
def sample_events():
    """Sample Polisen API events for testing"""
    return [
        {
            "id": 620014,
            "datetime": "2026-01-02 19:56:53 +01:00",
            "name": "02 januari 18.30, Misshandel, Linköping",
            "summary": "Bråk på buss i Linköping.",
            "url": "/aktuellt/handelser/2026/januari/2/02-januari-18.30-misshandel-linkoping/",
            "type": "Misshandel",
            "location": {"name": "Linköping", "gps": "58.410807,15.621373"}
        },
        {
            "id": 620015,
            "datetime": "2026-01-02 9:15:00 +01:00",
            "name": "Trafikolycka",
            "summary": "Singelolycka på E4",
            "url": "/test/",
            "type": "Trafikolycka",
            "location": {"name": "Stockholm", "gps": "59.329323,18.068581"}
        }
    ]


@pytest.fixture
def mock_oci_config():
    """Mock OCI configuration"""
    return {
        "user": "ocid1.user.oc1..test",
        "tenancy": "ocid1.tenancy.oc1..test",
        "fingerprint": "aa:bb:cc:dd:ee:ff",
        "key_content": "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----",
        "region": "eu-stockholm-1"
    }
```

### 8.2 Example Security Tests

**File: `tests/unit/test_secrets_manager.py`**

```python
"""
Unit tests for SecretsManager class
SECURITY-CRITICAL: These tests validate credential handling
"""
import base64
import pytest
from unittest.mock import Mock, MagicMock, patch
import oci.auth.signers
import oci.exceptions

from secrets_manager import SecretsManager, get_oci_config_from_vault, VAULT_NAME


class TestSecretsManagerInit:
    """Test SecretsManager initialization"""

    def test_init_instance_principal_mode(self, mocker):
        """Initialize with instance principal authentication"""
        # Arrange
        mock_signer = mocker.patch('oci.auth.signers.InstancePrincipalsSecurityTokenSigner')
        mock_secrets_client = mocker.patch('oci.secrets.SecretsClient')
        mock_vaults_client = mocker.patch('oci.vault.VaultsClient')

        # Act
        mgr = SecretsManager(use_instance_principal=True)

        # Assert
        mock_signer.assert_called_once()
        mock_secrets_client.assert_called_once()
        mock_vaults_client.assert_called_once()

    def test_init_config_file_mode(self, mocker, mock_oci_config):
        """Initialize with config file authentication"""
        # Arrange
        mocker.patch('oci.config.from_file', return_value=mock_oci_config)
        mock_secrets_client = mocker.patch('oci.secrets.SecretsClient')
        mock_vaults_client = mocker.patch('oci.vault.VaultsClient')

        # Act
        mgr = SecretsManager(use_instance_principal=False)

        # Assert
        mock_secrets_client.assert_called_once()
        mock_vaults_client.assert_called_once()

    def test_init_sets_frankfurt_region(self, mocker, mock_oci_config):
        """Verify Frankfurt region is set for vault access"""
        # Arrange
        mocker.patch('oci.config.from_file', return_value=mock_oci_config)
        mocker.patch('oci.secrets.SecretsClient')
        mocker.patch('oci.vault.VaultsClient')

        # Act
        mgr = SecretsManager(use_instance_principal=False)

        # Assert - Config should be modified to use Frankfurt
        # (This would need to inspect the config passed to clients)

    def test_init_instance_principal_failure(self, mocker):
        """Handle instance principal initialization failure"""
        # Arrange
        mocker.patch(
            'oci.auth.signers.InstancePrincipalsSecurityTokenSigner',
            side_effect=Exception("Instance principal not available")
        )

        # Act & Assert
        with pytest.raises(Exception, match="Instance principal not available"):
            SecretsManager(use_instance_principal=True)


class TestGetSecret:
    """Test secret retrieval - SECURITY CRITICAL"""

    def test_get_secret_success(self, mocker):
        """Successfully retrieve and decode a secret"""
        # Arrange
        mgr = self._create_manager(mocker)

        # Mock vault ID
        mocker.patch.object(mgr, 'get_vault_id', return_value='vault-ocid')

        # Mock secret list
        mock_secret = Mock()
        mock_secret.id = 'secret-ocid'
        mock_secret.lifecycle_state = 'ACTIVE'

        mock_list_response = Mock()
        mock_list_response.data = [mock_secret]
        mgr.vaults_client.list_secrets.return_value = mock_list_response

        # Mock secret bundle
        secret_value = "my-secret-value"
        secret_base64 = base64.b64encode(secret_value.encode('utf-8')).decode('utf-8')

        mock_bundle_content = Mock()
        mock_bundle_content.content = secret_base64

        mock_bundle = Mock()
        mock_bundle.secret_bundle_content = mock_bundle_content

        mock_bundle_response = Mock()
        mock_bundle_response.data = mock_bundle

        mgr.secrets_client.get_secret_bundle.return_value = mock_bundle_response

        # Act
        result = mgr.get_secret("test-secret")

        # Assert
        assert result == "my-secret-value"
        mgr.vaults_client.list_secrets.assert_called_once()
        mgr.secrets_client.get_secret_bundle.assert_called_once_with('secret-ocid')

    def test_get_secret_not_found(self, mocker):
        """Handle secret not found scenario"""
        # Arrange
        mgr = self._create_manager(mocker)
        mocker.patch.object(mgr, 'get_vault_id', return_value='vault-ocid')

        # Mock empty secret list
        mock_list_response = Mock()
        mock_list_response.data = []
        mgr.vaults_client.list_secrets.return_value = mock_list_response

        # Act & Assert
        with pytest.raises(ValueError, match="Secret 'missing-secret' not found"):
            mgr.get_secret("missing-secret")

    def test_get_secret_inactive_state(self, mocker):
        """Reject secrets in non-ACTIVE state"""
        # Arrange
        mgr = self._create_manager(mocker)
        mocker.patch.object(mgr, 'get_vault_id', return_value='vault-ocid')

        # Mock inactive secret
        mock_secret = Mock()
        mock_secret.id = 'secret-ocid'
        mock_secret.lifecycle_state = 'DELETED'

        mock_list_response = Mock()
        mock_list_response.data = [mock_secret]
        mgr.vaults_client.list_secrets.return_value = mock_list_response

        # Act & Assert
        with pytest.raises(ValueError, match="not active"):
            mgr.get_secret("deleted-secret")

    def test_get_secret_base64_decode_error(self, mocker):
        """Handle base64 decode errors"""
        # Arrange
        mgr = self._create_manager(mocker)
        mocker.patch.object(mgr, 'get_vault_id', return_value='vault-ocid')

        mock_secret = Mock()
        mock_secret.id = 'secret-ocid'
        mock_secret.lifecycle_state = 'ACTIVE'

        mock_list_response = Mock()
        mock_list_response.data = [mock_secret]
        mgr.vaults_client.list_secrets.return_value = mock_list_response

        # Mock invalid base64
        mock_bundle_content = Mock()
        mock_bundle_content.content = "invalid-base64!!!!"

        mock_bundle = Mock()
        mock_bundle.secret_bundle_content = mock_bundle_content

        mock_bundle_response = Mock()
        mock_bundle_response.data = mock_bundle

        mgr.secrets_client.get_secret_bundle.return_value = mock_bundle_response

        # Act & Assert
        with pytest.raises(Exception):
            mgr.get_secret("test-secret")

    def test_get_secret_no_credential_leakage_in_logs(self, mocker, caplog):
        """SECURITY: Ensure secrets never appear in logs"""
        # Arrange
        mgr = self._create_manager(mocker)
        mocker.patch.object(mgr, 'get_vault_id', return_value='vault-ocid')

        # Mock secret retrieval
        mock_secret = Mock()
        mock_secret.id = 'secret-ocid'
        mock_secret.lifecycle_state = 'ACTIVE'

        mock_list_response = Mock()
        mock_list_response.data = [mock_secret]
        mgr.vaults_client.list_secrets.return_value = mock_list_response

        # Mock secret bundle with sensitive data
        secret_value = "SUPER_SECRET_API_KEY_12345"
        secret_base64 = base64.b64encode(secret_value.encode('utf-8')).decode('utf-8')

        mock_bundle_content = Mock()
        mock_bundle_content.content = secret_base64

        mock_bundle = Mock()
        mock_bundle.secret_bundle_content = mock_bundle_content

        mock_bundle_response = Mock()
        mock_bundle_response.data = mock_bundle

        mgr.secrets_client.get_secret_bundle.return_value = mock_bundle_response

        # Act
        with caplog.at_level('DEBUG'):  # Capture all logging levels
            result = mgr.get_secret("api-key")

        # Assert - Secret value should NEVER appear in logs
        assert "SUPER_SECRET_API_KEY_12345" not in caplog.text
        assert secret_base64 not in caplog.text
        # Only log that we retrieved the secret (not its value)
        assert "Retrieved secret: api-key" in caplog.text

    @staticmethod
    def _create_manager(mocker):
        """Helper to create manager with mocked dependencies"""
        mocker.patch('oci.config.from_file', return_value={})
        mock_secrets = MagicMock()
        mock_vaults = MagicMock()
        mocker.patch('oci.secrets.SecretsClient', return_value=mock_secrets)
        mocker.patch('oci.vault.VaultsClient', return_value=mock_vaults)
        mgr = SecretsManager(use_instance_principal=False)
        return mgr


class TestGetOciConfig:
    """Test OCI config assembly - CRITICAL for authentication"""

    def test_get_oci_config_success(self, mocker):
        """Successfully assemble OCI config from vault secrets"""
        # Arrange
        mgr = self._create_manager(mocker)

        secrets = {
            "oci-user-ocid": "ocid1.user.oc1..test",
            "oci-tenancy-ocid": "ocid1.tenancy.oc1..test",
            "oci-fingerprint": "aa:bb:cc:dd:ee:ff",
            "oci-private-key": "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----",
            "oci-region": "eu-stockholm-1"
        }

        mocker.patch.object(mgr, 'get_secret', side_effect=lambda name: secrets[name])
        mocker.patch.object(mgr, 'get_secret_optional', return_value="eu-stockholm-1")

        # Act
        config = mgr.get_oci_config()

        # Assert
        assert config["user"] == "ocid1.user.oc1..test"
        assert config["tenancy"] == "ocid1.tenancy.oc1..test"
        assert config["fingerprint"] == "aa:bb:cc:dd:ee:ff"
        assert config["key_content"] == "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----"
        assert config["region"] == "eu-stockholm-1"

    def test_get_oci_config_missing_required_secret(self, mocker):
        """Fail if required secret is missing"""
        # Arrange
        mgr = self._create_manager(mocker)

        # Mock missing user OCID
        mocker.patch.object(
            mgr,
            'get_secret',
            side_effect=ValueError("Secret 'oci-user-ocid' not found")
        )

        # Act & Assert
        with pytest.raises(ValueError, match="oci-user-ocid"):
            mgr.get_oci_config()

    def test_get_oci_config_defaults_region(self, mocker):
        """Use default region if not in vault"""
        # Arrange
        mgr = self._create_manager(mocker)

        secrets = {
            "oci-user-ocid": "ocid1.user.oc1..test",
            "oci-tenancy-ocid": "ocid1.tenancy.oc1..test",
            "oci-fingerprint": "aa:bb:cc:dd:ee:ff",
            "oci-private-key": "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----",
        }

        def mock_get_secret(name):
            if name in secrets:
                return secrets[name]
            raise ValueError(f"Secret '{name}' not found")

        mocker.patch.object(mgr, 'get_secret', side_effect=mock_get_secret)
        mocker.patch.object(mgr, 'get_secret_optional', return_value="eu-stockholm-1")

        # Act
        config = mgr.get_oci_config()

        # Assert
        assert config["region"] == "eu-stockholm-1"

    @staticmethod
    def _create_manager(mocker):
        """Helper to create manager with mocked dependencies"""
        mocker.patch('oci.config.from_file', return_value={})
        mock_secrets = MagicMock()
        mock_vaults = MagicMock()
        mocker.patch('oci.secrets.SecretsClient', return_value=mock_secrets)
        mocker.patch('oci.vault.VaultsClient', return_value=mock_vaults)
        return SecretsManager(use_instance_principal=False)


@pytest.fixture
def mock_oci_config():
    """Mock OCI configuration"""
    return {
        "user": "ocid1.user.oc1..test",
        "tenancy": "ocid1.tenancy.oc1..test",
        "fingerprint": "aa:bb:cc:dd:ee:ff",
        "key_content": "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----",
        "region": "eu-frankfurt-1"
    }
```

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Week 1)
- ✓ Create test directory structure
- ✓ Add testing dependencies to requirements-dev.txt
- ✓ Configure pytest (pytest.ini, pyproject.toml)
- ✓ Set up basic fixtures in conftest.py
- ✓ Create first 10 unit tests for PolisenCollector.__init__()

### Phase 2: Core Unit Tests (Week 2-3)
- ✓ Implement all PolisenCollector unit tests (~50 tests)
- ✓ Implement all SecretsManager unit tests (~30 tests)
- ✓ Add helper function tests (normalize_datetime, etc.)
- ✓ Achieve 80%+ code coverage

### Phase 3: Integration Tests (Week 4)
- ✓ Set up test OCI environment
- ✓ Create OCI Object Storage integration tests
- ✓ Create Vault integration tests
- ✓ Implement API contract tests (rate-limited)

### Phase 4: E2E and CI/CD (Week 5)
- ✓ Implement end-to-end workflow tests
- ✓ Set up GitHub Actions CI pipeline
- ✓ Add pre-commit hooks for test execution
- ✓ Configure coverage reporting (Codecov/Coveralls)

### Phase 5: Quality and Documentation (Week 6)
- ✓ Add security-focused tests
- ✓ Performance/load testing for deduplication logic
- ✓ Document testing strategy
- ✓ Create contributing guidelines for tests

---

## 10. CI/CD Integration

### 10.1 GitHub Actions Workflow

**File: `.github/workflows/test.yml`** (to be created)

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run unit tests
      run: |
        pytest tests/unit -v --cov --cov-report=xml --cov-report=term

    - name: Run integration tests
      run: |
        pytest tests/integration -v -m integration
      env:
        # Set environment variables for test OCI config
        OCI_TEST_MODE: "true"

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-${{ matrix.python-version }}

    - name: Security scan with Bandit
      run: |
        bandit -r . -f json -o bandit-report.json || true

    - name: Dependency vulnerability check
      run: |
        safety check --json || true

  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install linting tools
      run: |
        pip install black flake8 mypy pylint

    - name: Run Black
      run: black --check .

    - name: Run Flake8
      run: flake8 . --max-line-length=100

    - name: Run MyPy
      run: mypy . --ignore-missing-imports || true

    - name: Run Pylint
      run: pylint *.py --fail-under=8.0 || true
```

### 10.2 Pre-commit Hooks

**File: `.pre-commit-config.yaml`** (to be created)

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100']

  - repo: local
    hooks:
      - id: pytest-unit
        name: Run unit tests
        entry: pytest tests/unit -v --maxfail=1
        language: system
        pass_filenames: false
        always_run: true
```

---

## 11. Key Recommendations Summary

### 11.1 CRITICAL Actions (Do First)

1. **Create test infrastructure** (Day 1)
   - Add requirements-dev.txt with pytest and dependencies
   - Create tests/ directory structure
   - Configure pytest.ini

2. **Write security tests** (Week 1)
   - Vault authentication failure handling
   - Secret retrieval error scenarios
   - Credential leakage prevention tests

3. **Unit test core logic** (Week 2-3)
   - PolisenCollector methods (all 7 methods)
   - SecretsManager methods (all 6 methods)
   - Helper functions (normalize_datetime)

4. **Add CI/CD pipeline** (Week 4)
   - GitHub Actions for automated testing
   - Pre-commit hooks for local validation
   - Coverage reporting integration

### 11.2 Test Coverage Targets

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| collect_events.py | 85%+ | CRITICAL |
| secrets_manager.py | 90%+ | CRITICAL |
| Overall project | 80%+ | HIGH |

### 11.3 Testing Best Practices

1. **Follow Test Pyramid**
   - 80% unit tests (fast, isolated)
   - 15% integration tests (component interaction)
   - 5% E2E tests (critical paths)

2. **Use pytest Framework**
   - Modern, Pythonic syntax
   - Rich fixture ecosystem
   - Better than unittest for new projects

3. **Mock External Dependencies**
   - Use pytest-mock for OCI SDK
   - Use responses for HTTP calls
   - Use freezegun for datetime

4. **Test Security-Critical Paths**
   - Authentication failures
   - Missing/corrupted secrets
   - Credential leakage prevention

5. **Maintain Test Independence**
   - No shared state between tests
   - Use fixtures for setup/teardown
   - Tests pass in any order

---

## 12. Conclusion

**Current State:** Zero test coverage represents a significant risk for a production data collection system handling sensitive credentials.

**Required Investment:** ~6 weeks to implement comprehensive testing infrastructure with 120+ tests covering unit, integration, and end-to-end scenarios.

**Expected Outcome:**
- 80%+ code coverage
- Automated quality gates in CI/CD
- Confidence in refactoring and feature additions
- Early detection of security vulnerabilities
- Reduced production incidents

**ROI:** The testing investment will pay for itself through:
- Fewer production bugs
- Faster development velocity
- Easier onboarding for new developers
- Reduced maintenance costs
- Improved security posture

**Next Steps:**
1. Review and approve testing strategy
2. Create requirements-dev.txt
3. Implement Phase 1 (Foundation)
4. Begin writing unit tests for PolisenCollector
5. Set up CI/CD pipeline

---

**Document Version:** 1.0
**Last Updated:** 2026-01-02
**Status:** Ready for Implementation
