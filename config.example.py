import os

# Default output directories
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
TEMP_DIR = os.path.join(OUTPUT_DIR, "osaka_temp")

# Browser for authentication - SECURITY NOTE: This gives yt-dlp access to your
# browser's login cookies. Only enable this if you trust yt-dlp and need to download
# from platforms requiring authentication. Set to None to disable authentication.
# Alternative: Use direct URLs or platforms that don't require login.
BROWSER = None  # Set to "firefox", "chrome", "edge", etc. only if needed 

# Minimum crop dimensions
MIN_CROP_WIDTH = 20
MIN_CROP_HEIGHT = 20

# Snap-to-edge tolerance for crop box (pixels)
SNAP_TOLERANCE = 2
