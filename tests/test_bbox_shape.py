"""Tests for bbox_shape module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sfeos_tools.bbox_shape import process_collection_bbox_shape, run_add_bbox_shape


class TestProcessCollectionBboxShape:
    """Tests for process_collection_bbox_shape function."""

    @pytest.mark.asyncio
    async def test_process_collection_bbox_shape_elasticsearch_updated(self):
        """Test processing a collection with Elasticsearch backend when bbox_shape is added."""
        mock_client = AsyncMock()
        collection_doc = {
            "_id": "test-collection",
            "_source": {
                "id": "test-collection",
                "bbox": [[-180, -90, 180, 90]],
            },
        }

        with patch(
            "sfeos_tools.bbox_shape.add_bbox_shape_to_collection", return_value=True
        ):
            result = await process_collection_bbox_shape(
                mock_client, collection_doc, "elasticsearch"
            )

        assert result is True
        mock_client.index.assert_called_once()
        call_kwargs = mock_client.index.call_args[1]
        assert call_kwargs["index"] == "collections"
        assert call_kwargs["id"] == "test-collection"
        assert call_kwargs["refresh"] is True
        assert "document" in call_kwargs

    @pytest.mark.asyncio
    async def test_process_collection_bbox_shape_opensearch_updated(self):
        """Test processing a collection with OpenSearch backend when bbox_shape is added."""
        mock_client = AsyncMock()
        collection_doc = {
            "_id": "test-collection",
            "_source": {
                "id": "test-collection",
                "bbox": [[-180, -90, 180, 90]],
            },
        }

        with patch(
            "sfeos_tools.bbox_shape.add_bbox_shape_to_collection", return_value=True
        ):
            result = await process_collection_bbox_shape(
                mock_client, collection_doc, "opensearch"
            )

        assert result is True
        mock_client.index.assert_called_once()
        call_kwargs = mock_client.index.call_args[1]
        assert call_kwargs["index"] == "collections"
        assert call_kwargs["id"] == "test-collection"
        assert call_kwargs["refresh"] is True
        assert "body" in call_kwargs

    @pytest.mark.asyncio
    async def test_process_collection_bbox_shape_not_updated(self):
        """Test processing a collection when bbox_shape is not added."""
        mock_client = AsyncMock()
        collection_doc = {
            "_id": "test-collection",
            "_source": {
                "id": "test-collection",
                "bbox": [[-180, -90, 180, 90]],
            },
        }

        with patch(
            "sfeos_tools.bbox_shape.add_bbox_shape_to_collection", return_value=False
        ):
            result = await process_collection_bbox_shape(
                mock_client, collection_doc, "elasticsearch"
            )

        assert result is False
        mock_client.index.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_collection_uses_id_from_source(self):
        """Test that collection ID is extracted from _source when available."""
        mock_client = AsyncMock()
        collection_doc = {
            "_id": "doc-id",
            "_source": {
                "id": "collection-id",
                "bbox": [[-180, -90, 180, 90]],
            },
        }

        with patch(
            "sfeos_tools.bbox_shape.add_bbox_shape_to_collection", return_value=True
        ):
            await process_collection_bbox_shape(
                mock_client, collection_doc, "elasticsearch"
            )

        call_kwargs = mock_client.index.call_args[1]
        assert call_kwargs["id"] == "collection-id"

    @pytest.mark.asyncio
    async def test_process_collection_falls_back_to_doc_id(self):
        """Test that collection ID falls back to _id when not in _source."""
        mock_client = AsyncMock()
        collection_doc = {
            "_id": "doc-id",
            "_source": {
                "bbox": [[-180, -90, 180, 90]],
            },
        }

        with patch(
            "sfeos_tools.bbox_shape.add_bbox_shape_to_collection", return_value=True
        ):
            await process_collection_bbox_shape(
                mock_client, collection_doc, "elasticsearch"
            )

        call_kwargs = mock_client.index.call_args[1]
        assert call_kwargs["id"] == "doc-id"


class TestRunAddBboxShape:
    """Tests for run_add_bbox_shape function."""

    @pytest.mark.asyncio
    async def test_run_add_bbox_shape_elasticsearch(self):
        """Test run_add_bbox_shape with Elasticsearch backend."""
        mock_client = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.create_client = mock_client

        mock_client.search.return_value = {
            "hits": {
                "total": {"value": 2},
                "hits": [
                    {
                        "_id": "collection-1",
                        "_source": {
                            "id": "collection-1",
                            "bbox": [[-180, -90, 180, 90]],
                        },
                    },
                    {
                        "_id": "collection-2",
                        "_source": {
                            "id": "collection-2",
                            "bbox": [[-180, -90, 180, 90]],
                        },
                    },
                ],
            }
        }

        with patch(
            "stac_fastapi.elasticsearch.config.AsyncElasticsearchSettings",
            return_value=mock_settings,
        ), patch(
            "sfeos_tools.bbox_shape.add_bbox_shape_to_collection", return_value=True
        ):
            await run_add_bbox_shape("elasticsearch")

        mock_client.search.assert_called_once()
        assert mock_client.index.call_count == 2
        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_add_bbox_shape_opensearch(self):
        """Test run_add_bbox_shape with OpenSearch backend."""
        mock_client = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.create_client = mock_client

        mock_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_id": "collection-1",
                        "_source": {
                            "id": "collection-1",
                            "bbox": [[-180, -90, 180, 90]],
                        },
                    },
                ],
            }
        }

        with patch(
            "stac_fastapi.opensearch.config.AsyncOpensearchSettings",
            return_value=mock_settings,
        ), patch(
            "sfeos_tools.bbox_shape.add_bbox_shape_to_collection", return_value=True
        ):
            await run_add_bbox_shape("opensearch")

        mock_client.search.assert_called_once()
        mock_client.index.assert_called_once()
        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_add_bbox_shape_handles_mixed_results(self):
        """Test run_add_bbox_shape with some collections updated and some skipped."""
        mock_client = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.create_client = mock_client

        mock_client.search.return_value = {
            "hits": {
                "total": {"value": 3},
                "hits": [
                    {
                        "_id": "collection-1",
                        "_source": {
                            "id": "collection-1",
                            "bbox": [[-180, -90, 180, 90]],
                        },
                    },
                    {
                        "_id": "collection-2",
                        "_source": {
                            "id": "collection-2",
                            "bbox": [[-180, -90, 180, 90]],
                        },
                    },
                    {
                        "_id": "collection-3",
                        "_source": {
                            "id": "collection-3",
                            "bbox": [[-180, -90, 180, 90]],
                        },
                    },
                ],
            }
        }

        side_effects = [True, False, True]

        with patch(
            "stac_fastapi.elasticsearch.config.AsyncElasticsearchSettings",
            return_value=mock_settings,
        ), patch(
            "sfeos_tools.bbox_shape.add_bbox_shape_to_collection",
            side_effect=side_effects,
        ):
            await run_add_bbox_shape("elasticsearch")

        assert mock_client.index.call_count == 2

    @pytest.mark.asyncio
    async def test_run_add_bbox_shape_closes_client_on_error(self):
        """Test that client is closed even when an error occurs."""
        mock_client = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.create_client = mock_client

        mock_client.search.side_effect = Exception("Connection error")

        with patch(
            "stac_fastapi.elasticsearch.config.AsyncElasticsearchSettings",
            return_value=mock_settings,
        ), pytest.raises(Exception, match="Connection error"):
            await run_add_bbox_shape("elasticsearch")

        mock_client.close.assert_called_once()
