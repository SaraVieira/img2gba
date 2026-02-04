# Butano Image Converter - Implementation Plan

A Python CLI/TUI tool to convert PNG images to Butano-compatible BMP files with proper indexed colors, transparency handling, and JSON generation.

---

## Goals

1. **Take a PNG file** (RGB/RGBA) as input
2. **Convert to indexed color** (16 or 256 colors)
3. **Handle transparency** - detect transparent pixels, assign a unique color, place it at palette index 0
4. **Warn about invalid sizes** - check against valid sprite/background dimensions
5. **Generate JSON metadata** - create the required `.json` file alongside the `.bmp`
6. **Output clean BMP** - uncompressed, no ICC profiles, compatible with grit

---

## Technology Stack

**Python + Pillow + Click → Textual TUI**

| Component | Library | Purpose |
|-----------|---------|---------|
| Image Processing | Pillow | Palette manipulation, quantization, BMP output |
| CLI | Click | Command-line interface |
| TUI | Textual | Interactive terminal UI (Phase 2) |

### Why Python + Pillow?

Pillow provides everything we need for indexed color manipulation:

| Requirement | Pillow Support |
|-------------|----------------|
| Write indexed BMP | ✅ Yes |
| Quantize to 16/256 colors | ✅ `quantize()` |
| Access palette array | ✅ `getpalette()` |
| Reorder palette | ✅ `putpalette()` |
| Set transparency index | ✅ Via palette position |
| Control bit depth | ✅ 4bpp/8bpp |

---

## Distribution

Users can install via multiple methods:

| Method | Command | Notes |
|--------|---------|-------|
| **Homebrew** | `brew install butano-img` | macOS/Linux, manages Python |
| **pipx** | `pipx install butano-img` | Isolated environment |
| **PyPI** | `pip install butano-img` | Standard Python install |
| **Standalone** | Download binary | PyInstaller bundle (~20MB) |

### Homebrew Formula (Future)

```ruby
class ButanoImg < Formula
  include Language::Python::Virtualenv

  desc "Convert images to Butano GBA format"
  homepage "https://github.com/user/butano-img"
  url "https://files.pythonhosted.org/packages/.../butano-img-0.1.0.tar.gz"

  depends_on "python@3.12"

  resource "pillow" do
    url "https://files.pythonhosted.org/packages/.../pillow-10.0.0.tar.gz"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/.../click-8.0.0.tar.gz"
  end

  def install
    virtualenv_install_with_resources
  end
end
```

---

## Core Algorithm

### Step 1: Load and Analyze PNG

```python
from PIL import Image

img = Image.open("input.png").convert("RGBA")
has_transparency = any(pixel[3] < 255 for pixel in img.getdata())
```

### Step 2: Generate Unique Transparency Color

If the image has transparency, find a color NOT used in the image:

```python
def find_unused_color(img):
    used_colors = set((r, g, b) for r, g, b, a in img.getdata())
    # Try magenta first (common transparency color)
    candidates = [(255, 0, 255), (0, 255, 255), (255, 255, 0)]
    for color in candidates:
        if color not in used_colors:
            return color
    # Generate random color if all candidates used
    import random
    while True:
        color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
        if color not in used_colors:
            return color
```

### Step 3: Replace Transparent Pixels

```python
def replace_transparency(img, trans_color):
    pixels = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]
            if a < 128:  # Consider as transparent
                pixels[x, y] = (*trans_color, 255)
    return img
```

### Step 4: Quantize to Indexed Colors

```python
def quantize_image(img, num_colors=256):
    # Convert to RGB (remove alpha channel)
    rgb_img = img.convert("RGB")
    # Quantize to palette
    indexed = rgb_img.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)
    return indexed
```

### Step 5: Reorder Palette (Transparency First)

```python
def reorder_palette_transparency_first(img, trans_color):
    palette = img.getpalette()  # Flat RGB list [r,g,b,r,g,b,...]

    # Find index of transparency color
    trans_index = None
    for i in range(0, len(palette), 3):
        if (palette[i], palette[i+1], palette[i+2]) == trans_color:
            trans_index = i // 3
            break

    if trans_index is None or trans_index == 0:
        return img  # Already first or not found

    # Swap palette entries
    new_palette = list(palette)
    new_palette[0:3], new_palette[trans_index*3:trans_index*3+3] = \
        new_palette[trans_index*3:trans_index*3+3], new_palette[0:3]

    # Remap pixel data
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
    new_img = Image.new('P', img.size)
    new_img.putdata(new_pixels)
    new_img.putpalette(new_palette)

    return new_img
```

### Step 6: Validate Dimensions

```python
VALID_SPRITE_SIZES = [
    (8, 8), (16, 16), (32, 32), (64, 64),      # Square
    (16, 8), (32, 8), (32, 16), (64, 32),      # Wide
    (8, 16), (8, 32), (16, 32), (32, 64),      # Tall
]

VALID_REGULAR_BG_SIZES = [
    (256, 256), (256, 512), (512, 256), (512, 512)
]

VALID_AFFINE_BG_SIZES = [
    (128, 128), (256, 256), (512, 512), (1024, 1024)
]

def validate_size(width, height, asset_type="sprite"):
    if asset_type == "sprite":
        valid = VALID_SPRITE_SIZES
    elif asset_type == "regular_bg":
        valid = VALID_REGULAR_BG_SIZES
    elif asset_type == "affine_bg":
        valid = VALID_AFFINE_BG_SIZES

    if (width, height) in valid:
        return {"valid": True}

    # Find closest valid size
    suggestions = sorted(valid, key=lambda s: abs(s[0]-width) + abs(s[1]-height))
    return {
        "valid": False,
        "current": (width, height),
        "suggestions": suggestions[:3]
    }
```

### Step 7: Save as BMP

```python
def save_bmp(img, output_path):
    # Pillow saves uncompressed BMP by default for P mode
    img.save(output_path, "BMP")
```

### Step 8: Generate JSON

```python
import json

def generate_json(output_path, asset_type="sprite", **options):
    json_path = output_path.replace(".bmp", ".json")

    data = {"type": asset_type}

    # Add optional fields
    if "bpp" in options:
        data["bpp_mode"] = f"bpp_{options['bpp']}"

    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)
```

---

## CLI Interface Design

```
butano-img convert input.png [OPTIONS]

Options:
  -o, --output PATH      Output path (default: same as input with .bmp)
  -t, --type TYPE        Asset type: sprite, regular_bg, affine_bg (default: sprite)
  -c, --colors INT       Number of colors: 16 or 256 (default: 256)
  --no-transparency      Don't handle transparency
  --trans-color R,G,B    Force specific transparency color
  --resize               Auto-resize to nearest valid size
  --json / --no-json     Generate JSON file (default: yes)
  -v, --verbose          Show detailed output

Examples:
  butano-img convert player.png
  butano-img convert background.png -t regular_bg -c 256
  butano-img convert tiles.png -c 16 --resize
```

---

## TUI Interface Design (Phase 2)

Using **Textual** for a modern Python TUI:

```
┌─────────────────────────────────────────────────────────┐
│  BUTANO IMAGE CONVERTER                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Input:  player.png                          [Browse]   │
│  Output: player.bmp                                     │
│                                                         │
│  ┌─ Asset Type ─────┐  ┌─ Colors ─────┐                │
│  │ ● Sprite         │  │ ○ 16 colors  │                │
│  │ ○ Regular BG     │  │ ● 256 colors │                │
│  │ ○ Affine BG      │  └──────────────┘                │
│  └──────────────────┘                                   │
│                                                         │
│  ⚠ Warning: Size 100x50 is not valid for sprites       │
│    Suggested sizes: 64x32, 64x64, 32x32                │
│    [ ] Auto-resize to nearest valid size               │
│                                                         │
│  [✓] Generate JSON file                                │
│  [✓] Handle transparency (first palette color)         │
│                                                         │
│  Preview:                                               │
│  ┌────────────┐  Palette:                              │
│  │            │  [#] [#] [#] [#] [#] [#] [#] [#]       │
│  │   (image)  │  [#] [#] [#] [#] [#] [#] [#] [#]       │
│  │            │  First color: RGB(255,0,255) TRANS     │
│  └────────────┘                                         │
│                                                         │
│              [ CONVERT ]    [ Cancel ]                  │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: CLI (MVP)
- [ ] Project setup (pyproject.toml, structure)
- [ ] Core conversion logic with Pillow
- [ ] Transparency detection and handling
- [ ] Palette reordering (transparency first)
- [ ] Size validation with warnings
- [ ] JSON generation
- [ ] CLI with Click
- [ ] Basic tests

### Phase 2: TUI
- [ ] Add Textual dependency
- [ ] File browser widget
- [ ] Options panel
- [ ] Preview display
- [ ] Palette visualization
- [ ] Batch processing

### Phase 3: Distribution
- [ ] PyPI package
- [ ] Homebrew formula
- [ ] PyInstaller standalone builds
- [ ] GitHub releases

---

## File Structure

```
butano-img/
├── src/
│   └── butano_img/
│       ├── __init__.py
│       ├── cli.py              # Click CLI entry point
│       ├── converter.py        # Main conversion orchestration
│       ├── palette.py          # Palette manipulation utilities
│       ├── transparency.py     # Transparency handling
│       ├── validator.py        # Size validation
│       ├── json_generator.py   # JSON file creation
│       └── constants.py        # Valid sizes, defaults
├── tests/
│   ├── test_converter.py
│   ├── test_palette.py
│   └── fixtures/               # Test images
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## Dependencies

```toml
[project]
name = "butano-img"
version = "0.1.0"
description = "Convert images to Butano GBA format"
requires-python = ">=3.10"
dependencies = [
    "Pillow>=10.0.0",
    "click>=8.0.0",
]

[project.optional-dependencies]
tui = [
    "textual>=0.40.0",
]
dev = [
    "pytest>=7.0.0",
    "pytest-cov",
]

[project.scripts]
butano-img = "butano_img.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## Success Criteria

1. ✅ Convert a 32-bit RGBA PNG to 8-bit indexed BMP
2. ✅ Transparent pixels mapped to palette index 0
3. ✅ Output BMP compiles successfully with Butano/grit
4. ✅ JSON file generated with correct structure
5. ✅ Warnings shown for invalid sprite/background sizes
6. ✅ Works on Windows, macOS, Linux
7. ✅ Installable via pip/pipx/brew

---

## References

- [Pillow Documentation](https://pillow.readthedocs.io/en/stable/)
- [Click Documentation](https://click.palletsprojects.com/)
- [Textual Documentation](https://textual.textualize.io/)
- [Butano Import Docs](https://gvaliente.github.io/butano/import.html)
