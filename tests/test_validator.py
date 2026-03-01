"""
Tests for the validator module.

These tests verify that:
- Valid sizes are recognized correctly
- Invalid sizes are rejected with suggestions
- All asset types work correctly

Run with: pytest tests/test_validator.py -v
"""

import pytest

from img2gba.validator import (
    validate_size,
    get_valid_sizes,
    format_valid_sizes,
    ValidationResult,
)
from img2gba.constants import (
    VALID_SPRITE_SIZES,
    VALID_REGULAR_BG_SIZES,
    VALID_AFFINE_BG_SIZES,
)


class TestValidateSize:
    """Tests for the validate_size() function."""

    # === Sprite size tests ===

    @pytest.mark.parametrize("width,height", VALID_SPRITE_SIZES)
    def test_valid_sprite_sizes(self, width, height):
        """All valid sprite sizes should return valid=True."""
        result = validate_size(width, height, "sprite")
        assert result.valid is True
        assert result.current_size == (width, height)
        assert len(result.suggestions) == 0

    def test_invalid_sprite_size_returns_false(self):
        """Invalid sprite sizes should return valid=False."""
        result = validate_size(100, 100, "sprite")
        assert result.valid is False
        assert result.current_size == (100, 100)

    def test_invalid_sprite_size_has_suggestions(self):
        """Invalid sizes should include up to 3 suggestions."""
        result = validate_size(100, 50, "sprite")
        assert len(result.suggestions) == 3
        # All suggestions should be valid sizes
        for suggestion in result.suggestions:
            assert suggestion in VALID_SPRITE_SIZES

    def test_suggestions_are_closest_sizes(self):
        """Suggestions should be the closest valid sizes."""
        # 65x65 is very close to 64x64
        result = validate_size(65, 65, "sprite")
        # 64x64 should be the first suggestion
        assert result.suggestions[0] == (64, 64)

    # === Regular background size tests ===

    @pytest.mark.parametrize("width,height", VALID_REGULAR_BG_SIZES)
    def test_valid_regular_bg_sizes(self, width, height):
        """All valid regular background sizes should return valid=True."""
        result = validate_size(width, height, "regular_bg")
        assert result.valid is True

    def test_invalid_regular_bg_size(self):
        """Invalid regular background sizes should return valid=False."""
        result = validate_size(300, 300, "regular_bg")
        assert result.valid is False
        assert len(result.suggestions) > 0

    # === Affine background size tests ===

    @pytest.mark.parametrize("width,height", VALID_AFFINE_BG_SIZES)
    def test_valid_affine_bg_sizes(self, width, height):
        """All valid affine background sizes should return valid=True."""
        result = validate_size(width, height, "affine_bg")
        assert result.valid is True

    def test_invalid_affine_bg_size(self):
        """Invalid affine background sizes should return valid=False."""
        result = validate_size(300, 300, "affine_bg")
        assert result.valid is False

    # === Message tests ===

    def test_valid_message_format(self):
        """Valid sizes should have appropriate message."""
        result = validate_size(32, 32, "sprite")
        assert "32x32" in result.message
        assert "valid" in result.message.lower()

    def test_invalid_message_includes_suggestions(self):
        """Invalid sizes should have message with suggestions."""
        result = validate_size(100, 50, "sprite")
        assert "100x50" in result.message
        assert "not valid" in result.message.lower()
        assert "Suggested" in result.message


class TestGetValidSizes:
    """Tests for the get_valid_sizes() function."""

    def test_returns_sprite_sizes(self):
        """Should return sprite sizes for 'sprite' type."""
        sizes = get_valid_sizes("sprite")
        assert sizes == VALID_SPRITE_SIZES

    def test_returns_regular_bg_sizes(self):
        """Should return regular background sizes for 'regular_bg' type."""
        sizes = get_valid_sizes("regular_bg")
        assert sizes == VALID_REGULAR_BG_SIZES

    def test_returns_affine_bg_sizes(self):
        """Should return affine background sizes for 'affine_bg' type."""
        sizes = get_valid_sizes("affine_bg")
        assert sizes == VALID_AFFINE_BG_SIZES

    def test_raises_for_unknown_type(self):
        """Should raise ValueError for unknown asset types."""
        with pytest.raises(ValueError, match="Unknown asset type"):
            get_valid_sizes("unknown_type")


class TestFormatValidSizes:
    """Tests for the format_valid_sizes() function."""

    def test_formats_sprite_sizes(self):
        """Should format sprite sizes as comma-separated string."""
        result = format_valid_sizes("sprite")
        assert "8x8" in result
        assert "64x64" in result
        assert "32x32" in result
        # Check it's comma-separated
        assert ", " in result

    def test_formats_regular_bg_sizes(self):
        """Should format regular background sizes."""
        result = format_valid_sizes("regular_bg")
        assert "256x256" in result
        assert "512x512" in result

    def test_formats_affine_bg_sizes(self):
        """Should format affine background sizes."""
        result = format_valid_sizes("affine_bg")
        assert "128x128" in result
        assert "1024x1024" in result


class TestValidationResult:
    """Tests for the ValidationResult dataclass."""

    def test_dataclass_fields(self):
        """ValidationResult should have expected fields."""
        result = ValidationResult(
            valid=True,
            current_size=(32, 32),
            suggestions=[],
            message="Test message",
        )
        assert result.valid is True
        assert result.current_size == (32, 32)
        assert result.suggestions == []
        assert result.message == "Test message"

    def test_dataclass_equality(self):
        """Two ValidationResults with same data should be equal."""
        result1 = ValidationResult(True, (32, 32), [], "msg")
        result2 = ValidationResult(True, (32, 32), [], "msg")
        assert result1 == result2
