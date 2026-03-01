"""Constants for GBA image conversion."""

# Sprite sizes - all valid (width, height) combinations for GBA OAM
VALID_SPRITE_SIZES: list[tuple[int, int]] = [
    (8, 8), (16, 16), (32, 32), (64, 64),      # Square
    (16, 8), (32, 8), (32, 16), (64, 32),       # Wide
    (8, 16), (8, 32), (16, 32), (32, 64),       # Tall
]

# Background sizes
VALID_REGULAR_BG_SIZES: list[tuple[int, int]] = [
    (256, 256), (256, 512), (512, 256), (512, 512),
]

VALID_AFFINE_BG_SIZES: list[tuple[int, int]] = [
    (128, 128), (256, 256), (512, 512), (1024, 1024),
]

# Asset types (matching Butano JSON metadata format)
ASSET_TYPE_SPRITE = "sprite"
ASSET_TYPE_REGULAR_BG = "regular_bg"
ASSET_TYPE_AFFINE_BG = "affine_bg"

VALID_ASSET_TYPES: list[str] = [
    ASSET_TYPE_SPRITE,
    ASSET_TYPE_REGULAR_BG,
    ASSET_TYPE_AFFINE_BG,
]

# Color modes
COLORS_16 = 16    # 4bpp
COLORS_256 = 256  # 8bpp

# Compression types supported by Butano/grit
COMPRESSION_NONE = "none"
COMPRESSION_LZ77 = "lz77"
COMPRESSION_RUN_LENGTH = "run_length"
COMPRESSION_HUFFMAN = "huffman"
COMPRESSION_AUTO = "auto"

VALID_COMPRESSION_TYPES: list[str] = [
    COMPRESSION_NONE,
    COMPRESSION_LZ77,
    COMPRESSION_RUN_LENGTH,
    COMPRESSION_HUFFMAN,
    COMPRESSION_AUTO,
]

# Additional asset types for separate tiles/palette generation
ASSET_TYPE_SPRITE_TILES = "sprite_tiles"
ASSET_TYPE_SPRITE_PALETTE = "sprite_palette"
ASSET_TYPE_REGULAR_BG_TILES = "regular_bg_tiles"
ASSET_TYPE_BG_PALETTE = "bg_palette"

VALID_ASSET_TYPES_EXTENDED: list[str] = [
    ASSET_TYPE_SPRITE,
    ASSET_TYPE_SPRITE_TILES,
    ASSET_TYPE_SPRITE_PALETTE,
    ASSET_TYPE_REGULAR_BG,
    ASSET_TYPE_REGULAR_BG_TILES,
    ASSET_TYPE_BG_PALETTE,
    ASSET_TYPE_AFFINE_BG,
]

# Transparency color candidates, tried in order.
# Magenta first because it's the traditional GBA convention.
DEFAULT_TRANSPARENCY_COLORS: list[tuple[int, int, int]] = [
    (255, 0, 255),
    (0, 255, 255),
    (255, 255, 0),
    (0, 255, 0),
    (255, 0, 0),
    (0, 0, 255),
]
