"""
Display Configuration Manager
Manages persistent storage and editing of display configuration files.
User-modified configurations are stored separately to persist across addon updates.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration directories
DEFAULT_DISPLAYS_DIR = Path(__file__).parent / "displays"
PERSISTENT_DISPLAYS_DIR = Path("/data/eink_art/displays")  # Outside the addon container


class DisplayConfigManager:
    """Manages display configurations with persistent storage"""

    def __init__(self):
        """Initialize the display config manager"""
        # Ensure persistent directory exists
        self.persistent_dir = PERSISTENT_DISPLAYS_DIR
        self.persistent_dir.mkdir(parents=True, exist_ok=True)

        self.default_dir = DEFAULT_DISPLAYS_DIR
        logger.info(f"DisplayConfigManager initialized")
        logger.info(f"  Default configs: {self.default_dir}")
        logger.info(f"  Persistent configs: {self.persistent_dir}")

    def get_display_config_file(self, display_name: str) -> Path:
        """
        Get the appropriate config file for a display (persistent or default).

        Args:
            display_name: Name of the display (without .yaml extension)

        Returns:
            Path to the config file

        Raises:
            FileNotFoundError: If config doesn't exist
        """
        # Check persistent storage first
        persistent_file = self.persistent_dir / f"{display_name}.yaml"
        if persistent_file.exists():
            return persistent_file

        # Fall back to default configs
        default_file = self.default_dir / f"{display_name}.yaml"
        if default_file.exists():
            return default_file

        raise FileNotFoundError(f"Display config not found: {display_name}")

    def list_displays(self) -> List[Dict]:
        """
        List all available display configurations.

        Returns:
            List of display info dicts with keys:
            - name: Display name
            - is_custom: True if modified by user, False if default
            - modified_at: Timestamp of last modification (for custom configs)
        """
        displays = {}

        # Add default displays
        if self.default_dir.exists():
            for config_file in self.default_dir.glob("*.yaml"):
                name = config_file.stem
                displays[name] = {"name": name, "is_custom": False, "modified_at": None}

        # Override with persistent/custom displays
        if self.persistent_dir.exists():
            for config_file in self.persistent_dir.glob("*.yaml"):
                name = config_file.stem
                stat = config_file.stat()
                displays[name] = {
                    "name": name,
                    "is_custom": True,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }

        return sorted(displays.values(), key=lambda x: x["name"])

    def load_display_config(self, display_name: str) -> str:
        """
        Load a display configuration YAML as a string.

        Args:
            display_name: Name of the display (without .yaml extension)

        Returns:
            YAML content as string

        Raises:
            FileNotFoundError: If config doesn't exist
        """
        config_file = self.get_display_config_file(display_name)
        try:
            with open(config_file, "r") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading display config {display_name}: {e}")
            raise

    def save_display_config(self, display_name: str, yaml_content: str) -> Dict:
        """
        Save a display configuration YAML.
        Creates a persistent copy if editing a default config.

        Args:
            display_name: Name of the display (without .yaml extension)
            yaml_content: YAML content as string

        Returns:
            Dictionary with save status info

        Raises:
            ValueError: If YAML is invalid
        """
        # Validate YAML
        try:
            yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")

        # Save to persistent storage
        config_file = self.persistent_dir / f"{display_name}.yaml"
        try:
            with open(config_file, "w") as f:
                f.write(yaml_content)

            logger.info(f"Display config saved: {display_name}")

            return {
                "status": "success",
                "message": f"Configuration for '{display_name}' saved successfully",
                "display_name": display_name,
                "is_custom": True,
                "modified_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error saving display config {display_name}: {e}")
            raise

    def reset_display_config(self, display_name: str) -> Dict:
        """
        Reset a custom display config to its default version.

        Args:
            display_name: Name of the display (without .yaml extension)

        Returns:
            Dictionary with reset status info

        Raises:
            FileNotFoundError: If default config doesn't exist
        """
        persistent_file = self.persistent_dir / f"{display_name}.yaml"

        if not persistent_file.exists():
            raise FileNotFoundError(
                f"No custom configuration found for '{display_name}'"
            )

        # Check that default exists
        default_file = self.default_dir / f"{display_name}.yaml"
        if not default_file.exists():
            raise FileNotFoundError(
                f"Default configuration not found for '{display_name}'"
            )

        try:
            persistent_file.unlink()
            logger.info(f"Display config reset to default: {display_name}")

            return {
                "status": "success",
                "message": f"Configuration for '{display_name}' reset to default",
                "display_name": display_name,
                "is_custom": False,
                "modified_at": None,
            }
        except Exception as e:
            logger.error(f"Error resetting display config {display_name}: {e}")
            raise

    def duplicate_display_config(self, source_name: str, new_name: str) -> Dict:
        """
        Duplicate a display configuration.

        Args:
            source_name: Name of the source display config
            new_name: Name for the new display config

        Returns:
            Dictionary with duplication status info

        Raises:
            FileNotFoundError: If source doesn't exist
            ValueError: If new name already exists or is invalid
        """
        # Validate new name
        if not new_name or not new_name.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Display name must contain only alphanumeric characters, hyphens, and underscores"
            )

        # Check source exists
        source_file = self.get_display_config_file(source_name)

        # Check new name doesn't exist
        new_file = self.persistent_dir / f"{new_name}.yaml"
        if new_file.exists():
            raise ValueError(f"Display configuration '{new_name}' already exists")

        try:
            with open(source_file, "r") as f:
                content = f.read()

            with open(new_file, "w") as f:
                f.write(content)

            logger.info(f"Display config duplicated: {source_name} -> {new_name}")

            return {
                "status": "success",
                "message": f"Configuration '{source_name}' duplicated as '{new_name}'",
                "source_name": source_name,
                "new_name": new_name,
                "is_custom": True,
                "modified_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error duplicating display config: {e}")
            raise

    def delete_display_config(self, display_name: str) -> Dict:
        """
        Delete a custom display configuration.
        Only custom configs can be deleted.

        Args:
            display_name: Name of the display (without .yaml extension)

        Returns:
            Dictionary with deletion status info

        Raises:
            FileNotFoundError: If custom config doesn't exist
            ValueError: If trying to delete a default config
        """
        persistent_file = self.persistent_dir / f"{display_name}.yaml"

        if not persistent_file.exists():
            raise FileNotFoundError(
                f"Custom configuration not found for '{display_name}'"
            )

        try:
            persistent_file.unlink()
            logger.info(f"Display config deleted: {display_name}")

            return {
                "status": "success",
                "message": f"Configuration '{display_name}' deleted successfully",
                "display_name": display_name,
            }
        except Exception as e:
            logger.error(f"Error deleting display config {display_name}: {e}")
            raise

    def export_display_config(self, display_name: str) -> Tuple[str, str]:
        """
        Export a display configuration as YAML.

        Args:
            display_name: Name of the display (without .yaml extension)

        Returns:
            Tuple of (filename, content)

        Raises:
            FileNotFoundError: If config doesn't exist
        """
        content = self.load_display_config(display_name)
        filename = f"{display_name}.yaml"
        return filename, content

    def import_display_config(
        self, filename: str, yaml_content: str, overwrite: bool = False
    ) -> Dict:
        """
        Import a display configuration from YAML.

        Args:
            filename: Filename (should end with .yaml)
            yaml_content: YAML content as string
            overwrite: Whether to overwrite existing config

        Returns:
            Dictionary with import status info

        Raises:
            ValueError: If filename is invalid or YAML is invalid
            FileExistsError: If config exists and overwrite is False
        """
        # Validate filename
        if not filename.endswith(".yaml"):
            raise ValueError("Filename must end with .yaml")

        display_name = filename[:-5]  # Remove .yaml extension

        if (
            not display_name
            or not display_name.replace("_", "").replace("-", "").isalnum()
        ):
            raise ValueError(
                "Display name must contain only alphanumeric characters, hyphens, and underscores"
            )

        # Check if exists
        config_file = self.persistent_dir / f"{display_name}.yaml"
        if config_file.exists() and not overwrite:
            raise FileExistsError(f"Configuration '{display_name}' already exists")

        # Validate YAML
        try:
            yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")

        try:
            with open(config_file, "w") as f:
                f.write(yaml_content)

            logger.info(f"Display config imported: {display_name}")

            return {
                "status": "success",
                "message": f"Configuration '{display_name}' imported successfully",
                "display_name": display_name,
                "is_custom": True,
                "modified_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error importing display config: {e}")
            raise
