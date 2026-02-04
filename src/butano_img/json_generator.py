"""
JSON metadata generation for Butano assets.

Why This Module Exists:
-----------------------
Butano requires every image asset to have an accompanying JSON file with
metadata about the asset. The JSON file must have the same name as the
BMP file but with a .json extension.

Example:
    player.bmp  →  player.json

The JSON file tells Butano:
- What type of asset it is (sprite, regular_bg, affine_bg)
- Color depth (4bpp = 16 colors, 8bpp = 256 colors)
- Optionally: other settings like palette sharing, compression, etc.

Minimum JSON Content:
---------------------
The simplest valid JSON file just specifies the type:

    {
        "type": "sprite"
    }

With color depth:

    {
        "type": "sprite",
        "bpp_mode": "bpp_8"
    }

For sprite sheets (multiple sprites in one image):

    {
        "type": "sprite",
        "height": 32
    }

With compression (reduces ROM size):

    {
        "type": "regular_bg",
        "compression": "lz77"
    }

For more complex configurations, see the Butano documentation:
https://gvaliente.github.io/butano/import.html

Example Usage:
--------------
    from butano_img.json_generator import generate_json, read_json

    # Generate JSON for a sprite
    json_path = generate_json("player.bmp", asset_type="sprite", bpp=8)
    print(f"Created: {json_path}")  # "player.json"

    # Read it back
    data = read_json("player.json")
    print(data)  # {"type": "sprite", "bpp_mode": "bpp_8"}
"""

import json
from pathlib import Path
from typing import Any


def generate_json(
    output_path: str | Path,
    asset_type: str,
    bpp: int | None = None,
    height: int | None = None,
    compression: str | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> Path:
    """
    Generate a JSON metadata file for a Butano asset.

    Creates a JSON file alongside the BMP file with the same base name.
    For example, if output_path is "graphics/player.bmp", this creates
    "graphics/player.json".

    Args:
        output_path: Path to the BMP file. The JSON will be created in the
                    same directory with the same name but .json extension.

        asset_type: What type of Butano asset this is:
                   - "sprite": A moveable game object
                   - "regular_bg": A scrollable tile-based background
                   - "affine_bg": A background that can rotate/scale

        bpp: Bits per pixel for the image (optional):
             - 4: 16-color mode (smaller, multiple palettes possible)
             - 8: 256-color mode (more colors, one shared palette)
             - None: Don't specify (Butano will use default)

        height: Height of each sprite/frame in pixels (optional).
                Used for sprite sheets - an image with 128px total height
                and height=32 would be split into 4 sprites.
                Only meaningful for sprite and regular_bg types.

        compression: Compression method for grit to use (optional):
                    - "none": No compression (fastest loading)
                    - "lz77": LZ77 compression (good balance)
                    - "run_length": Run-length encoding
                    - "huffman": Huffman coding
                    - "auto": Let grit choose the best method

        extra_fields: Additional fields to include in the JSON (optional).
                     Useful for advanced Butano settings like:
                     - "palette": path to shared palette
                     See Butano docs for all options.

    Returns:
        Path object pointing to the created JSON file.

    Example:
        >>> # Basic usage
        >>> json_path = generate_json("player.bmp", "sprite", bpp=8)
        >>> print(json_path)
        player.json

        >>> # Sprite sheet with 4 frames of 32px each
        >>> json_path = generate_json("run_cycle.bmp", "sprite", height=32)

        >>> # Background with compression
        >>> json_path = generate_json("level.bmp", "regular_bg", compression="lz77")

    Generated JSON Examples:
        Basic sprite:
            {"type": "sprite", "bpp_mode": "bpp_8"}

        Sprite sheet:
            {"type": "sprite", "height": 32}

        Background with compression:
            {"type": "regular_bg", "compression": "lz77"}
    """
    # Convert to Path for consistent handling
    output_path = Path(output_path)

    # Create the JSON path by changing the extension
    # "player.bmp" → "player.json"
    json_path = output_path.with_suffix(".json")

    # Build the JSON data dictionary
    # Start with the required "type" field
    data: dict[str, Any] = {"type": asset_type}

    # Add bpp_mode if specified
    # Butano expects the format "bpp_4" or "bpp_8"
    if bpp is not None:
        if bpp == 4:
            data["bpp_mode"] = "bpp_4"
        elif bpp == 8:
            data["bpp_mode"] = "bpp_8"
        # Note: Invalid bpp values are silently ignored
        # (could add validation here if needed)

    # Add height for sprite sheets
    # This tells Butano how to split a single image into multiple sprites/frames
    if height is not None:
        data["height"] = height

    # Add compression method
    # This tells grit how to compress the data during build
    if compression is not None and compression != "none":
        data["compression"] = compression

    # Merge in any extra fields the caller wants to add
    if extra_fields:
        # update() adds all key-value pairs from extra_fields to data
        data.update(extra_fields)

    # Write the JSON file
    # - "w" mode creates/overwrites the file
    # - indent=4 makes it human-readable
    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)

    return json_path


def read_json(json_path: str | Path) -> dict[str, Any]:
    """
    Read an existing JSON metadata file.

    Useful for:
    - Checking what settings an existing asset has
    - Modifying and rewriting JSON files
    - Testing that generated JSON is correct

    Args:
        json_path: Path to the JSON file to read.

    Returns:
        Dictionary containing the JSON data.

    Raises:
        FileNotFoundError: If the JSON file doesn't exist.
        json.JSONDecodeError: If the file isn't valid JSON.

    Example:
        >>> data = read_json("player.json")
        >>> data["type"]
        "sprite"
        >>> data.get("bpp_mode", "not specified")
        "bpp_8"
    """
    # Convert to Path for consistent handling
    json_path = Path(json_path)

    # Read and parse the JSON file
    with open(json_path) as f:
        return json.load(f)
