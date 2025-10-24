"""Tests for the viewer module."""
from unittest.mock import Mock, patch

from sfeos_tools.viewer import STACClient


class TestSTACClient:
    """Test the STAC client."""

    def test_init(self):
        """Test client initialization."""
        client = STACClient("http://localhost:8080")
        assert client.base_url == "http://localhost:8080"

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from base URL."""
        client = STACClient("http://localhost:8080/")
        assert client.base_url == "http://localhost:8080"

    @patch("sfeos_tools.viewer.httpx.Client")
    def test_get_collections_success(self, mock_client_class):
        """Test successful collection fetching."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "collections": [{"id": "test-collection", "title": "Test Collection"}]
        }
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Test
        client = STACClient("http://localhost:8080")
        collections = client.get_collections()

        assert len(collections) == 1
        assert collections[0]["id"] == "test-collection"
        mock_client.get.assert_called_once_with("http://localhost:8080/collections")

    @patch("sfeos_tools.viewer.httpx.Client")
    def test_get_collections_error(self, mock_client_class):
        """Test collection fetching with error."""
        # Setup mock to raise exception
        mock_client = Mock()
        mock_client.get.side_effect = Exception("Connection error")
        mock_client_class.return_value = mock_client

        # Test - should return empty list on error
        client = STACClient("http://localhost:8080")
        with patch("streamlit.error"):  # Mock streamlit error display
            collections = client.get_collections()

        assert collections == []

    @patch("sfeos_tools.viewer.httpx.Client")
    def test_get_collection_success(self, mock_client_class):
        """Test successful single collection fetch."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "test-collection",
            "title": "Test Collection",
        }
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Test
        client = STACClient("http://localhost:8080")
        collection = client.get_collection("test-collection")

        assert collection["id"] == "test-collection"
        mock_client.get.assert_called_once_with(
            "http://localhost:8080/collections/test-collection"
        )

    @patch("sfeos_tools.viewer.httpx.Client")
    def test_search_items_basic(self, mock_client_class):
        """Test basic item search."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "features": [
                {"id": "item-1", "type": "Feature"},
                {"id": "item-2", "type": "Feature"},
            ]
        }
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Test
        client = STACClient("http://localhost:8080")
        items = client.search_items(limit=100)

        assert len(items) == 2
        assert items[0]["id"] == "item-1"
        mock_client.get.assert_called_once()

    @patch("sfeos_tools.viewer.httpx.Client")
    def test_search_items_with_collection(self, mock_client_class):
        """Test item search with collection filter."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {"features": []}
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Test
        client = STACClient("http://localhost:8080")
        client.search_items(collection_id="test-collection", limit=50)

        # Should use GET with collection parameter
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://localhost:8080/search"
        assert call_args[1]["params"]["collections"] == "test-collection"
        assert call_args[1]["params"]["limit"] == 50

    @patch("sfeos_tools.viewer.httpx.Client")
    def test_search_items_with_bbox(self, mock_client_class):
        """Test item search with bbox filter."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {"features": []}
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Test
        client = STACClient("http://localhost:8080")
        bbox = [-180, -90, 180, 90]
        client.search_items(bbox=bbox, limit=100)

        # Should use GET with bbox as comma-separated string
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://localhost:8080/search"
        assert call_args[1]["params"]["bbox"] == "-180,-90,180,90"
        assert call_args[1]["params"]["limit"] == 100
