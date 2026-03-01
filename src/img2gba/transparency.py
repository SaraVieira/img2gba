"""Transparency detection and handling for GBA color-key conversion."""

import random
from PIL import Image

from .constants import DEFAULT_TRANSPARENCY_COLORS


def has_transparency(img: Image.Image) -> bool:
    """Check if an image has any transparent pixels."""
    if img.mode != "RGBA":
        return False

    alpha_channel = img.getchannel("A")
    min_alpha, max_alpha = alpha_channel.getextrema()
    return min_alpha < 255


def find_unused_color(img: Image.Image) -> tuple[int, int, int]:
    """Find an RGB color not present in the image, for use as transparency key."""
    rgb_img = img.convert("RGB")
    used_colors: set[tuple[int, int, int]] = set(rgb_img.getdata())

    for color in DEFAULT_TRANSPARENCY_COLORS:
        if color not in used_colors:
            return color

    for _ in range(10000):
        random_color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
        if random_color not in used_colors:
            return random_color

    return (255, 0, 255)


def replace_transparent_pixels(
    img: Image.Image,
    trans_color: tuple[int, int, int],
    threshold: int = 128,
) -> Image.Image:
    """Replace transparent pixels (alpha < threshold) with a solid color."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    result = img.copy()
    pixels = result.load()

    for y in range(result.height):
        for x in range(result.width):
            red, green, blue, alpha = pixels[x, y]
            if alpha < threshold:
                pixels[x, y] = (*trans_color, 255)

    return result
