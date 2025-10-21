"""Bbox shape migration utilities for SFEOS collections."""

import logging

from stac_fastapi.sfeos_helpers.database import add_bbox_shape_to_collection
from stac_fastapi.sfeos_helpers.mappings import COLLECTIONS_INDEX

logger = logging.getLogger(__name__)


async def process_collection_bbox_shape(client, collection_doc, backend):
    """Process a single collection document to add bbox_shape field.

    Args:
        client: Elasticsearch/OpenSearch client
        collection_doc: Collection document from database
        backend: Backend type ('elasticsearch' or 'opensearch')

    Returns:
        bool: True if collection was updated, False if no update was needed
    """
    collection = collection_doc["_source"]
    collection_id = collection.get("id", collection_doc["_id"])

    # Use the shared function to add bbox_shape
    was_added = add_bbox_shape_to_collection(collection)

    if not was_added:
        return False

    # Update the collection in the database
    if backend == "elasticsearch":
        await client.index(
            index=COLLECTIONS_INDEX,
            id=collection_id,
            document=collection,
            refresh=True,
        )
    else:  # opensearch
        await client.index(
            index=COLLECTIONS_INDEX,
            id=collection_id,
            body=collection,
            refresh=True,
        )

    logger.info(f"Collection '{collection_id}': Added bbox_shape field")
    return True


async def run_add_bbox_shape(backend):
    """Add bbox_shape field to all existing collections.

    Args:
        backend: Backend type ('elasticsearch' or 'opensearch')
    """
    import os

    logger.info(
        f"Starting migration: Adding bbox_shape to existing collections ({backend})"
    )

    # Log connection info (showing what will be used by the client)
    es_host = os.getenv("ES_HOST", "localhost")
    es_port = os.getenv(
        "ES_PORT", "9200"
    )  # Both backends default to 9200 in their config
    es_use_ssl = os.getenv("ES_USE_SSL", "true")
    logger.info(f"Connecting to {backend} at {es_host}:{es_port} (SSL: {es_use_ssl})")

    # Create client based on backend
    if backend == "elasticsearch":
        from stac_fastapi.elasticsearch.config import AsyncElasticsearchSettings

        settings = AsyncElasticsearchSettings()
    else:  # opensearch
        from stac_fastapi.opensearch.config import AsyncOpensearchSettings

        settings = AsyncOpensearchSettings()

    client = settings.create_client

    try:
        # Get all collections
        response = await client.search(
            index=COLLECTIONS_INDEX,
            body={
                "query": {"match_all": {}},
                "size": 10000,
            },  # Adjust size if you have more collections
        )

        total_collections = response["hits"]["total"]["value"]
        logger.info(f"Found {total_collections} collections to process")

        updated_count = 0
        skipped_count = 0

        for hit in response["hits"]["hits"]:
            was_updated = await process_collection_bbox_shape(client, hit, backend)
            if was_updated:
                updated_count += 1
            else:
                skipped_count += 1

        logger.info(
            f"Migration complete: {updated_count} collections updated, {skipped_count} skipped"
        )

    except Exception as e:
        logger.error(f"Migration failed with error: {e}")
        raise
    finally:
        await client.close()
