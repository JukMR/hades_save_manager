from __future__ import annotations

import curses
from typing import List

import core


def prompt(stdscr, y: int, msg: str) -> str:
    curses.echo()
    stdscr.addstr(y, 2, msg)
    stdscr.clrtoeol()
    val = stdscr.getstr(y, 2 + len(msg)).decode()
    curses.noecho()
    return val


def draw(stdscr, items: List[core.Path], idx: int) -> None:
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    left_w = w // 2

    stdscr.addstr(0, 2, "Snapshots")
    stdscr.addstr(0, left_w + 2, "Metadata")

    for i, snap in enumerate(items[: h - 4]):
        marker = "➤" if i == idx else " "
        stdscr.addstr(2 + i, 2, f"{marker} {snap.name}")

    if items:
        meta = core.read_meta(items[idx])
        y = 2
        stdscr.addstr(y, left_w + 2, f"Created: {meta.get('created_at', '')}")
        y += 2
        stdscr.addstr(y, left_w + 2, f"Tags: {', '.join(meta.get('tags', []))}")
        y += 2
        stdscr.addstr(y, left_w + 2, "Note:")
        y += 1
        for line in (meta.get("note") or "").splitlines():
            stdscr.addstr(y, left_w + 4, line)
            y += 1

    stdscr.addstr(
        h - 2,
        2,
        "[↑↓] move  [b] backup  [r] restore  [t] restore-tag  [d] delete  [q] quit",
    )

    stdscr.refresh()


def main(stdscr) -> None:
    curses.curs_set(0)
    idx = 0

    while True:
        items = core.list_snapshots()
        if items:
            idx = max(0, min(idx, len(items) - 1))

        draw(stdscr, items, idx)
        key = stdscr.getch()

        if key == curses.KEY_UP:
            idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN:
            idx = min(len(items) - 1, idx + 1)
        elif key == ord("q"):
            break
        elif key == ord("b"):
            tags = prompt(stdscr, 1, "Tags (comma): ").split(",")
            note = prompt(stdscr, 2, "Note: ")
            core.backup([t.strip() for t in tags if t.strip()], note)
        elif key == ord("r") and items:
            core.restore(items[idx])
        elif key == ord("d") and items:
            core.delete_snapshot(items[idx])
        elif key == ord("t"):
            tag = prompt(stdscr, 1, "Restore tag: ")
            core.restore_by_tag(tag)


if __name__ == "__main__":
    curses.wrapper(main)
