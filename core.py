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

BACKUP_ROOT = Path.home() / ".local/share/hades_backups"
TAGS_DIR = BACKUP_ROOT / "tags"

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


# ---------- snapshots ----------


def list_snapshots() -> List[Path]:
    if not BACKUP_ROOT.exists():
        return []
    return sorted(
        [p for p in BACKUP_ROOT.iterdir() if p.is_dir() and p.name != "tags"],
        reverse=True,
    )


def backup(tags: List[str], note: Optional[str]) -> Path:
    assert_game_closed()

    dest = BACKUP_ROOT / now_ts()
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

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

    restore(BACKUP_ROOT / sorted(matches)[-1])


def delete_snapshot(snapshot: Path) -> None:
    shutil.rmtree(snapshot)
