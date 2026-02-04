"""Transparency detection and handling for Butano images."""

import random
from PIL import Image

from .constants import DEFAULT_TRANSPARENCY_COLORS


def has_transparency(img: Image.Image) -> bool:
    """Check if an RGBA image has any transparent pixels.

    Args:
        img: PIL Image in RGBA mode

    Returns:
        True if any pixel has alpha < 255
    """
    if img.mode != "RGBA":
        return False

    # Check alpha channel for any non-opaque pixels
    alpha = img.getchannel("A")
    return alpha.getextrema()[0] < 255


def find_unused_color(img: Image.Image) -> tuple[int, int, int]:
    """Find a color not used in the image to use as transparency.

    Args:
        img: PIL Image (will be converted to RGB for analysis)

    Returns:
        RGB tuple of an unused color
    """
    # Get all unique RGB colors in the image
    rgb_img = img.convert("RGB")
    used_colors = set(rgb_img.getdata())

    # Try default candidates first
    for color in DEFAULT_TRANSPARENCY_COLORS:
        if color not in used_colors:
            return color

    # If all candidates are used, find a random unused color
    # This is rare but possible for images with many colors
    attempts = 0
    while attempts < 10000:
        color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
        if color not in used_colors:
            return color
        attempts += 1

    # Fallback: return magenta anyway (extremely rare edge case)
    return (255, 0, 255)


def replace_transparent_pixels(
    img: Image.Image,
    trans_color: tuple[int, int, int],
    threshold: int = 128,
) -> Image.Image:
    """Replace transparent pixels with the transparency color.

    Args:
        img: PIL Image in RGBA mode
        trans_color: RGB tuple to use for transparent pixels
        threshold: Alpha value below which pixels are considered transparent

    Returns:
        New RGBA image with transparent pixels replaced
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Create a copy to avoid modifying the original
    result = img.copy()
    pixels = result.load()

    for y in range(result.height):
        for x in range(result.width):
            r, g, b, a = pixels[x, y]
            if a < threshold:
                pixels[x, y] = (*trans_color, 255)

    return result
