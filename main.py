from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


HADES_SAVE_DIR = Path.home() / ".local/share/Supergiant Games/Hades"
BACKUP_ROOT = Path.home() / ".local/share/hades_backups"


def assert_game_closed() -> None:
    if not HADES_SAVE_DIR.exists():
        raise RuntimeError("Hades save directory not found.")


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H-%M-%S")


def backup() -> Path:
    assert_game_closed()

    dest = BACKUP_ROOT / timestamp()
    dest.parent.mkdir(parents=True, exist_ok=True)

    shutil.copytree(HADES_SAVE_DIR, dest)
    update_latest_symlink(dest)

    print(f"Backup created: {dest}")
    return dest


def restore(backup_name: str) -> None:
    assert_game_closed()

    src = BACKUP_ROOT / backup_name
    if not src.exists():
        raise ValueError(f"Backup not found: {backup_name}")

    tmp = HADES_SAVE_DIR.with_suffix(".tmp")

    if tmp.exists():
        shutil.rmtree(tmp)

    shutil.move(HADES_SAVE_DIR, tmp)
    shutil.copytree(src, HADES_SAVE_DIR)
    shutil.rmtree(tmp)

    print(f"Restored backup: {backup_name}")


def list_backups() -> None:
    if not BACKUP_ROOT.exists():
        return

    for p in sorted(BACKUP_ROOT.iterdir()):
        if p.is_dir() and p.name != "latest":
            print(p.name)


def update_latest_symlink(target: Path) -> None:
    link = BACKUP_ROOT / "latest"
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(target.name)


def main() -> None:
    parser = argparse.ArgumentParser("Hades save backup tool")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("backup")
    sub.add_parser("list")

    restore_p = sub.add_parser("restore")
    restore_p.add_argument("name", help="Backup name or 'latest'")

    args = parser.parse_args()

    if args.cmd == "backup":
        backup()
    elif args.cmd == "list":
        list_backups()
    elif args.cmd == "restore":
        restore(args.name)


if __name__ == "__main__":
    main()
