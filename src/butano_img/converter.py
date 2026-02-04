"""Main conversion logic for Butano images."""

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
    """Result of image conversion."""

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
    verbose: bool = False,
) -> ConversionResult:
    """Convert a PNG image to Butano-compatible indexed BMP.

    Args:
        input_path: Path to input PNG file
        output_path: Path for output BMP (default: same name with .bmp)
        asset_type: One of 'sprite', 'regular_bg', 'affine_bg'
        num_colors: Number of colors (16 or 256)
        handle_transparency: Whether to detect and handle transparency
        trans_color: Force specific transparency color (auto-detect if None)
        generate_json_file: Whether to create the JSON metadata file
        verbose: Print detailed progress

    Returns:
        ConversionResult with status and details
    """
    input_path = Path(input_path)

    # Determine output path
    if output_path is None:
        output_path = input_path.with_suffix(".bmp")
    else:
        output_path = Path(output_path)

    # Load the image
    if verbose:
        print(f"Loading {input_path}...")

    img = Image.open(input_path).convert("RGBA")

    # Validate dimensions
    validation = validate_size(img.width, img.height, asset_type)
    if not validation.valid and verbose:
        print(f"Warning: {validation.message}")

    # Handle transparency
    used_trans_color = None

    if handle_transparency:
        if has_transparency(img):
            if trans_color is None:
                used_trans_color = find_unused_color(img)
            else:
                used_trans_color = trans_color

            if verbose:
                print(f"Detected transparency, using color: RGB{used_trans_color}")

            img = replace_transparent_pixels(img, used_trans_color)
        elif verbose:
            print("No transparency detected in image")

    # Quantize to indexed color
    if verbose:
        print(f"Quantizing to {num_colors} colors...")

    indexed_img = quantize_image(img, num_colors)

    # Reorder palette if we have a transparency color
    if used_trans_color is not None:
        if verbose:
            print("Reordering palette (transparency first)...")

        indexed_img = reorder_palette_transparency_first(indexed_img, used_trans_color)

    # Save as BMP
    if verbose:
        print(f"Saving to {output_path}...")

    indexed_img.save(output_path, "BMP")

    # Generate JSON if requested
    json_path = None
    if generate_json_file:
        bpp = 4 if num_colors <= 16 else 8
        json_path = generate_json(output_path, asset_type, bpp=bpp)
        if verbose:
            print(f"Generated JSON: {json_path}")

    return ConversionResult(
        success=True,
        output_path=output_path,
        json_path=json_path,
        validation=validation,
        transparency_color=used_trans_color,
        num_colors=num_colors,
        message=f"Successfully converted {input_path.name} to {output_path.name}",
    )
