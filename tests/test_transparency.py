"""Tests for the transparency module."""

import pytest
from PIL import Image

from img2gba.transparency import (
    has_transparency,
    find_unused_color,
    replace_transparent_pixels,
)
from img2gba.constants import DEFAULT_TRANSPARENCY_COLORS


class TestHasTransparency:
    """Tests for the has_transparency() function."""

    def test_fully_opaque_image_returns_false(self):
        """An image with all pixels at alpha=255 should return False."""
        # Create a 10x10 fully opaque red image
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        assert has_transparency(img) is False

    def test_fully_transparent_image_returns_true(self):
        """An image with all pixels at alpha=0 should return True."""
        # Create a 10x10 fully transparent image
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        assert has_transparency(img) is True

    def test_single_transparent_pixel_returns_true(self):
        """An image with just one transparent pixel should return True."""
        # Create opaque image
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        # Make one pixel transparent
        img.putpixel((5, 5), (0, 0, 0, 0))
        assert has_transparency(img) is True

    def test_semi_transparent_pixel_returns_true(self):
        """An image with a semi-transparent pixel (alpha < 255) should return True."""
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        # Make one pixel semi-transparent (alpha=128)
        img.putpixel((5, 5), (255, 0, 0, 128))
        assert has_transparency(img) is True

    def test_rgb_image_returns_false(self):
        """An RGB image (no alpha channel) should return False."""
        img = Image.new("RGB", (10, 10), (255, 0, 0))
        assert has_transparency(img) is False

    def test_grayscale_image_returns_false(self):
        """A grayscale image should return False."""
        img = Image.new("L", (10, 10), 128)
        assert has_transparency(img) is False


class TestFindUnusedColor:
    """Tests for the find_unused_color() function."""

    def test_returns_magenta_for_simple_image(self):
        """For an image not using magenta, should return magenta."""
        # Create solid red image (doesn't use magenta)
        img = Image.new("RGB", (10, 10), (255, 0, 0))
        color = find_unused_color(img)
        # Magenta is the first default candidate
        assert color == (255, 0, 255)

    def test_skips_used_colors(self):
        """If magenta is used, should return the next candidate."""
        # Create image using magenta
        img = Image.new("RGB", (10, 10), (255, 0, 255))
        color = find_unused_color(img)
        # Should be cyan (second candidate)
        assert color == (0, 255, 255)

    def test_finds_unused_when_many_candidates_used(self):
        """Should find an unused color even when many candidates are used."""
        # Create image and manually add all default candidate colors
        img = Image.new("RGB", (100, 100), (128, 128, 128))
        pixels = img.load()

        # Add each default transparency color to the image
        for i, color in enumerate(DEFAULT_TRANSPARENCY_COLORS):
            pixels[i, 0] = color

        # Should still find a color (might be random)
        color = find_unused_color(img)
        # Verify it's not one of the used colors
        used_colors = set(img.getdata())
        assert color not in used_colors

    def test_works_with_rgba_image(self):
        """Should work with RGBA images (converts internally)."""
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        color = find_unused_color(img)
        assert color == (255, 0, 255)


class TestReplaceTransparentPixels:
    """Tests for the replace_transparent_pixels() function."""

    def test_replaces_fully_transparent_pixels(self):
        """Fully transparent pixels should be replaced."""
        # Create image with transparent center
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        img.putpixel((5, 5), (0, 0, 0, 0))  # Transparent pixel

        result = replace_transparent_pixels(img, (255, 0, 255))

        # The transparent pixel should now be magenta
        assert result.getpixel((5, 5)) == (255, 0, 255, 255)
        # Other pixels should be unchanged
        assert result.getpixel((0, 0)) == (255, 0, 0, 255)

    def test_replaces_semi_transparent_below_threshold(self):
        """Pixels with alpha below threshold should be replaced."""
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        img.putpixel((5, 5), (100, 100, 100, 64))  # Alpha = 64 < 128

        result = replace_transparent_pixels(img, (255, 0, 255), threshold=128)

        assert result.getpixel((5, 5)) == (255, 0, 255, 255)

    def test_keeps_semi_transparent_above_threshold(self):
        """Pixels with alpha at or above threshold should be kept."""
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        img.putpixel((5, 5), (100, 100, 100, 200))  # Alpha = 200 > 128

        result = replace_transparent_pixels(img, (255, 0, 255), threshold=128)

        # Should keep original color (with alpha)
        assert result.getpixel((5, 5)) == (100, 100, 100, 200)

    def test_custom_threshold(self):
        """Custom threshold should be respected."""
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        img.putpixel((5, 5), (100, 100, 100, 200))  # Alpha = 200

        # With threshold 250, this pixel should be replaced
        result = replace_transparent_pixels(img, (255, 0, 255), threshold=250)
        assert result.getpixel((5, 5)) == (255, 0, 255, 255)

    def test_does_not_modify_original(self):
        """The original image should not be modified."""
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        img.putpixel((5, 5), (0, 0, 0, 0))
        original_pixel = img.getpixel((5, 5))

        replace_transparent_pixels(img, (255, 0, 255))

        # Original should be unchanged
        assert img.getpixel((5, 5)) == original_pixel

    def test_converts_rgb_to_rgba(self):
        """Should convert RGB images to RGBA before processing."""
        img = Image.new("RGB", (10, 10), (255, 0, 0))
        result = replace_transparent_pixels(img, (255, 0, 255))

        # Should return RGBA image
        assert result.mode == "RGBA"
        # No pixels should be replaced (RGB has no transparency)
        assert result.getpixel((5, 5)) == (255, 0, 0, 255)
