# Butano Image Handling - DX Issues & Requirements

This document outlines the image requirements and constraints for Butano GBA development, identifying the key challenges we aim to solve for a better developer experience.

---

## Core Problem Statement

Butano (and the underlying GBA hardware) has strict image requirements that are unfamiliar to modern developers. Most image editors and workflows produce incompatible files, leading to frustrating build errors and manual conversion steps.

---

## Image Requirements Summary

### 1. Indexed Color Mode (Not RGB)

**Requirement:** Images MUST be indexed/paletted (4bpp or 8bpp), NOT true color RGB.

| Mode | Colors | Use Case |
|------|--------|----------|
| 4bpp | 16 colors max | Sprites with `bpp_4`, smaller palette |
| 8bpp | 256 colors max | Full palette sprites/backgrounds |

**DX Issue:** Most modern image editors (Photoshop, Figma exports, web assets) default to RGB/RGBA. Developers must manually convert to indexed color mode, which is a non-obvious step.

---

### 2. First Palette Color = Transparency

**Requirement:** The **first color (index 0)** in the palette is treated as transparent/backdrop.

**DX Issues:**
- This is counterintuitive - most developers expect alpha channels or a specific "transparent" color like magenta
- When converting from RGBA to indexed, the transparent areas need to be mapped to palette index 0
- If index 0 contains a visible color, that color will appear transparent in-game
- Reordering palette colors is not straightforward in most editors

---

### 3. BMP Format Constraints

**Requirement:** Images must be uncompressed BMP files without:
- RLE or other compression
- Color space information (ICC profiles)
- Extended headers

**DX Issue:** Modern image software often adds metadata, compression, or color profiles by default. Even "Save as BMP" can produce incompatible files.

**Recommended Tool:** [Usenti](https://www.coranac.com/projects/usenti/) - works with 15bpp colors like GBA and uses grit internally.

---

### 4. Valid Sprite Sizes (Hardware Constraint)

Sprites must match one of these exact dimensions:

| Shape | Size 0 | Size 1 | Size 2 | Size 3 |
|-------|--------|--------|--------|--------|
| **Square** | 8x8 | 16x16 | 32x32 | 64x64 |
| **Wide** | 16x8 | 32x8 | 32x16 | 64x32 |
| **Tall** | 8x16 | 8x32 | 16x32 | 32x64 |

**Valid sizes (all 12):**
- `8x8`, `16x16`, `32x32`, `64x64`
- `16x8`, `32x8`, `32x16`, `64x32`
- `8x16`, `8x32`, `16x32`, `32x64`

**DX Issue:** Arbitrary sprite sizes are not supported. Artists must design within these constraints or images must be padded/cropped to fit.

---

### 5. Valid Background Sizes

#### Regular Backgrounds (scrollable, tile-based)
| Small (faster) | Big (any multiple of 256px) |
|----------------|----------------------------|
| 256x256 | 256xN, Nx256, etc. |
| 256x512 | |
| 512x256 | |
| 512x512 | |

- Max 1024 tiles per background

#### Affine Backgrounds (can rotate/scale)
| Small (faster) | Big (any multiple of 256px) |
|----------------|----------------------------|
| 128x128 | 256xN, Nx256, etc. |
| 256x256 | |
| 512x512 | |
| 1024x1024 | |

- Max 256 tiles per background
- Only 2 affine backgrounds can display simultaneously

**DX Issue:** Background dimensions must match specific sizes. Arbitrary sizes require the "big" background mode which is slower.

---

### 6. Shared Palette Constraints

**For 8bpp (256 color) sprites:**
> If you use two 8bpp sprites at the same time, Butano assumes they share the same palette (same colors in the same order).

**For 8bpp backgrounds:**
> If you use two 8bpp backgrounds, Butano assumes they share the same palette.

**DX Issue:** Multiple sprites/backgrounds with different color palettes need careful palette management or must use 4bpp mode.

---

### 7. JSON Metadata Requirement

Every `.bmp` file needs an accompanying `.json` file with the same name:

```
character.bmp
character.json
```

Minimum JSON content:
```json
{
    "type": "sprite"
}
```

Or for backgrounds:
```json
{
    "type": "regular_bg"
}
```

**DX Issue:** Manual creation of JSON files for every image asset is tedious and error-prone.

---

## Summary: DX Pain Points to Solve

1. **Color Mode Conversion** - Automatically convert RGB/RGBA images to indexed color
2. **Transparency Handling** - Properly map transparent pixels to palette index 0
3. **Palette Ordering** - Ensure transparency color is first in the palette
4. **Format Conversion** - Convert PNG/other formats to clean, uncompressed BMP
5. **Size Validation** - Validate and/or resize images to valid sprite/background dimensions
6. **JSON Generation** - Auto-generate required JSON metadata files
7. **Palette Management** - Help manage shared palettes across multiple assets
8. **Color Reduction** - Reduce colors to 16 or 256 while preserving visual quality

---

## References

- [Butano GitHub Repository](https://github.com/GValiente/butano)
- [Butano Import Documentation](https://gvaliente.github.io/butano/import.html)
- [Butano FAQ](https://gvaliente.github.io/butano/faq.html)
- [Graphics Import - DeepWiki](https://deepwiki.com/GValiente/butano/6.1-graphics-import)
- [Grit - Graphics Conversion Tool](https://github.com/blocksds/grit)
- [GBA Sprite/Background Overview (Tonc)](https://www.coranac.com/tonc/text/objbg.htm)
