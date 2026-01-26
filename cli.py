from __future__ import annotations

import argparse

import core


def main() -> None:
    parser = argparse.ArgumentParser("Hades save backup tool")
    sub = parser.add_subparsers(dest="cmd", required=True)

    backup_p = sub.add_parser("backup")
    backup_p.add_argument("--tag", action="append", default=[])
    backup_p.add_argument("--note")

    list_p = sub.add_parser("list")
    list_p.add_argument("--meta", action="store_true")

    sub.add_parser("list-tags")

    restore_p = sub.add_parser("restore")
    restore_p.add_argument("name")

    restore_tag_p = sub.add_parser("restore-tag")
    restore_tag_p.add_argument("tag")

    args = parser.parse_args()

    if args.cmd == "backup":
        core.backup(args.tag, args.note)

    elif args.cmd == "list":
        for snap in core.list_snapshots():
            if args.meta:
                meta = core.read_meta(snap)
                print(f"{snap.name} tags={meta.get('tags', [])} note={meta.get('note')}")
            else:
                print(snap.name)

    elif args.cmd == "list-tags":
        for tag in core.list_tags():
            print(tag)

    elif args.cmd == "restore":
        core.restore(core.BACKUP_ROOT / args.name)

    elif args.cmd == "restore-tag":
        core.restore_by_tag(args.tag)


if __name__ == "__main__":
    main()
