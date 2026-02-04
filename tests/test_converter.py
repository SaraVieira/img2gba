"""
Tests for the converter module.

These tests verify the complete conversion pipeline:
- Loading images
- Handling transparency
- Quantizing colors
- Saving output files
- Generating JSON metadata

Run with: pytest tests/test_converter.py -v
"""

import pytest
from pathlib import Path
from PIL import Image

from butano_img.converter import convert_image, ConversionResult


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def sample_sprite(temp_dir):
    """Create a sample 32x32 sprite with transparency."""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))  # Fully transparent
    pixels = img.load()

    # Draw a colored square in the center (16x16)
    for x in range(8, 24):
        for y in range(8, 24):
            pixels[x, y] = (255, 0, 0, 255)  # Solid red

    path = temp_dir / "sprite.png"
    img.save(path)
    return path


@pytest.fixture
def sample_opaque_image(temp_dir):
    """Create a sample opaque image (no transparency)."""
    img = Image.new("RGB", (32, 32), (100, 150, 200))
    path = temp_dir / "opaque.png"
    img.save(path)
    return path


@pytest.fixture
def sample_gradient(temp_dir):
    """Create a gradient image with many colors."""
    img = Image.new("RGB", (64, 64))
    pixels = img.load()
    for x in range(64):
        for y in range(64):
            pixels[x, y] = (x * 4, y * 4, (x + y) * 2)
    path = temp_dir / "gradient.png"
    img.save(path)
    return path


class TestConvertImage:
    """Tests for the convert_image() function."""

    def test_basic_conversion(self, sample_sprite, temp_dir):
        """Basic conversion should produce BMP and JSON files."""
        result = convert_image(sample_sprite)

        assert result.success is True
        assert result.output_path.exists()
        assert result.output_path.suffix == ".bmp"
        assert result.json_path is not None
        assert result.json_path.exists()

    def test_output_path_override(self, sample_sprite, temp_dir):
        """Should respect custom output path."""
        custom_output = temp_dir / "custom_output.bmp"
        result = convert_image(sample_sprite, output_path=custom_output)

        assert result.output_path == custom_output
        assert custom_output.exists()

    def test_transparency_detected(self, sample_sprite):
        """Transparent images should have transparency_color set."""
        result = convert_image(sample_sprite)

        assert result.transparency_color is not None
        # Should be an RGB tuple
        assert len(result.transparency_color) == 3
        assert all(0 <= c <= 255 for c in result.transparency_color)

    def test_no_transparency_for_opaque(self, sample_opaque_image):
        """Opaque images should have transparency_color=None."""
        result = convert_image(sample_opaque_image)

        assert result.transparency_color is None

    def test_custom_transparency_color(self, sample_sprite):
        """Should use custom transparency color when specified."""
        custom_color = (0, 255, 255)  # Cyan
        result = convert_image(sample_sprite, trans_color=custom_color)

        assert result.transparency_color == custom_color

    def test_disable_transparency_handling(self, sample_sprite):
        """Should skip transparency when handle_transparency=False."""
        result = convert_image(sample_sprite, handle_transparency=False)

        assert result.transparency_color is None

    def test_16_color_mode(self, sample_gradient):
        """Should quantize to 16 colors when specified."""
        result = convert_image(sample_gradient, num_colors=16)

        assert result.num_colors == 16
        # Check the output is actually indexed
        output_img = Image.open(result.output_path)
        assert output_img.mode == "P"

    def test_256_color_mode(self, sample_gradient):
        """Should quantize to 256 colors (default)."""
        result = convert_image(sample_gradient, num_colors=256)

        assert result.num_colors == 256

    def test_skip_json_generation(self, sample_sprite):
        """Should skip JSON when generate_json_file=False."""
        result = convert_image(sample_sprite, generate_json_file=False)

        assert result.json_path is None

    def test_asset_type_in_validation(self, sample_sprite):
        """Validation should use the specified asset type."""
        result = convert_image(sample_sprite, asset_type="sprite")

        # 32x32 is valid for sprite
        assert result.validation.valid is True

    def test_invalid_size_produces_warning(self, temp_dir):
        """Invalid sizes should produce a validation warning."""
        # Create image with invalid sprite size
        img = Image.new("RGB", (100, 50), (255, 0, 0))
        path = temp_dir / "invalid_size.png"
        img.save(path)

        result = convert_image(path, asset_type="sprite")

        assert result.validation.valid is False
        assert len(result.validation.suggestions) > 0

    def test_regular_bg_asset_type(self, temp_dir):
        """Should handle regular_bg asset type."""
        img = Image.new("RGB", (256, 256), (0, 100, 200))
        path = temp_dir / "bg.png"
        img.save(path)

        result = convert_image(path, asset_type="regular_bg")

        assert result.success is True
        assert result.validation.valid is True

    def test_affine_bg_asset_type(self, temp_dir):
        """Should handle affine_bg asset type."""
        img = Image.new("RGB", (128, 128), (200, 100, 50))
        path = temp_dir / "affine.png"
        img.save(path)

        result = convert_image(path, asset_type="affine_bg")

        assert result.success is True
        assert result.validation.valid is True


class TestConversionResult:
    """Tests for the ConversionResult dataclass."""

    def test_result_fields(self, sample_sprite):
        """ConversionResult should have all expected fields."""
        result = convert_image(sample_sprite)

        assert hasattr(result, "success")
        assert hasattr(result, "output_path")
        assert hasattr(result, "json_path")
        assert hasattr(result, "validation")
        assert hasattr(result, "transparency_color")
        assert hasattr(result, "num_colors")
        assert hasattr(result, "message")

    def test_result_message(self, sample_sprite):
        """Result message should describe the conversion."""
        result = convert_image(sample_sprite)

        assert "sprite" in result.message.lower() or "converted" in result.message.lower()


class TestOutputFileFormat:
    """Tests for the output file format."""

    def test_output_is_indexed_bmp(self, sample_sprite):
        """Output should be an indexed (palette) BMP."""
        result = convert_image(sample_sprite)
        output_img = Image.open(result.output_path)

        assert output_img.format == "BMP"
        assert output_img.mode == "P"  # Palette mode

    def test_output_has_palette(self, sample_sprite):
        """Output should have a palette."""
        result = convert_image(sample_sprite)
        output_img = Image.open(result.output_path)

        palette = output_img.getpalette()
        assert palette is not None
        # Palette should have at least some colors (length divisible by 3 for RGB)
        assert len(palette) >= 3
        assert len(palette) % 3 == 0

    def test_transparency_at_index_0(self, sample_sprite):
        """Transparency color should be at palette index 0."""
        result = convert_image(sample_sprite)

        if result.transparency_color:
            output_img = Image.open(result.output_path)
            palette = output_img.getpalette()
            # First 3 values should be our transparency color
            index_0_color = (palette[0], palette[1], palette[2])
            assert index_0_color == result.transparency_color


class TestJSONOutput:
    """Tests for JSON metadata output."""

    def test_json_has_type_field(self, sample_sprite):
        """JSON should have 'type' field."""
        import json

        result = convert_image(sample_sprite, asset_type="sprite")

        with open(result.json_path) as f:
            data = json.load(f)

        assert "type" in data
        assert data["type"] == "sprite"

    def test_json_has_bpp_mode(self, sample_sprite):
        """JSON should have 'bpp_mode' field."""
        import json

        result = convert_image(sample_sprite, num_colors=256)

        with open(result.json_path) as f:
            data = json.load(f)

        assert "bpp_mode" in data
        assert data["bpp_mode"] == "bpp_8"

    def test_json_bpp_4_for_16_colors(self, sample_sprite):
        """JSON should have bpp_4 for 16-color mode."""
        import json

        result = convert_image(sample_sprite, num_colors=16)

        with open(result.json_path) as f:
            data = json.load(f)

        assert data["bpp_mode"] == "bpp_4"
