"""
generate_topo_maps.py

Generates topographic base map + steepness overlay PNGs at 3 zoom levels,
centered on the same area as a cropped DTM GeoTIFF. All 3 levels cover the
SAME real-world extent (so panning never loses area as you zoom in) -- each
level just requests a higher pixel resolution for that same area, doubling
each step. Because the bounding box is derived directly from the tif's own
geotransform, the resulting map images line up with the Unity terrain built
from that same tif.

Requires:
    - GDAL Python bindings (osgeo) - comes with OSGeo4W
    - requests
    - Pillow

Run with the OSGeo4W Python (the one that already has `osgeo` available):
    C:\\OSGeo4W\\apps\\Python312\\python.exe generate_topo_maps.py

If requests/Pillow aren't installed yet:
    C:\\OSGeo4W\\apps\\Python312\\python.exe -m pip install requests pillow
"""

import argparse
import io
import json
import os

import requests
from osgeo import gdal, osr
from PIL import Image

# ---------------------------------------------------------------------------
# CONFIG - edit these for your setup
# ---------------------------------------------------------------------------

# All zoom levels share the SAME real-world extent (so panning never "loses"
# area as you zoom in) -- what changes is the pixel resolution requested for
# that same extent, which is what actually reveals more detail.
#
# BASE_SCALE sets that shared extent (fills the whole map window at the
# least-zoomed level, level 1). Each subsequent level doubles pixel_size,
# halving the effective ground resolution (2x the detail) for the same area.
#
# NOTE: Kartverket/NVE servers may cap the max image width/height they'll
# return (often 4096px). If the 8192px request below fails, try lowering
# that level's pixel_size to 4096.
BASE_SCALE = 19905

LEVELS = [
    {"label": "01_zoom", "pixel_size": 1024},
    {"label": "02_zoom", "pixel_size": 2048},
    {"label": "03_zoom", "pixel_size": 4096},
]

EXPECTED_EPSG = 25833

# Kartverket topo WMS (base map)
KARTVERKET_WMS_URL = "https://wms.geonorge.no/skwms1/wms.topo"
KARTVERKET_LAYER = "topo"

# NVE steepness (Bratthet med utlop) - ArcGIS MapServer export endpoint
NVE_EXPORT_URL = "https://gis3.nve.no/arcgis/rest/services/wmts/Bratthet_med_utlop_2024/MapServer/export"
NVE_LAYER_ID = 0  # "Bratthet med utlop Norge"

# Standard OGC pixel size used to relate map scale <-> ground resolution.
# (0.28 mm per pixel - this is the same constant Kartverket/Norgeskart use
# internally, so using it here keeps our zoom levels feeling identical to
# Norgeskart's.)
STANDARD_PIXEL_SIZE_M = 0.00028


# ---------------------------------------------------------------------------
# Step 1: read the tif's center point
# ---------------------------------------------------------------------------

def get_tif_center(tif_path):
    ds = gdal.Open(tif_path)
    if ds is None:
        raise RuntimeError(f"Could not open tif: {tif_path}")

    # Sanity-check the projection so a mismatched CRS fails loudly instead
    # of silently producing a misaligned map.
    srs = osr.SpatialReference(wkt=ds.GetProjection())
    epsg = srs.GetAuthorityCode(None)
    if epsg is None or int(epsg) != EXPECTED_EPSG:
        print(f"WARNING: tif CRS is EPSG:{epsg}, expected EPSG:{EXPECTED_EPSG}. "
              f"Bounding boxes below will be wrong unless you reproject the tif first.")

    gt = ds.GetGeoTransform()
    width_px = ds.RasterXSize
    height_px = ds.RasterYSize

    xmin = gt[0]
    ymax = gt[3]
    xmax = xmin + width_px * gt[1]
    ymin = ymax + height_px * gt[5]  # gt[5] is negative

    center_x = (xmin + xmax) / 2
    center_y = (ymin + ymax) / 2

    print(f"Tif extent: ({xmin:.1f}, {ymin:.1f}) to ({xmax:.1f}, {ymax:.1f})")
    print(f"Tif center: ({center_x:.1f}, {center_y:.1f})")

    return center_x, center_y


# ---------------------------------------------------------------------------
# Step 2: compute a bounding box for a given scale, centered on the tif center
# ---------------------------------------------------------------------------

def compute_bbox(center_x, center_y, scale, output_size_px):
    resolution_m_per_px = scale * STANDARD_PIXEL_SIZE_M
    extent_m = resolution_m_per_px * output_size_px
    half = extent_m / 2

    return (
        center_x - half,  # xmin
        center_y - half,  # ymin
        center_x + half,  # xmax
        center_y + half,  # ymax
    )


# ---------------------------------------------------------------------------
# Step 3: fetch imagery
# ---------------------------------------------------------------------------

def fetch_kartverket_topo(bbox, size_px):
    xmin, ymin, xmax, ymax = bbox
    params = {
        "service": "WMS",
        "request": "GetMap",
        "version": "1.3.0",
        "layers": KARTVERKET_LAYER,
        "styles": "",
        "crs": f"EPSG:{EXPECTED_EPSG}",
        "bbox": f"{xmin},{ymin},{xmax},{ymax}",
        "width": size_px,
        "height": size_px,
        "format": "image/png",
        "bgcolor": "0xFFFFFF",
    }
    resp = requests.get(KARTVERKET_WMS_URL, params=params, timeout=60)
    resp.raise_for_status()
    return Image.open(io.BytesIO(resp.content))


def fetch_nve_steepness(bbox, size_px):
    xmin, ymin, xmax, ymax = bbox
    params = {
        "bbox": f"{xmin},{ymin},{xmax},{ymax}",
        "bboxSR": EXPECTED_EPSG,
        "imageSR": EXPECTED_EPSG,
        "size": f"{size_px},{size_px}",
        "format": "png32",       # supports transparency
        "transparent": "true",
        "layers": f"show:{NVE_LAYER_ID}",
        "f": "image",
    }
    resp = requests.get(NVE_EXPORT_URL, params=params, timeout=60)
    resp.raise_for_status()
    return Image.open(io.BytesIO(resp.content))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate topo + steepness map PNGs centered on a cropped DTM tif."
    )
    parser.add_argument("tif_path", help="Path to the cropped DTM GeoTIFF")
    parser.add_argument(
        "-o", "--output-dir",
        default=None,
        help="Output folder for the PNGs (default: a 'maps' folder next to the tif)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    tif_path = args.tif_path
    output_dir = args.output_dir or os.path.join(os.path.dirname(tif_path), "maps")

    os.makedirs(output_dir, exist_ok=True)

    center_x, center_y = get_tif_center(tif_path) 

    # One shared bbox for every level -- see LEVELS comment above.
    bbox = compute_bbox(center_x, center_y, BASE_SCALE, LEVELS[0]["pixel_size"])
    print(f"Shared bounding box (all levels): {bbox}")

    metadata = {
        "crs": f"EPSG:{EXPECTED_EPSG}",
        "center": {"x": center_x, "y": center_y},
        "base_scale": BASE_SCALE,
        "levels": [],
    }

    for level in LEVELS:
        label = level["label"]
        size_px = level["pixel_size"]
        resolution_m_per_px = (bbox[2] - bbox[0]) / size_px
        print(f"\n--- {label} ({size_px}x{size_px}px, {resolution_m_per_px:.2f} m/px) ---")

        print("Fetching base map...")
        base_img = fetch_kartverket_topo(bbox, size_px)
        base_path = os.path.join(output_dir, f"{label}_base.png")
        base_img.save(base_path)
        print(f"Saved {base_path}")

        print("Fetching steepness overlay...")
        overlay_img = fetch_nve_steepness(bbox, size_px)
        overlay_path = os.path.join(output_dir, f"{label}_steepness.png")
        overlay_img.save(overlay_path)
        print(f"Saved {overlay_path}")

        metadata["levels"].append({
            "label": label,
            "pixel_size": size_px,
            "resolution_m_per_px": resolution_m_per_px,
            "bbox": {
                "xmin": bbox[0], "ymin": bbox[1],
                "xmax": bbox[2], "ymax": bbox[3],
            },
        })

    meta_path = os.path.join(output_dir, "map_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nSaved metadata (bbox per level, for Unity world-space <-> map "
          f"pixel conversion later) to {meta_path}")


if __name__ == "__main__":
    main()
