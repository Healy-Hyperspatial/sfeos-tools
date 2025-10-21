# SFEOS Tools Change Log

All notable changes to this project will be documented in this file.

The format is (loosely) based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

## [v0.1.1] - 2025-10-21

### Changed

- Moved `add_bbox_shape` logic from `cli.py` to new `bbox_shape.py` module for better code organization

### Added

- Comprehensive test suite for `bbox_shape` module with 9 test cases covering both Elasticsearch and OpenSearch backends
- Added `pytest-asyncio` to dev dependencies for async test support

## [v0.1.0] - 2025-10-15

### Added

- Initial release

[Unreleased]: https://github.com/healy-hyperspatial/sfeos-tools/compare/v0.1.0..main
[v0.1.0]: https://github.com/healy-hyperspatial/sfeos-tools/releases/tag/v0.1.0
