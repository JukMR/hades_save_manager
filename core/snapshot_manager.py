"""Snapshot management for Hades save backups."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from .constants import BACKUP_SAVE_ROOT, HADES_SAVE_DIR, TAGS_DIR
from .logger import logger
from .metadata_handler import read_meta
from .tag_manager import add_tag


def now_ts() -> str:
    """Generate current timestamp for snapshot naming.
    
    Returns:
        Timestamp string in YYYY-MM-DDTHH-MM-SS format
    """
    return datetime.now().strftime("%Y-%m-%dT%H-%M-%S")


def assert_game_folder_exist() -> None:
    """Assert that the Hades save folder exists.
    
    Raises:
        RuntimeError: If the Hades save directory doesn't exist
    """
    if not HADES_SAVE_DIR.exists():
        raise RuntimeError("Hades save directory not found.")


def list_snapshots() -> List[Path]:
    """Get list of all snapshot directories.
    
    Returns:
        Sorted list of snapshot paths (newest first)
    """
    if not BACKUP_SAVE_ROOT.exists():
        return []
    return sorted(
        [p for p in BACKUP_SAVE_ROOT.iterdir() if p.is_dir() and p.name != "tags"],
        reverse=True,
    )


def save(tags: List[str], note: Optional[str]) -> Tuple[Optional[Path], str]:
    """Create a new snapshot.
    
    Args:
        tags: List of tags to associate with the snapshot
        note: Optional note about the snapshot
        
    Returns:
        Tuple of (snapshot_path, message)
    """
    try:
        assert_game_folder_exist()

        dest = BACKUP_SAVE_ROOT / now_ts()
        BACKUP_SAVE_ROOT.mkdir(parents=True, exist_ok=True)

        shutil.copytree(HADES_SAVE_DIR, dest)
        
        # Import here to avoid circular imports
        from .metadata_handler import write_meta
        write_meta(dest, tags, note)

        for tag in tags:
            add_tag(tag, dest.name)

        tag_str = f" with tags {tags}" if tags else ""
        note_str = f" (note: {note})" if note else ""
        success_msg = f"Created snapshot {dest.name}{tag_str}{note_str}"
        logger.success(success_msg)
        return dest, success_msg
    except Exception as e:
        error_msg = f"Failed to create snapshot: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def restore(snapshot: Path) -> Tuple[bool, str]:
    """Restore a snapshot.
    
    Args:
        snapshot: Path to the snapshot to restore
        
    Returns:
        Tuple of (success, message)
    """
    try:
        assert_game_folder_exist()

        tmp = HADES_SAVE_DIR.with_suffix(".tmp")
        if tmp.exists():
            shutil.rmtree(tmp)

        shutil.move(HADES_SAVE_DIR, tmp)
        shutil.copytree(snapshot, HADES_SAVE_DIR)
        shutil.rmtree(tmp)

        success_msg = f"Restored snapshot {snapshot.name}"
        logger.success(success_msg)
        return True, success_msg
    except Exception as e:
        error_msg = f"Failed to restore snapshot: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def restore_by_tag(tag: str) -> Tuple[bool, str]:
    """Restore latest snapshot with given tag.
    
    Args:
        tag: Tag name to restore from
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Import here to avoid circular imports
        from .tag_manager import snapshots_for_tag
        
        matches = snapshots_for_tag(tag)
        if not matches:
            error_msg = f"No snapshots for tag '{tag}'"
            logger.error(error_msg)
            return False, error_msg

        latest_snapshot = BACKUP_SAVE_ROOT / sorted(matches)[-1]
        return restore(latest_snapshot)
    except Exception as e:
        error_msg = f"Failed to restore by tag: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def delete_snapshot(snapshot: Path) -> Tuple[bool, str]:
    """Delete a snapshot and clean up tag references.
    
    Args:
        snapshot: Path to the snapshot to delete
        
    Returns:
        Tuple of (success, message)
    """
    try:
        meta = read_meta(snapshot)
        snapshot_name = snapshot.name

        # Remove snapshot from tag files
        for tag in meta.get("tags", []):
            tag_file = TAGS_DIR / f"{tag}.json"
            if tag_file.exists():
                items = json.loads(tag_file.read_text())
                if snapshot_name in items:
                    items.remove(snapshot_name)
                    tag_file.write_text(json.dumps(sorted(items), indent=2))

        shutil.rmtree(snapshot)

        success_msg = f"Deleted snapshot {snapshot.name}"
        logger.success(success_msg)
        return True, success_msg

    except Exception as e:
        error_msg = f"Failed to delete snapshot: {str(e)}"
        logger.error(error_msg)
        return False, error_msg