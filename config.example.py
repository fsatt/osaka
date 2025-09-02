import os

# Default output directories
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
TEMP_DIR = os.path.join(OUTPUT_DIR, "osaka_temp")

# Minimum crop dimensions
MIN_CROP_WIDTH = 20
MIN_CROP_HEIGHT = 20

# Snap-to-edge tolerance for crop box (pixels)
SNAP_TOLERANCE = 2
