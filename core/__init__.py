"""Core module for Hades save backup tool.

This module provides all the core functionality for managing Hades game saves,
including snapshot creation, restoration, tagging, and metadata management.
"""

# Re-export all functions for backward compatibility
from .config import get_last_tag, set_last_tag
from .constants import *
from .logger import logger
from .metadata_handler import read_meta, write_meta
from .snapshot_manager import (
    assert_game_folder_exist,
    delete_snapshot,
    list_snapshots,
    now_ts,
    restore,
    restore_by_tag,
    save,
)
from .tag_manager import (
    add_tag,
    delete_tag,
    get_tag_count,
    list_tags,
    merge_tags,
    rename_tag,
    snapshots_for_tag,
)

__all__ = [
    # Constants
    "HADES_SAVE_DIR",
    "BACKUP_SAVE_ROOT",
    "SAVES_DIR",
    "CONFIG_FILE",
    "LOG_FILE",
    # Logger
    "logger",
    # Metadata
    "read_meta",
    "write_meta",
    # Tags
    "add_tag",
    "delete_tag",
    "get_tag_count",
    "list_tags",
    "merge_tags",
    "rename_tag",
    "snapshots_for_tag",
    # Config
    "get_last_tag",
    "set_last_tag",
    # Snapshots
    "assert_game_folder_exist",
    "delete_snapshot",
    "list_snapshots",
    "now_ts",
    "restore",
    "restore_by_tag",
    "save",
]
