from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "outputs"

YEARS = list(range(2013, 2025))

# Jharkhand bounding box: west, south, east, north (degrees)
BBOX = (83.3, 21.9, 87.9, 25.4)

# Tile h26v06 covers lon 80-90, lat 20-30 with 2400 x 2400 pixels
TILE_BOUNDS = (80.0, 20.0, 90.0, 30.0)
TILE_SIZE = 2400

# Internal HDF5 paths. CHECK THESE against the output of inspect_h5.py
# and edit if the printed names are different.
RADIANCE_LAYER = (
    "HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields/"
    "AllAngle_Composite_Snow_Free"
)
QUALITY_LAYER = (
    "HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields/"
    "AllAngle_Composite_Snow_Free_Quality"
)
# Quality values to DROP (255 = fill; 2 = poor quality as far as I recall,
# confirm in Table 9 of the Black Marble user guide).
DROP_QUALITY_VALUES = (2, 255)
RADIANCE_FILL_MAX = -900.0   # radiance fill value is -999.9

# Baseline change rules (tune these once you see real maps)
MIN_LAST_RADIANCE = 5.0    # new/brighter place must be at least this bright
MIN_DIFF = 5.0             # last mean minus first mean
MIN_SLOPE = 0.5            # radiance gain per year

# "Emergence": places that were dark and became clearly lit
EMERGE_FIRST_MAX = 1.0
EMERGE_LAST_MIN = 3.0
EMERGE_SLOPE_MIN = 0.2

# Sites
MIN_SITE_PIXELS = 3          # ignore specks smaller than this
N_LABEL_SITES = 50           # top sites exported for hand-labelling
N_NEGATIVE_SAMPLES = 25      # random unflagged places exported as negatives
