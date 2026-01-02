"""
Unit tests for PolisenCollector initialization

PRIORITY: CRITICAL - Authentication and client setup
"""
import pytest
from unittest.mock import MagicMock, patch
from collect_events import PolisenCollector


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
        """Verify Stockholm region is set for data residency compliance"""
        # Arrange
        mocker.patch('collect_events.get_oci_config_from_vault', return_value=mock_oci_config)
        mocker.patch('oci.object_storage.ObjectStorageClient')

        # Act
        collector = PolisenCollector(use_vault=True)

        # Assert
        assert collector.config["region"] == "eu-stockholm-1"

    def test_init_logs_authentication_mode_vault(self, mocker, mock_oci_config, caplog):
        """Verify appropriate logging for vault authentication mode"""
        # Arrange
        mocker.patch('collect_events.get_oci_config_from_vault', return_value=mock_oci_config)
        mocker.patch('oci.object_storage.ObjectStorageClient')

        # Act
        with caplog.at_level('INFO'):
            PolisenCollector(use_vault=True)

        # Assert
        assert "Loading OCI credentials from vault (secure mode)" in caplog.text
        assert "OCI client initialized successfully" in caplog.text

    def test_init_logs_authentication_mode_local(self, mocker, mock_oci_config, caplog):
        """Verify warning when using local config (insecure mode)"""
        # Arrange
        mocker.patch('oci.config.from_file', return_value=mock_oci_config)
        mocker.patch('oci.object_storage.ObjectStorageClient')

        # Act
        with caplog.at_level('WARNING'):
            PolisenCollector(use_vault=False)

        # Assert
        assert "Using local config file (INSECURE - only for testing!)" in caplog.text

    def test_init_creates_object_storage_client(self, mocker, mock_oci_config):
        """Verify ObjectStorageClient is created with correct config"""
        # Arrange
        mocker.patch('collect_events.get_oci_config_from_vault', return_value=mock_oci_config)
        mock_client_class = mocker.patch('oci.object_storage.ObjectStorageClient')

        # Act
        collector = PolisenCollector(use_vault=True)

        # Assert
        mock_client_class.assert_called_once()
        call_args = mock_client_class.call_args[0][0]
        assert call_args["region"] == "eu-stockholm-1"
        assert "user" in call_args
        assert "tenancy" in call_args

    def test_init_oci_client_failure(self, mocker, mock_oci_config):
        """Handle OCI client initialization failure"""
        # Arrange
        mocker.patch('collect_events.get_oci_config_from_vault', return_value=mock_oci_config)
        mocker.patch(
            'oci.object_storage.ObjectStorageClient',
            side_effect=Exception("Failed to create OCI client")
        )

        # Act & Assert
        with pytest.raises(Exception, match="Failed to create OCI client"):
            PolisenCollector(use_vault=True)

    @pytest.mark.security
    def test_init_no_secrets_in_logs(self, mocker, mock_oci_config, caplog):
        """SECURITY: Ensure secrets never appear in initialization logs"""
        # Arrange
        sensitive_config = {
            **mock_oci_config,
            "key_content": "-----BEGIN PRIVATE KEY-----\nSUPER_SECRET_KEY\n-----END PRIVATE KEY-----",
            "fingerprint": "aa:bb:cc:dd:ee:ff:11:22:33:44"
        }
        mocker.patch('collect_events.get_oci_config_from_vault', return_value=sensitive_config)
        mocker.patch('oci.object_storage.ObjectStorageClient')

        # Act
        with caplog.at_level('DEBUG'):  # Capture all log levels
            collector = PolisenCollector(use_vault=True)

        # Assert - No sensitive data in logs
        assert "SUPER_SECRET_KEY" not in caplog.text
        assert "BEGIN PRIVATE KEY" not in caplog.text
        assert sensitive_config["fingerprint"] not in caplog.text
        assert sensitive_config["user"] not in caplog.text
        assert sensitive_config["tenancy"] not in caplog.text

    def test_init_default_vault_mode(self, mocker, mock_oci_config):
        """Verify default initialization uses vault (secure by default)"""
        # Arrange
        mock_vault = mocker.patch(
            'collect_events.get_oci_config_from_vault',
            return_value=mock_oci_config
        )
        mocker.patch('oci.object_storage.ObjectStorageClient')

        # Act - Not specifying use_vault parameter
        collector = PolisenCollector()

        # Assert - Should use vault by default
        mock_vault.assert_called_once()
