# Butano Image Converter

Convert PNG images to Butano GBA-compatible indexed BMP format.

## Features

- Convert RGBA PNG to indexed color BMP (16 or 256 colors)
- Automatic transparency handling (first palette color = transparent)
- Size validation for sprites and backgrounds
- JSON metadata generation for Butano
- **Sprite sheet support** - Split multi-frame images with `--height`
- **Compression options** - LZ77, run-length, huffman, or auto
- **Interactive TUI** for visual file selection and conversion

## Installation

```bash
pip install img2gba
```

With TUI support:

```bash
pip install img2gba[tui]
```

Or with pipx:

```bash
pipx install img2gba[tui]
```

### Development Installation

To install from source for development:

```bash
# Clone the repository
git clone https://github.com/SaraVieira/gba-images.git
cd gba-images

# Create a virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

Each time you open a new terminal, activate the venv with `source venv/bin/activate`.

## Usage

### Basic conversion

```bash
img2gba convert player.png
```

### Specify asset type

```bash
img2gba convert background.png -t regular_bg
```

### Use 16 colors instead of 256

```bash
img2gba convert tiles.png -c 16
```

### Show valid sizes

```bash
img2gba sizes sprite
img2gba sizes regular_bg
img2gba sizes affine_bg
```

### Validate an image

```bash
img2gba validate player.png -t sprite
```

### Convert a sprite sheet

For an image containing multiple animation frames stacked vertically:

```bash
img2gba convert walk_cycle.png -h 32  # Each frame is 32px tall
```

This generates JSON with `"height": 32`, telling Butano to split the image.

### Use compression

Reduce ROM size with compression (processed during Butano build):

```bash
img2gba convert level.png -t regular_bg --compression lz77
```

Available compression options: `none`, `lz77`, `run_length`, `huffman`, `auto`

### Interactive TUI

Launch the terminal user interface for visual file browsing:

```bash
img2gba tui
```

Or use the standalone command:

```bash
img2gba-tui
```

**TUI Features:**
- Browse files with a directory tree
- See image dimensions and validation status in real-time
- Select asset type and color mode
- Configure sprite height and compression
- Convert with a single keypress

**Keyboard shortcuts:**
- `C` - Convert selected file
- `R` - Refresh directory tree
- `Q` - Quit

## Valid Sizes

### Sprites

| Shape  | Sizes                    |
|--------|--------------------------|
| Square | 8x8, 16x16, 32x32, 64x64 |
| Wide   | 16x8, 32x8, 32x16, 64x32 |
| Tall   | 8x16, 8x32, 16x32, 32x64 |

### Regular Backgrounds

256x256, 256x512, 512x256, 512x512

### Affine Backgrounds

128x128, 256x256, 512x512, 1024x1024

## How It Works

1. Loads PNG image (RGB or RGBA)
2. Detects transparent pixels
3. Finds an unused color for transparency
4. Replaces transparent pixels with that color
5. Quantizes to 16 or 256 colors
6. Reorders palette so transparency color is at index 0
7. Saves as uncompressed indexed BMP
8. Generates JSON metadata file

## License

MIT
