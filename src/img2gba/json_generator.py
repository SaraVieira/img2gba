"""JSON metadata generation for Butano assets."""

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
    """Generate a JSON metadata file alongside the BMP for Butano."""
    output_path = Path(output_path)
    json_path = output_path.with_suffix(".json")

    data: dict[str, Any] = {"type": asset_type}

    if bpp is not None:
        if bpp == 4:
            data["bpp_mode"] = "bpp_4"
        elif bpp == 8:
            data["bpp_mode"] = "bpp_8"

    if height is not None:
        data["height"] = height

    if compression is not None and compression != "none":
        data["compression"] = compression

    if extra_fields:
        data.update(extra_fields)

    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)

    return json_path


def read_json(json_path: str | Path) -> dict[str, Any]:
    """Read an existing JSON metadata file."""
    json_path = Path(json_path)
    with open(json_path) as f:
        return json.load(f)
