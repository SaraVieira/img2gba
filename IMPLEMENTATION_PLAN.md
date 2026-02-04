# Butano Image Converter - Implementation Plan

A tool to convert PNG images to Butano-compatible BMP files with proper indexed colors, transparency handling, and JSON generation.

---

## Goals

1. **Take a PNG file** (RGB/RGBA) as input
2. **Convert to indexed color** (16 or 256 colors)
3. **Handle transparency** - detect transparent pixels, assign a unique color, place it at palette index 0
4. **Warn about invalid sizes** - check against valid sprite/background dimensions
5. **Generate JSON metadata** - create the required `.json` file alongside the `.bmp`
6. **Output clean BMP** - uncompressed, no ICC profiles, compatible with grit

---

## Technology Evaluation

### Language Options

| Language | Pros | Cons |
|----------|------|------|
| **Python** | Best palette manipulation (Pillow), easy to prototype, cross-platform | Requires Python runtime, slower |
| **Rust** | Fast, single binary, great for CLI/TUI, Tauri for GUI | Limited indexed BMP writing in `image` crate |
| **Node.js** | Familiar to web devs, good for Electron | Poor indexed color support in sharp/jimp |

### Image Processing Libraries

| Library | Indexed Support | BMP Writing | Palette Control |
|---------|-----------------|-------------|-----------------|
| **Python Pillow** | Excellent | Yes | Full control with `putpalette()` |
| **ImageMagick** | Excellent | Yes (BMP3) | Via CLI flags |
| **Rust image crate** | Read only | Limited | No palette write support |
| **Rust imagequant** | Quantization only | No | N/A (output to other crate) |
| **Node.js sharp** | PNG only | No BMP | Limited |

### UI Framework Options

| Type | Framework | Binary Size | Best For |
|------|-----------|-------------|----------|
| **CLI** | Python argparse/click | N/A (needs Python) | Quick & portable |
| **CLI** | Rust clap | ~2-5 MB | Single binary distribution |
| **TUI** | Rust ratatui | ~3-6 MB | Interactive terminal |
| **GUI** | Tauri | ~8-15 MB | Lightweight desktop app |
| **GUI** | Electron | ~80-120 MB | Rich web-based UI |

---

## Recommended Approach

### Option A: Python CLI (Fastest to Build) ⭐ Recommended to Start

**Stack:** Python + Pillow + Click

**Why:**
- Pillow has the best palette manipulation capabilities
- Can reorder palette, set transparency index, control BMP output
- Quick to prototype and iterate
- Can be packaged with PyInstaller for distribution

**Architecture:**
```
butano-img/
├── butano_img/
│   ├── __init__.py
│   ├── cli.py          # Click CLI interface
│   ├── converter.py    # Core conversion logic
│   ├── palette.py      # Palette manipulation
│   ├── validator.py    # Size validation
│   └── json_gen.py     # JSON file generation
├── pyproject.toml
└── README.md
```

---

### Option B: Rust CLI + Python Core (Best of Both)

**Stack:** Rust CLI shell calling Python for image processing

**Why:**
- Single binary distribution via Rust
- Python handles complex palette manipulation
- Embedded Python or subprocess calls

---

### Option C: Rust + Tauri GUI (Best UX)

**Stack:** Rust + Tauri + imagequant + custom BMP writer

**Why:**
- Beautiful drag-and-drop interface
- Tiny binary (~10 MB)
- No runtime dependencies

**Challenge:** Need to implement indexed BMP writing manually or find/create a crate for it.

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
    used_colors = set(img.getdata())
    # Try magenta first (common transparency color)
    candidates = [(255, 0, 255), (0, 255, 255), (255, 255, 0)]
    for color in candidates:
        if (color[0], color[1], color[2], 255) not in used_colors:
            return color
    # Generate random color if all candidates used
    import random
    while True:
        color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
        if (color[0], color[1], color[2], 255) not in used_colors:
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
def quantize_image(img, num_colors=256, trans_color=None):
    # Convert to RGB (remove alpha channel)
    rgb_img = img.convert("RGB")

    # Quantize to palette
    # Reserve one slot for transparency color
    actual_colors = num_colors - 1 if trans_color else num_colors
    indexed = rgb_img.quantize(colors=actual_colors, method=Image.Quantize.MEDIANCUT)

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
    # Swap index 0 with trans_index
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

## TUI Interface Design (Future)

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

## GUI (Tauri) Interface Design (Future)

A drag-and-drop interface where users can:
1. Drop PNG files onto the window
2. See a preview with detected issues
3. Configure options via simple toggles
4. Batch convert multiple files
5. See the generated palette with transparency highlighted

---

## Implementation Phases

### Phase 1: Python CLI (MVP)
- [ ] Basic PNG to indexed BMP conversion
- [ ] Transparency detection and handling
- [ ] Palette reordering (transparency first)
- [ ] Size validation with warnings
- [ ] JSON generation
- [ ] CLI with Click

**Estimated effort:** Core functionality

### Phase 2: Enhanced CLI
- [ ] Batch processing (multiple files/directories)
- [ ] Auto-resize option
- [ ] Custom transparency color
- [ ] Verbose/debug output
- [ ] Config file support

### Phase 3: TUI (Optional)
- [ ] Rust TUI with ratatui
- [ ] Interactive file browser
- [ ] Live preview
- [ ] Palette visualization

### Phase 4: GUI (Optional)
- [ ] Tauri app with drag-and-drop
- [ ] Image preview
- [ ] Batch processing UI
- [ ] Settings persistence

---

## File Structure (Phase 1)

```
butano-img/
├── butano_img/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point
│   ├── converter.py        # Main conversion orchestration
│   ├── palette.py          # Palette manipulation utilities
│   ├── transparency.py     # Transparency handling
│   ├── validator.py        # Size validation
│   ├── json_generator.py   # JSON file creation
│   └── constants.py        # Valid sizes, defaults
├── tests/
│   ├── test_converter.py
│   ├── test_palette.py
│   └── fixtures/           # Test images
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## Dependencies (Phase 1)

```toml
[project]
name = "butano-img"
version = "0.1.0"
dependencies = [
    "Pillow>=10.0.0",
    "click>=8.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov",
]

[project.scripts]
butano-img = "butano_img.cli:main"
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Pillow BMP output not compatible with grit | High | Test with actual Butano build; fallback to ImageMagick subprocess |
| Color quantization loses too much detail | Medium | Offer multiple algorithms (median cut, octree); allow manual palette |
| Large images cause memory issues | Low | Stream processing; warn on large files |

---

## Success Criteria

1. ✅ Convert a 32-bit RGBA PNG to 8-bit indexed BMP
2. ✅ Transparent pixels mapped to palette index 0
3. ✅ Output BMP compiles successfully with Butano/grit
4. ✅ JSON file generated with correct structure
5. ✅ Warnings shown for invalid sprite/background sizes
6. ✅ Works on Windows, macOS, Linux

---

## References

- [Pillow Documentation](https://pillow.readthedocs.io/en/stable/)
- [imagequant (Rust)](https://lib.rs/crates/imagequant)
- [quantette (Rust)](https://lib.rs/crates/quantette)
- [Ratatui TUI](https://ratatui.rs/)
- [Tauri](https://tauri.app/)
- [Click CLI](https://click.palletsprojects.com/)
- [Butano Import Docs](https://gvaliente.github.io/butano/import.html)
