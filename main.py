from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional


# ========= CONFIG =========

HADES_SAVE_DIR = Path(
    "/mnt/jupiter/SteamLibrary/steamapps/compatdata/1145360/"
    "pfx/drive_c/users/steamuser/Documents/Saved Games/Hades"
)

BACKUP_ROOT = Path.home() / ".local/share/hades_backups"
TAGS_DIR = BACKUP_ROOT / "tags"

# ==========================


def assert_game_closed() -> None:
    if not HADES_SAVE_DIR.exists():
        raise RuntimeError("Hades save directory not found.")


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H-%M-%S")


# ---------- metadata ----------


def write_meta(snapshot: Path, tags: Iterable[str], note: Optional[str]) -> None:
    meta = {
        "created_at": snapshot.name,
        "tags": sorted(set(tags)),
        "note": note,
    }
    with (snapshot / "meta.json").open("w") as f:
        json.dump(meta, f, indent=2)


def read_meta(snapshot: Path) -> dict:
    meta_file = snapshot / "meta.json"
    if not meta_file.exists():
        return {}
    return json.loads(meta_file.read_text())


# ---------- tags index ----------


def add_tag(tag: str, snapshot_name: str) -> None:
    TAGS_DIR.mkdir(parents=True, exist_ok=True)
    tag_file = TAGS_DIR / f"{tag}.json"

    snapshots: set[str] = set()
    if tag_file.exists():
        snapshots = set(json.loads(tag_file.read_text()))

    snapshots.add(snapshot_name)
    tag_file.write_text(json.dumps(sorted(snapshots), indent=2))


def snapshots_for_tag(tag: str) -> List[str]:
    tag_file = TAGS_DIR / f"{tag}.json"
    if not tag_file.exists():
        return []
    return json.loads(tag_file.read_text())


# ---------- backup / restore ----------


def update_latest_symlink(target: Path) -> None:
    link = BACKUP_ROOT / "latest"
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(target.name)


def backup(tags: List[str], note: Optional[str]) -> Path:
    assert_game_closed()

    dest = BACKUP_ROOT / now_ts()
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    shutil.copytree(HADES_SAVE_DIR, dest)
    write_meta(dest, tags, note)

    for tag in tags:
        add_tag(tag, dest.name)

    update_latest_symlink(dest)
    print(f"Backup created: {dest.name}  tags={tags}")
    return dest


def restore(snapshot_name: str) -> None:
    assert_game_closed()

    src = BACKUP_ROOT / snapshot_name
    if not src.exists():
        raise ValueError(f"Snapshot not found: {snapshot_name}")

    tmp = HADES_SAVE_DIR.with_suffix(".tmp")

    if tmp.exists():
        shutil.rmtree(tmp)

    shutil.move(HADES_SAVE_DIR, tmp)
    shutil.copytree(src, HADES_SAVE_DIR)
    shutil.rmtree(tmp)

    print(f"Restored snapshot: {snapshot_name}")


def restore_by_tag(tag: str) -> None:
    matches = snapshots_for_tag(tag)
    if not matches:
        raise ValueError(f"No snapshots found for tag '{tag}'")

    # deterministic: most recent snapshot with that tag
    restore(sorted(matches)[-1])


def list_snapshots(show_meta: bool) -> None:
    if not BACKUP_ROOT.exists():
        return

    for p in sorted(BACKUP_ROOT.iterdir()):
        if not p.is_dir() or p.name == "tags":
            continue

        if show_meta:
            meta = read_meta(p)
            tags = ",".join(meta.get("tags", []))
            note = meta.get("note", "")
            print(f"{p.name}  tags=[{tags}]  note={note}")
        else:
            print(p.name)


def list_tags() -> None:
    if not TAGS_DIR.exists():
        return
    for p in sorted(TAGS_DIR.iterdir()):
        print(p.stem)


# ---------- CLI ----------


def main() -> None:
    parser = argparse.ArgumentParser("Hades save backup tool")
    sub = parser.add_subparsers(dest="cmd", required=True)

    backup_p = sub.add_parser("backup")
    backup_p.add_argument("--tag", action="append", default=[])
    backup_p.add_argument("--note")

    sub.add_parser("list").add_argument("--meta", action="store_true")

    sub.add_parser("list-tags")

    restore_p = sub.add_parser("restore")
    restore_p.add_argument("name")

    restore_tag_p = sub.add_parser("restore-tag")
    restore_tag_p.add_argument("tag")

    args = parser.parse_args()

    if args.cmd == "backup":
        backup(args.tag, args.note)
    elif args.cmd == "list":
        list_snapshots(args.meta)
    elif args.cmd == "list-tags":
        list_tags()
    elif args.cmd == "restore":
        restore(args.name)
    elif args.cmd == "restore-tag":
        restore_by_tag(args.tag)


if __name__ == "__main__":
    main()

