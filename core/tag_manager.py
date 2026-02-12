"""Tag management for Hades save snapshots."""

import json
import shutil
from typing import List, Tuple

from .constants import BACKUP_SAVE_ROOT, TAGS_BASE_DIR
from .logger import logger
from .metadata_handler import read_meta, write_meta


def add_tag(tag: str, snapshot_name: str) -> None:
    """Add a snapshot to a tag by creating a symlink.

    Args:
        tag: Name of the tag
        snapshot_name: Name of the snapshot to add
    """
    TAGS_BASE_DIR.mkdir(parents=True, exist_ok=True)
    tag_dir = TAGS_BASE_DIR / tag
    tag_dir.mkdir(exist_ok=True)

    # Create a symlink from the tag directory to the actual snapshot
    snapshot_src = BACKUP_SAVE_ROOT / snapshot_name
    snapshot_link = tag_dir / snapshot_name
    
    if snapshot_src.exists() and not snapshot_link.exists():
        snapshot_link.symlink_to(snapshot_src)


def snapshots_for_tag(tag: str) -> List[str]:
    """Get all snapshots for a given tag.

    Args:
        tag: Name of the tag

    Returns:
        List of snapshot names, empty if tag doesn't exist
    """
    tag_dir = TAGS_BASE_DIR / tag
    if not tag_dir.exists():
        return []
    
    # Return the names of all symlinks in the tag directory (which represent snapshots)
    return [item.name for item in tag_dir.iterdir() if item.is_symlink() or item.is_dir()]


def list_tags() -> List[str]:
    """Get list of all available tags.

    Returns:
        Sorted list of tag names
    """
    if not TAGS_BASE_DIR.exists():
        return []
    return sorted(p.name for p in TAGS_BASE_DIR.iterdir() if p.is_dir())


def get_tag_count(tag: str) -> int:
    """Get number of snapshots for a given tag.

    Args:
        tag: Name of the tag

    Returns:
        Number of snapshots with this tag
    """
    return len(snapshots_for_tag(tag))


def rename_tag(old_tag: str, new_tag: str) -> Tuple[bool, str]:
    """Rename a tag with enhanced validation and metadata update."""
    if not old_tag or not new_tag:
        return False, "Tag names cannot be empty"
    if old_tag == new_tag:
        return False, "New tag name is the same as old name"

    old_dir = TAGS_BASE_DIR / old_tag
    new_dir = TAGS_BASE_DIR / new_tag

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

        # Update metadata in all snapshots
        snapshots = snapshots_for_tag(new_tag)
        updated_count = _update_metadata_tag_references(
            snapshots, old_tag, new_tag, "rename"
        )

        success_msg = f"Renamed tag '{old_tag}' to '{new_tag}' (updated {updated_count} snapshots)"
        logger.success(success_msg)
        return True, success_msg
    except Exception as e:
        error_msg = f"Failed to rename tag: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def delete_tag(tag: str) -> Tuple[bool, str]:
    """Delete a tag completely.

    Args:
        tag: Name of the tag to delete

    Returns:
        Tuple of (success, message)
    """
    tag_dir = TAGS_BASE_DIR / tag

    if not tag_dir.exists():
        error_msg = f"Tag '{tag}' does not exist"
        logger.error(error_msg)
        return False, error_msg

    try:
        # Remove tag from metadata in all snapshots
        snapshots = snapshots_for_tag(tag)
        updated_count = _update_metadata_tag_references(snapshots, tag, None, "delete")

        # Delete tag directory and all its symlinks (but not the actual snapshots)
        import shutil
        shutil.rmtree(tag_dir)

        success_msg = f"Deleted tag '{tag}' (removed from {updated_count} snapshots)"
        logger.success(success_msg)
        return True, success_msg
    except Exception as e:
        error_msg = f"Failed to delete tag: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def merge_tags(source_tag: str, target_tag: str) -> Tuple[bool, str]:
    """Merge source_tag into target_tag.

    Args:
        source_tag: Tag to merge from
        target_tag: Tag to merge into

    Returns:
        Tuple of (success, message)
    """
    if source_tag == target_tag:
        return False, "Cannot merge tag into itself"

    source_dir = TAGS_BASE_DIR / source_tag
    target_dir = TAGS_BASE_DIR / target_tag

    if not source_dir.exists():
        error_msg = f"Source tag '{source_tag}' does not exist"
        logger.error(error_msg)
        return False, error_msg

    try:
        # Create target directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)

        # Get all snapshots from both tags
        source_snapshots = set(snapshots_for_tag(source_tag))
        target_snapshots = set(snapshots_for_tag(target_tag))

        # Create symlinks in target directory for all source snapshots
        for snapshot_name in source_snapshots:
            source_snapshot_path = BACKUP_SAVE_ROOT / snapshot_name
            target_snapshot_link = target_dir / snapshot_name
            
            # Create a symlink in the target directory pointing to the actual snapshot
            if source_snapshot_path.exists() and not target_snapshot_link.exists():
                target_snapshot_link.symlink_to(source_snapshot_path)

        # Update metadata for all affected snapshots
        all_snapshots = source_snapshots.union(target_snapshots)
        updated_count = 0
        for snapshot_name in all_snapshots:
            snapshot_path = BACKUP_SAVE_ROOT / snapshot_name
            if snapshot_path.exists():
                meta = read_meta(snapshot_path)
                tags = set(meta.get("tags", []))

                # Remove source tag, add target tag
                tags.discard(source_tag)
                tags.add(target_tag)

                meta["tags"] = sorted(tags)
                write_meta(snapshot_path, meta["tags"], meta.get("note"))
                updated_count += 1

        # Delete source tag directory
        import shutil
        shutil.rmtree(source_dir)

        success_msg = f"Merged tag '{source_tag}' into '{target_tag}' (updated {updated_count} snapshots)"
        logger.success(success_msg)
        return True, success_msg
    except Exception as e:
        error_msg = f"Failed to merge tags: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def _update_metadata_tag_references(
    snapshots: List[str], old_tag: str, new_tag: str | None, operation: str
) -> int:
    """Update tag references in snapshot metadata.

    Args:
        snapshots: List of snapshot names to update
        old_tag: Tag to replace/remove
        new_tag: New tag to add (None for delete operation)
        operation: Type of operation ("rename" or "delete")

    Returns:
        Number of snapshots updated
    """
    updated_count = 0
    for snapshot_name in snapshots:
        snapshot_path = BACKUP_SAVE_ROOT / snapshot_name
        if snapshot_path.exists():
            meta = read_meta(snapshot_path)
            tags = meta.get("tags", [])

            if old_tag in tags:
                tags.remove(old_tag)

                if operation == "rename" and new_tag:
                    tags.append(new_tag)

                meta["tags"] = sorted(set(tags))
                write_meta(snapshot_path, meta["tags"], meta.get("note"))
                updated_count += 1

    return updated_count
