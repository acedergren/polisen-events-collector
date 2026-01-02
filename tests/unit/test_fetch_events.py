"""
Unit tests for API event fetching

PRIORITY: CRITICAL - External API interactions and error handling
"""
import pytest
import json
from unittest.mock import Mock, MagicMock
import requests
from collect_events import PolisenCollector, API_URL


class TestFetchEvents:
    """Test API event fetching"""

    def test_fetch_events_success(self, mocker, sample_events):
        """Successfully fetch events from API"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = sample_events
        mock_response.status_code = 200
        mock_get = mocker.patch('requests.get', return_value=mock_response)

        collector = self._create_collector(mocker)

        # Act
        events = collector.fetch_events()

        # Assert
        assert events == sample_events
        assert len(events) == 2
        mock_get.assert_called_once()

    def test_fetch_events_includes_user_agent(self, mocker, sample_events):
        """Verify User-Agent header is included (API requirement)"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = sample_events
        mock_response.status_code = 200
        mock_get = mocker.patch('requests.get', return_value=mock_response)

        collector = self._create_collector(mocker)

        # Act
        collector.fetch_events()

        # Assert
        call_args = mock_get.call_args
        assert call_args[0][0] == API_URL
        assert 'headers' in call_args[1]
        assert 'User-Agent' in call_args[1]['headers']
        assert 'PolisEnEventsCollector' in call_args[1]['headers']['User-Agent']

    def test_fetch_events_timeout_configured(self, mocker, sample_events):
        """Verify timeout is set on requests"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = sample_events
        mock_get = mocker.patch('requests.get', return_value=mock_response)

        collector = self._create_collector(mocker)

        # Act
        collector.fetch_events()

        # Assert
        call_kwargs = mock_get.call_args[1]
        assert 'timeout' in call_kwargs
        assert call_kwargs['timeout'] == 30

    def test_fetch_events_timeout_raises_exception(self, mocker):
        """Handle timeout errors appropriately"""
        # Arrange
        mocker.patch('requests.get', side_effect=requests.Timeout("Connection timeout"))
        collector = self._create_collector(mocker)

        # Act & Assert
        with pytest.raises(requests.Timeout, match="Connection timeout"):
            collector.fetch_events()

    def test_fetch_events_connection_error(self, mocker):
        """Handle connection errors appropriately"""
        # Arrange
        mocker.patch(
            'requests.get',
            side_effect=requests.ConnectionError("Failed to connect to API")
        )
        collector = self._create_collector(mocker)

        # Act & Assert
        with pytest.raises(requests.ConnectionError, match="Failed to connect"):
            collector.fetch_events()

    def test_fetch_events_http_404_error(self, mocker):
        """Handle HTTP 404 errors"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mocker.patch('requests.get', return_value=mock_response)
        collector = self._create_collector(mocker)

        # Act & Assert
        with pytest.raises(requests.HTTPError):
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

    def test_fetch_events_http_503_service_unavailable(self, mocker):
        """Handle service unavailable errors"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "503 Service Unavailable"
        )
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
        mock_response.status_code = 200
        mocker.patch('requests.get', return_value=mock_response)
        collector = self._create_collector(mocker)

        # Act & Assert
        with pytest.raises(json.JSONDecodeError):
            collector.fetch_events()

    def test_fetch_events_empty_response(self, mocker, caplog):
        """Handle empty event list from API"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.status_code = 200
        mocker.patch('requests.get', return_value=mock_response)
        collector = self._create_collector(mocker)

        # Act
        with caplog.at_level('INFO'):
            events = collector.fetch_events()

        # Assert
        assert events == []
        assert len(events) == 0
        assert "Fetched 0 events from API" in caplog.text

    def test_fetch_events_logs_count(self, mocker, sample_events, caplog):
        """Verify event count is logged"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = sample_events
        mock_response.status_code = 200
        mocker.patch('requests.get', return_value=mock_response)
        collector = self._create_collector(mocker)

        # Act
        with caplog.at_level('INFO'):
            collector.fetch_events()

        # Assert
        assert "Fetched 2 events from API" in caplog.text
        assert f"Fetching events from {API_URL}" in caplog.text

    def test_fetch_events_logs_errors(self, mocker, caplog):
        """Verify errors are logged appropriately"""
        # Arrange
        mocker.patch(
            'requests.get',
            side_effect=requests.ConnectionError("Network error")
        )
        collector = self._create_collector(mocker)

        # Act
        with caplog.at_level('ERROR'):
            try:
                collector.fetch_events()
            except requests.ConnectionError:
                pass

        # Assert
        assert "Failed to fetch events" in caplog.text

    def test_fetch_events_uses_https(self, mocker, sample_events):
        """Verify HTTPS is used (API requirement)"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = sample_events
        mock_get = mocker.patch('requests.get', return_value=mock_response)

        collector = self._create_collector(mocker)

        # Act
        collector.fetch_events()

        # Assert
        called_url = mock_get.call_args[0][0]
        assert called_url.startswith('https://'), "API must use HTTPS"

    @pytest.mark.parametrize("event_count", [0, 1, 10, 100, 500])
    def test_fetch_events_various_sizes(self, mocker, event_count):
        """Test fetching various event list sizes"""
        # Arrange
        events = [{"id": i, "name": f"Event {i}"} for i in range(event_count)]
        mock_response = Mock()
        mock_response.json.return_value = events
        mock_response.status_code = 200
        mocker.patch('requests.get', return_value=mock_response)

        collector = self._create_collector(mocker)

        # Act
        result = collector.fetch_events()

        # Assert
        assert len(result) == event_count

    def test_fetch_events_request_exception_generic(self, mocker):
        """Handle generic request exceptions"""
        # Arrange
        mocker.patch(
            'requests.get',
            side_effect=requests.RequestException("Generic request error")
        )
        collector = self._create_collector(mocker)

        # Act & Assert
        with pytest.raises(requests.RequestException):
            collector.fetch_events()

    @staticmethod
    def _create_collector(mocker):
        """Helper to create collector with mocked dependencies"""
        mocker.patch('collect_events.get_oci_config_from_vault')
        mocker.patch('oci.object_storage.ObjectStorageClient')
        return PolisenCollector(use_vault=True)
