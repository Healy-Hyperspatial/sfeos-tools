# SFEOS Tools Change Log

All notable changes to this project will be documented in this file.

The format is (loosely) based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Added

- Added `viewer` command to launch interactive Streamlit-based web viewer for exploring STAC collections and items
- New `viewer.py` module with STACClient for STAC API interaction and map visualization using Folium
- New optional dependency group `[viewer]` for Streamlit, Folium, streamlit-folium, and Pillow packages
- Asset preview and imagery display in viewer:
  - Display thumbnails and full images from STAC item assets
  - Support for JPEG, PNG, TIFF, and other image formats
  - Asset selector to browse all available assets
  - Automatic thumbnail detection from asset roles
  - Three-column layout with map, metadata, and asset preview

## [v0.2.0] - 2025-10-21

### Added

- Added `load-data` command to load STAC items into the database via the SFEOS STAC API [#2](https://github.com/healy-hyperspatial/sfeos-tools/pull/2)

## [v0.1.1] - 2025-10-21

### Changed

- Moved `add_bbox_shape` logic from `cli.py` to new `bbox_shape.py` module for better code organization [#1](https://github.com/healy-hyperspatial/sfeos-tools/pull/1)

### Added

- Comprehensive test suite for `bbox_shape` module with 9 test cases covering both Elasticsearch and OpenSearch backends [#1](https://github.com/healy-hyperspatial/sfeos-tools/pull/1)

### Removed

- Python 3.8 support [#1](https://github.com/healy-hyperspatial/sfeos-tools/pull/1)

## [v0.1.0] - 2025-10-15 [#1](https://github.com/healy-hyperspatial/sfeos-tools/pull/1)

### Added

- Initial release

[Unreleased]: https://github.com/healy-hyperspatial/sfeos-tools/compare/v0.1.1..main
[v0.1.1]: https://github.com/healy-hyperspatial/sfeos-tools/compare/v0.1.0...v0.1.1
[v0.1.0]: https://github.com/healy-hyperspatial/sfeos-tools/compare/v0.1.0
