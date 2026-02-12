"""Metadata handling for Hades save snapshots."""

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def write_meta(
    snapshot: Path, tags: Iterable[str], note: Optional[str]
) -> None:
    """Write metadata for a snapshot.
    In the new system, we primarily rely on directory names for notes,
    but we'll still maintain minimal metadata for compatibility.

    Args:
        snapshot: Path to the snapshot directory
        tags: Iterable of tag names
        note: Optional note about the snapshot
    """
    # In the new system, the note is part of the directory name
    # So we'll just store the provided note as-is
    meta = {
        "created_at": snapshot.name,  # Store the full name including note
        "tags": sorted(set(tags)),
        "note": note,  # Store the original note
    }
    (snapshot / "meta.json").write_text(json.dumps(meta, indent=2))


def read_meta(snapshot: Path) -> Dict[str, Any]:
    """Read metadata for a snapshot.

    Args:
        snapshot: Path to the snapshot directory

    Returns:
        Dictionary containing metadata, empty if no metadata exists
    """
    meta_file = snapshot / "meta.json"
    if not meta_file.exists():
        # Fallback: extract info from directory name
        snapshot_name = snapshot.name
        parts = snapshot_name.split('_', 1)  # Split on first underscore
        timestamp_part = parts[0]
        note_part = parts[1] if len(parts) > 1 else ""
        
        return {
            "created_at": timestamp_part,
            "tags": [],  # We don't track tags in metadata anymore
            "note": note_part
        }
    return json.loads(meta_file.read_text())
