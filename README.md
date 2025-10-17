# SFEOS Tools

CLI tools for managing [stac-fastapi-elasticsearch-opensearch](https://github.com/stac-utils/stac-fastapi-elasticsearch-opensearch) deployments.

<!-- markdownlint-disable MD033 MD041 -->


<p align="left">
  <img src="https://raw.githubusercontent.com/stac-utils/stac-fastapi-elasticsearch-opensearch/refs/heads/main/assets/sfeos.png" width=1000>
</p>

<!-- **Jump to:** [Project Introduction](#project-introduction---what-is-sfeos) | [Quick Start](#quick-start) | [Table of Contents](#table-of-contents) -->

  [![Downloads](https://static.pepy.tech/badge/sfeos-tools?color=blue)](https://pepy.tech/project/sfeos-tools)
  [![GitHub contributors](https://img.shields.io/github/contributors/healy-hyperspatial/sfeos-tools?color=blue)](https://github.com/healy-hyperspatial/sfeos-tools/graphs/contributors)
  [![GitHub stars](https://img.shields.io/github/stars/healy-hyperspatial/sfeos-tools.svg?color=blue)](https://github.com/healy-hyperspatial/sfeos-tools/stargazers)
  [![GitHub forks](https://img.shields.io/github/forks/healy-hyperspatial/sfeos-tools.svg?color=blue)](https://github.com/healy-hyperspatial/sfeos-tools/network/members)
   [![PyPI version](https://img.shields.io/pypi/v/sfeos-tools.svg?color=blue)](https://pypi.org/project/sfeos-tools/)
  [![STAC](https://img.shields.io/badge/STAC-1.1.0-blue.svg)](https://github.com/radiantearth/stac-spec/tree/v1.1.0)

## Table of Contents

- [Installation](#installation)
  - [For Elasticsearch](#for-elasticsearch)
  - [For OpenSearch](#for-opensearch)
  - [For Development](#for-development-both-backends)
- [Usage](#usage)
- [Commands](#commands)
  - [add-bbox-shape](#add-bbox-shape)
  - [reindex](#reindex)
- [Development](#development)
- [License](#license)

## Installation

### For Elasticsearch

```bash
pip install sfeos-tools[elasticsearch]
```

Or for local development:
```bash
pip install -e sfeos_tools[elasticsearch]
```

### For OpenSearch

```bash
pip install sfeos-tools[opensearch]
```

Or for local development:
```bash
pip install -e sfeos_tools[opensearch]
```

### For Development (both backends)

```bash
pip install sfeos-tools[dev]
```

Or for local development:
```bash
pip install -e sfeos_tools[dev]
```

## Usage

After installation, the `sfeos-tools` command will be available:

```bash
# View available commands
sfeos-tools --help

# View version
sfeos-tools --version
```

## Commands

### add-bbox-shape

Adds a `bbox_shape` field to existing collections for spatial search support. This migration is required for collections created before spatial search was added. Collections created or updated after this feature will automatically have the `bbox_shape` field.

```bash
sfeos-tools add-bbox-shape --backend [elasticsearch|opensearch] [options]
```

Options:
- `--backend`: Database backend to use (required, choices: elasticsearch, opensearch)
- `--host`: Database host (default: localhost or ES_HOST env var)
- `--port`: Database port (default: 9200 for ES, 9202 for OS, or ES_PORT env var)
- `--use-ssl/--no-ssl`: Use SSL connection (default: true or ES_USE_SSL env var)
- `--user`: Database username (default: ES_USER env var)
- `--password`: Database password (default: ES_PASS env var)

### reindex

Reindexes all STAC indexes to the next version and updates aliases. This command performs the following actions:
- Creates/updates index templates
- Reindexes collections and item indexes to a new version
- Applies asset migration script for compatibility
- Switches aliases to the new indexes

```bash
sfeos-tools reindex --backend [elasticsearch|opensearch] [options]
```

Options:
- `--backend`: Database backend to use (required, choices: elasticsearch, opensearch)
- `--host`: Database host (default: localhost or ES_HOST env var)
- `--port`: Database port (default: 9200 for ES, 9202 for OS, or ES_PORT env var)
- `--use-ssl/--no-ssl`: Use SSL connection (default: true or ES_USE_SSL env var)
- `--user`: Database username (default: ES_USER env var)
- `--password`: Database password (default: ES_PASS env var)
- `--yes`: Skip confirmation prompt

Example:
```bash
# Reindex Elasticsearch with custom host and no SSL
sfeos-tools reindex --backend elasticsearch --host localhost --port 9200 --no-ssl

# Reindex OpenSearch with default settings
sfeos-tools reindex --backend opensearch
```

# Get help for a specific command
sfeos-tools add-bbox-shape --help
```

## Commands

### add-bbox-shape

Add `bbox_shape` field to existing collections for spatial search support.

**Basic usage:**

```bash
# Elasticsearch
sfeos-tools add-bbox-shape --backend elasticsearch

# OpenSearch
sfeos-tools add-bbox-shape --backend opensearch
```

**Connection options:**

```bash
# Local Docker Compose (no SSL)
sfeos-tools add-bbox-shape --backend elasticsearch --no-ssl

# Remote server with SSL
sfeos-tools add-bbox-shape \
  --backend elasticsearch \
  --host db.example.com \
  --port 9200 \
  --user admin \
  --password secret

# Using environment variables
ES_HOST=my-cluster.cloud.com ES_PORT=9243 ES_USER=elastic ES_PASS=changeme \
  sfeos-tools add-bbox-shape --backend elasticsearch
```

**Available options:**

- `--backend`: Database backend (elasticsearch or opensearch) - **required**
- `--host`: Database host (default: localhost or ES_HOST env var)
- `--port`: Database port (default: 9200 or ES_PORT env var)
- `--use-ssl / --no-ssl`: Use SSL connection (default: true or ES_USE_SSL env var)
- `--user`: Database username (default: ES_USER env var)
- `--password`: Database password (default: ES_PASS env var)

## Development

To develop sfeos-tools locally:

```bash
# Install in editable mode with dev dependencies
pip install -e ./sfeos_tools[dev]

# Run the CLI
sfeos-tools --help

# Run tests
pytest

# Format code
pre-commit install
pre-commit run --all-files
```

