"""
Shared test fixtures and configuration for all tests
"""
import pytest
from unittest.mock import Mock, MagicMock


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
