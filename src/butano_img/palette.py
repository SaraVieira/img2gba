"""Palette manipulation for Butano images."""

from PIL import Image


def quantize_image(
    img: Image.Image,
    num_colors: int = 256,
    method: int = Image.Quantize.MEDIANCUT,
) -> Image.Image:
    """Quantize an image to a limited color palette.

    Args:
        img: PIL Image (RGB or RGBA)
        num_colors: Number of colors in palette (16 or 256)
        method: Quantization method (MEDIANCUT, MAXCOVERAGE, FASTOCTREE)

    Returns:
        PIL Image in P (palette) mode
    """
    # Convert to RGB if needed (remove alpha)
    rgb_img = img.convert("RGB")

    # Quantize to palette
    indexed = rgb_img.quantize(colors=num_colors, method=method)

    return indexed


def get_palette_as_tuples(img: Image.Image) -> list[tuple[int, int, int]]:
    """Get the palette as a list of RGB tuples.

    Args:
        img: PIL Image in P (palette) mode

    Returns:
        List of RGB tuples
    """
    if img.mode != "P":
        raise ValueError("Image must be in palette mode (P)")

    palette = img.getpalette()
    if palette is None:
        return []

    colors = []
    for i in range(0, len(palette), 3):
        colors.append((palette[i], palette[i + 1], palette[i + 2]))

    return colors


def find_color_index(img: Image.Image, color: tuple[int, int, int]) -> int | None:
    """Find the palette index of a specific color.

    Args:
        img: PIL Image in P (palette) mode
        color: RGB tuple to find

    Returns:
        Palette index or None if not found
    """
    palette = img.getpalette()
    if palette is None:
        return None

    for i in range(0, len(palette), 3):
        if (palette[i], palette[i + 1], palette[i + 2]) == color:
            return i // 3

    return None


def reorder_palette_transparency_first(
    img: Image.Image,
    trans_color: tuple[int, int, int],
) -> Image.Image:
    """Reorder palette so transparency color is at index 0.

    Args:
        img: PIL Image in P (palette) mode
        trans_color: RGB tuple of the transparency color

    Returns:
        New PIL Image with reordered palette
    """
    if img.mode != "P":
        raise ValueError("Image must be in palette mode (P)")

    palette = img.getpalette()
    if palette is None:
        return img

    # Find the transparency color index
    trans_index = find_color_index(img, trans_color)

    if trans_index is None or trans_index == 0:
        # Color not found or already at index 0
        return img

    # Create new palette with swapped entries
    new_palette = list(palette)

    # Swap index 0 with trans_index
    idx0 = 0
    idx_trans = trans_index * 3

    # Swap the RGB values
    new_palette[idx0:idx0 + 3], new_palette[idx_trans:idx_trans + 3] = (
        new_palette[idx_trans:idx_trans + 3],
        new_palette[idx0:idx0 + 3],
    )

    # Remap all pixel data
    pixel_data = list(img.getdata())
    new_pixels = []

    for p in pixel_data:
        if p == 0:
            new_pixels.append(trans_index)
        elif p == trans_index:
            new_pixels.append(0)
        else:
            new_pixels.append(p)

    # Create new image with reordered palette
    new_img = Image.new("P", img.size)
    new_img.putdata(new_pixels)
    new_img.putpalette(new_palette)

    return new_img
