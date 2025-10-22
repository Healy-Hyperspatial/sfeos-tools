"""Tests for bbox_shape module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from sfeos_tools.bbox_shape import process_collection_bbox_shape, run_add_bbox_shape
from sfeos_tools.cli import cli


def _consume_coroutine(coro):
    """Helper to consume a coroutine without awaiting it (for mocking asyncio.run)."""
    try:
        coro.close()
    except (StopIteration, RuntimeError, GeneratorExit):
        pass


def _consume_coroutine_with_exception(exception):
    """Helper that consumes coroutine and raises exception (for error tests)."""

    def _side_effect(coro):
        try:
            coro.close()
        except (StopIteration, RuntimeError, GeneratorExit):
            pass
        raise exception

    return _side_effect


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


class TestCLIAddBboxShape:
    """Tests for CLI add-bbox-shape command."""

    def test_cli_add_bbox_shape_elasticsearch_success(self):
        """Test CLI add-bbox-shape command with Elasticsearch backend."""
        runner = CliRunner()

        with patch(
            "sfeos_tools.cli.asyncio.run", side_effect=_consume_coroutine
        ) as mock_asyncio_run:
            result = runner.invoke(
                cli,
                [
                    "add-bbox-shape",
                    "--backend",
                    "elasticsearch",
                ],
            )

        assert result.exit_code == 0
        assert "✓ Migration completed successfully" in result.output
        mock_asyncio_run.assert_called_once()

    def test_cli_add_bbox_shape_opensearch_success(self):
        """Test CLI add-bbox-shape command with OpenSearch backend."""
        runner = CliRunner()

        with patch(
            "sfeos_tools.cli.asyncio.run", side_effect=_consume_coroutine
        ) as mock_asyncio_run:
            result = runner.invoke(
                cli,
                [
                    "add-bbox-shape",
                    "--backend",
                    "opensearch",
                ],
            )

        assert result.exit_code == 0
        assert "✓ Migration completed successfully" in result.output
        mock_asyncio_run.assert_called_once()

    def test_cli_add_bbox_shape_with_connection_options(self):
        """Test CLI add-bbox-shape command with connection options."""
        runner = CliRunner()

        with patch("sfeos_tools.cli.asyncio.run") as mock_asyncio_run, patch.dict(
            "os.environ", {}, clear=True
        ):
            result = runner.invoke(
                cli,
                [
                    "add-bbox-shape",
                    "--backend",
                    "elasticsearch",
                    "--host",
                    "db.example.com",
                    "--port",
                    "9200",
                    "--no-ssl",
                    "--user",
                    "admin",
                    "--password",
                    "secret",
                ],
            )

        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()

    def test_cli_add_bbox_shape_missing_backend(self):
        """Test CLI add-bbox-shape command fails without backend."""
        runner = CliRunner()
        result = runner.invoke(cli, ["add-bbox-shape"])

        assert result.exit_code != 0
        assert "Missing option '--backend'" in result.output

    def test_cli_add_bbox_shape_invalid_backend(self):
        """Test CLI add-bbox-shape command with invalid backend."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "add-bbox-shape",
                "--backend",
                "invalid",
            ],
        )

        assert result.exit_code != 0
        assert "Invalid value for '--backend'" in result.output

    def test_cli_add_bbox_shape_handles_error(self):
        """Test CLI add-bbox-shape command handles errors gracefully."""
        runner = CliRunner()

        with patch(
            "sfeos_tools.cli.asyncio.run",
            side_effect=_consume_coroutine_with_exception(
                Exception("Migration failed")
            ),
        ):
            result = runner.invoke(
                cli,
                ["add-bbox-shape", "--backend", "elasticsearch"],
            )

        assert result.exit_code == 1
        assert "✗ Migration failed" in result.output
        assert "Migration failed" in result.output

    def test_cli_add_bbox_shape_handles_ssl_error(self):
        """Test CLI add-bbox-shape command provides SSL error hint."""
        runner = CliRunner()

        with patch(
            "sfeos_tools.cli.asyncio.run",
            side_effect=_consume_coroutine_with_exception(
                Exception("TLS verification failed")
            ),
        ):
            result = runner.invoke(
                cli,
                ["add-bbox-shape", "--backend", "elasticsearch"],
            )

        assert result.exit_code == 1
        assert "✗ Migration failed" in result.output
        assert "💡 Hint" in result.output
        assert "--no-ssl" in result.output

    def test_cli_add_bbox_shape_handles_connection_error(self):
        """Test CLI add-bbox-shape command provides connection error hint."""
        runner = CliRunner()

        with patch(
            "sfeos_tools.cli.asyncio.run",
            side_effect=_consume_coroutine_with_exception(
                Exception("Connection refused")
            ),
        ):
            result = runner.invoke(
                cli,
                ["add-bbox-shape", "--backend", "elasticsearch"],
            )

        assert result.exit_code == 1
        assert "✗ Migration failed" in result.output
        assert "💡 Hint" in result.output
        assert "database is running" in result.output

    def test_cli_add_bbox_shape_handles_keyboard_interrupt(self):
        """Test CLI add-bbox-shape command handles keyboard interrupt."""
        runner = CliRunner()

        with patch(
            "sfeos_tools.cli.asyncio.run",
            side_effect=_consume_coroutine_with_exception(KeyboardInterrupt()),
        ):
            result = runner.invoke(
                cli,
                ["add-bbox-shape", "--backend", "elasticsearch"],
            )

        assert result.exit_code == 1
        assert "✗ Migration interrupted by user" in result.output

    def test_cli_add_bbox_shape_sets_env_vars(self):
        """Test that CLI options are properly set as environment variables."""
        import os

        runner = CliRunner()

        with patch("sfeos_tools.cli.asyncio.run"), patch.dict(
            "os.environ", {}, clear=True
        ):
            result = runner.invoke(
                cli,
                [
                    "add-bbox-shape",
                    "--backend",
                    "elasticsearch",
                    "--host",
                    "custom-host",
                    "--port",
                    "9300",
                    "--use-ssl",
                    "--user",
                    "testuser",
                    "--password",
                    "testpass",
                ],
            )

            # Verify environment variables were set
            assert os.environ["ES_HOST"] == "custom-host"
            assert os.environ["ES_PORT"] == "9300"
            assert os.environ["ES_USE_SSL"] == "true"
            assert os.environ["ES_USER"] == "testuser"
            assert os.environ["ES_PASS"] == "testpass"
            assert result.exit_code == 0

    def test_cli_add_bbox_shape_no_ssl_flag(self):
        """Test that --no-ssl flag sets environment variable correctly."""
        import os

        runner = CliRunner()

        with patch("sfeos_tools.cli.asyncio.run"), patch.dict(
            "os.environ", {}, clear=True
        ):
            result = runner.invoke(
                cli,
                [
                    "add-bbox-shape",
                    "--backend",
                    "elasticsearch",
                    "--no-ssl",
                ],
            )

            assert os.environ["ES_USE_SSL"] == "false"
            assert result.exit_code == 0
