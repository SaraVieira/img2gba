"""
Size validation for Butano images.

Why This Module Exists:
-----------------------
The GBA hardware has strict requirements for sprite and background dimensions.
You can't use arbitrary sizes - only specific combinations are allowed.

This module:
1. Validates if an image's dimensions are valid for a given asset type
2. Suggests the closest valid sizes if the dimensions are invalid

This helps developers catch sizing issues early, before they hit cryptic
build errors from Butano/grit.

Valid Size Reference:
---------------------
See constants.py for the full list, but briefly:

Sprites (12 valid sizes):
    Square: 8x8, 16x16, 32x32, 64x64
    Wide:   16x8, 32x8, 32x16, 64x32
    Tall:   8x16, 8x32, 16x32, 32x64

Regular Backgrounds:
    256x256, 256x512, 512x256, 512x512

Affine Backgrounds:
    128x128, 256x256, 512x512, 1024x1024

Example Usage:
--------------
    from butano_img.validator import validate_size

    # Check a sprite
    result = validate_size(100, 50, "sprite")
    if not result.valid:
        print(f"Warning: {result.message}")
        # Output: "Size 100x50 is not valid for sprite. Suggested sizes: 64x32, 32x32, 32x64"
"""

from dataclasses import dataclass

from .constants import (
    ASSET_TYPE_SPRITE,
    ASSET_TYPE_REGULAR_BG,
    ASSET_TYPE_AFFINE_BG,
    VALID_SPRITE_SIZES,
    VALID_REGULAR_BG_SIZES,
    VALID_AFFINE_BG_SIZES,
)


@dataclass
class ValidationResult:
    """
    Result of validating image dimensions.

    This is a "dataclass" - a Python feature that automatically creates
    __init__, __repr__, and other methods based on the fields you define.
    Think of it as a simple struct/record type.

    Attributes:
        valid: True if the dimensions are valid for the asset type.

        current_size: The (width, height) tuple that was checked.

        suggestions: List of up to 3 valid sizes closest to the current size.
                    Empty if the current size is valid.

        message: Human-readable message describing the result.
                 Can be shown directly to the user.

    Example:
        >>> result = validate_size(100, 50, "sprite")
        >>> result.valid
        False
        >>> result.suggestions
        [(64, 32), (32, 32), (32, 64)]
        >>> result.message
        "Size 100x50 is not valid for sprite. Suggested sizes: 64x32, 32x32, 32x64"
    """

    valid: bool
    current_size: tuple[int, int]
    suggestions: list[tuple[int, int]]
    message: str


def get_valid_sizes(asset_type: str) -> list[tuple[int, int]]:
    """
    Get the list of valid sizes for an asset type.

    Args:
        asset_type: One of 'sprite', 'regular_bg', or 'affine_bg'.
                   Use the constants from constants.py for safety.

    Returns:
        List of (width, height) tuples that are valid for this asset type.

    Raises:
        ValueError: If asset_type is not recognized.

    Example:
        >>> sizes = get_valid_sizes("sprite")
        >>> (32, 32) in sizes
        True
        >>> (100, 100) in sizes
        False
    """
    # Match the asset type to its valid sizes
    if asset_type == ASSET_TYPE_SPRITE:
        return VALID_SPRITE_SIZES
    elif asset_type == ASSET_TYPE_REGULAR_BG:
        return VALID_REGULAR_BG_SIZES
    elif asset_type == ASSET_TYPE_AFFINE_BG:
        return VALID_AFFINE_BG_SIZES
    else:
        # Unknown asset type - this is a programming error
        raise ValueError(
            f"Unknown asset type: '{asset_type}'. "
            f"Valid types are: sprite, regular_bg, affine_bg"
        )


def validate_size(
    width: int,
    height: int,
    asset_type: str = ASSET_TYPE_SPRITE,
) -> ValidationResult:
    """
    Check if image dimensions are valid for a given asset type.

    This is the main function you'll use from this module. It checks if
    the given width and height match one of the valid sizes for the
    specified asset type.

    Args:
        width: The image width in pixels.
        height: The image height in pixels.
        asset_type: What kind of asset this is. Defaults to "sprite".
                   Options: "sprite", "regular_bg", "affine_bg"

    Returns:
        A ValidationResult containing:
        - valid: True if dimensions are valid
        - suggestions: Up to 3 closest valid sizes (if invalid)
        - message: Human-readable description

    Example:
        >>> # Valid size
        >>> result = validate_size(32, 32, "sprite")
        >>> result.valid
        True

        >>> # Invalid size
        >>> result = validate_size(100, 50, "sprite")
        >>> result.valid
        False
        >>> result.suggestions[:2]
        [(64, 32), (32, 32)]

    How Suggestions Work:
        When the size is invalid, we find the closest valid sizes using
        "Manhattan distance" - the sum of the absolute differences in
        width and height. This tends to suggest sizes that are visually
        similar to what you have.

        distance = |valid_width - width| + |valid_height - height|

        For example, if you have 100x50:
        - 64x32: distance = |64-100| + |32-50| = 36 + 18 = 54
        - 32x32: distance = |32-100| + |32-50| = 68 + 18 = 86
        - 64x64: distance = |64-100| + |64-50| = 36 + 14 = 50
    """
    # Get the list of valid sizes for this asset type
    valid_sizes = get_valid_sizes(asset_type)

    # The current dimensions as a tuple (for easy comparison)
    current = (width, height)

    # Check if the current size is in the valid list
    if current in valid_sizes:
        # Valid! Return success result
        return ValidationResult(
            valid=True,
            current_size=current,
            suggestions=[],  # No suggestions needed
            message=f"Size {width}x{height} is valid for {asset_type}",
        )

    # --- Invalid size: find suggestions ---

    # Define a function to calculate how "far" a valid size is from current
    # We use Manhattan distance because it's simple and works well
    def distance(size: tuple[int, int]) -> int:
        valid_width, valid_height = size
        return abs(valid_width - width) + abs(valid_height - height)

    # Sort valid sizes by distance and take the 3 closest
    # sorted() with key=distance sorts by the distance values
    # [:3] takes just the first 3 elements
    suggestions = sorted(valid_sizes, key=distance)[:3]

    # Format suggestions for the message (e.g., "64x32, 32x32, 32x64")
    suggestion_strs = [f"{s[0]}x{s[1]}" for s in suggestions]

    # Return the result with suggestions
    return ValidationResult(
        valid=False,
        current_size=current,
        suggestions=suggestions,
        message=(
            f"Size {width}x{height} is not valid for {asset_type}. "
            f"Suggested sizes: {', '.join(suggestion_strs)}"
        ),
    )


def format_valid_sizes(asset_type: str) -> str:
    """
    Format all valid sizes for an asset type as a readable string.

    Useful for help text and documentation.

    Args:
        asset_type: One of 'sprite', 'regular_bg', or 'affine_bg'.

    Returns:
        A comma-separated string of all valid sizes.

    Example:
        >>> format_valid_sizes("regular_bg")
        "256x256, 256x512, 512x256, 512x512"

        >>> format_valid_sizes("sprite")
        "8x8, 16x16, 32x32, 64x64, 16x8, 32x8, 32x16, 64x32, 8x16, 8x32, 16x32, 32x64"
    """
    valid_sizes = get_valid_sizes(asset_type)

    # Convert each (width, height) tuple to "WxH" format
    size_strs = [f"{width}x{height}" for width, height in valid_sizes]

    # Join with commas
    return ", ".join(size_strs)
