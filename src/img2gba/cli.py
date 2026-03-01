"""Command-line interface for Butano image converter."""

import sys
from pathlib import Path

import click

from . import __version__
from .converter import convert_image
from .constants import VALID_ASSET_TYPES, COLORS_16, COLORS_256, VALID_COMPRESSION_TYPES
from .validator import format_valid_sizes


def parse_color(ctx, param, value):
    """Parse a color string like '255,0,255' into a tuple."""
    if value is None:
        return None
    try:
        parts = value.split(",")
        if len(parts) != 3:
            raise ValueError()
        return tuple(int(p.strip()) for p in parts)
    except (ValueError, AttributeError):
        raise click.BadParameter("Color must be in format 'R,G,B' (e.g., '255,0,255')")


@click.group()
@click.version_option(version=__version__, prog_name="img2gba")
def main():
    """Butano Image Converter - Convert images to GBA format.

    Convert PNG images to Butano-compatible indexed BMP files with proper
    transparency handling, palette management, and JSON metadata generation.
    """
    pass


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    help="Output BMP path (default: same as input with .bmp extension)",
)
@click.option(
    "-t", "--type",
    "asset_type",
    type=click.Choice(VALID_ASSET_TYPES),
    default="sprite",
    help="Asset type (default: sprite)",
)
@click.option(
    "-c", "--colors",
    type=click.Choice(["16", "256"]),
    default="16",
    help="Number of colors (default: 16)",
)
@click.option(
    "--no-transparency",
    is_flag=True,
    help="Don't handle transparency",
)
@click.option(
    "--trans-color",
    callback=parse_color,
    help="Force specific transparency color (format: R,G,B)",
)
@click.option(
    "--no-json",
    is_flag=True,
    help="Don't generate JSON metadata file",
)
@click.option(
    "-h", "--height",
    "sprite_height",
    type=int,
    help="Height of each sprite in a sprite sheet (for multi-sprite images)",
)
@click.option(
    "--compression",
    type=click.Choice(VALID_COMPRESSION_TYPES),
    help="Compression method (none, lz77, run_length, huffman, auto)",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Show detailed output",
)
def convert(
    input_file: Path,
    output: Path | None,
    asset_type: str,
    colors: str,
    no_transparency: bool,
    trans_color: tuple[int, int, int] | None,
    no_json: bool,
    sprite_height: int | None,
    compression: str | None,
    verbose: bool,
):
    """Convert a PNG image to Butano-compatible BMP format.

    INPUT_FILE: Path to the PNG image to convert

    Examples:

        img2gba convert player.png

        img2gba convert background.png -t regular_bg

        img2gba convert tiles.png -c 16 -v

        img2gba convert spritesheet.png -h 32  # Split into 32px high sprites

        img2gba convert level.png -t regular_bg --compression lz77
    """
    num_colors = COLORS_16 if colors == "16" else COLORS_256

    try:
        result = convert_image(
            input_path=input_file,
            output_path=output,
            asset_type=asset_type,
            num_colors=num_colors,
            handle_transparency=not no_transparency,
            trans_color=trans_color,
            generate_json_file=not no_json,
            sprite_height=sprite_height,
            compression=compression,
            verbose=verbose,
        )

        # Print result
        if result.success:
            click.secho(f"Converted: {result.output_path}", fg="green")

            if result.json_path:
                click.echo(f"    JSON: {result.json_path}")

            if result.transparency_color:
                r, g, b = result.transparency_color
                click.echo(f"    Transparency: RGB({r}, {g}, {b}) at index 0")

            if sprite_height:
                click.echo(f"    Sprite height: {sprite_height}px (sprite sheet mode)")

            if compression and compression != "none":
                click.echo(f"    Compression: {compression}")

            if not result.validation.valid:
                click.secho(f"    Warning: {result.validation.message}", fg="yellow")

    except FileNotFoundError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument("asset_type", type=click.Choice(VALID_ASSET_TYPES))
def sizes(asset_type: str):
    """Show valid sizes for an asset type.

    ASSET_TYPE: One of 'sprite', 'regular_bg', 'affine_bg'
    """
    click.echo(f"Valid sizes for {asset_type}:")
    click.echo(f"  {format_valid_sizes(asset_type)}")


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-t", "--type",
    "asset_type",
    type=click.Choice(VALID_ASSET_TYPES),
    default="sprite",
    help="Asset type to validate against (default: sprite)",
)
def validate(input_file: Path, asset_type: str):
    """Validate an image's dimensions for Butano.

    INPUT_FILE: Path to the image to validate
    """
    from PIL import Image
    from .validator import validate_size

    img = Image.open(input_file)
    result = validate_size(img.width, img.height, asset_type)

    click.echo(f"Image: {input_file}")
    click.echo(f"Size: {img.width}x{img.height}")
    click.echo(f"Asset type: {asset_type}")

    if result.valid:
        click.secho("Status: VALID", fg="green")
    else:
        click.secho("Status: INVALID", fg="red")
        suggestions = [f"{s[0]}x{s[1]}" for s in result.suggestions]
        click.echo(f"Suggested sizes: {', '.join(suggestions)}")


@main.command()
def tui():
    """Launch the interactive TUI (Terminal User Interface).

    Requires the 'tui' extra: pip install img2gba[tui]
    """
    try:
        from .tui import main as tui_main
        tui_main()
    except ImportError:
        click.secho(
            "Error: TUI dependencies not installed.\n"
            "Install with: pip install img2gba[tui]",
            fg="red",
            err=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
