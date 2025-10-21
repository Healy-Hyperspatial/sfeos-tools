"""SFEOS CLI Tools - Utilities for managing stac-fastapi-elasticsearch-opensearch deployments.

This tool provides various utilities for managing and maintaining SFEOS deployments,
including database migrations, maintenance tasks, and more.

Usage:
    sfeos-tools add-bbox-shape --backend elasticsearch
    sfeos-tools add-bbox-shape --backend opensearch
"""

import asyncio
import logging
import sys

import click

from .bbox_shape import run_add_bbox_shape
from .reindex import run as unified_reindex_run

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="0.1.0", prog_name="sfeos-tools")
def cli():
    """SFEOS Tools - Utilities for managing stac-fastapi-elasticsearch-opensearch deployments."""
    pass


@cli.command("add-bbox-shape")
@click.option(
    "--backend",
    type=click.Choice(["elasticsearch", "opensearch"], case_sensitive=False),
    required=True,
    help="Database backend to use",
)
@click.option(
    "--host",
    type=str,
    default=None,
    help="Database host (default: localhost or ES_HOST env var)",
)
@click.option(
    "--port",
    type=int,
    default=None,
    help="Database port (default: 9200 for ES, 9202 for OS, or ES_PORT env var)",
)
@click.option(
    "--use-ssl/--no-ssl",
    default=None,
    help="Use SSL connection (default: true or ES_USE_SSL env var)",
)
@click.option(
    "--user",
    type=str,
    default=None,
    help="Database username (default: ES_USER env var)",
)
@click.option(
    "--password",
    type=str,
    default=None,
    help="Database password (default: ES_PASS env var)",
)
def add_bbox_shape(backend, host, port, use_ssl, user, password):
    """Add bbox_shape field to existing collections for spatial search support.

    This migration is required for collections created before spatial search
    was added. Collections created or updated after this feature will
    automatically have the bbox_shape field.

    Examples:
        sfeos_tools.py add-bbox-shape --backend elasticsearch
        sfeos_tools.py add-bbox-shape --backend opensearch --host db.example.com --port 9200
        sfeos_tools.py add-bbox-shape --backend elasticsearch --no-ssl --host localhost
    """
    import os

    # Set environment variables from CLI options if provided
    if host:
        os.environ["ES_HOST"] = host
    if port:
        os.environ["ES_PORT"] = str(port)
    if use_ssl is not None:
        os.environ["ES_USE_SSL"] = "true" if use_ssl else "false"
    if user:
        os.environ["ES_USER"] = user
    if password:
        os.environ["ES_PASS"] = password

    try:
        asyncio.run(run_add_bbox_shape(backend.lower()))
        click.echo(click.style("✓ Migration completed successfully", fg="green"))
    except KeyboardInterrupt:
        click.echo(click.style("\n✗ Migration interrupted by user", fg="yellow"))
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        click.echo(click.style(f"✗ Migration failed: {error_msg}", fg="red"))

        # Provide helpful hints for common errors
        if "TLS" in error_msg or "SSL" in error_msg:
            click.echo(
                click.style(
                    "\n💡 Hint: If you're connecting to a local Docker Compose instance, "
                    "try adding --no-ssl flag",
                    fg="yellow",
                )
            )
        elif "Connection refused" in error_msg:
            click.echo(
                click.style(
                    "\n💡 Hint: Make sure your database is running and accessible at the specified host:port",
                    fg="yellow",
                )
            )
        sys.exit(1)


@cli.command("reindex")
@click.option(
    "--backend",
    type=click.Choice(["elasticsearch", "opensearch"], case_sensitive=False),
    required=True,
    help="Database backend to use",
)
@click.option(
    "--host",
    type=str,
    default=None,
    help="Database host (default: localhost or ES_HOST env var)",
)
@click.option(
    "--port",
    type=int,
    default=None,
    help="Database port (default: 9200 for ES, 9202 for OS, or ES_PORT env var)",
)
@click.option(
    "--use-ssl/--no-ssl",
    default=None,
    help="Use SSL connection (default: true or ES_USE_SSL env var)",
)
@click.option(
    "--user",
    type=str,
    default=None,
    help="Database username (default: ES_USER env var)",
)
@click.option(
    "--password",
    type=str,
    default=None,
    help="Database password (default: ES_PASS env var)",
)
@click.option(
    "--yes",
    is_flag=True,
    help="Skip confirmation prompt",
)
def reindex(backend, host, port, use_ssl, user, password, yes):
    """Reindex all STAC indexes to the next version and update aliases.

    For Elasticsearch, this runs a migration that:
    - Creates/updates index templates
    - Reindexes collections and item indexes to a new version
    - Applies asset migration script for compatibility
    - Switches aliases to the new indexes
    """
    import os

    backend = backend.lower()

    if not yes:
        proceed = click.confirm(
            "This will reindex all collections and item indexes and update aliases. Proceed?",
            default=False,
        )
        if not proceed:
            click.echo(click.style("Aborted", fg="yellow"))
            return

    # Set environment variables from CLI options if provided
    if host:
        os.environ["ES_HOST"] = host
    if port:
        os.environ["ES_PORT"] = str(port)
    if use_ssl is not None:
        os.environ["ES_USE_SSL"] = "true" if use_ssl else "false"
    if user:
        os.environ["ES_USER"] = user
    if password:
        os.environ["ES_PASS"] = password

    try:
        asyncio.run(unified_reindex_run(backend))
        click.echo(
            click.style(
                f"✓ Reindex ({backend.title()}) completed successfully", fg="green"
            )
        )
    except KeyboardInterrupt:
        click.echo(click.style("\n✗ Reindex interrupted by user", fg="yellow"))
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        click.echo(click.style(f"✗ Reindex failed: {error_msg}", fg="red"))
        # Provide helpful hints for common errors
        if "TLS" in error_msg or "SSL" in error_msg:
            click.echo(
                click.style(
                    "\n💡 Hint: If you're connecting to a local Docker Compose instance, try adding --no-ssl flag",
                    fg="yellow",
                )
            )
        elif "Connection refused" in error_msg:
            click.echo(
                click.style(
                    "\n💡 Hint: Make sure your database is running and accessible at the specified host:port",
                    fg="yellow",
                )
            )
        sys.exit(1)


if __name__ == "__main__":
    cli()
