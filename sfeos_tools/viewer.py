"""Streamlit-based viewer for exploring STAC collections and items."""
from io import BytesIO
from typing import Any, Dict, List, Optional, Union

import httpx
import streamlit as st


class STACClient:
    """Simple STAC API client."""

    def __init__(self, base_url: str):
        """Initialize."""
        self.base_url: str = base_url.rstrip("/")  # Fixing incompatible type assignment
        self.client: httpx.Client = httpx.Client(timeout=30.0)

    def get_collections(self) -> List[Dict[str, Any]]:
        """Fetch all collections."""
        try:
            response = self.client.get(f"{self.base_url}/collections")
            response.raise_for_status()
            data = response.json()
            return data.get("collections", [])
        except Exception as e:
            st.error(f"Error fetching collections: {e}")
            return []

    def get_collection(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific collection."""
        try:
            response = self.client.get(f"{self.base_url}/collections/{collection_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error fetching collection {collection_id}: {e}")
            return None

    def search_items(
        self,
        collection_id: Optional[str] = None,
        bbox: Optional[List[float]] = None,
        limit: int = 100,
        q: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search for items using GET requests only.

        Args:
            collection_id: The collection ID to filter by
            bbox: Bounding box [minx, miny, maxx, maxy]
            limit: Maximum number of items to return
            q: Free text search query

        Returns:
            List of STAC items matching the search criteria
        """
        try:
            # Initialize params
            params: Dict[str, Union[int, str]] = {"limit": limit}

            # Add collection to params if specified
            if collection_id:
                params["collections"] = str(collection_id)

            # Add bbox to params if specified
            if bbox:
                params["bbox"] = ",".join(map(str, bbox))

            # Add q to params if specified
            if q and q.strip():
                params["q"] = q.strip()

            # Make GET request
            response = self.client.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("features", [])
        except Exception as e:
            st.error(f"Error searching items: {e}")
            return []

    def get_item(self, collection_id: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific item."""
        try:
            response = self.client.get(
                f"{self.base_url}/collections/{collection_id}/items/{item_id}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error fetching item {item_id}: {e}")
            return None


def get_asset_urls(item: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """Extract asset URLs from a STAC item."""
    assets: Dict[str, Dict[str, str]] = {}
    if not item.get("assets"):
        return assets

    for asset_key, asset_data in item["assets"].items():
        if isinstance(asset_data, dict) and "href" in asset_data:
            asset_type = asset_data.get("type", "")
            roles = asset_data.get("roles", [])

            assets[asset_key] = {
                "href": asset_data["href"],
                "type": asset_type,
                "roles": roles,
                "title": asset_data.get("title", asset_key),
            }

    return assets


def get_thumbnail_url(item: Dict[str, Any]) -> Optional[str]:
    """Get thumbnail URL from STAC item assets."""
    assets = get_asset_urls(item)

    # Priority order for thumbnails
    thumbnail_keys = ["thumbnail", "preview", "overview"]

    for key in thumbnail_keys:
        if key in assets:
            return assets[key]["href"]

    # Look for assets with 'thumbnail' or 'overview' role
    for asset_key, asset_data in assets.items():
        if "thumbnail" in asset_data.get("roles", []) or "overview" in asset_data.get(
            "roles", []
        ):
            return asset_data["href"]

    # Fallback to any image asset
    for asset_key, asset_data in assets.items():
        asset_type = asset_data.get("type", "").lower()
        if any(
            img_type in asset_type
            for img_type in ["image/jpeg", "image/png", "image/jpg"]
        ):
            return asset_data["href"]

    return None


def load_image_from_url(url: str) -> Optional[Any]:
    """Load an image from a URL."""
    try:
        from PIL import Image

        response = httpx.get(url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return None


def create_map(items: List[Dict[str, Any]]) -> Any:
    """Create a folium map with items."""
    import folium
    from folium.plugins import Fullscreen

    # Calculate center from items or use default
    if items:
        lats, lons = [], []
        for item in items:
            if item.get("geometry") and item["geometry"].get("coordinates"):
                coords = item["geometry"]["coordinates"]
                if item["geometry"]["type"] == "Point":
                    lons.append(coords[0])
                    lats.append(coords[1])
                elif item["geometry"]["type"] == "Polygon":
                    for ring in coords:
                        for coord in ring:
                            lons.append(coord[0])
                            lats.append(coord[1])

        if lats and lons:
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
        else:
            center_lat, center_lon = 0, 0
    else:
        center_lat, center_lon = 0, 0

    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=2 if not items else 6,
        tiles="OpenStreetMap",
    )

    # Add fullscreen button
    Fullscreen(
        position="topright",
        title="Fullscreen",
        title_cancel="Exit Fullscreen",
        force_separate_button=True,
    ).add_to(m)

    # Add items to map
    for item in items:
        if not item.get("geometry"):
            continue

        geom = item["geometry"]
        item_id = item.get("id", "Unknown")
        collection = item.get("collection", "Unknown")

        # Create popup content
        popup_html = f"""
<div style="width: 200px;">
<b>ID:</b> {item_id}<br>
<b>Collection:</b> {collection}<br>
</div>
"""

        if geom["type"] == "Point":
            coords = geom["coordinates"]
            folium.Marker(
                location=[coords[1], coords[0]],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=item_id,
            ).add_to(m)

        elif geom["type"] == "Polygon":
            coords = geom["coordinates"]
            # Convert to lat/lon format for folium
            polygon_coords = [
                [[coord[1], coord[0]] for coord in ring] for ring in coords
            ]
            folium.Polygon(
                locations=polygon_coords[0],  # Outer ring
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=item_id,
                color="blue",
                fill=True,
                fillOpacity=0.2,
            ).add_to(m)

    return m


def run_viewer(base_url: str):
    """Streamlit app."""
    st.set_page_config(page_title="SFEOS Viewer", page_icon="🗺️", layout="wide")

    st.title("🗺️ SFEOS STAC Viewer")
    st.markdown(f"**Connected to:** `{base_url}`")
    st.markdown("---")

    # Initialize client
    client = STACClient(base_url)

    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")

        # Fetch collections
        collections = client.get_collections()

        if not collections:
            st.warning("No collections found or unable to connect to STAC API")
            st.stop()

        collection_names = ["All Collections"] + [
            c.get("id", "Unknown") for c in collections
        ]
        selected_collection = st.selectbox("Select Collection", collection_names)

        # Item limit
        item_limit = st.slider("Max Items to Display", 10, 500, 100)

        # Free text search
        search_query = st.text_input("Search (keywords, properties, etc.)")

        # Search button
        search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)

    # Main content area - 3 column layout
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.subheader("Map View")

        # Search items
        if search_clicked or "items" not in st.session_state:
            with st.spinner("Searching items..."):
                collection_id = (
                    None
                    if selected_collection == "All Collections"
                    else selected_collection
                )
                items = client.search_items(
                    collection_id=collection_id,
                    limit=item_limit,
                    q=search_query if search_query.strip() else None,
                )
                st.session_state.items = items

                if search_query.strip() and not items:
                    st.info("No items found matching your search query.")

        items = st.session_state.get("items", [])

        if items:
            st.info(f"Displaying {len(items)} items")
            map_obj = create_map(items)

            # Display map
            from streamlit_folium import st_folium

            st_folium(map_obj, width=None, height=800, returned_objects=[])
        else:
            st.warning("No items found. Try adjusting your search parameters.")

    with col2:
        st.subheader("Collection Info")

        if selected_collection != "All Collections":
            collection = client.get_collection(selected_collection)
            if collection:
                st.markdown(f"**ID:** `{collection.get('id')}`")
                st.markdown(f"**Title:** {collection.get('title', 'N/A')}")
                st.markdown(f"**Description:** {collection.get('description', 'N/A')}")

                # License
                if collection.get("license"):
                    st.markdown(f"**License:** {collection['license']}")

                # Extent
                if collection.get("extent"):
                    extent = collection["extent"]
                    if extent.get("spatial"):
                        bbox = extent["spatial"].get("bbox", [[]])[0]
                        if bbox:
                            st.markdown("**Spatial Extent:**")
                            st.code(f"[{', '.join(map(str, bbox))}]")

        # Item details
        st.subheader("Items")
        items = st.session_state.get("items", [])

        if items:
            # Item selector
            item_ids = [
                item.get("id", f"Item {i}") for i, item in enumerate(items[:50])
            ]
            selected_item_id = st.selectbox(
                "Select item to view details", item_ids, key="item_selector"
            )

            # Find selected item
            selected_item = None
            for item in items:
                if item.get("id") == selected_item_id:
                    selected_item = item
                    break

            if selected_item:
                st.session_state.selected_item = selected_item

            # Create a simple table view
            item_data = []
            for item in items[:20]:  # Show first 20
                item_data.append(
                    {
                        "ID": item.get("id", "N/A"),
                        "Collection": item.get("collection", "N/A"),
                        "Type": item.get("geometry", {}).get("type", "N/A"),
                    }
                )

            st.dataframe(item_data, width="stretch", height=300)

            if len(items) > 20:
                st.caption(f"Showing 20 of {len(items)} items")
        else:
            st.info("No items to display")

    with col3:
        st.subheader("Asset Preview")

        selected_item = st.session_state.get("selected_item")

        if selected_item:
            # Display item metadata
            st.markdown(f"**Item ID:** `{selected_item.get('id', 'N/A')}`")

            # Get assets
            assets = get_asset_urls(selected_item)

            if assets:
                st.markdown(f"**Assets:** {len(assets)}")

                # Asset selector
                asset_keys = list(assets.keys())
                selected_asset_key = st.selectbox(
                    "Select asset",
                    asset_keys,
                    format_func=lambda x: assets[x]["title"],
                    key="asset_selector",
                )

                if selected_asset_key:
                    asset = assets[selected_asset_key]
                    st.markdown(f"**Type:** {asset['type']}")
                    st.markdown(
                        f"**Roles:** {', '.join(asset['roles']) if asset['roles'] else 'N/A'}"
                    )

                    # Display image if it's an image asset
                    asset_type = asset["type"].lower()
                    if any(
                        img_type in asset_type
                        for img_type in ["image/", "jpeg", "png", "jpg", "tif"]
                    ):
                        with st.spinner("Loading image..."):
                            img = load_image_from_url(asset["href"])
                            if img:
                                st.image(img, caption=asset["title"], width="stretch")
                            else:
                                st.warning("Could not load image")
                                st.markdown(f"[View Image]({asset['href']})")
                    else:
                        st.info(f"Non-image asset: {asset['type']}")
                        st.markdown(f"[Download Asset]({asset['href']})")
            else:
                st.info("No assets available for this item")

            # Display thumbnail if available
            thumbnail_url = get_thumbnail_url(selected_item)
            if thumbnail_url and not assets:
                with st.spinner("Loading thumbnail..."):
                    img = load_image_from_url(thumbnail_url)
                    if img:
                        st.image(img, caption="Thumbnail", width="stretch")
        else:
            st.info("Select an item to view assets")


# Entry point when run directly by Streamlit
if __name__ == "__main__":
    import os

    base_url = os.environ.get("SFEOS_STAC_URL", "http://localhost:8080")
    run_viewer(base_url)
