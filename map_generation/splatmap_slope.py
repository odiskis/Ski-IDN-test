"""
generate_splatmap.py
--------------------
Generates a slope-based snow/rock splatmap PNG for Unity terrain texturing within OSGEO4Wshell

Usage:
    python generate_splatmap.py <input_dtm.tif> <output_folder>

Example:
    python generate_splatmap.py fanaraken_test_4097_flipped.tif output/

Outputs:
    <output_folder>/slope.tif          - Slope raster in degrees
    <output_folder>/splatmap.png       - Two-channel splatmap (R=snow, G=rock)

Snow/rock thresholds (degrees):
    < 55     -> full snow
    55 - 65  -> transition zone (snow fades, rock emerges)
    > 65     -> full rock
"""

import sys
import os
import numpy as np
from osgeo import gdal

gdal.UseExceptions() # Enable GDAL exceptions for better error handling
# -----------------------------------------------------------------------
# Thresholds (degrees) - edit these to tune the result
SNOW_FULL    = 55.0   # below this: 100% snow
ROCK_FULL    = 65.0   # above this: 100% rock
# between SNOW_FULL and ROCK_FULL: linear blend from snow to rock
# -----------------------------------------------------------------------


def compute_slope(input_path, output_path):
    """Run gdaldem slope on the input DTM, save to output_path."""
    print(f"Computing slope -> {output_path}")
    result = gdal.DEMProcessing(
        output_path,
        input_path,
        "slope",
        slopeFormat="degree",
        creationOptions=["TILED=YES", "BLOCKXSIZE=512", "BLOCKYSIZE=512"]
    )
    if result is None:
        raise RuntimeError("gdaldem slope failed — check your input file path.")
    result = None  # flush/close


def read_raster(path):
    """Read a single-band raster, return (array, nodata_value)."""
    ds = gdal.Open(path)
    if ds is None:
        raise RuntimeError(f"Could not open: {path}")
    band = ds.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    arr = band.ReadAsArray().astype(np.float32)
    ds = None
    return arr, nodata


def slope_to_weights(slope_arr, nodata):
    """
    Convert slope array (degrees) to snow/rock weights in 0-255 range.

    Returns:
        snow_channel (uint8 array)
        rock_channel (uint8 array)
    """
    # Mask nodata pixels
    if nodata is not None:
        valid = slope_arr != nodata
    else:
        valid = np.ones(slope_arr.shape, dtype=bool)

    # Snow weight: 1.0 below SNOW_FULL, linear fade to 0.0 at ROCK_FULL
    snow_weight = np.where(
        slope_arr <= SNOW_FULL,
        1.0,
        np.where(
            slope_arr >= ROCK_FULL,
            0.0,
            1.0 - (slope_arr - SNOW_FULL) / (ROCK_FULL - SNOW_FULL)
        )
    ).astype(np.float32)

    # Rock weight is simply the inverse
    rock_weight = 1.0 - snow_weight

    # Apply nodata mask — set both to 0 where data is invalid
    snow_weight[~valid] = 0.0
    rock_weight[~valid] = 0.0

    # Scale to 0-255 uint8
    snow_channel = (snow_weight * 255).clip(0, 255).astype(np.uint8)
    rock_channel = (rock_weight * 255).clip(0, 255).astype(np.uint8)

    return snow_channel, rock_channel


def save_splatmap_png(snow, rock, output_path):
    """Save snow/rock as a 2-band PNG (R=snow, G=rock, B=0)."""
    print(f"Saving splatmap -> {output_path}")

    rows, cols = snow.shape

    # PNG requires CreateCopy via a MEM driver intermediate
    mem_driver = gdal.GetDriverByName("MEM")
    mem_ds = mem_driver.Create("", cols, rows, 3, gdal.GDT_Byte)

    mem_ds.GetRasterBand(1).WriteArray(snow)
    mem_ds.GetRasterBand(2).WriteArray(rock)
    mem_ds.GetRasterBand(3).WriteArray(np.zeros_like(snow))

    png_driver = gdal.GetDriverByName("PNG")
    png_driver.CreateCopy(output_path, mem_ds)

    mem_ds = None


def main():
    if len(sys.argv) != 3:
        print("Usage: python generate_splatmap.py <input_dtm.tif> <output_folder>")
        sys.exit(1)

    input_dtm    = sys.argv[1]
    output_folder = sys.argv[2]

    # Validate input
    if not os.path.exists(input_dtm):
        print(f"ERROR: Input file not found: {input_dtm}")
        sys.exit(1)

    # Create output folder if needed
    os.makedirs(output_folder, exist_ok=True)

    slope_path    = os.path.join(output_folder, "slope.tif")
    splatmap_path = os.path.join(output_folder, "splatmap.png")

    # Step 1: compute slope
    compute_slope(input_dtm, slope_path)

    # Step 2: read slope raster
    slope_arr, nodata = read_raster(slope_path)
    print(f"Slope range: {slope_arr.min():.1f} - {slope_arr.max():.1f} degrees")

    # Step 3: convert to snow/rock weights
    snow, rock = slope_to_weights(slope_arr, nodata)
    print(f"Snow channel: min={snow.min()}, max={snow.max()}")
    print(f"Rock channel: min={rock.min()}, max={rock.max()}")

    # Step 4: save splatmap PNG
    save_splatmap_png(snow, rock, splatmap_path)

    print("\nDone!")
    print(f"  Slope raster : {slope_path}")
    print(f"  Splatmap PNG : {splatmap_path}")
    print(f"\nIn Unity:")
    print(f"  Layer 0 (Snow) driven by Red channel")
    print(f"  Layer 1 (Rock) driven by Green channel")


if __name__ == "__main__":
    main()