"""
Transparency detection and handling for Butano images.

Why This Module Exists:
-----------------------
The GBA doesn't support alpha transparency in the way modern formats like PNG do.
Instead, it uses a "color key" system: one color in the palette (always index 0)
is designated as "transparent" and those pixels aren't drawn.

This module handles the conversion from PNG's alpha channel transparency
to the GBA's color-key transparency system.

How It Works:
-------------
1. Detect if the image has any transparent pixels (alpha < 255)
2. Find a color that isn't used anywhere in the image
3. Replace all transparent pixels with that color
4. Later (in palette.py), that color will be moved to palette index 0

Example:
--------
    from PIL import Image
    from img2gba.transparency import (
        has_transparency,
        find_unused_color,
        replace_transparent_pixels,
    )

    img = Image.open("sprite.png").convert("RGBA")

    if has_transparency(img):
        trans_color = find_unused_color(img)
        img = replace_transparent_pixels(img, trans_color)
        # Now all transparent pixels are filled with trans_color
"""

import random
from PIL import Image

from .constants import DEFAULT_TRANSPARENCY_COLORS


def has_transparency(img: Image.Image) -> bool:
    """
    Check if an image has any transparent or semi-transparent pixels.

    This function checks the alpha channel of an RGBA image to see if
    any pixels have an alpha value less than 255 (fully opaque).

    Args:
        img: A PIL Image object. Should be in RGBA mode, but will return
             False for other modes (which don't have transparency).

    Returns:
        True if the image has any pixels with alpha < 255.
        False if the image is fully opaque or not in RGBA mode.

    Example:
        >>> from PIL import Image
        >>> img = Image.new('RGBA', (10, 10), (255, 0, 0, 255))  # Fully opaque red
        >>> has_transparency(img)
        False
        >>> img.putpixel((5, 5), (255, 0, 0, 0))  # Make one pixel transparent
        >>> has_transparency(img)
        True

    Technical Note:
        We use getextrema() which returns (min, max) of the channel.
        If min alpha < 255, there's at least one non-opaque pixel.
        This is much faster than checking every pixel individually.
    """
    # Only RGBA images can have transparency
    if img.mode != "RGBA":
        return False

    # Extract just the alpha channel (A) from RGBA
    # This creates a new grayscale image where each pixel is the alpha value
    alpha_channel = img.getchannel("A")

    # getextrema() returns (min_value, max_value) for the channel
    # If the minimum alpha is less than 255, we have some transparency
    min_alpha, max_alpha = alpha_channel.getextrema()

    return min_alpha < 255


def find_unused_color(img: Image.Image) -> tuple[int, int, int]:
    """
    Find an RGB color that isn't used anywhere in the image.

    This function identifies a color we can safely use as the "transparency
    key" - a color that will represent transparent pixels without conflicting
    with any actual colors in the artwork.

    Args:
        img: A PIL Image object (any mode - will be converted to RGB internally).

    Returns:
        A tuple of (red, green, blue) values, each 0-255, representing a color
        that doesn't appear anywhere in the image.

    Algorithm:
        1. First, try common transparency colors (magenta, cyan, etc.)
           in order of preference. Magenta (255, 0, 255) is traditional.
        2. If all common colors are used, generate random colors until
           we find one that isn't in the image.
        3. As an absolute fallback, return magenta anyway (this would only
           happen if the image somehow uses all 16.7 million possible colors).

    Example:
        >>> from PIL import Image
        >>> img = Image.new('RGB', (10, 10), (255, 0, 0))  # Solid red
        >>> color = find_unused_color(img)
        >>> color
        (255, 0, 255)  # Magenta, since red image doesn't use it

    Why Magenta?
        Magenta (255, 0, 255) is the traditional choice for transparency in
        game development because:
        - It's visually distinctive (you'll notice if something goes wrong)
        - It rarely appears in natural artwork
        - It's a convention dating back to early game development
    """
    # Convert to RGB to analyze colors (removes alpha channel)
    # This lets us compare with our candidate colors which are RGB tuples
    rgb_img = img.convert("RGB")

    # Get all unique colors as a set for fast lookup
    # getdata() returns a flat sequence of all pixels
    # set() removes duplicates
    used_colors: set[tuple[int, int, int]] = set(rgb_img.getdata())

    # Try our preferred transparency colors first
    # These are defined in constants.py, starting with magenta
    for color in DEFAULT_TRANSPARENCY_COLORS:
        if color not in used_colors:
            return color

    # If all our preferred colors are somehow used, find a random one
    # This is extremely rare - the image would need to use magenta, cyan,
    # yellow, green, red, AND blue as exact RGB values
    max_attempts = 10000
    for _ in range(max_attempts):
        # Generate a random RGB color
        random_color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
        if random_color not in used_colors:
            return random_color

    # Absolute fallback - this should never happen in practice
    # (Would require an image using all 16.7 million colors)
    return (255, 0, 255)


def replace_transparent_pixels(
    img: Image.Image,
    trans_color: tuple[int, int, int],
    threshold: int = 128,
) -> Image.Image:
    """
    Replace all transparent pixels with a solid transparency color.

    This function converts from "alpha channel transparency" (where each pixel
    has an opacity value) to "color key transparency" (where one specific
    color means "transparent").

    Args:
        img: A PIL Image object. Will be converted to RGBA if not already.

        trans_color: The RGB color to use for transparent pixels.
                     Should be a color not used elsewhere in the image
                     (use find_unused_color() to get this).

        threshold: Alpha value below which pixels are considered transparent.
                   Default is 128 (50% opacity).
                   - Pixels with alpha < threshold become transparent
                   - Pixels with alpha >= threshold keep their color

    Returns:
        A new RGBA image with transparent pixels replaced. The original
        image is not modified.

    Example:
        >>> from PIL import Image
        >>> # Create a 10x10 image with a transparent center
        >>> img = Image.new('RGBA', (10, 10), (255, 0, 0, 255))  # Red
        >>> for x in range(3, 7):
        ...     for y in range(3, 7):
        ...         img.putpixel((x, y), (0, 0, 0, 0))  # Transparent center
        >>> result = replace_transparent_pixels(img, (255, 0, 255))
        >>> # Now the center is magenta instead of transparent

    Technical Note:
        We iterate pixel-by-pixel which is slow for large images.
        For better performance on large images, you could use NumPy:
            import numpy as np
            data = np.array(img)
            mask = data[:, :, 3] < threshold
            data[mask] = [*trans_color, 255]
            return Image.fromarray(data)
        But for typical GBA sprite sizes (up to 64x64), this is fine.
    """
    # Ensure we're working with RGBA (has alpha channel)
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Create a copy so we don't modify the original image
    # This is important for testing and allows the caller to keep the original
    result = img.copy()

    # Get pixel access object for direct pixel manipulation
    # This is faster than using getpixel/putpixel in a loop
    pixels = result.load()

    # Iterate through every pixel
    for y in range(result.height):
        for x in range(result.width):
            # Unpack the pixel's RGBA values
            red, green, blue, alpha = pixels[x, y]

            # If the pixel is transparent (alpha below threshold),
            # replace it with the transparency color (fully opaque)
            if alpha < threshold:
                # *trans_color unpacks (r, g, b) into three values
                # So this becomes (r, g, b, 255)
                pixels[x, y] = (*trans_color, 255)

    return result
