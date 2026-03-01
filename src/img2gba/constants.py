"""
Constants for Butano image conversion.

This module defines all the constant values used throughout the img2gba tool.
Centralizing constants here makes them easy to find and modify.

GBA Hardware Background:
------------------------
The Game Boy Advance has specific limitations on sprite and background sizes.
These aren't arbitrary - they're dictated by the hardware's Object Attribute
Memory (OAM) and background map structures.

Sprites use a "shape + size" system:
- Shape can be: Square, Wide (horizontal), or Tall (vertical)
- Size can be: 0, 1, 2, or 3 (meaning different pixel dimensions per shape)

Backgrounds can be either:
- Regular: Tile-based, scrollable, up to 4 layers
- Affine: Can rotate/scale, but limited to 2 layers and 256 tiles
"""

# =============================================================================
# SPRITE SIZES
# =============================================================================

# Valid sprite sizes for GBA hardware.
# These are ALL the valid combinations - no other sizes are allowed.
#
# The GBA stores sprite size as two 2-bit values:
#   - Shape (2 bits): 0=Square, 1=Wide, 2=Tall
#   - Size (2 bits): 0-3, meaning varies by shape
#
# This table shows what each combination means in pixels:
#
#   Shape    | Size 0  | Size 1  | Size 2  | Size 3
#   ---------|---------|---------|---------|--------
#   Square   |   8x8   |  16x16  |  32x32  |  64x64
#   Wide     |  16x8   |  32x8   |  32x16  |  64x32
#   Tall     |  8x16   |  8x32   |  16x32  |  32x64
#
# Format: (width, height) in pixels
VALID_SPRITE_SIZES: list[tuple[int, int]] = [
    # Square sprites (shape = 0)
    (8, 8),      # Size 0: Tiny, good for particles, bullets
    (16, 16),    # Size 1: Small characters, items, icons
    (32, 32),    # Size 2: Medium characters, common choice
    (64, 64),    # Size 3: Large characters, bosses

    # Wide/Horizontal sprites (shape = 1)
    (16, 8),     # Size 0: Small horizontal bar
    (32, 8),     # Size 1: Health bar, platform
    (32, 16),    # Size 2: Horizontal enemy, vehicle
    (64, 32),    # Size 3: Large horizontal sprite

    # Tall/Vertical sprites (shape = 2)
    (8, 16),     # Size 0: Small vertical bar
    (8, 32),     # Size 1: Tall thin sprite
    (16, 32),    # Size 2: Standing character
    (32, 64),    # Size 3: Large vertical sprite
]

# =============================================================================
# BACKGROUND SIZES
# =============================================================================

# Valid regular background sizes.
# Regular backgrounds are tile-based and scrollable.
# They can have up to 1024 unique tiles.
#
# "Small" backgrounds (listed here) are faster because they use
# simpler memory mapping. Larger backgrounds use "big" mode which
# requires more CPU cycles to manage.
#
# For sizes larger than these, Butano uses "big background" mode
# which can be any multiple of 256 pixels, but is slower.
VALID_REGULAR_BG_SIZES: list[tuple[int, int]] = [
    (256, 256),   # 1 screen (GBA screen is 240x160)
    (256, 512),   # 2 screens tall
    (512, 256),   # 2 screens wide
    (512, 512),   # 4 screens (2x2)
]

# Valid affine background sizes.
# Affine backgrounds can be rotated, scaled, and skewed.
# They're limited to 256 unique tiles and only 2 can be shown at once.
#
# The sizes must be powers of 2 for the hardware transformation math.
VALID_AFFINE_BG_SIZES: list[tuple[int, int]] = [
    (128, 128),    # Half screen
    (256, 256),    # 1 screen
    (512, 512),    # 4 screens
    (1024, 1024),  # 16 screens (max without "big" mode)
]

# =============================================================================
# ASSET TYPES
# =============================================================================

# String identifiers for asset types.
# These match what Butano expects in the JSON metadata files.
ASSET_TYPE_SPRITE = "sprite"
ASSET_TYPE_REGULAR_BG = "regular_bg"
ASSET_TYPE_AFFINE_BG = "affine_bg"

# List of all valid asset types (used for CLI validation)
VALID_ASSET_TYPES: list[str] = [
    ASSET_TYPE_SPRITE,
    ASSET_TYPE_REGULAR_BG,
    ASSET_TYPE_AFFINE_BG,
]

# =============================================================================
# COLOR MODES
# =============================================================================

# Number of colors in each mode.
#
# 4bpp (4 bits per pixel) = 16 colors
#   - Each pixel uses 4 bits, so 2 pixels fit in 1 byte
#   - Sprites can have multiple 16-color palettes
#   - Good for simple graphics, saves memory
#
# 8bpp (8 bits per pixel) = 256 colors
#   - Each pixel uses 8 bits (1 byte)
#   - Single palette shared by all 8bpp sprites
#   - Good for detailed graphics, photos
COLORS_16 = 16    # 4bpp mode
COLORS_256 = 256  # 8bpp mode

# =============================================================================
# COMPRESSION TYPES
# =============================================================================

# Compression options supported by Butano/grit.
# These can be specified in the JSON file to reduce ROM size.
#
# Note: The compression happens during Butano's build process, not in this tool.
# We just set the flag in the JSON file to tell grit what compression to use.
COMPRESSION_NONE = "none"           # No compression (default, fastest loading)
COMPRESSION_LZ77 = "lz77"           # LZ77 compression (good balance)
COMPRESSION_RUN_LENGTH = "run_length"  # Run-length encoding (good for simple images)
COMPRESSION_HUFFMAN = "huffman"     # Huffman coding (best for varied data)
COMPRESSION_AUTO = "auto"           # Let grit choose the best method

# List of valid compression types (used for CLI validation)
VALID_COMPRESSION_TYPES: list[str] = [
    COMPRESSION_NONE,
    COMPRESSION_LZ77,
    COMPRESSION_RUN_LENGTH,
    COMPRESSION_HUFFMAN,
    COMPRESSION_AUTO,
]

# =============================================================================
# ADDITIONAL ASSET TYPES (for separate tiles/palette generation)
# =============================================================================

# These types generate only part of the asset, useful for palette sharing
ASSET_TYPE_SPRITE_TILES = "sprite_tiles"
ASSET_TYPE_SPRITE_PALETTE = "sprite_palette"
ASSET_TYPE_REGULAR_BG_TILES = "regular_bg_tiles"
ASSET_TYPE_BG_PALETTE = "bg_palette"

# Extended list including separate tile/palette types
VALID_ASSET_TYPES_EXTENDED: list[str] = [
    ASSET_TYPE_SPRITE,
    ASSET_TYPE_SPRITE_TILES,
    ASSET_TYPE_SPRITE_PALETTE,
    ASSET_TYPE_REGULAR_BG,
    ASSET_TYPE_REGULAR_BG_TILES,
    ASSET_TYPE_BG_PALETTE,
    ASSET_TYPE_AFFINE_BG,
]

# =============================================================================
# TRANSPARENCY
# =============================================================================

# Default transparency color candidates.
# When we need to pick a color to represent transparency, we try these
# in order. We use the first one that isn't already in the image.
#
# Magenta (255, 0, 255) is the traditional choice because:
#   1. It's ugly and rarely used in actual art
#   2. It's visually obvious if something goes wrong
#   3. It's a GBA/retro game development convention
#
# If all these colors are somehow used in the image, we'll generate
# a random color that isn't used.
DEFAULT_TRANSPARENCY_COLORS: list[tuple[int, int, int]] = [
    (255, 0, 255),  # Magenta - most common choice
    (0, 255, 255),  # Cyan
    (255, 255, 0),  # Yellow
    (0, 255, 0),    # Bright green
    (255, 0, 0),    # Red
    (0, 0, 255),    # Blue
]
