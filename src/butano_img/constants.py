"""Constants for Butano image conversion."""

# Valid sprite sizes for GBA hardware
# Format: (width, height)
VALID_SPRITE_SIZES = [
    # Square
    (8, 8),
    (16, 16),
    (32, 32),
    (64, 64),
    # Wide
    (16, 8),
    (32, 8),
    (32, 16),
    (64, 32),
    # Tall
    (8, 16),
    (8, 32),
    (16, 32),
    (32, 64),
]

# Valid regular background sizes (tile-based, scrollable)
# Small sizes are faster
VALID_REGULAR_BG_SIZES = [
    (256, 256),
    (256, 512),
    (512, 256),
    (512, 512),
]

# Valid affine background sizes (can rotate/scale)
# Small sizes are faster, max 256 tiles
VALID_AFFINE_BG_SIZES = [
    (128, 128),
    (256, 256),
    (512, 512),
    (1024, 1024),
]

# Asset types
ASSET_TYPE_SPRITE = "sprite"
ASSET_TYPE_REGULAR_BG = "regular_bg"
ASSET_TYPE_AFFINE_BG = "affine_bg"

VALID_ASSET_TYPES = [ASSET_TYPE_SPRITE, ASSET_TYPE_REGULAR_BG, ASSET_TYPE_AFFINE_BG]

# Color modes
COLORS_16 = 16  # 4bpp
COLORS_256 = 256  # 8bpp

# Default transparency color candidates (in order of preference)
DEFAULT_TRANSPARENCY_COLORS = [
    (255, 0, 255),  # Magenta (most common)
    (0, 255, 255),  # Cyan
    (255, 255, 0),  # Yellow
    (0, 255, 0),    # Green
    (255, 0, 0),    # Red
    (0, 0, 255),    # Blue
]
