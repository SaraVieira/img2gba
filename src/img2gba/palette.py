"""Palette quantization and reordering for GBA indexed images."""

from PIL import Image


def quantize_image(
    img: Image.Image,
    num_colors: int = 256,
    method: int = Image.Quantize.MEDIANCUT,
) -> Image.Image:
    """Reduce an image's colors to a limited palette (16 or 256 for GBA)."""
    rgb_img = img.convert("RGB")
    return rgb_img.quantize(colors=num_colors, method=method)


def get_palette_as_tuples(img: Image.Image) -> list[tuple[int, int, int]]:
    """Get the image's palette as a list of (R, G, B) tuples."""
    if img.mode != "P":
        raise ValueError(
            f"Image must be in palette mode (P), but got mode '{img.mode}'"
        )

    palette = img.getpalette()
    if palette is None:
        return []

    colors: list[tuple[int, int, int]] = []
    for i in range(0, len(palette), 3):
        colors.append((palette[i], palette[i + 1], palette[i + 2]))
    return colors


def find_color_index(img: Image.Image, color: tuple[int, int, int]) -> int | None:
    """Find which palette index contains a specific color, or None."""
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
    """Swap palette so the transparency color is at index 0 (where GBA expects it)."""
    if img.mode != "P":
        raise ValueError(
            f"Image must be in palette mode (P), but got mode '{img.mode}'"
        )

    palette = img.getpalette()
    if palette is None:
        return img

    trans_index = find_color_index(img, trans_color)
    if trans_index is None or trans_index == 0:
        return img

    # Swap palette entries
    new_palette = list(palette)
    byte_offset_0 = 0
    byte_offset_trans = trans_index * 3

    (
        new_palette[byte_offset_0 : byte_offset_0 + 3],
        new_palette[byte_offset_trans : byte_offset_trans + 3],
    ) = (
        new_palette[byte_offset_trans : byte_offset_trans + 3],
        new_palette[byte_offset_0 : byte_offset_0 + 3],
    )

    # Remap pixel indices
    pixel_data = list(img.getdata())
    new_pixels = []
    for pixel_index in pixel_data:
        if pixel_index == 0:
            new_pixels.append(trans_index)
        elif pixel_index == trans_index:
            new_pixels.append(0)
        else:
            new_pixels.append(pixel_index)

    new_img = Image.new("P", img.size)
    new_img.putdata(new_pixels)
    new_img.putpalette(new_palette)
    return new_img
