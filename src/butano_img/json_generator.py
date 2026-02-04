"""JSON metadata generation for Butano assets."""

import json
from pathlib import Path
from typing import Any


def generate_json(
    output_path: str | Path,
    asset_type: str,
    bpp: int | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> Path:
    """Generate a JSON metadata file for a Butano asset.

    Args:
        output_path: Path to the BMP file (JSON will be created alongside)
        asset_type: One of 'sprite', 'regular_bg', 'affine_bg'
        bpp: Bits per pixel (4 or 8), optional
        extra_fields: Additional fields to include in JSON

    Returns:
        Path to the created JSON file
    """
    output_path = Path(output_path)
    json_path = output_path.with_suffix(".json")

    data: dict[str, Any] = {"type": asset_type}

    # Add bpp mode if specified
    if bpp is not None:
        if bpp == 4:
            data["bpp_mode"] = "bpp_4"
        elif bpp == 8:
            data["bpp_mode"] = "bpp_8"

    # Add any extra fields
    if extra_fields:
        data.update(extra_fields)

    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)

    return json_path


def read_json(json_path: str | Path) -> dict[str, Any]:
    """Read an existing JSON metadata file.

    Args:
        json_path: Path to the JSON file

    Returns:
        Dictionary with JSON contents
    """
    json_path = Path(json_path)

    with open(json_path) as f:
        return json.load(f)
