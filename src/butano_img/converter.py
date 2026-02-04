"""
Main conversion logic for Butano images.

This is the "orchestrator" module - it coordinates all the other modules
to perform a complete image conversion. If you're looking at this codebase
for the first time, this is a good place to understand the full conversion
pipeline.

The Conversion Pipeline:
------------------------
    Input PNG
        ↓
    [Load & convert to RGBA]
        ↓
    [Validate dimensions] → Warning if invalid
        ↓
    [Handle transparency]
        - Detect transparent pixels
        - Find unused color
        - Replace transparent pixels
        ↓
    [Quantize colors] → Reduce to 16 or 256
        ↓
    [Reorder palette] → Move transparency to index 0
        ↓
    [Save as BMP]
        ↓
    [Generate JSON metadata]
        ↓
    Output BMP + JSON

Example Usage:
--------------
    from butano_img.converter import convert_image

    # Simple usage - convert with all defaults
    result = convert_image("player.png")
    print(f"Created: {result.output_path}")

    # With options
    result = convert_image(
        "background.png",
        output_path="bg.bmp",
        asset_type="regular_bg",
        num_colors=256,
        verbose=True,
    )
"""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .constants import ASSET_TYPE_SPRITE, COLORS_256
from .transparency import (
    has_transparency,
    find_unused_color,
    replace_transparent_pixels,
)
from .palette import quantize_image, reorder_palette_transparency_first
from .validator import validate_size, ValidationResult
from .json_generator import generate_json


@dataclass
class ConversionResult:
    """
    Result of a complete image conversion.

    This dataclass contains all the information about a conversion,
    including whether it succeeded, where files were written, and
    details about the conversion process.

    Attributes:
        success: True if conversion completed successfully.

        output_path: Path where the BMP file was written.

        json_path: Path where the JSON file was written (or None if skipped).

        validation: The result of size validation. Check validation.valid
                    to see if the size was valid for the asset type.

        transparency_color: The RGB color used for transparency, or None
                           if no transparency was detected/handled.

        num_colors: Number of colors in the output (16 or 256).

        message: Human-readable summary of the conversion.

    Example:
        >>> result = convert_image("sprite.png")
        >>> result.success
        True
        >>> result.output_path
        PosixPath('sprite.bmp')
        >>> result.transparency_color
        (255, 0, 255)  # Magenta
    """

    success: bool
    output_path: Path
    json_path: Path | None
    validation: ValidationResult
    transparency_color: tuple[int, int, int] | None
    num_colors: int
    message: str


def convert_image(
    input_path: str | Path,
    output_path: str | Path | None = None,
    asset_type: str = ASSET_TYPE_SPRITE,
    num_colors: int = COLORS_256,
    handle_transparency: bool = True,
    trans_color: tuple[int, int, int] | None = None,
    generate_json_file: bool = True,
    sprite_height: int | None = None,
    compression: str | None = None,
    verbose: bool = False,
) -> ConversionResult:
    """
    Convert a PNG image to a Butano-compatible indexed BMP file.

    This is the main function of the butano-img tool. It takes a PNG file
    and produces a BMP file that Butano/grit can use, along with the
    required JSON metadata file.

    Args:
        input_path: Path to the input image file (usually PNG).
                   Can be a string or Path object.

        output_path: Where to save the output BMP file.
                    If None (default), uses the input filename with .bmp extension.
                    Example: "player.png" → "player.bmp"

        asset_type: What type of GBA asset this will be:
                   - "sprite" (default): A moveable game object
                   - "regular_bg": A scrollable tile-based background
                   - "affine_bg": A background that can rotate/scale
                   This affects size validation and JSON output.

        num_colors: How many colors in the output palette:
                   - 256 (default): 8bpp mode, more colors
                   - 16: 4bpp mode, saves memory

        handle_transparency: If True (default), detect transparent pixels
                            and convert them to the GBA transparency system.
                            Set to False if your image has no transparency.

        trans_color: Force a specific RGB color for transparency.
                    If None (default), automatically finds an unused color.
                    Example: (255, 0, 255) for magenta

        generate_json_file: If True (default), create the JSON metadata file
                           that Butano requires alongside the BMP.

        sprite_height: Height of each sprite/frame in a sprite sheet (optional).
                      For an image with 128px height and sprite_height=32,
                      Butano will split it into 4 separate sprites.

        compression: Compression method for grit to use (optional):
                    - "none": No compression (fastest loading)
                    - "lz77": LZ77 compression (good balance)
                    - "run_length": Run-length encoding
                    - "huffman": Huffman coding
                    - "auto": Let grit choose the best method

        verbose: If True, print progress messages during conversion.
                Useful for debugging or understanding what's happening.

    Returns:
        A ConversionResult with all the details about what was done.

    Raises:
        FileNotFoundError: If input_path doesn't exist.
        PIL.UnidentifiedImageError: If the input isn't a valid image.

    Example:
        >>> # Basic usage
        >>> result = convert_image("player.png")
        >>> print(result.output_path)
        player.bmp

        >>> # With all options
        >>> result = convert_image(
        ...     "enemy.png",
        ...     output_path="graphics/enemy.bmp",
        ...     asset_type="sprite",
        ...     num_colors=16,
        ...     verbose=True,
        ... )
        Loading enemy.png...
        Detected transparency, using color: RGB(255, 0, 255)
        Quantizing to 16 colors...
        Reordering palette (transparency first)...
        Saving to graphics/enemy.bmp...
        Generated JSON: graphics/enemy.json

    Pipeline Details:
        1. LOAD: Open the image and convert to RGBA mode (ensuring we have
           an alpha channel to check for transparency).

        2. VALIDATE: Check if dimensions are valid for the asset type.
           Invalid sizes produce a warning but don't stop conversion.

        3. TRANSPARENCY: If enabled and the image has transparent pixels:
           - Find a color not used in the image (usually magenta)
           - Replace all transparent pixels with that color
           This converts from PNG alpha transparency to GBA color-key transparency.

        4. QUANTIZE: Reduce from millions of colors to 16 or 256.
           Uses the median cut algorithm for good quality.

        5. REORDER: If we have transparency, swap the palette so the
           transparency color is at index 0 (where GBA expects it).

        6. SAVE: Write the indexed BMP file (uncompressed, grit-compatible).

        7. JSON: Generate the metadata file Butano needs.
    """
    # Convert input to Path object for consistent handling
    input_path = Path(input_path)

    # --- Determine output path ---
    # If not specified, use the input name with .bmp extension
    if output_path is None:
        output_path = input_path.with_suffix(".bmp")
    else:
        output_path = Path(output_path)

    # --- Step 1: Load the image ---
    if verbose:
        print(f"Loading {input_path}...")

    # Open and convert to RGBA mode
    # - RGBA ensures we have an alpha channel to check transparency
    # - Works regardless of the input format (RGB, P, L, etc.)
    img = Image.open(input_path).convert("RGBA")

    # --- Step 2: Validate dimensions ---
    validation = validate_size(img.width, img.height, asset_type)

    # Print warning for invalid sizes (but continue conversion)
    if not validation.valid and verbose:
        print(f"Warning: {validation.message}")

    # --- Step 3: Handle transparency ---
    # This will hold the color we use for transparency (or None)
    used_trans_color: tuple[int, int, int] | None = None

    if handle_transparency:
        # Check if the image actually has any transparent pixels
        if has_transparency(img):
            # Determine which color to use for transparency
            if trans_color is None:
                # Auto-detect: find a color not used in the image
                used_trans_color = find_unused_color(img)
            else:
                # Use the color specified by the caller
                used_trans_color = trans_color

            if verbose:
                r, g, b = used_trans_color
                print(f"Detected transparency, using color: RGB({r}, {g}, {b})")

            # Replace all transparent pixels with the transparency color
            img = replace_transparent_pixels(img, used_trans_color)

        else:
            # No transparency in the image, but GBA still treats index 0 as transparent.
            # We need to reserve index 0 for an unused color so no visible pixels
            # accidentally become transparent.
            if trans_color is None:
                used_trans_color = find_unused_color(img)
            else:
                used_trans_color = trans_color

            if verbose:
                r, g, b = used_trans_color
                print(f"No transparency detected, reserving index 0 for: RGB({r}, {g}, {b})")

            # Add the reserved color to the image so it ends up in the palette.
            # We put a single pixel of this color at position (0, 0).
            # This pixel will become transparent on GBA, but since it's just one
            # pixel in the corner, it's usually not noticeable.
            img = img.copy()  # Don't modify the original
            img.putpixel((0, 0), used_trans_color + (255,))  # RGBA format

    # --- Step 4: Quantize to indexed color ---
    if verbose:
        print(f"Quantizing to {num_colors} colors...")

    # This converts from RGB (millions of colors) to a palette (16 or 256 colors)
    indexed_img = quantize_image(img, num_colors)

    # --- Step 5: Reorder palette for transparency ---
    # Only needed if we have a transparency color
    if used_trans_color is not None:
        if verbose:
            print("Reordering palette (transparency first)...")

        # Swap palette so transparency color is at index 0
        indexed_img = reorder_palette_transparency_first(indexed_img, used_trans_color)

    # --- Step 6: Save as BMP ---
    if verbose:
        print(f"Saving to {output_path}...")

    # Pillow saves indexed images as uncompressed BMP by default
    # This is exactly what grit/Butano needs
    indexed_img.save(output_path, "BMP")

    # --- Step 7: Generate JSON metadata ---
    json_path: Path | None = None

    if generate_json_file:
        # Determine bpp (bits per pixel) from color count
        # 16 colors = 4bpp, 256 colors = 8bpp
        bpp = 4 if num_colors <= 16 else 8

        # Create the JSON file with all configured options
        json_path = generate_json(
            output_path,
            asset_type,
            bpp=bpp,
            height=sprite_height,
            compression=compression,
        )

        if verbose:
            print(f"Generated JSON: {json_path}")
            if sprite_height:
                print(f"  Sprite height: {sprite_height}px")
            if compression and compression != "none":
                print(f"  Compression: {compression}")

    # --- Return the result ---
    return ConversionResult(
        success=True,
        output_path=output_path,
        json_path=json_path,
        validation=validation,
        transparency_color=used_trans_color,
        num_colors=num_colors,
        message=f"Successfully converted {input_path.name} to {output_path.name}",
    )
