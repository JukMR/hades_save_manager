"""Snapshot management for Hades save backups."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from .constants import BACKUP_SAVE_ROOT, HADES_SAVE_DIR
from .logger import logger
from .tag_manager import add_tag


def now_ts(note: Optional[str] = None) -> str:
    """Generate current timestamp for snapshot naming with optional note suffix.

    Args:
        note: Optional note to append to timestamp

    Returns:
        Timestamp string in YYYY-MM-DDTHH-MM-SS[_note] format
    """
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    if note:
        # Sanitize note to be filesystem-safe
        sanitized_note = "".join(c for c in note if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        if sanitized_note:
            timestamp = f"{timestamp}_{sanitized_note}"
    return timestamp


def assert_game_folder_exist() -> None:
    """Assert that the Hades save folder exists.

    Raises:
        RuntimeError: If the Hades save directory doesn't exist
    """
    if not HADES_SAVE_DIR.exists():
        raise RuntimeError("Hades save directory not found.")


def list_snapshots() -> List[Path]:
    """Get list of all snapshot directories from all tag directories.

    Returns:
        Sorted list of snapshot paths (newest first)
    """
    all_snapshots = []
    if not BACKUP_SAVE_ROOT.exists():
        return []
    
    # Look for snapshots in all tag directories (excluding reserved names)
    reserved_names = {'config.json', 'hades.log'}
    for item in BACKUP_SAVE_ROOT.iterdir():
        if item.is_dir() and item.name not in reserved_names:
            # Add all snapshots from this tag directory
            for snapshot in item.iterdir():
                if snapshot.is_dir():
                    # Only add each snapshot once (by checking if it's already in the list)
                    if not any(s.name == snapshot.name for s in all_snapshots):
                        all_snapshots.append(snapshot)
    
    return sorted(all_snapshots, reverse=True)


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

        # Create snapshot in the first tag directory
        snapshot_name = now_ts(note)
        
        if not tags:
            # If no tags specified, create a default "untagged" tag
            tags = ["untagged"]
        
        # Create snapshot in the first tag directory
        first_tag = tags[0]
        tag_dir = BACKUP_SAVE_ROOT / first_tag
        tag_dir.mkdir(exist_ok=True)
        
        dest = tag_dir / snapshot_name
        shutil.copytree(HADES_SAVE_DIR, dest)

        # Add to additional tags by copying to those directories
        for tag in tags[1:]:
            add_tag(tag, dest)

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

        # Find the latest snapshot in the tag directory
        tag_dir = BACKUP_SAVE_ROOT / tag
        snapshot_paths = [tag_dir / name for name in matches]
        latest_snapshot = sorted(snapshot_paths, reverse=True)[0]
        return restore(latest_snapshot)
    except Exception as e:
        error_msg = f"Failed to restore by tag: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def delete_snapshot(snapshot: Path) -> Tuple[bool, str]:
    """Delete a snapshot from all tag directories.

    Args:
        snapshot: Path to the snapshot to delete

    Returns:
        Tuple of (success, message)
    """
    try:
        snapshot_name = snapshot.name
        
        # Remove from all tag directories where it exists
        reserved_names = {'config.json', 'hades.log'}
        for tag_dir in BACKUP_SAVE_ROOT.iterdir():
            if tag_dir.is_dir() and tag_dir.name not in reserved_names:
                snapshot_in_tag = tag_dir / snapshot_name
                if snapshot_in_tag.exists() and snapshot_in_tag.is_dir():
                    shutil.rmtree(snapshot_in_tag)

        success_msg = f"Deleted snapshot {snapshot.name}"
        logger.success(success_msg)
        return True, success_msg

    except Exception as e:
        error_msg = f"Failed to delete snapshot: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
