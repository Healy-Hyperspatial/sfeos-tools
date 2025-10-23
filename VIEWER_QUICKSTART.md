# SFEOS Viewer Quick Start

The SFEOS Viewer is a Streamlit-based interactive web application for exploring STAC collections and items with map visualization.

## Installation

Install the viewer dependencies:

```bash
pip install -e .[viewer]
```

Or if you want all dev dependencies including the viewer:

```bash
pip install -e .[dev]
```

## Usage

### Basic Usage

Launch the viewer with default settings (connects to http://localhost:8080):

```bash
sfeos-tools viewer
```

### Custom STAC API

Connect to a different STAC API:

```bash
sfeos-tools viewer --stac-url https://my-stac-api.com
```

### Custom Port

Run on a different port:

```bash
sfeos-tools viewer --port 8502
```

## Features

- **Interactive Map**: Visualize STAC items on an OpenStreetMap-based map using Folium
- **Collection Browser**: Select and explore different STAC collections
- **Item Search**: Search for items with configurable limits
- **Metadata Display**: View collection and item metadata in a clean interface
- **Asset Preview**: Display imagery and other assets from STAC items
  - Automatic thumbnail detection
  - Full image viewer for JPEG, PNG, TIFF formats
  - Asset selector to browse all available assets
  - Support for COG (Cloud Optimized GeoTIFF) and other formats
- **Responsive Layout**: Three-column layout with map, metadata, and asset preview

## Architecture

### Components

1. **STACClient** (`viewer.py`): Simple HTTP client for STAC API interactions
   - `get_collections()`: Fetch all collections
   - `get_collection(id)`: Fetch a specific collection
   - `search_items()`: Search for items with optional filters
   - `get_item()`: Fetch a specific item with full details

2. **Asset Management**: Extract and display STAC assets
   - `get_asset_urls()`: Extract all asset URLs from items
   - `get_thumbnail_url()`: Smart thumbnail detection
   - `load_image_from_url()`: Load and display images using Pillow

3. **Map Visualization**: Folium-based map rendering
   - Supports Point and Polygon geometries
   - Interactive popups with item metadata
   - Auto-centering based on item locations

4. **Streamlit UI**: Clean, responsive interface
   - Sidebar controls for collection selection and search
   - Main map view
   - Collection info and item selector
   - Asset preview panel with image display

### File Structure

```
sfeos_tools/
├── viewer.py           # Main viewer module
├── cli.py              # CLI command integration
tests/
├── test_viewer.py      # Unit tests for viewer
```

## Development

### Running Tests

```bash
pytest tests/test_viewer.py -v
```

### Modifying the Viewer

The viewer is designed to be easily extensible:

- **Add new filters**: Modify the sidebar section in `run_viewer()`
- **Change map style**: Update the `folium.Map()` initialization in `create_map()`
- **Add new visualizations**: Extend the Streamlit layout in `run_viewer()`

### Testing Locally

1. Start your STAC API (e.g., SFEOS instance)
2. Load some test data using `sfeos-tools load-data`
3. Launch the viewer: `sfeos-tools viewer`
4. Open http://localhost:8501 in your browser

## Troubleshooting

### "Streamlit is not installed"

Install the viewer dependencies:
```bash
pip install -e .[viewer]
```

### "No collections found"

- Verify your STAC API is running
- Check the STAC URL is correct
- Ensure the API is accessible from your machine

### Port already in use

Use a different port:
```bash
sfeos-tools viewer --port 8502
```

## Future Enhancements

Potential improvements for the viewer:

- [ ] Advanced search filters (date range, bbox drawing)
- [x] Asset preview (thumbnails, imagery) ✅
- [ ] Export functionality (GeoJSON, CSV)
- [ ] Bookmark/save searches
- [ ] Multi-collection comparison
- [ ] Custom basemap options
- [ ] Item detail modal with full metadata
- [ ] COG band visualization and manipulation
- [ ] Image histogram and statistics
- [ ] Side-by-side asset comparison
