# Butano Image Converter

Convert PNG images to Butano GBA-compatible indexed BMP format.

## Features

- Convert RGBA PNG to indexed color BMP (16 or 256 colors)
- Automatic transparency handling (first palette color = transparent)
- Size validation for sprites and backgrounds
- JSON metadata generation for Butano
- **Interactive TUI** for visual file selection and conversion

## Installation

```bash
pip install butano-img
```

With TUI support:

```bash
pip install butano-img[tui]
```

Or with pipx:

```bash
pipx install butano-img[tui]
```

## Usage

### Basic conversion

```bash
butano-img convert player.png
```

### Specify asset type

```bash
butano-img convert background.png -t regular_bg
```

### Use 16 colors instead of 256

```bash
butano-img convert tiles.png -c 16
```

### Show valid sizes

```bash
butano-img sizes sprite
butano-img sizes regular_bg
butano-img sizes affine_bg
```

### Validate an image

```bash
butano-img validate player.png -t sprite
```

### Interactive TUI

Launch the terminal user interface for visual file browsing and conversion:

```bash
butano-img tui
```

Or use the standalone command:

```bash
butano-img-tui
```

**TUI Features:**
- Browse files with a directory tree
- See image dimensions and validation status in real-time
- Select asset type and color mode with radio buttons
- Convert with a single keypress
- View output log with conversion results

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
