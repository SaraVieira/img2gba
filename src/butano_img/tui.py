"""
Textual TUI for Butano Image Converter.

A terminal user interface for converting images to Butano GBA format.
Provides an interactive way to select files, configure options, and convert.

Run with:
    butano-img-tui
    # or
    python -m butano_img.tui
"""

from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    DirectoryTree,
    Footer,
    Header,
    Input,
    Label,
    RadioButton,
    RadioSet,
    RichLog,
    Static,
)

from .constants import VALID_ASSET_TYPES, COLORS_16, COLORS_256
from .converter import convert_image
from .validator import validate_size

# File extensions we accept
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}


class FilteredDirectoryTree(DirectoryTree):
    """A directory tree that only shows image files and directories."""

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        """Filter to only show directories and image files."""
        return [
            path
            for path in paths
            if path.is_dir() or path.suffix.lower() in IMAGE_EXTENSIONS
        ]


class ButanoImgApp(App):
    """Butano Image Converter TUI Application."""

    TITLE = "Butano Image Converter"
    SUB_TITLE = "Convert images to GBA format"

    CSS = """
    /* Main layout */
    #main-container {
        layout: horizontal;
        height: 100%;
    }

    /* Left panel - file browser */
    #file-panel {
        width: 40%;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }

    #file-panel-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    #directory-tree {
        height: 100%;
    }

    /* Right panel - options and output */
    #options-panel {
        width: 60%;
        height: 100%;
        padding: 1;
    }

    /* Selected file display */
    #selected-file-container {
        height: auto;
        margin-bottom: 1;
        padding: 1;
        border: solid $secondary;
    }

    #selected-file-label {
        text-style: bold;
    }

    #selected-file {
        color: $success;
    }

    #file-info {
        color: $text-muted;
    }

    /* Validation status */
    #validation-container {
        height: auto;
        margin-bottom: 1;
        padding: 1;
        border: solid $secondary;
    }

    .validation-valid {
        color: $success;
    }

    .validation-invalid {
        color: $error;
    }

    /* Options section */
    #options-container {
        height: auto;
        margin-bottom: 1;
        padding: 1;
        border: solid $secondary;
    }

    .option-group {
        margin-bottom: 1;
    }

    .option-label {
        text-style: bold;
        margin-bottom: 0;
    }

    RadioSet {
        height: auto;
        margin-left: 2;
    }

    /* Buttons */
    #button-container {
        height: auto;
        margin-bottom: 1;
    }

    #convert-button {
        width: 100%;
        margin-bottom: 1;
    }

    /* Output log */
    #output-container {
        height: 1fr;
        border: solid $secondary;
        padding: 1;
    }

    #output-label {
        text-style: bold;
        margin-bottom: 1;
    }

    RichLog {
        height: 100%;
        background: $surface;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("c", "convert", "Convert"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.selected_file: Path | None = None
        self.asset_type = "sprite"
        self.num_colors = 256

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header()

        with Container(id="main-container"):
            # Left panel - file browser
            with Vertical(id="file-panel"):
                yield Label("Select Image File", id="file-panel-title")
                yield FilteredDirectoryTree(Path.cwd(), id="directory-tree")

            # Right panel - options and output
            with Vertical(id="options-panel"):
                # Selected file display
                with Vertical(id="selected-file-container"):
                    yield Label("Selected File:", id="selected-file-label")
                    yield Static("No file selected", id="selected-file")
                    yield Static("", id="file-info")

                # Validation status
                with Vertical(id="validation-container"):
                    yield Label("Size Validation:", classes="option-label")
                    yield Static("Select a file to validate", id="validation-status")

                # Options
                with Vertical(id="options-container"):
                    yield Label("Options", classes="option-label")

                    with Vertical(classes="option-group"):
                        yield Label("Asset Type:", classes="option-label")
                        with RadioSet(id="asset-type-radio"):
                            yield RadioButton("Sprite", value=True, id="radio-sprite")
                            yield RadioButton("Regular BG", id="radio-regular-bg")
                            yield RadioButton("Affine BG", id="radio-affine-bg")

                    with Vertical(classes="option-group"):
                        yield Label("Colors:", classes="option-label")
                        with RadioSet(id="colors-radio"):
                            yield RadioButton("256 colors (8bpp)", value=True, id="radio-256")
                            yield RadioButton("16 colors (4bpp)", id="radio-16")

                # Convert button
                with Horizontal(id="button-container"):
                    yield Button("Convert", id="convert-button", variant="primary")

                # Output log
                with Vertical(id="output-container"):
                    yield Label("Output:", id="output-label")
                    yield RichLog(id="output-log", highlight=True, markup=True)

        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.log_message("[bold]Welcome to Butano Image Converter![/bold]")
        self.log_message("Select an image file from the left panel.")
        self.log_message("Press [bold]C[/bold] to convert, [bold]Q[/bold] to quit.")

    @on(DirectoryTree.FileSelected)
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection from directory tree."""
        path = event.path

        # Check if it's an image file
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            self.log_message(f"[yellow]Skipped:[/yellow] {path.name} is not an image file")
            return

        self.selected_file = path
        self.update_file_display()
        self.update_validation()
        self.log_message(f"[green]Selected:[/green] {path.name}")

    @on(RadioSet.Changed, "#asset-type-radio")
    def on_asset_type_changed(self, event: RadioSet.Changed) -> None:
        """Handle asset type radio selection."""
        radio_id = str(event.pressed.id)
        if radio_id == "radio-sprite":
            self.asset_type = "sprite"
        elif radio_id == "radio-regular-bg":
            self.asset_type = "regular_bg"
        elif radio_id == "radio-affine-bg":
            self.asset_type = "affine_bg"

        self.log_message(f"Asset type: [cyan]{self.asset_type}[/cyan]")
        self.update_validation()

    @on(RadioSet.Changed, "#colors-radio")
    def on_colors_changed(self, event: RadioSet.Changed) -> None:
        """Handle colors radio selection."""
        radio_id = str(event.pressed.id)
        if radio_id == "radio-256":
            self.num_colors = 256
        elif radio_id == "radio-16":
            self.num_colors = 16

        self.log_message(f"Colors: [cyan]{self.num_colors}[/cyan]")

    @on(Button.Pressed, "#convert-button")
    def on_convert_pressed(self, event: Button.Pressed) -> None:
        """Handle convert button press."""
        self.action_convert()

    def action_convert(self) -> None:
        """Convert the selected image."""
        if self.selected_file is None:
            self.log_message("[red]Error:[/red] No file selected!")
            return

        if not self.selected_file.exists():
            self.log_message(f"[red]Error:[/red] File not found: {self.selected_file}")
            return

        self.log_message("")
        self.log_message(f"[bold]Converting {self.selected_file.name}...[/bold]")

        try:
            result = convert_image(
                input_path=self.selected_file,
                asset_type=self.asset_type,
                num_colors=self.num_colors,
                verbose=False,
            )

            if result.success:
                self.log_message(f"[green]Success![/green] Created: {result.output_path.name}")

                if result.json_path:
                    self.log_message(f"  JSON: {result.json_path.name}")

                if result.transparency_color:
                    r, g, b = result.transparency_color
                    self.log_message(f"  Transparency: RGB({r}, {g}, {b}) at index 0")

                if not result.validation.valid:
                    self.log_message(f"  [yellow]Warning:[/yellow] {result.validation.message}")

                self.log_message("")
            else:
                self.log_message(f"[red]Failed:[/red] {result.message}")

        except Exception as e:
            self.log_message(f"[red]Error:[/red] {e}")

    def action_refresh(self) -> None:
        """Refresh the directory tree."""
        tree = self.query_one("#directory-tree", DirectoryTree)
        tree.reload()
        self.log_message("[cyan]Refreshed[/cyan] directory tree")

    def update_file_display(self) -> None:
        """Update the selected file display."""
        file_display = self.query_one("#selected-file", Static)
        info_display = self.query_one("#file-info", Static)

        if self.selected_file is None:
            file_display.update("No file selected")
            info_display.update("")
            return

        file_display.update(str(self.selected_file.name))

        # Get file info
        try:
            from PIL import Image
            with Image.open(self.selected_file) as img:
                info_display.update(
                    f"Size: {img.width}x{img.height}  |  Mode: {img.mode}  |  "
                    f"Path: {self.selected_file.parent}"
                )
        except Exception as e:
            info_display.update(f"Could not read image: {e}")

    def update_validation(self) -> None:
        """Update the validation status display."""
        status = self.query_one("#validation-status", Static)

        if self.selected_file is None:
            status.update("Select a file to validate")
            status.remove_class("validation-valid", "validation-invalid")
            return

        try:
            from PIL import Image
            with Image.open(self.selected_file) as img:
                result = validate_size(img.width, img.height, self.asset_type)

                if result.valid:
                    status.update(f"✓ {img.width}x{img.height} is valid for {self.asset_type}")
                    status.add_class("validation-valid")
                    status.remove_class("validation-invalid")
                else:
                    suggestions = ", ".join(f"{s[0]}x{s[1]}" for s in result.suggestions)
                    status.update(
                        f"✗ {img.width}x{img.height} is not valid for {self.asset_type}\n"
                        f"  Suggested: {suggestions}"
                    )
                    status.add_class("validation-invalid")
                    status.remove_class("validation-valid")

        except Exception as e:
            status.update(f"Could not validate: {e}")
            status.remove_class("validation-valid", "validation-invalid")

    def log_message(self, message: str) -> None:
        """Add a message to the output log."""
        log = self.query_one("#output-log", RichLog)
        log.write(message)


def main() -> None:
    """Entry point for the TUI application."""
    app = ButanoImgApp()
    app.run()


if __name__ == "__main__":
    main()
