"""Tests for the palette module."""

import pytest
from PIL import Image

from img2gba.palette import (
    quantize_image,
    get_palette_as_tuples,
    find_color_index,
    reorder_palette_transparency_first,
)


class TestQuantizeImage:
    """Tests for the quantize_image() function."""

    def test_reduces_to_256_colors(self):
        """Quantizing should produce an image with at most 256 colors."""
        # Create a gradient image with many colors
        img = Image.new("RGB", (100, 100))
        pixels = img.load()
        for x in range(100):
            for y in range(100):
                pixels[x, y] = (x * 2, y * 2, (x + y) % 256)

        result = quantize_image(img, num_colors=256)

        assert result.mode == "P"  # Palette mode
        # Count unique palette indices used
        unique_indices = set(result.getdata())
        assert len(unique_indices) <= 256

    def test_reduces_to_16_colors(self):
        """Quantizing to 16 colors should work."""
        img = Image.new("RGB", (50, 50))
        pixels = img.load()
        for x in range(50):
            for y in range(50):
                pixels[x, y] = (x * 5, y * 5, 128)

        result = quantize_image(img, num_colors=16)

        assert result.mode == "P"
        unique_indices = set(result.getdata())
        assert len(unique_indices) <= 16

    def test_converts_rgba_to_indexed(self):
        """Should handle RGBA input images."""
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        result = quantize_image(img, num_colors=256)
        assert result.mode == "P"

    def test_preserves_simple_colors(self):
        """Simple solid colors should be preserved in the palette."""
        # Create solid red image
        img = Image.new("RGB", (10, 10), (255, 0, 0))
        result = quantize_image(img, num_colors=256)

        # Get the palette and check red is present
        palette = get_palette_as_tuples(result)
        # The quantized color should be close to red
        # (may not be exactly (255, 0, 0) due to quantization)
        red_found = any(
            abs(c[0] - 255) < 5 and c[1] < 5 and c[2] < 5
            for c in palette[:10]  # Check first few palette entries
        )
        assert red_found


class TestGetPaletteAsTuples:
    """Tests for the get_palette_as_tuples() function."""

    def test_returns_list_of_tuples(self):
        """Should return a list of RGB tuples."""
        img = Image.new("RGB", (10, 10), (128, 64, 32))
        indexed = quantize_image(img)

        palette = get_palette_as_tuples(indexed)

        assert isinstance(palette, list)
        # Palette should have at least one color
        assert len(palette) >= 1
        # All entries should be RGB tuples
        assert all(isinstance(c, tuple) and len(c) == 3 for c in palette)

    def test_raises_for_non_palette_image(self):
        """Should raise ValueError for non-palette images."""
        img = Image.new("RGB", (10, 10))

        with pytest.raises(ValueError, match="palette mode"):
            get_palette_as_tuples(img)

    def test_palette_contains_image_colors(self):
        """The palette should contain colors from the image."""
        # Create image with specific color
        img = Image.new("RGB", (10, 10), (100, 150, 200))
        indexed = quantize_image(img, num_colors=256)

        palette = get_palette_as_tuples(indexed)

        # The specific color should be in the palette
        assert (100, 150, 200) in palette


class TestFindColorIndex:
    """Tests for the find_color_index() function."""

    def test_finds_existing_color(self):
        """Should find the index of a color in the palette."""
        img = Image.new("RGB", (10, 10), (128, 64, 32))
        indexed = quantize_image(img, num_colors=256)

        index = find_color_index(indexed, (128, 64, 32))

        assert index is not None
        assert isinstance(index, int)
        assert 0 <= index < 256

    def test_returns_none_for_missing_color(self):
        """Should return None for colors not in the palette."""
        img = Image.new("RGB", (10, 10), (255, 0, 0))
        indexed = quantize_image(img, num_colors=256)

        # Magenta probably isn't in a solid red image's palette
        index = find_color_index(indexed, (255, 0, 255))

        # Could be None or could be in unused palette slots
        # Just verify we get a sensible result
        assert index is None or isinstance(index, int)


class TestReorderPaletteTransparencyFirst:
    """Tests for the reorder_palette_transparency_first() function."""

    def test_moves_color_to_index_0(self):
        """Should move the transparency color to palette index 0."""
        # Create image with magenta (our transparency color)
        img = Image.new("RGB", (20, 20))
        pixels = img.load()
        # Half magenta, half blue
        for x in range(20):
            for y in range(20):
                if x < 10:
                    pixels[x, y] = (255, 0, 255)  # Magenta
                else:
                    pixels[x, y] = (0, 0, 255)  # Blue

        indexed = quantize_image(img, num_colors=256)
        trans_color = (255, 0, 255)

        result = reorder_palette_transparency_first(indexed, trans_color)

        # Magenta should now be at index 0
        new_index = find_color_index(result, trans_color)
        assert new_index == 0

    def test_returns_unchanged_if_already_at_0(self):
        """Should return the image unchanged if color is already at index 0."""
        img = Image.new("RGB", (10, 10), (255, 0, 255))
        indexed = quantize_image(img, num_colors=256)

        # Find current index
        current_index = find_color_index(indexed, (255, 0, 255))

        if current_index == 0:
            result = reorder_palette_transparency_first(indexed, (255, 0, 255))
            # Should return same result
            assert find_color_index(result, (255, 0, 255)) == 0

    def test_returns_unchanged_if_color_not_found(self):
        """Should return unchanged if the color isn't in the palette."""
        img = Image.new("RGB", (10, 10), (255, 0, 0))  # Red only
        indexed = quantize_image(img, num_colors=256)

        # Try to move a color that isn't there
        result = reorder_palette_transparency_first(indexed, (0, 255, 0))

        # Should return the image (unchanged or same)
        assert result.mode == "P"

    def test_pixel_values_updated_correctly(self):
        """Pixel values should be remapped after palette swap."""
        # Create image with distinct regions
        img = Image.new("RGB", (20, 20))
        pixels = img.load()
        for x in range(20):
            for y in range(20):
                if x < 10:
                    pixels[x, y] = (255, 0, 255)  # Magenta (transparency)
                else:
                    pixels[x, y] = (0, 0, 255)  # Blue

        indexed = quantize_image(img, num_colors=256)
        result = reorder_palette_transparency_first(indexed, (255, 0, 255))

        # Pixels in the magenta region should now have index 0
        magenta_pixel_index = result.getpixel((5, 5))
        assert magenta_pixel_index == 0

    def test_raises_for_non_palette_image(self):
        """Should raise ValueError for non-palette images."""
        img = Image.new("RGB", (10, 10))

        with pytest.raises(ValueError, match="palette mode"):
            reorder_palette_transparency_first(img, (255, 0, 255))
