"""Image dimension validation against GBA hardware constraints."""

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
    valid: bool
    current_size: tuple[int, int]
    suggestions: list[tuple[int, int]]
    message: str


def get_valid_sizes(asset_type: str) -> list[tuple[int, int]]:
    """Get the list of valid sizes for an asset type."""
    if asset_type == ASSET_TYPE_SPRITE:
        return VALID_SPRITE_SIZES
    elif asset_type == ASSET_TYPE_REGULAR_BG:
        return VALID_REGULAR_BG_SIZES
    elif asset_type == ASSET_TYPE_AFFINE_BG:
        return VALID_AFFINE_BG_SIZES
    else:
        raise ValueError(
            f"Unknown asset type: '{asset_type}'. "
            f"Valid types are: sprite, regular_bg, affine_bg"
        )


def validate_size(
    width: int,
    height: int,
    asset_type: str = ASSET_TYPE_SPRITE,
) -> ValidationResult:
    """Check if image dimensions are valid for a given GBA asset type."""
    valid_sizes = get_valid_sizes(asset_type)
    current = (width, height)

    if current in valid_sizes:
        return ValidationResult(
            valid=True,
            current_size=current,
            suggestions=[],
            message=f"Size {width}x{height} is valid for {asset_type}",
        )

    def distance(size: tuple[int, int]) -> int:
        return abs(size[0] - width) + abs(size[1] - height)

    suggestions = sorted(valid_sizes, key=distance)[:3]
    suggestion_strs = [f"{s[0]}x{s[1]}" for s in suggestions]

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
    """Format all valid sizes for an asset type as a comma-separated string."""
    valid_sizes = get_valid_sizes(asset_type)
    return ", ".join(f"{w}x{h}" for w, h in valid_sizes)
