"""Configuration management for Hades backup tool."""

import json
from typing import Optional

from .constants import BACKUP_SAVE_ROOT, CONFIG_FILE


def get_last_tag() -> Optional[str]:
    """Get the most recently used tag.

    Returns:
        The last used tag name, or None if not found
    """
    if not CONFIG_FILE.exists():
        return None

    try:
        config = json.loads(CONFIG_FILE.read_text())
        return config.get("last_tag")
    except (json.JSONDecodeError, KeyError):
        return None


def set_last_tag(tag: str) -> None:
    """Set the most recently used tag.

    Args:
        tag: Tag name to save as last used
    """
    BACKUP_SAVE_ROOT.mkdir(parents=True, exist_ok=True)

    config = {}
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            config = {}

    config["last_tag"] = tag
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
