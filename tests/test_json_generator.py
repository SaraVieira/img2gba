"""
Tests for the JSON generator module.

These tests verify that:
- JSON files are generated with the correct structure
- Height option is included for sprite sheets
- Compression option is included when specified
- BPP mode is correctly set

Run with: pytest tests/test_json_generator.py -v
"""

import json
import pytest
from pathlib import Path
import tempfile
import os

from img2gba.json_generator import generate_json, read_json


class TestGenerateJsonBasic:
    """Tests for basic JSON generation."""

    def test_generates_json_file(self, tmp_path):
        """Should create a JSON file alongside the BMP."""
        bmp_path = tmp_path / "sprite.bmp"
        bmp_path.touch()  # Create empty file

        json_path = generate_json(bmp_path, "sprite")

        assert json_path.exists()
        assert json_path.suffix == ".json"
        assert json_path.stem == "sprite"

    def test_contains_type_field(self, tmp_path):
        """Generated JSON should contain the type field."""
        bmp_path = tmp_path / "test.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "sprite")
        data = read_json(json_path)

        assert "type" in data
        assert data["type"] == "sprite"

    def test_sprite_type(self, tmp_path):
        """Should generate JSON with sprite type."""
        bmp_path = tmp_path / "test.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "sprite")
        data = read_json(json_path)

        assert data["type"] == "sprite"

    def test_regular_bg_type(self, tmp_path):
        """Should generate JSON with regular_bg type."""
        bmp_path = tmp_path / "test.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "regular_bg")
        data = read_json(json_path)

        assert data["type"] == "regular_bg"

    def test_affine_bg_type(self, tmp_path):
        """Should generate JSON with affine_bg type."""
        bmp_path = tmp_path / "test.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "affine_bg")
        data = read_json(json_path)

        assert data["type"] == "affine_bg"


class TestBppMode:
    """Tests for BPP mode in JSON generation."""

    def test_bpp_4_mode(self, tmp_path):
        """Should generate bpp_4 for 4-bit mode."""
        bmp_path = tmp_path / "test.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "sprite", bpp=4)
        data = read_json(json_path)

        assert data["bpp_mode"] == "bpp_4"

    def test_bpp_8_mode(self, tmp_path):
        """Should generate bpp_8 for 8-bit mode."""
        bmp_path = tmp_path / "test.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "sprite", bpp=8)
        data = read_json(json_path)

        assert data["bpp_mode"] == "bpp_8"

    def test_no_bpp_when_not_specified(self, tmp_path):
        """Should not include bpp_mode when not specified."""
        bmp_path = tmp_path / "test.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "sprite")
        data = read_json(json_path)

        assert "bpp_mode" not in data


class TestSpriteHeight:
    """Tests for sprite height (sprite sheet) option."""

    def test_height_included_when_specified(self, tmp_path):
        """Should include height when specified."""
        bmp_path = tmp_path / "spritesheet.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "sprite", height=32)
        data = read_json(json_path)

        assert "height" in data
        assert data["height"] == 32

    def test_height_not_included_when_none(self, tmp_path):
        """Should not include height when not specified."""
        bmp_path = tmp_path / "sprite.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "sprite")
        data = read_json(json_path)

        assert "height" not in data

    def test_height_with_different_values(self, tmp_path):
        """Should work with various height values."""
        for height in [8, 16, 32, 64, 128]:
            bmp_path = tmp_path / f"sheet_{height}.bmp"
            bmp_path.touch()

            json_path = generate_json(bmp_path, "sprite", height=height)
            data = read_json(json_path)

            assert data["height"] == height

    def test_height_with_bpp(self, tmp_path):
        """Should include both height and bpp_mode."""
        bmp_path = tmp_path / "spritesheet.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "sprite", bpp=4, height=32)
        data = read_json(json_path)

        assert data["height"] == 32
        assert data["bpp_mode"] == "bpp_4"


class TestCompression:
    """Tests for compression option."""

    def test_lz77_compression(self, tmp_path):
        """Should include lz77 compression."""
        bmp_path = tmp_path / "test.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "regular_bg", compression="lz77")
        data = read_json(json_path)

        assert data["compression"] == "lz77"

    def test_run_length_compression(self, tmp_path):
        """Should include run_length compression."""
        bmp_path = tmp_path / "test.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "regular_bg", compression="run_length")
        data = read_json(json_path)

        assert data["compression"] == "run_length"

    def test_huffman_compression(self, tmp_path):
        """Should include huffman compression."""
        bmp_path = tmp_path / "test.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "regular_bg", compression="huffman")
        data = read_json(json_path)

        assert data["compression"] == "huffman"

    def test_auto_compression(self, tmp_path):
        """Should include auto compression."""
        bmp_path = tmp_path / "test.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "regular_bg", compression="auto")
        data = read_json(json_path)

        assert data["compression"] == "auto"

    def test_none_compression_not_included(self, tmp_path):
        """Should not include compression field when set to 'none'."""
        bmp_path = tmp_path / "test.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "sprite", compression="none")
        data = read_json(json_path)

        assert "compression" not in data

    def test_no_compression_when_not_specified(self, tmp_path):
        """Should not include compression when not specified."""
        bmp_path = tmp_path / "sprite.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "sprite")
        data = read_json(json_path)

        assert "compression" not in data


class TestCombinedOptions:
    """Tests for combining multiple options."""

    def test_all_options_combined(self, tmp_path):
        """Should correctly combine all options."""
        bmp_path = tmp_path / "complex.bmp"
        bmp_path.touch()

        json_path = generate_json(
            bmp_path,
            "sprite",
            bpp=4,
            height=32,
            compression="lz77",
        )
        data = read_json(json_path)

        assert data["type"] == "sprite"
        assert data["bpp_mode"] == "bpp_4"
        assert data["height"] == 32
        assert data["compression"] == "lz77"

    def test_extra_fields_still_work(self, tmp_path):
        """Should still support extra_fields parameter."""
        bmp_path = tmp_path / "custom.bmp"
        bmp_path.touch()

        json_path = generate_json(
            bmp_path,
            "sprite",
            height=32,
            extra_fields={"custom_field": "value"},
        )
        data = read_json(json_path)

        assert data["height"] == 32
        assert data["custom_field"] == "value"


class TestReadJson:
    """Tests for the read_json function."""

    def test_reads_generated_json(self, tmp_path):
        """Should read back what was generated."""
        bmp_path = tmp_path / "test.bmp"
        bmp_path.touch()

        json_path = generate_json(bmp_path, "sprite", bpp=8, height=64)
        data = read_json(json_path)

        assert data["type"] == "sprite"
        assert data["bpp_mode"] == "bpp_8"
        assert data["height"] == 64

    def test_raises_for_missing_file(self, tmp_path):
        """Should raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            read_json(tmp_path / "nonexistent.json")
