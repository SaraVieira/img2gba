"""
Palette manipulation for Butano images.

What is a Palette?
------------------
A palette (or "color lookup table") is a list of colors. Instead of storing
the actual RGB values for each pixel, an "indexed" or "paletted" image stores
a number (index) that refers to a color in the palette.

Example:
    Palette: [Red, Green, Blue, Yellow, ...]  (indices 0, 1, 2, 3, ...)
    Pixel data: [0, 0, 1, 2, 0, 3, ...]       (means: Red, Red, Green, Blue, Red, Yellow)

This saves memory (1 byte per pixel vs 3 bytes for RGB) and is how the GBA
stores most of its graphics.

Why This Module Exists:
-----------------------
1. PNG images are usually "true color" (millions of colors). We need to reduce
   them to 16 or 256 colors for the GBA. This is called "quantization".

2. The GBA treats palette index 0 as transparent. After quantization, the
   transparency color might be at any index. We need to move it to index 0.

Key Functions:
--------------
- quantize_image(): Reduce colors from millions to 16 or 256
- reorder_palette_transparency_first(): Move transparency color to index 0

Example Usage:
--------------
    from PIL import Image
    from img2gba.palette import quantize_image, reorder_palette_transparency_first

    # Load and prepare image
    img = Image.open("sprite.png")

    # Quantize to 256 colors
    indexed = quantize_image(img, num_colors=256)

    # Move transparency color (magenta) to index 0
    result = reorder_palette_transparency_first(indexed, trans_color=(255, 0, 255))
"""

from PIL import Image


def quantize_image(
    img: Image.Image,
    num_colors: int = 256,
    method: int = Image.Quantize.MEDIANCUT,
) -> Image.Image:
    """
    Reduce an image's colors to a limited palette.

    This process is called "quantization" - converting from potentially millions
    of colors to a small fixed palette (16 or 256 colors for GBA).

    Args:
        img: A PIL Image in any mode (RGB, RGBA, etc.).
             Will be converted to RGB internally.

        num_colors: How many colors to reduce to. For GBA:
                   - 16 colors (4bpp mode) - saves memory, multiple palettes
                   - 256 colors (8bpp mode) - more colors, one shared palette

        method: The algorithm to use for color reduction:
               - Image.Quantize.MEDIANCUT (default): Good balance of speed/quality
               - Image.Quantize.MAXCOVERAGE: Better for images with few colors
               - Image.Quantize.FASTOCTREE: Fastest, but lower quality

    Returns:
        A new PIL Image in "P" (palette) mode.
        Each pixel is now an index (0-255) into the palette.

    Example:
        >>> from PIL import Image
        >>> # Load a photo with millions of colors
        >>> photo = Image.open("photo.png")
        >>> # Reduce to 256 colors
        >>> indexed = quantize_image(photo, num_colors=256)
        >>> indexed.mode
        'P'

    How Quantization Works (Median Cut Algorithm):
        1. Put all pixels in a "box" in RGB color space
        2. Find which axis (R, G, or B) has the most variation
        3. Sort pixels along that axis and split the box in half
        4. Repeat until you have enough boxes (= colors)
        5. Average the pixels in each box to get the palette color

    Note:
        The alpha channel (transparency) is removed during quantization.
        Handle transparency BEFORE calling this function by replacing
        transparent pixels with a solid color.
    """
    # Convert to RGB first
    # - This removes the alpha channel (we handle transparency separately)
    # - This ensures consistent input regardless of source format
    rgb_img = img.convert("RGB")

    # Perform quantization
    # - This analyzes the image and picks the best N colors
    # - Returns a new image in 'P' mode (paletted/indexed)
    indexed_img = rgb_img.quantize(colors=num_colors, method=method)

    return indexed_img


def get_palette_as_tuples(img: Image.Image) -> list[tuple[int, int, int]]:
    """
    Get the image's palette as a list of RGB tuples.

    Pillow stores palettes as a flat list: [R0, G0, B0, R1, G1, B1, ...]
    This function converts it to a more usable format: [(R0, G0, B0), (R1, G1, B1), ...]

    Args:
        img: A PIL Image in "P" (palette) mode.

    Returns:
        A list of RGB tuples, where index i is the color for palette entry i.

    Raises:
        ValueError: If the image is not in palette mode.

    Example:
        >>> indexed = quantize_image(some_image, num_colors=16)
        >>> palette = get_palette_as_tuples(indexed)
        >>> palette[0]  # First color in palette
        (128, 64, 32)
        >>> len(palette)
        256  # Always 256 entries (unused ones are typically black)
    """
    # This function only makes sense for paletted images
    if img.mode != "P":
        raise ValueError(
            f"Image must be in palette mode (P), but got mode '{img.mode}'"
        )

    # Get the raw palette data from Pillow
    # This is a flat list of 768 integers: [R0, G0, B0, R1, G1, B1, ..., R255, G255, B255]
    palette = img.getpalette()

    if palette is None:
        return []

    # Convert flat list to list of tuples
    # We step through 3 values at a time (R, G, B)
    colors: list[tuple[int, int, int]] = []
    for i in range(0, len(palette), 3):
        rgb_tuple = (palette[i], palette[i + 1], palette[i + 2])
        colors.append(rgb_tuple)

    return colors


def find_color_index(img: Image.Image, color: tuple[int, int, int]) -> int | None:
    """
    Find which palette index contains a specific color.

    Args:
        img: A PIL Image in "P" (palette) mode.
        color: The RGB tuple to search for, e.g., (255, 0, 255) for magenta.

    Returns:
        The palette index (0-255) if found, or None if the color isn't in the palette.

    Example:
        >>> # Find where magenta is in the palette
        >>> index = find_color_index(indexed_img, (255, 0, 255))
        >>> if index is not None:
        ...     print(f"Magenta is at palette index {index}")
        ... else:
        ...     print("Magenta not found in palette")

    Note:
        This does an exact match. (255, 0, 255) won't match (254, 0, 255).
        After quantization, colors may shift slightly, so the exact color
        might not be present if it was affected by the quantization process.
    """
    palette = img.getpalette()
    if palette is None:
        return None

    # Search through the palette for a matching color
    # We check every 3 values (R, G, B) and compare as a tuple
    for i in range(0, len(palette), 3):
        palette_color = (palette[i], palette[i + 1], palette[i + 2])
        if palette_color == color:
            # Found it! Convert byte offset to palette index
            return i // 3

    # Color not found in palette
    return None


def reorder_palette_transparency_first(
    img: Image.Image,
    trans_color: tuple[int, int, int],
) -> Image.Image:
    """
    Reorder the palette so the transparency color is at index 0.

    The GBA hardware treats palette index 0 as transparent. After quantization,
    our transparency color might be at any index (e.g., index 47). This function
    swaps it with whatever is at index 0.

    Args:
        img: A PIL Image in "P" (palette) mode.
        trans_color: The RGB tuple of the transparency color, e.g., (255, 0, 255).

    Returns:
        A new PIL Image with the palette reordered. The original is not modified.
        If the transparency color is not found or already at index 0, returns
        the original image unchanged.

    Example:
        >>> # After quantization, magenta might be at index 47
        >>> index = find_color_index(indexed, (255, 0, 255))
        >>> print(f"Magenta is at index {index}")  # e.g., "47"
        >>> # Move it to index 0
        >>> reordered = reorder_palette_transparency_first(indexed, (255, 0, 255))
        >>> new_index = find_color_index(reordered, (255, 0, 255))
        >>> print(f"Magenta is now at index {new_index}")  # "0"

    How It Works:
        1. Find the current index of the transparency color
        2. Swap the palette entries at index 0 and the found index
        3. Update ALL pixel data to use the new indices:
           - Pixels that were 0 become trans_index
           - Pixels that were trans_index become 0
           - All other pixels stay the same

    Why We Need This:
        When Butano/grit loads the image, it assumes index 0 is transparent.
        If magenta is at index 47, all those pixels would show as the color
        that was originally at index 0 (probably not what you want).
    """
    # This only makes sense for paletted images
    if img.mode != "P":
        raise ValueError(
            f"Image must be in palette mode (P), but got mode '{img.mode}'"
        )

    # Get the current palette
    palette = img.getpalette()
    if palette is None:
        return img

    # Find where the transparency color currently is
    trans_index = find_color_index(img, trans_color)

    # If not found or already at index 0, nothing to do
    if trans_index is None:
        # Color not in palette - maybe quantization changed it
        # Just return the original image
        return img

    if trans_index == 0:
        # Already at index 0, nothing to swap
        return img

    # --- Step 1: Swap the palette entries ---

    # Make a mutable copy of the palette
    new_palette = list(palette)

    # Calculate byte offsets in the flat palette array
    # Index 0 starts at byte 0 (bytes 0, 1, 2 are R, G, B)
    # Index N starts at byte N*3 (bytes N*3, N*3+1, N*3+2 are R, G, B)
    byte_offset_0 = 0
    byte_offset_trans = trans_index * 3

    # Swap the two RGB entries
    # Python's tuple unpacking makes this a clean swap
    (
        new_palette[byte_offset_0 : byte_offset_0 + 3],
        new_palette[byte_offset_trans : byte_offset_trans + 3],
    ) = (
        new_palette[byte_offset_trans : byte_offset_trans + 3],
        new_palette[byte_offset_0 : byte_offset_0 + 3],
    )

    # --- Step 2: Remap all pixel data ---

    # Get all pixel values as a list of indices
    pixel_data = list(img.getdata())

    # Create new pixel data with swapped indices
    new_pixels = []
    for pixel_index in pixel_data:
        if pixel_index == 0:
            # Was pointing to index 0, now should point to where we moved that color
            new_pixels.append(trans_index)
        elif pixel_index == trans_index:
            # Was pointing to trans color, now should point to index 0
            new_pixels.append(0)
        else:
            # All other indices stay the same
            new_pixels.append(pixel_index)

    # --- Step 3: Create new image with updated palette and pixels ---

    # Create a new paletted image of the same size
    new_img = Image.new("P", img.size)

    # Set the pixel data
    new_img.putdata(new_pixels)

    # Set the palette
    new_img.putpalette(new_palette)

    return new_img
