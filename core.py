from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

# ========= CONFIG =========

HADES_SAVE_DIR = Path(
    "/mnt/jupiter/SteamLibrary/steamapps/compatdata/1145360/pfx/drive_c/users/steamuser/Documents/Saved Games/Hades"
)

BACKUP_SAVE_ROOT = Path.home() / ".local/share/hades_backups"
TAGS_DIR = BACKUP_SAVE_ROOT / "tags"
CONFIG_FILE = BACKUP_SAVE_ROOT / "config.json"

# ==========================


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H-%M-%S")


def assert_game_closed() -> None:
    if not HADES_SAVE_DIR.exists():
        raise RuntimeError("Hades save directory not found.")


# ---------- metadata ----------


def write_meta(snapshot: Path, tags: Iterable[str], note: Optional[str]) -> None:
    meta = {
        "created_at": snapshot.name,
        "tags": sorted(set(tags)),
        "note": note,
    }
    (snapshot / "meta.json").write_text(json.dumps(meta, indent=2))


def read_meta(snapshot: Path) -> dict:
    meta_file = snapshot / "meta.json"
    if not meta_file.exists():
        return {}
    return json.loads(meta_file.read_text())


# ---------- tags ----------


def add_tag(tag: str, snapshot_name: str) -> None:
    TAGS_DIR.mkdir(parents=True, exist_ok=True)
    tag_file = TAGS_DIR / f"{tag}.json"

    items: set[str] = set()
    if tag_file.exists():
        items = set(json.loads(tag_file.read_text()))

    items.add(snapshot_name)
    tag_file.write_text(json.dumps(sorted(items), indent=2))


def snapshots_for_tag(tag: str) -> List[str]:
    tag_file = TAGS_DIR / f"{tag}.json"
    if not tag_file.exists():
        return []
    return json.loads(tag_file.read_text())


def list_tags() -> List[str]:
    if not TAGS_DIR.exists():
        return []
    return sorted(p.stem for p in TAGS_DIR.iterdir())


def get_tag_count(tag: str) -> int:
    """Get number of snapshots for a given tag"""
    return len(snapshots_for_tag(tag))


# ---------- config ----------


def get_last_tag() -> Optional[str]:
    """Get the most recently used tag"""
    if not CONFIG_FILE.exists():
        return None

    try:
        config = json.loads(CONFIG_FILE.read_text())
        return config.get("last_tag")
    except (json.JSONDecodeError, KeyError):
        return None


def set_last_tag(tag: str) -> None:
    """Set the most recently used tag"""
    BACKUP_SAVE_ROOT.mkdir(parents=True, exist_ok=True)

    config = {}
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            config = {}

    config["last_tag"] = tag
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


# ---------- tag management ----------


def rename_tag(old_tag: str, new_tag: str) -> None:
    """Rename a tag"""
    if old_tag == new_tag:
        return

    old_file = TAGS_DIR / f"{old_tag}.json"
    new_file = TAGS_DIR / f"{new_tag}.json"

    if not old_file.exists():
        raise ValueError(f"Tag '{old_tag}' does not exist")

    if new_file.exists():
        raise ValueError(f"Tag '{new_tag}' already exists")

    TAGS_DIR.mkdir(parents=True, exist_ok=True)

    # Update tag file
    snapshots = snapshots_for_tag(old_tag)
    new_file.write_text(json.dumps(snapshots, indent=2))
    old_file.unlink()

    # Update metadata in all snapshots
    for snapshot_name in snapshots:
        snapshot_path = BACKUP_SAVE_ROOT / snapshot_name
        if snapshot_path.exists():
            meta = read_meta(snapshot_path)
            tags = meta.get("tags", [])
            if old_tag in tags:
                tags.remove(old_tag)
                tags.append(new_tag)
                meta["tags"] = sorted(set(tags))
                write_meta(snapshot_path, meta["tags"], meta.get("note"))


def delete_tag(tag: str) -> None:
    """Delete a tag completely"""
    tag_file = TAGS_DIR / f"{tag}.json"

    if not tag_file.exists():
        raise ValueError(f"Tag '{tag}' does not exist")

    # Remove tag from metadata in all snapshots
    snapshots = snapshots_for_tag(tag)
    for snapshot_name in snapshots:
        snapshot_path = BACKUP_SAVE_ROOT / snapshot_name
        if snapshot_path.exists():
            meta = read_meta(snapshot_path)
            tags = meta.get("tags", [])
            if tag in tags:
                tags.remove(tag)
                meta["tags"] = sorted(set(tags))
                write_meta(snapshot_path, meta["tags"], meta.get("note"))

    # Delete tag file
    tag_file.unlink()


def merge_tags(source_tag: str, target_tag: str) -> None:
    """Merge source_tag into target_tag"""
    if source_tag == target_tag:
        return

    source_file = TAGS_DIR / f"{source_tag}.json"
    target_file = TAGS_DIR / f"{target_tag}.json"

    if not source_file.exists():
        raise ValueError(f"Source tag '{source_tag}' does not exist")

    TAGS_DIR.mkdir(parents=True, exist_ok=True)

    # Get all snapshots from both tags
    source_snapshots = set(snapshots_for_tag(source_tag))
    target_snapshots = set(snapshots_for_tag(target_tag))

    # Merge snapshots
    all_snapshots = source_snapshots.union(target_snapshots)

    # Update target tag file
    target_file.write_text(json.dumps(sorted(all_snapshots), indent=2))

    # Update metadata for all affected snapshots
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

    # Delete source tag file
    source_file.unlink()


# ---------- snapshots ----------


def list_snapshots() -> List[Path]:
    if not BACKUP_SAVE_ROOT.exists():
        return []
    return sorted(
        [p for p in BACKUP_SAVE_ROOT.iterdir() if p.is_dir() and p.name != "tags"],
        reverse=True,
    )


def save(tags: List[str], note: Optional[str]) -> Path:
    assert_game_closed()

    dest = BACKUP_SAVE_ROOT / now_ts()
    BACKUP_SAVE_ROOT.mkdir(parents=True, exist_ok=True)

    shutil.copytree(HADES_SAVE_DIR, dest)
    write_meta(dest, tags, note)

    for tag in tags:
        add_tag(tag, dest.name)

    return dest


def restore(snapshot: Path) -> None:
    assert_game_closed()

    tmp = HADES_SAVE_DIR.with_suffix(".tmp")
    if tmp.exists():
        shutil.rmtree(tmp)

    shutil.move(HADES_SAVE_DIR, tmp)
    shutil.copytree(snapshot, HADES_SAVE_DIR)
    shutil.rmtree(tmp)


def restore_by_tag(tag: str) -> None:
    matches = snapshots_for_tag(tag)
    if not matches:
        raise ValueError(f"No snapshots for tag '{tag}'")

    restore(BACKUP_SAVE_ROOT / sorted(matches)[-1])


def delete_snapshot(snapshot: Path) -> None:
    shutil.rmtree(snapshot)
