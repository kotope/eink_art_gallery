"""
Display Configuration Loader
Provides functions to load and parse eink display configuration files.
"""

import yaml
from pathlib import Path
from typing import Dict, Tuple, List
from PIL import Image


class DisplayConfig:
    """Represents an e-ink display configuration."""

    def __init__(self, config_data: dict, display_type: str):
        """
        Initialize a DisplayConfig object.

        Args:
            config_data: Dictionary containing the configuration
            display_type: The name of the display type (for reference)
        """
        self.display_type = display_type
        self.resolution = config_data.get("resolution", {})
        self.color_mapping = config_data.get("color_mapping", {})
        self.gamma = config_data.get("gamma", 1.0)

        # Validate required fields
        if (
            not self.resolution
            or "width" not in self.resolution
            or "height" not in self.resolution
        ):
            raise ValueError(
                f"Invalid config for {display_type}: missing or invalid resolution"
            )

        if not self.color_mapping or "palette" not in self.color_mapping:
            raise ValueError(
                f"Invalid config for {display_type}: missing or invalid color_mapping"
            )

    def get_resolution(self) -> Tuple[int, int]:
        """
        Get the display resolution.

        Returns:
            Tuple of (width, height)
        """
        return (self.resolution["width"], self.resolution["height"])

    def get_palette_image(self) -> Image.Image:
        """
        Create a PIL Image with the configured color palette.

        Returns:
            A 1x1 PIL Image in palette mode with the configured colors
        """
        palette = self.color_mapping["palette"]

        # Flatten the RGB colors into a single list
        palette_data = []
        for color in palette:
            if isinstance(color, (list, tuple)) and len(color) == 3:
                palette_data.extend(color)
            else:
                raise ValueError(f"Invalid color format: {color}. Expected [R, G, B]")

        # Pad to 768 entries (256 colors * 3 channels)
        while len(palette_data) < 768:
            palette_data.append(0)

        # Create and return palette image
        p_image = Image.new("P", (1, 1))
        p_image.putpalette(palette_data)
        return p_image

    def to_process_image_params(self) -> Dict:
        """
        Convert the configuration to parameters for the process_image() function.

        Returns:
            Dictionary with keys: width, height, palette_image, gamma
        """
        width, height = self.get_resolution()
        return {
            "width": width,
            "height": height,
            "palette_image": self.get_palette_image(),
            "gamma": self.gamma,
        }


def load_display_config(display_type: str, displays_dir: Path = None) -> DisplayConfig:
    """
    Load a display configuration from a YAML file.
    Supports both default and persistent (user-modified) configurations.

    Args:
        display_type: The name of the display type (matches filename without .yaml)
        displays_dir: Path to the displays directory. Defaults to ./displays

    Returns:
        DisplayConfig object

    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        ValueError: If the configuration is invalid
    """
    if displays_dir is None:
        displays_dir = Path(__file__).parent / "displays"

    # Check for persistent (custom) config first
    persistent_dir = Path("/data/eink_art/displays")
    persistent_file = persistent_dir / f"{display_type}.yaml"

    if persistent_file.exists():
        config_file = persistent_file
    else:
        config_file = displays_dir / f"{display_type}.yaml"

    if not config_file.exists():
        raise FileNotFoundError(
            f"Display configuration not found: {config_file}\n"
            f"Available displays: {', '.join(f.stem for f in displays_dir.glob('*.yaml'))}"
        )

    try:
        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {config_file}: {e}")

    return DisplayConfig(config_data, display_type)


def list_available_displays(displays_dir: Path = None) -> List[str]:
    """
    List all available display types (both default and custom).

    Args:
        displays_dir: Path to the displays directory. Defaults to ./displays

    Returns:
        List of available display type names
    """
    if displays_dir is None:
        displays_dir = Path(__file__).parent / "displays"

    display_names = set()

    # Add default displays
    if displays_dir.exists():
        display_names.update(f.stem for f in displays_dir.glob("*.yaml"))

    # Add persistent (custom) displays
    persistent_dir = Path("/data/eink_art/displays")
    if persistent_dir.exists():
        display_names.update(f.stem for f in persistent_dir.glob("*.yaml"))

    return sorted(list(display_names))
