"""Tag management for Hades save snapshots."""

import json
from pathlib import Path
from typing import List, Tuple

from .constants import BACKUP_SAVE_ROOT, TAGS_DIR
from .logger import logger
from .metadata_handler import read_meta, write_meta


def add_tag(tag: str, snapshot_name: str) -> None:
    """Add a snapshot to a tag file.
    
    Args:
        tag: Name of the tag
        snapshot_name: Name of the snapshot to add
    """
    TAGS_DIR.mkdir(parents=True, exist_ok=True)
    tag_file = TAGS_DIR / f"{tag}.json"

    items: set[str] = set()
    if tag_file.exists():
        items = set(json.loads(tag_file.read_text()))

    items.add(snapshot_name)
    tag_file.write_text(json.dumps(sorted(items), indent=2))


def snapshots_for_tag(tag: str) -> List[str]:
    """Get all snapshots for a given tag.
    
    Args:
        tag: Name of the tag
        
    Returns:
        List of snapshot names, empty if tag doesn't exist
    """
    tag_file = TAGS_DIR / f"{tag}.json"
    if not tag_file.exists():
        return []
    return json.loads(tag_file.read_text())


def list_tags() -> List[str]:
    """Get list of all available tags.
    
    Returns:
        Sorted list of tag names
    """
    if not TAGS_DIR.exists():
        return []
    return sorted(p.stem for p in TAGS_DIR.iterdir())


def get_tag_count(tag: str) -> int:
    """Get number of snapshots for a given tag.
    
    Args:
        tag: Name of the tag
        
    Returns:
        Number of snapshots with this tag
    """
    return len(snapshots_for_tag(tag))


def rename_tag(old_tag: str, new_tag: str) -> Tuple[bool, str]:
    """Rename a tag.
    
    Args:
        old_tag: Current tag name
        new_tag: New tag name
        
    Returns:
        Tuple of (success, message)
    """
    if old_tag == new_tag:
        return False, "New tag name is the same as old name"

    old_file = TAGS_DIR / f"{old_tag}.json"
    new_file = TAGS_DIR / f"{new_tag}.json"

    if not old_file.exists():
        error_msg = f"Tag '{old_tag}' does not exist"
        logger.error(error_msg)
        return False, error_msg

    if new_file.exists():
        error_msg = f"Tag '{new_tag}' already exists"
        logger.error(error_msg)
        return False, error_msg

    try:
        TAGS_DIR.mkdir(parents=True, exist_ok=True)

        # Update tag file
        snapshots = snapshots_for_tag(old_tag)
        new_file.write_text(json.dumps(snapshots, indent=2))
        old_file.unlink()

        # Update metadata in all snapshots
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
    tag_file = TAGS_DIR / f"{tag}.json"

    if not tag_file.exists():
        error_msg = f"Tag '{tag}' does not exist"
        logger.error(error_msg)
        return False, error_msg

    try:
        # Remove tag from metadata in all snapshots
        snapshots = snapshots_for_tag(tag)
        updated_count = _update_metadata_tag_references(
            snapshots, tag, None, "delete"
        )

        # Delete tag file
        tag_file.unlink()

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

    source_file = TAGS_DIR / f"{source_tag}.json"
    target_file = TAGS_DIR / f"{target_tag}.json"

    if not source_file.exists():
        error_msg = f"Source tag '{source_tag}' does not exist"
        logger.error(error_msg)
        return False, error_msg

    try:
        TAGS_DIR.mkdir(parents=True, exist_ok=True)

        # Get all snapshots from both tags
        source_snapshots = set(snapshots_for_tag(source_tag))
        target_snapshots = set(snapshots_for_tag(target_tag))

        # Merge snapshots
        all_snapshots = source_snapshots.union(target_snapshots)

        # Update target tag file
        target_file.write_text(json.dumps(sorted(all_snapshots), indent=2))

        # Update metadata for all affected snapshots
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

        # Delete source tag file
        source_file.unlink()

        success_msg = f"Merged tag '{source_tag}' into '{target_tag}' (updated {updated_count} snapshots)"
        logger.success(success_msg)
        return True, success_msg
    except Exception as e:
        error_msg = f"Failed to merge tags: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def _update_metadata_tag_references(
    snapshots: List[str], 
    old_tag: str, 
    new_tag: str | None, 
    operation: str
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