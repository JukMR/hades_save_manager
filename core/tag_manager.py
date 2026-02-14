"""Tag management for Hades save snapshots."""

import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from .constants import BACKUP_SAVE_ROOT
from .logger import logger


def add_tag(tag: str, snapshot_path: Path) -> None:
    """Copy a snapshot to a tag directory.

    Args:
        tag: Name of the tag
        snapshot_path: Path to the snapshot to add
    """
    tag_dir = BACKUP_SAVE_ROOT / tag
    tag_dir.mkdir(exist_ok=True)

    # Copy the snapshot to the tag directory
    # This allows the same snapshot to exist in multiple tags
    new_snapshot_path = tag_dir / snapshot_path.name
    if not new_snapshot_path.exists():
        import shutil
        shutil.copytree(snapshot_path, new_snapshot_path)


def snapshots_for_tag(tag: str) -> List[str]:
    """Get all snapshots for a given tag.

    Args:
        tag: Name of the tag

    Returns:
        List of snapshot names, empty if tag doesn't exist
    """
    tag_dir = BACKUP_SAVE_ROOT / tag
    if not tag_dir.exists():
        return []
    
    # Return the names of all directories in the tag directory (which represent snapshots)
    return [item.name for item in tag_dir.iterdir() if item.is_dir()]


def list_tags() -> List[str]:
    """Get list of all available tags.

    Returns:
        Sorted list of tag names
    """
    # Tags are directories in the backup root that are not reserved names
    reserved_names = {'saves', 'config.json', 'hades.log', 'tags'}
    if not BACKUP_SAVE_ROOT.exists():
        return []
    return sorted(
        p.name for p in BACKUP_SAVE_ROOT.iterdir() 
        if p.is_dir() and p.name not in reserved_names
    )


def get_tag_count(tag: str) -> int:
    """Get number of snapshots for a given tag.

    Args:
        tag: Name of the tag

    Returns:
        Number of snapshots with this tag
    """
    return len(snapshots_for_tag(tag))


def rename_tag(old_tag: str, new_tag: str) -> Tuple[bool, str]:
    """Rename a tag (directory).

    Args:
        old_tag: Current tag name
        new_tag: New tag name

    Returns:
        Tuple of (success, message)
    """
    if not old_tag or not new_tag:
        return False, "Tag names cannot be empty"
    if old_tag == new_tag:
        return False, "New tag name is the same as old name"

    old_dir = BACKUP_SAVE_ROOT / old_tag
    new_dir = BACKUP_SAVE_ROOT / new_tag

    if not old_dir.exists():
        error_msg = f"Tag '{old_tag}' does not exist"
        logger.error(error_msg)
        return False, error_msg

    if new_dir.exists():
        error_msg = f"Tag '{new_tag}' already exists"
        logger.error(error_msg)
        return False, error_msg

    try:
        # Rename the tag directory
        old_dir.rename(new_dir)

        success_msg = f"Renamed tag '{old_tag}' to '{new_tag}'"
        logger.success(success_msg)
        return True, success_msg
    except Exception as e:
        error_msg = f"Failed to rename tag: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def delete_tag(tag: str) -> Tuple[bool, str]:
    """Delete a tag completely (and all snapshots in it).

    Args:
        tag: Name of the tag to delete

    Returns:
        Tuple of (success, message)
    """
    tag_dir = BACKUP_SAVE_ROOT / tag

    if not tag_dir.exists():
        error_msg = f"Tag '{tag}' does not exist"
        logger.error(error_msg)
        return False, error_msg

    try:
        # Delete tag directory and all its contents
        shutil.rmtree(tag_dir)

        success_msg = f"Deleted tag '{tag}' and all its snapshots"
        logger.success(success_msg)
        return True, success_msg
    except Exception as e:
        error_msg = f"Failed to delete tag: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def get_snapshot_tag(snapshot_path: Path) -> Optional[str]:
    """Get the tag directory name that contains this snapshot.

    Args:
        snapshot_path: Path to the snapshot

    Returns:
        Name of the tag directory, or None if not found
    """
    if not BACKUP_SAVE_ROOT.exists():
        return None
    
    reserved_names = {'saves', 'config.json', 'hades.log', 'tags'}
    
    for tag_dir in BACKUP_SAVE_ROOT.iterdir():
        if tag_dir.is_dir() and tag_dir.name not in reserved_names:
            # Check if this snapshot exists in this tag directory
            snapshot_in_tag = tag_dir / snapshot_path.name
            if snapshot_in_tag.exists() and snapshot_in_tag.is_dir():
                return tag_dir.name
    
    return None


def merge_tags(source_tag: str, target_tag: str) -> Tuple[bool, str]:
    """Merge source_tag into target_tag by moving all snapshots.

    Args:
        source_tag: Tag to merge from
        target_tag: Tag to merge into

    Returns:
        Tuple of (success, message)
    """
    if source_tag == target_tag:
        return False, "Cannot merge tag into itself"

    source_dir = BACKUP_SAVE_ROOT / source_tag
    target_dir = BACKUP_SAVE_ROOT / target_tag

    if not source_dir.exists():
        error_msg = f"Source tag '{source_tag}' does not exist"
        logger.error(error_msg)
        return False, error_msg

    try:
        # Create target directory if it doesn't exist
        target_dir.mkdir(exist_ok=True)

        # Move all snapshots from source to target
        for snapshot in source_dir.iterdir():
            if snapshot.is_dir():
                target_snapshot_path = target_dir / snapshot.name
                if not target_snapshot_path.exists():
                    # Copy the snapshot to target directory
                    shutil.copytree(snapshot, target_snapshot_path)

        # Delete source tag directory
        shutil.rmtree(source_dir)

        success_msg = f"Merged tag '{source_tag}' into '{target_tag}'"
        logger.success(success_msg)
        return True, success_msg
    except Exception as e:
        error_msg = f"Failed to merge tags: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
