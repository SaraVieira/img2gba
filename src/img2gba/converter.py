"""Main conversion pipeline: PNG -> indexed BMP + JSON metadata."""

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
    """Convert a PNG image to a Butano-compatible indexed BMP file."""
    input_path = Path(input_path)

    if output_path is None:
        output_path = input_path.with_suffix(".bmp")
    else:
        output_path = Path(output_path)

    if verbose:
        print(f"Loading {input_path}...")

    img = Image.open(input_path).convert("RGBA")

    validation = validate_size(img.width, img.height, asset_type)
    if not validation.valid and verbose:
        print(f"Warning: {validation.message}")

    used_trans_color: tuple[int, int, int] | None = None

    if handle_transparency:
        if has_transparency(img):
            used_trans_color = trans_color or find_unused_color(img)

            if verbose:
                r, g, b = used_trans_color
                print(f"Detected transparency, using color: RGB({r}, {g}, {b})")

            img = replace_transparent_pixels(img, used_trans_color)
        else:
            # Reserve index 0 for transparency even on opaque images
            used_trans_color = trans_color or find_unused_color(img)

            if verbose:
                r, g, b = used_trans_color
                print(f"No transparency detected, reserving index 0 for: RGB({r}, {g}, {b})")

            img = img.copy()
            img.putpixel((0, 0), used_trans_color + (255,))

    if verbose:
        print(f"Quantizing to {num_colors} colors...")

    indexed_img = quantize_image(img, num_colors)

    if used_trans_color is not None:
        if verbose:
            print("Reordering palette (transparency first)...")
        indexed_img = reorder_palette_transparency_first(indexed_img, used_trans_color)

    if verbose:
        print(f"Saving to {output_path}...")

    indexed_img.save(output_path, "BMP")

    json_path: Path | None = None
    if generate_json_file:
        bpp = 4 if num_colors <= 16 else 8
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

    return ConversionResult(
        success=True,
        output_path=output_path,
        json_path=json_path,
        validation=validation,
        transparency_color=used_trans_color,
        num_colors=num_colors,
        message=f"Successfully converted {input_path.name} to {output_path.name}",
    )
