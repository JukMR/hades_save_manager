from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

# ========= CONFIG =========

HADES_SAVE_DIR = Path(
    "/mnt/jupiter/SteamLibrary/steamapps/compatdata/1145360/pfx/drive_c/users/steamuser/Documents/Saved Games/Hades"
)

BACKUP_SAVE_ROOT = Path.home() / ".local/share/hades_backups"
TAGS_DIR = BACKUP_SAVE_ROOT / "tags"
CONFIG_FILE = BACKUP_SAVE_ROOT / "config.json"
LOG_FILE = BACKUP_SAVE_ROOT / "hades.log"

# ==========================


# ---------- logging ----------


class Logger:
    """Simple logging system for Hades backup operations"""

    def __init__(self):
        self.logs: List[Tuple[datetime, str, str]] = []  # (timestamp, level, message)
        self.max_logs = 50  # Keep last 50 log entries

    def log(self, level: str, message: str) -> None:
        """Add a log entry"""
        timestamp = datetime.now()
        entry = (timestamp, level, message)
        self.logs.append(entry)

        # Keep only the last max_logs entries
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs :]

        # Also write to file
        self._write_to_file(timestamp, level, message)

    def info(self, message: str) -> None:
        """Log an info message"""
        self.log("INFO", message)

    def error(self, message: str) -> None:
        """Log an error message"""
        self.log("ERROR", message)

    def success(self, message: str) -> None:
        """Log a success message"""
        self.log("SUCCESS", message)

    def warning(self, message: str) -> None:
        """Log a warning message"""
        self.log("WARNING", message)

    def get_recent_logs(self, count: int = 10) -> List[str]:
        """Get recent log entries as formatted strings"""
        recent = self.logs[-count:] if self.logs else []
        return [f"[{ts.strftime('%H:%M:%S')}] {level}: {msg}" for ts, level, msg in recent]

    def clear(self) -> None:
        """Clear all logs"""
        self.logs.clear()

    def _write_to_file(self, timestamp: datetime, level: str, message: str) -> None:
        """Write log entry to file"""
        try:
            BACKUP_SAVE_ROOT.mkdir(parents=True, exist_ok=True)
            log_line = f"{timestamp.isoformat()} {level}: {message}\n"
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            # Don't let logging errors break the application
            pass


# Global logger instance
logger = Logger()


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H-%M-%S")


def assert_game_folder_exist() -> None:
    if not HADES_SAVE_DIR.exists():
        raise RuntimeError("Hades save directory not found.")


# ---------- metadata ----------w


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


def rename_tag(old_tag: str, new_tag: str) -> Tuple[bool, str]:
    """Rename a tag. Returns (success, message)"""
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
        updated_count = 0
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
                    updated_count += 1

        success_msg = f"Renamed tag '{old_tag}' to '{new_tag}' (updated {updated_count} snapshots)"
        logger.success(success_msg)
        return True, success_msg
    except Exception as e:
        error_msg = f"Failed to rename tag: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def delete_tag(tag: str) -> Tuple[bool, str]:
    """Delete a tag completely. Returns (success, message)"""
    tag_file = TAGS_DIR / f"{tag}.json"

    if not tag_file.exists():
        error_msg = f"Tag '{tag}' does not exist"
        logger.error(error_msg)
        return False, error_msg

    try:
        # Remove tag from metadata in all snapshots
        snapshots = snapshots_for_tag(tag)
        updated_count = 0
        for snapshot_name in snapshots:
            snapshot_path = BACKUP_SAVE_ROOT / snapshot_name
            if snapshot_path.exists():
                meta = read_meta(snapshot_path)
                tags = meta.get("tags", [])
                if tag in tags:
                    tags.remove(tag)
                    meta["tags"] = sorted(set(tags))
                    write_meta(snapshot_path, meta["tags"], meta.get("note"))
                    updated_count += 1

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
    """Merge source_tag into target_tag. Returns (success, message)"""
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


# ---------- snapshots ----------


def list_snapshots() -> List[Path]:
    if not BACKUP_SAVE_ROOT.exists():
        return []
    return sorted(
        [p for p in BACKUP_SAVE_ROOT.iterdir() if p.is_dir() and p.name != "tags"],
        reverse=True,
    )


def save(tags: List[str], note: Optional[str]) -> Tuple[Optional[Path], str]:
    """Create a new snapshot. Returns (path, message)"""
    try:
        assert_game_folder_exist()

        dest = BACKUP_SAVE_ROOT / now_ts()
        BACKUP_SAVE_ROOT.mkdir(parents=True, exist_ok=True)

        shutil.copytree(HADES_SAVE_DIR, dest)
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
    """Restore a snapshot. Returns (success, message)"""
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
    """Restore latest snapshot with given tag. Returns (success, message)"""
    try:
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
    """Delete a snapshot and clean up tag references."""
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
