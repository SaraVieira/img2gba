# Developer Documentation

This guide explains how the butano-img tool works internally, how to set up a development environment, and how to contribute.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [How It Works](#how-it-works)
4. [Module Guide](#module-guide)
5. [Testing](#testing)
6. [Common Python Patterns Used](#common-python-patterns-used)
7. [Adding New Features](#adding-new-features)

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Check your Python version

```bash
python3 --version
# Should show Python 3.10.x or higher
```

### Clone and install

```bash
# Clone the repository
git clone <repo-url>
cd gba-images

# Install in "editable" mode with dev dependencies
# The -e flag means changes to the code take effect immediately
# The [dev] part installs testing tools (pytest)
pip install -e ".[dev]"

# To also install TUI dependencies (Textual)
pip install -e ".[dev,tui]"
```

### Verify installation

```bash
# Should show help text
butano-img --help

# Run the tests
pytest

# Launch the TUI (if installed with tui extra)
butano-img tui
```

---

## Project Structure

```
gba-images/
├── src/
│   └── butano_img/           # Main package (all the code lives here)
│       ├── __init__.py       # Package initialization, exports public API
│       ├── cli.py            # Command-line interface (what users interact with)
│       ├── tui.py            # Terminal User Interface (Textual app)
│       ├── constants.py      # Valid sizes and other constants
│       ├── converter.py      # Main orchestration (coordinates all the steps)
│       ├── json_generator.py # Creates the .json metadata files
│       ├── palette.py        # Color quantization and palette reordering
│       ├── transparency.py   # Detects and handles transparent pixels
│       └── validator.py      # Validates image dimensions
├── tests/
│   ├── fixtures/             # Test images
│   ├── test_transparency.py  # Tests for transparency module
│   ├── test_palette.py       # Tests for palette module
│   ├── test_validator.py     # Tests for validator module
│   └── test_converter.py     # Tests for converter module
├── pyproject.toml            # Project configuration (dependencies, metadata)
├── README.md                 # User documentation
├── CONTRIBUTING.md           # This file
└── .gitignore               # Files Git should ignore
```

### What each file does

| File | Purpose |
|------|---------|
| `__init__.py` | Makes the folder a "package". Also defines what gets exported when someone does `from butano_img import ...` |
| `cli.py` | Defines the command-line commands (`convert`, `validate`, `sizes`, `tui`) using the Click library |
| `tui.py` | Terminal User Interface using Textual - provides interactive file browser, options, and conversion |
| `constants.py` | Stores all the valid sprite/background sizes. Easy to find and modify. |
| `converter.py` | The "brain" - coordinates loading images, processing them, and saving results |
| `json_generator.py` | Simple module to create the `.json` files Butano needs |
| `palette.py` | Handles color reduction (quantization) and reordering the palette |
| `transparency.py` | Finds transparent pixels and replaces them with a solid color |
| `validator.py` | Checks if image dimensions are valid for GBA sprites/backgrounds |

---

## How It Works

### The Conversion Pipeline

When you run `butano-img convert image.png`, here's what happens:

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. LOAD IMAGE                                                    │
│    - Open PNG file using Pillow                                  │
│    - Convert to RGBA mode (ensures we have alpha channel)        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. VALIDATE SIZE                                                 │
│    - Check if dimensions match valid GBA sizes                   │
│    - If not, generate warning with suggestions                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. HANDLE TRANSPARENCY                                           │
│    - Scan all pixels for transparency (alpha < 128)              │
│    - If found, pick a color not used in the image                │
│    - Replace all transparent pixels with that color              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. QUANTIZE COLORS                                               │
│    - Reduce from millions of colors to 16 or 256                 │
│    - Uses "median cut" algorithm (Pillow built-in)               │
│    - Result is an indexed/paletted image                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. REORDER PALETTE                                               │
│    - Find the transparency color in the palette                  │
│    - Swap it with whatever is at index 0                         │
│    - Update all pixel references accordingly                     │
│    (GBA treats palette index 0 as transparent)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. SAVE OUTPUT                                                   │
│    - Save as BMP (Pillow handles the format)                     │
│    - Generate JSON metadata file                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why These Steps?

**Why indexed colors?** The GBA hardware can only display images with a limited palette (16 or 256 colors). Each pixel stores an index into the palette, not the actual color.

**Why reorder the palette?** The GBA treats palette index 0 as transparent. If your transparency color isn't at index 0, transparent areas will show the wrong color.

**Why BMP format?** Butano's build system (grit) expects BMP files. BMP is a simple, uncompressed format that's easy for tools to parse.

---

## Module Guide

### constants.py

Defines valid sizes for GBA graphics:

```python
# Sprite sizes are limited by GBA hardware
# These are the ONLY valid combinations
VALID_SPRITE_SIZES = [
    (8, 8), (16, 16), (32, 32), (64, 64),    # Square
    (16, 8), (32, 8), (32, 16), (64, 32),    # Wide (horizontal)
    (8, 16), (8, 32), (16, 32), (32, 64),    # Tall (vertical)
]
```

**To add a new asset type**, you would add a new list here and update `validator.py`.

### transparency.py

Two main functions:

```python
# Check if an image has any transparent pixels
has_transparency(image) -> bool

# Find a color that isn't used in the image
find_unused_color(image) -> tuple[int, int, int]

# Replace transparent pixels with a solid color
replace_transparency(image, color) -> Image
```

**Key concept:** We can't keep alpha transparency in the final image (BMP doesn't support it the way we need). So we replace transparent pixels with a solid "magic" color that becomes the transparent color in the palette.

### palette.py

Handles color reduction:

```python
# Reduce colors to 16 or 256
quantize_image(image, num_colors=256) -> Image

# Move transparency color to palette index 0
reorder_palette_for_transparency(image, trans_color) -> Image
```

**Key concept:** After quantization, the image becomes "indexed" - each pixel is a number (0-255) that refers to a color in the palette, rather than storing RGB values directly.

### validator.py

Checks dimensions:

```python
# Returns a ValidationResult with valid=True/False and suggestions
validate_size(width, height, asset_type="sprite") -> ValidationResult
```

### converter.py

Orchestrates everything:

```python
# Main entry point - does the full conversion
convert_image(
    input_path,
    output_path=None,      # Optional, defaults to input with .bmp extension
    asset_type="sprite",
    num_colors=256,
    handle_transparency=True,
    trans_color=None,      # Optional, auto-detected if not specified
    generate_json_file=True,
    verbose=False,
) -> ConversionResult
```

### cli.py

Defines commands using Click:

```python
@click.command()
@click.argument("input_file")
@click.option("-t", "--type", ...)
def convert(input_file, ...):
    # Calls converter.convert_image()
    pass
```

**Click** is a library that makes it easy to create command-line tools. The decorators (`@click.command()`, `@click.option()`) define how arguments are parsed.

### tui.py

The Terminal User Interface built with **Textual**. Textual is a Python framework for building rich terminal applications with mouse support, styled widgets, and reactive updates.

#### TUI Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ Header                                                        │
├─────────────────────────┬────────────────────────────────────┤
│                         │ Selected File                       │
│   Directory Tree        ├────────────────────────────────────┤
│   (FilteredDirectoryTree)│ Validation Status                  │
│                         ├────────────────────────────────────┤
│   - Only shows images   │ Options                             │
│   - .png, .jpg, etc.    │   - Asset Type (RadioSet)           │
│                         │   - Colors (RadioSet)               │
│                         ├────────────────────────────────────┤
│                         │ [Convert Button]                    │
│                         ├────────────────────────────────────┤
│                         │ Output Log (RichLog)                │
├─────────────────────────┴────────────────────────────────────┤
│ Footer (key bindings)                                         │
└──────────────────────────────────────────────────────────────┘
```

#### Key Components

```python
class FilteredDirectoryTree(DirectoryTree):
    """Custom directory tree that only shows image files."""

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        # Only show directories and image files
        return [p for p in paths if p.is_dir() or p.suffix.lower() in IMAGE_EXTENSIONS]


class ButanoImgApp(App):
    """Main application class."""

    # CSS styling (inline, similar to web CSS)
    CSS = """
    #file-panel { width: 40%; }
    .validation-valid { color: $success; }
    """

    # Keyboard shortcuts
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("c", "convert", "Convert"),
    ]

    def compose(self) -> ComposeResult:
        """Build the UI widget tree."""
        yield Header()
        yield DirectoryTree(...)
        yield Footer()

    @on(DirectoryTree.FileSelected)
    def on_file_selected(self, event):
        """Handle file selection events."""
        pass
```

#### Textual Concepts

**Widgets**: UI components like `Button`, `Label`, `DirectoryTree`, `RadioSet`

**Containers**: Layout widgets like `Vertical`, `Horizontal`, `Container`

**Events**: User actions that trigger handlers (decorated with `@on`)

**Bindings**: Keyboard shortcuts defined in `BINDINGS` list

**CSS**: Styling uses a CSS-like syntax (not actual CSS, but similar)

**Reactive**: Properties can trigger UI updates when changed

#### Running the TUI

```bash
# Via CLI
butano-img tui

# Direct entry point
butano-img-tui

# During development
python -m butano_img.tui
```

#### Extending the TUI

To add a new option:

1. Add a widget in `compose()`:
```python
yield RadioButton("New Option", id="radio-new")
```

2. Add an event handler:
```python
@on(RadioSet.Changed, "#my-radio-set")
def on_option_changed(self, event):
    self.my_option = event.pressed.id
```

3. Use the value in `action_convert()`:
```python
result = convert_image(..., my_option=self.my_option)
```

---

## Testing

### Running tests

```bash
# Run all tests
pytest

# Run with verbose output (see each test name)
pytest -v

# Run a specific test file
pytest tests/test_validator.py

# Run a specific test function
pytest tests/test_validator.py::test_valid_sprite_sizes

# Run with coverage report
pytest --cov=butano_img
```

### Writing tests

Tests use **pytest**, which is simple:

```python
# tests/test_example.py

def test_something():
    """Description of what this tests."""
    result = some_function(input)
    assert result == expected_value

def test_something_else():
    """Test another case."""
    assert some_condition == True
```

**Key pytest features:**

- Test files must start with `test_`
- Test functions must start with `test_`
- Use `assert` to check conditions
- Tests fail if any `assert` is False or an exception is raised

### Test fixtures

Pytest "fixtures" provide test data:

```python
import pytest

@pytest.fixture
def sample_image():
    """Create a test image."""
    from PIL import Image
    return Image.new('RGBA', (32, 32), (255, 0, 0, 255))

def test_with_fixture(sample_image):
    # sample_image is automatically provided by pytest
    assert sample_image.size == (32, 32)
```

---

## Common Python Patterns Used

### Type Hints

We use type hints to document what types functions expect/return:

```python
def find_unused_color(img: Image.Image) -> tuple[int, int, int]:
    """
    img: Image.Image  - expects a Pillow Image object
    -> tuple[int, int, int]  - returns a tuple of 3 integers (R, G, B)
    """
    pass
```

Type hints don't enforce anything at runtime - they're documentation that tools like IDEs can use.

### Dataclasses

We use dataclasses for structured data:

```python
from dataclasses import dataclass

@dataclass
class ValidationResult:
    valid: bool
    message: str
    suggestions: list[tuple[int, int]]
```

This automatically creates `__init__`, `__repr__`, etc. It's like a simple class for holding data.

### Path objects

We use `pathlib.Path` instead of string paths:

```python
from pathlib import Path

path = Path("folder/file.png")
path.suffix        # ".png"
path.stem          # "file"
path.with_suffix(".bmp")  # Path("folder/file.bmp")
path.exists()      # True/False
```

### Optional values

```python
def func(value: int | None = None):
    """value can be an int OR None (the default)"""
    if value is None:
        value = calculate_default()
```

---

## Adding New Features

### Adding a new CLI option

1. Add the option in `cli.py`:

```python
@click.option(
    "--my-option",
    is_flag=True,  # or type=int, type=str, etc.
    help="Description of what this does",
)
def convert(..., my_option):
    pass
```

2. Pass it through to `convert_image()` in `converter.py`

3. Add tests for the new option

### Adding a new asset type

1. Add valid sizes in `constants.py`:

```python
VALID_MY_TYPE_SIZES = [(256, 256), ...]
```

2. Update `validator.py` to handle the new type

3. Add to `VALID_ASSET_TYPES` in `constants.py`

4. Update tests

### Adding a new output format

1. Create a new module (e.g., `gba_format.py`)

2. Add functions to convert/save in that format

3. Add CLI option to choose format

4. Add tests

---

## Debugging Tips

### Print debugging

```python
print(f"Variable value: {variable}")
print(f"Image size: {img.size}, mode: {img.mode}")
```

### Using the verbose flag

The `-v` flag enables verbose output. Add print statements inside `if verbose:` blocks:

```python
if verbose:
    click.echo(f"Processing: {input_path}")
```

### Inspecting Pillow images

```python
img = Image.open("file.png")
print(f"Size: {img.size}")       # (width, height)
print(f"Mode: {img.mode}")       # 'RGB', 'RGBA', 'P' (palette), etc.
print(f"Palette: {img.getpalette()[:30]}")  # First 30 palette values
print(f"Pixel at (0,0): {img.getpixel((0, 0))}")
```

### Common issues

**"Module not found" errors:** Make sure you installed with `pip install -e .`

**Tests can't find modules:** Run pytest from the project root directory

**Image looks wrong:** Check the mode (`img.mode`) - might need `.convert('RGBA')` or `.convert('RGB')`

---

## Questions?

Open an issue on GitHub or check the existing issues for similar problems.
