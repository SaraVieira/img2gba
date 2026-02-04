"""Size validation for Butano images."""

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
    """Result of size validation."""

    valid: bool
    current_size: tuple[int, int]
    suggestions: list[tuple[int, int]]
    message: str


def get_valid_sizes(asset_type: str) -> list[tuple[int, int]]:
    """Get valid sizes for an asset type.

    Args:
        asset_type: One of 'sprite', 'regular_bg', 'affine_bg'

    Returns:
        List of valid (width, height) tuples
    """
    if asset_type == ASSET_TYPE_SPRITE:
        return VALID_SPRITE_SIZES
    elif asset_type == ASSET_TYPE_REGULAR_BG:
        return VALID_REGULAR_BG_SIZES
    elif asset_type == ASSET_TYPE_AFFINE_BG:
        return VALID_AFFINE_BG_SIZES
    else:
        raise ValueError(f"Unknown asset type: {asset_type}")


def validate_size(
    width: int,
    height: int,
    asset_type: str = ASSET_TYPE_SPRITE,
) -> ValidationResult:
    """Validate image dimensions for a given asset type.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        asset_type: One of 'sprite', 'regular_bg', 'affine_bg'

    Returns:
        ValidationResult with validity status and suggestions
    """
    valid_sizes = get_valid_sizes(asset_type)
    current = (width, height)

    if current in valid_sizes:
        return ValidationResult(
            valid=True,
            current_size=current,
            suggestions=[],
            message=f"Size {width}x{height} is valid for {asset_type}",
        )

    # Find closest valid sizes by Manhattan distance
    def distance(size: tuple[int, int]) -> int:
        return abs(size[0] - width) + abs(size[1] - height)

    suggestions = sorted(valid_sizes, key=distance)[:3]

    suggestion_strs = [f"{s[0]}x{s[1]}" for s in suggestions]

    return ValidationResult(
        valid=False,
        current_size=current,
        suggestions=suggestions,
        message=f"Size {width}x{height} is not valid for {asset_type}. "
                f"Suggested sizes: {', '.join(suggestion_strs)}",
    )


def format_valid_sizes(asset_type: str) -> str:
    """Format valid sizes as a human-readable string.

    Args:
        asset_type: One of 'sprite', 'regular_bg', 'affine_bg'

    Returns:
        Formatted string listing valid sizes
    """
    valid_sizes = get_valid_sizes(asset_type)
    size_strs = [f"{w}x{h}" for w, h in valid_sizes]
    return ", ".join(size_strs)
