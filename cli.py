from __future__ import annotations

import argparse

import core


def main() -> None:
    parser = argparse.ArgumentParser("Hades save backup tool")
    sub = parser.add_subparsers(dest="cmd", required=True)

    save_p = sub.add_parser("save")
    save_p.add_argument("--tag", action="append", default=[])
    save_p.add_argument("--note")

    list_p = sub.add_parser("list")
    list_p.add_argument("--meta", action="store_true")

    sub.add_parser("list-tags")

    restore_p = sub.add_parser("restore")
    restore_p.add_argument("name")

    restore_tag_p = sub.add_parser("restore-tag")
    restore_tag_p.add_argument("tag")

    # Tag management commands
    rename_p = sub.add_parser("rename-tag")
    rename_p.add_argument("old")
    rename_p.add_argument("new")

    delete_tag_p = sub.add_parser("delete-tag")
    delete_tag_p.add_argument("tag")

    merge_p = sub.add_parser("merge-tags")
    merge_p.add_argument("source")
    merge_p.add_argument("target")

    # Log viewing
    sub.add_parser("logs")

    args = parser.parse_args()

    if args.cmd == "save":
        result, message = core.save(args.tag, args.note)
        if result:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            exit(1)

    elif args.cmd == "list":
        for snap in core.list_snapshots():
            if args.meta:
                meta = core.read_meta(snap)
                print(f"{snap.name} tags={meta.get('tags', [])} note={meta.get('note')}")
            else:
                print(snap.name)

    elif args.cmd == "list-tags":
        for tag in core.list_tags():
            count = core.get_tag_count(tag)
            print(f"{tag} ({count} snapshots)")

    elif args.cmd == "restore":
        result, message = core.restore(core.BACKUP_SAVE_ROOT / args.name)
        if result:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            exit(1)

    elif args.cmd == "restore-tag":
        result, message = core.restore_by_tag(args.tag)
        if result:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            exit(1)

    elif args.cmd == "rename-tag":
        result, message = core.rename_tag(args.old, args.new)
        if result:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            exit(1)

    elif args.cmd == "delete-tag":
        result, message = core.delete_tag(args.tag)
        if result:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            exit(1)

    elif args.cmd == "merge-tags":
        result, message = core.merge_tags(args.source, args.target)
        if result:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            exit(1)

    elif args.cmd == "logs":
        logs = core.logger.get_recent_logs(20)
        if logs:
            print("Recent logs:")
            for log in logs:
                print(log)
        else:
            print("No logs available")


if __name__ == "__main__":
    main()
