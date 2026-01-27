"""Metadata handling for Hades save snapshots."""

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def write_meta(snapshot: Path, tags: Iterable[str], note: Optional[str]) -> None:
    """Write metadata for a snapshot.
    
    Args:
        snapshot: Path to the snapshot directory
        tags: Iterable of tag names
        note: Optional note about the snapshot
    """
    meta = {
        "created_at": snapshot.name,
        "tags": sorted(set(tags)),
        "note": note,
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
        return {}
    return json.loads(meta_file.read_text())