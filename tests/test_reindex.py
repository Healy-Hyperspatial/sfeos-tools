"""Tests for reindex module."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from sfeos_tools.cli import cli
from sfeos_tools.reindex import _reindex_single_index, run


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


class TestReindexSingleIndex:
    """Tests for _reindex_single_index function."""

    @pytest.mark.asyncio
    async def test_reindex_single_index_success(self):
        """Test successful reindexing of a single index."""
        mock_client = AsyncMock()
        # client.options() is NOT async, it returns a modified client synchronously
        mock_options = Mock()
        mock_options.indices = mock_client.indices
        mock_client.options = Mock(return_value=mock_options)
        mock_client.indices.create.return_value = {"acknowledged": True}
        mock_client.reindex.return_value = {"task": "task-123"}
        mock_client.tasks.get.return_value = {"completed": True}
        mock_client.indices.update_aliases.return_value = {"acknowledged": True}

        index = "collections-000001"
        new_index = "collections-000002"
        aliases = {"aliases": ["collections"]}

        await _reindex_single_index(mock_client, index, new_index, aliases)

        mock_client.indices.create.assert_called_once_with(index=new_index)
        mock_client.reindex.assert_called_once()
        mock_client.tasks.get.assert_called_once_with(task_id="task-123")
        mock_client.indices.update_aliases.assert_called_once()

        # Verify alias actions
        call_args = mock_client.indices.update_aliases.call_args
        actions = call_args[1]["actions"]
        assert {"add": {"index": new_index, "alias": "collections"}} in actions
        assert {"remove": {"index": index, "alias": "collections"}} in actions

    @pytest.mark.asyncio
    async def test_reindex_single_index_with_script(self):
        """Test that reindex includes the asset migration script."""
        mock_client = AsyncMock()
        mock_options = Mock()
        mock_options.indices = mock_client.indices
        mock_client.options = Mock(return_value=mock_options)
        mock_client.indices.create.return_value = {"acknowledged": True}
        mock_client.reindex.return_value = {"task": "task-123"}
        mock_client.tasks.get.return_value = {"completed": True}
        mock_client.indices.update_aliases.return_value = {"acknowledged": True}

        index = "items-test-000001"
        new_index = "items-test-000002"
        aliases = {"aliases": ["items-test"]}

        await _reindex_single_index(mock_client, index, new_index, aliases)

        # Verify script is included in reindex call
        reindex_call = mock_client.reindex.call_args
        assert "script" in reindex_call[1]
        script = reindex_call[1]["script"]
        assert script["lang"] == "painless"
        assert "assets" in script["source"]
        assert "item_assets" in script["source"]

    @pytest.mark.asyncio
    async def test_reindex_single_index_multiple_aliases(self):
        """Test reindexing with multiple aliases."""
        mock_client = AsyncMock()
        mock_options = Mock()
        mock_options.indices = mock_client.indices
        mock_client.options = Mock(return_value=mock_options)
        mock_client.indices.create.return_value = {"acknowledged": True}
        mock_client.reindex.return_value = {"task": "task-123"}
        mock_client.tasks.get.return_value = {"completed": True}
        mock_client.indices.update_aliases.return_value = {"acknowledged": True}

        index = "collections-000001"
        new_index = "collections-000002"
        aliases = {"aliases": ["collections", "collections-read"]}

        await _reindex_single_index(mock_client, index, new_index, aliases)

        # Verify all aliases are updated
        call_args = mock_client.indices.update_aliases.call_args
        actions = call_args[1]["actions"]
        assert len(actions) == 4  # 2 add + 2 remove
        assert {"add": {"index": new_index, "alias": "collections"}} in actions
        assert {"add": {"index": new_index, "alias": "collections-read"}} in actions
        assert {"remove": {"index": index, "alias": "collections"}} in actions
        assert {"remove": {"index": index, "alias": "collections-read"}} in actions

    @pytest.mark.asyncio
    async def test_reindex_single_index_task_polling(self):
        """Test that reindex polls task status until completion."""
        mock_client = AsyncMock()
        mock_options = Mock()
        mock_options.indices = mock_client.indices
        mock_client.options = Mock(return_value=mock_options)
        mock_client.indices.create.return_value = {"acknowledged": True}
        mock_client.reindex.return_value = {"task": "task-123"}

        # Simulate task not completed, then completed
        mock_client.tasks.get.side_effect = [
            {"completed": False},
            {"completed": False},
            {"completed": True},
        ]
        mock_client.indices.update_aliases.return_value = {"acknowledged": True}

        index = "collections-000001"
        new_index = "collections-000002"
        aliases = {"aliases": ["collections"]}

        with patch("sfeos_tools.reindex.time.sleep") as mock_sleep:
            await _reindex_single_index(mock_client, index, new_index, aliases)

        # Should poll multiple times
        assert mock_client.tasks.get.call_count == 3
        # Should sleep between polls
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_reindex_single_index_with_error(self):
        """Test reindex handling when task returns error."""
        mock_client = AsyncMock()
        mock_options = Mock()
        mock_options.indices = mock_client.indices
        mock_client.options = Mock(return_value=mock_options)
        mock_client.indices.create.return_value = {"acknowledged": True}
        mock_client.reindex.return_value = {"task": "task-123"}
        mock_client.tasks.get.return_value = {
            "completed": False,
            "error": {"type": "exception", "reason": "Something went wrong"},
        }
        mock_client.indices.update_aliases.return_value = {"acknowledged": True}

        index = "collections-000001"
        new_index = "collections-000002"
        aliases = {"aliases": ["collections"]}

        await _reindex_single_index(mock_client, index, new_index, aliases)

        # Should still attempt to update aliases even with error
        mock_client.indices.update_aliases.assert_called_once()

    @pytest.mark.asyncio
    async def test_reindex_single_index_no_aliases(self):
        """Test reindex with no aliases to update."""
        mock_client = AsyncMock()
        mock_options = Mock()
        mock_options.indices = mock_client.indices
        mock_client.options = Mock(return_value=mock_options)
        mock_client.indices.create.return_value = {"acknowledged": True}
        mock_client.reindex.return_value = {"task": "task-123"}
        mock_client.tasks.get.return_value = {"completed": True}

        index = "collections-000001"
        new_index = "collections-000002"
        aliases = {"aliases": []}

        await _reindex_single_index(mock_client, index, new_index, aliases)

        # Should not call update_aliases if no aliases
        mock_client.indices.update_aliases.assert_not_called()


class TestRun:
    """Tests for run function."""

    @pytest.mark.asyncio
    async def test_run_elasticsearch_success(self):
        """Test successful reindex run with Elasticsearch backend."""
        mock_client = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.create_client = mock_client

        # Mock collection response
        mock_client.indices.get_alias.side_effect = [
            {"collections-000001": {"aliases": ["collections"]}},
            {"items-test-collection-000001": {"aliases": ["items-test-collection"]}},
        ]

        mock_client.search.return_value = {
            "hits": {
                "hits": [
                    {"_id": "test-collection", "_source": {"id": "test-collection"}}
                ]
            }
        }

        mock_options = Mock()
        mock_options.indices = mock_client.indices
        mock_client.options = Mock(return_value=mock_options)
        mock_client.indices.create.return_value = {"acknowledged": True}
        mock_client.reindex.return_value = {"task": "task-123"}
        mock_client.tasks.get.return_value = {"completed": True}
        mock_client.indices.update_aliases.return_value = {"acknowledged": True}

        with patch(
            "stac_fastapi.elasticsearch.config.AsyncElasticsearchSettings",
            return_value=mock_settings,
        ), patch(
            "stac_fastapi.elasticsearch.database_logic.create_index_templates",
            new_callable=AsyncMock,
        ) as mock_create_templates:
            await run("elasticsearch")

        mock_create_templates.assert_called_once()
        mock_client.search.assert_called_once()
        # Should reindex collections and items
        assert mock_client.reindex.call_count == 2
        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_opensearch_success(self):
        """Test successful reindex run with OpenSearch backend."""
        mock_client = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.create_client = mock_client

        mock_client.indices.get_alias.side_effect = [
            {"collections-000001": {"aliases": ["collections"]}},
        ]

        mock_client.search.return_value = {"hits": {"hits": []}}

        mock_options = Mock()
        mock_options.indices = mock_client.indices
        mock_client.options = Mock(return_value=mock_options)
        mock_client.indices.create.return_value = {"acknowledged": True}
        mock_client.reindex.return_value = {"task": "task-123"}
        mock_client.tasks.get.return_value = {"completed": True}
        mock_client.indices.update_aliases.return_value = {"acknowledged": True}

        with patch(
            "stac_fastapi.opensearch.config.AsyncOpensearchSettings",
            return_value=mock_settings,
        ), patch(
            "stac_fastapi.opensearch.database_logic.create_index_templates",
            new_callable=AsyncMock,
        ) as mock_create_templates:
            await run("opensearch")

        mock_create_templates.assert_called_once()
        mock_client.search.assert_called_once()
        # Should reindex only collections (no items)
        assert mock_client.reindex.call_count == 1
        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_multiple_collections(self):
        """Test reindex with multiple collections."""
        mock_client = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.create_client = mock_client

        mock_client.indices.get_alias.side_effect = [
            {"collections-000001": {"aliases": ["collections"]}},
            {"items-collection1-000001": {"aliases": ["items-collection1"]}},
            {"items-collection2-000001": {"aliases": ["items-collection2"]}},
        ]

        mock_client.search.return_value = {
            "hits": {
                "hits": [
                    {"_id": "collection1", "_source": {"id": "collection1"}},
                    {"_id": "collection2", "_source": {"id": "collection2"}},
                ]
            }
        }

        mock_options = Mock()
        mock_options.indices = mock_client.indices
        mock_client.options = Mock(return_value=mock_options)
        mock_client.indices.create.return_value = {"acknowledged": True}
        mock_client.reindex.return_value = {"task": "task-123"}
        mock_client.tasks.get.return_value = {"completed": True}
        mock_client.indices.update_aliases.return_value = {"acknowledged": True}

        with patch(
            "stac_fastapi.elasticsearch.config.AsyncElasticsearchSettings",
            return_value=mock_settings,
        ), patch(
            "stac_fastapi.elasticsearch.database_logic.create_index_templates",
            new_callable=AsyncMock,
        ):
            await run("elasticsearch")

        # Should reindex collections + 2 item indexes
        assert mock_client.reindex.call_count == 3

    @pytest.mark.asyncio
    async def test_run_version_increment(self):
        """Test that version numbers are correctly incremented."""
        mock_client = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.create_client = mock_client

        mock_client.indices.get_alias.side_effect = [
            {"collections-000005": {"aliases": ["collections"]}},
        ]

        mock_client.search.return_value = {"hits": {"hits": []}}

        mock_options = Mock()
        mock_options.indices = mock_client.indices
        mock_client.options = Mock(return_value=mock_options)
        mock_client.indices.create.return_value = {"acknowledged": True}
        mock_client.reindex.return_value = {"task": "task-123"}
        mock_client.tasks.get.return_value = {"completed": True}
        mock_client.indices.update_aliases.return_value = {"acknowledged": True}

        with patch(
            "stac_fastapi.elasticsearch.config.AsyncElasticsearchSettings",
            return_value=mock_settings,
        ), patch(
            "stac_fastapi.elasticsearch.database_logic.create_index_templates",
            new_callable=AsyncMock,
        ):
            await run("elasticsearch")

        # Verify new index name has incremented version
        create_call = mock_client.indices.create.call_args
        assert create_call[1]["index"] == "collections-000006"

    @pytest.mark.asyncio
    async def test_run_unsupported_backend(self):
        """Test that unsupported backend raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported backend: invalid"):
            await run("invalid")

    @pytest.mark.asyncio
    async def test_run_closes_client_on_error(self):
        """Test that client is closed even when an error occurs."""
        mock_client = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.create_client = mock_client

        mock_client.indices.get_alias.side_effect = Exception("Connection error")

        with patch(
            "stac_fastapi.elasticsearch.config.AsyncElasticsearchSettings",
            return_value=mock_settings,
        ), patch(
            "stac_fastapi.elasticsearch.database_logic.create_index_templates",
            new_callable=AsyncMock,
        ), pytest.raises(
            Exception, match="Connection error"
        ):
            await run("elasticsearch")

        mock_client.close.assert_called_once()


class TestCLIReindex:
    """Tests for CLI reindex command."""

    def test_cli_reindex_elasticsearch_success(self):
        """Test CLI reindex command with Elasticsearch backend."""
        runner = CliRunner()

        with patch(
            "sfeos_tools.cli.asyncio.run", side_effect=_consume_coroutine
        ) as mock_asyncio_run:
            result = runner.invoke(
                cli,
                [
                    "reindex",
                    "--backend",
                    "elasticsearch",
                    "--yes",
                ],
            )

        assert result.exit_code == 0
        assert "✓ Reindex (Elasticsearch) completed successfully" in result.output
        mock_asyncio_run.assert_called_once()

    def test_cli_reindex_opensearch_success(self):
        """Test CLI reindex command with OpenSearch backend."""
        runner = CliRunner()

        with patch(
            "sfeos_tools.cli.asyncio.run", side_effect=_consume_coroutine
        ) as mock_asyncio_run:
            result = runner.invoke(
                cli,
                [
                    "reindex",
                    "--backend",
                    "opensearch",
                    "--yes",
                ],
            )

        assert result.exit_code == 0
        assert "✓ Reindex (Opensearch) completed successfully" in result.output
        mock_asyncio_run.assert_called_once()

    def test_cli_reindex_with_connection_options(self):
        """Test CLI reindex command with connection options."""
        runner = CliRunner()

        with patch("sfeos_tools.cli.asyncio.run") as mock_asyncio_run, patch.dict(
            "os.environ", {}, clear=True
        ):
            result = runner.invoke(
                cli,
                [
                    "reindex",
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
                    "--yes",
                ],
            )

        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()

    def test_cli_reindex_missing_backend(self):
        """Test CLI reindex command fails without backend."""
        runner = CliRunner()
        result = runner.invoke(cli, ["reindex", "--yes"])

        assert result.exit_code != 0
        assert "Missing option '--backend'" in result.output

    def test_cli_reindex_requires_confirmation(self):
        """Test CLI reindex command requires confirmation without --yes flag."""
        runner = CliRunner()

        # Simulate user declining confirmation
        result = runner.invoke(
            cli,
            ["reindex", "--backend", "elasticsearch"],
            input="n\n",
        )

        assert result.exit_code == 0
        assert "Aborted" in result.output

    def test_cli_reindex_accepts_confirmation(self):
        """Test CLI reindex command proceeds with user confirmation."""
        runner = CliRunner()

        with patch(
            "sfeos_tools.cli.asyncio.run", side_effect=_consume_coroutine
        ) as mock_asyncio_run:
            result = runner.invoke(
                cli,
                ["reindex", "--backend", "elasticsearch"],
                input="y\n",
            )

        assert result.exit_code == 0
        assert "✓ Reindex (Elasticsearch) completed successfully" in result.output
        mock_asyncio_run.assert_called_once()

    def test_cli_reindex_handles_error(self):
        """Test CLI reindex command handles errors gracefully."""
        runner = CliRunner()

        with patch(
            "sfeos_tools.cli.asyncio.run",
            side_effect=_consume_coroutine_with_exception(Exception("Reindex failed")),
        ):
            result = runner.invoke(
                cli,
                ["reindex", "--backend", "elasticsearch", "--yes"],
            )

        assert result.exit_code == 1
        assert "✗ Reindex failed" in result.output
        assert "Reindex failed" in result.output

    def test_cli_reindex_handles_ssl_error(self):
        """Test CLI reindex command provides SSL error hint."""
        runner = CliRunner()

        with patch(
            "sfeos_tools.cli.asyncio.run",
            side_effect=_consume_coroutine_with_exception(
                Exception("TLS verification failed")
            ),
        ):
            result = runner.invoke(
                cli,
                ["reindex", "--backend", "elasticsearch", "--yes"],
            )

        assert result.exit_code == 1
        assert "✗ Reindex failed" in result.output
        assert "💡 Hint" in result.output
        assert "--no-ssl" in result.output

    def test_cli_reindex_handles_connection_error(self):
        """Test CLI reindex command provides connection error hint."""
        runner = CliRunner()

        with patch(
            "sfeos_tools.cli.asyncio.run",
            side_effect=_consume_coroutine_with_exception(
                Exception("Connection refused")
            ),
        ):
            result = runner.invoke(
                cli,
                ["reindex", "--backend", "elasticsearch", "--yes"],
            )

        assert result.exit_code == 1
        assert "✗ Reindex failed" in result.output
        assert "💡 Hint" in result.output
        assert "database is running" in result.output

    def test_cli_reindex_handles_keyboard_interrupt(self):
        """Test CLI reindex command handles keyboard interrupt."""
        runner = CliRunner()

        with patch(
            "sfeos_tools.cli.asyncio.run",
            side_effect=_consume_coroutine_with_exception(KeyboardInterrupt()),
        ):
            result = runner.invoke(
                cli,
                ["reindex", "--backend", "elasticsearch", "--yes"],
            )

        assert result.exit_code == 1
        assert "✗ Reindex interrupted by user" in result.output
