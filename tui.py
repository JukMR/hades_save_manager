from __future__ import annotations

import curses
from typing import List

import core

# ---------- colors ----------


def init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_CYAN, -1)  # headers
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)  # selected row
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # metadata
    curses.init_pair(4, curses.COLOR_RED, -1)  # warnings
    curses.init_pair(5, curses.COLOR_GREEN, -1)  # success / hints


# ---------- UI helpers ----------


def prompt(stdscr, y: int, msg: str) -> str:
    curses.echo()
    stdscr.addstr(y, 2, msg, curses.color_pair(3))
    stdscr.clrtoeol()
    val = stdscr.getstr(y, 2 + len(msg)).decode()
    curses.noecho()
    return val


def confirm(stdscr, title: str, msg: str) -> bool:
    h, w = stdscr.getmaxyx()
    win_h, win_w = 7, max(len(msg) + 6, 40)

    win = curses.newwin(
        win_h,
        win_w,
        (h - win_h) // 2,
        (w - win_w) // 2,
    )
    win.box()

    win.addstr(1, 2, title, curses.color_pair(4) | curses.A_BOLD)
    win.addstr(3, 2, msg)
    win.addstr(5, 2, "[y] Yes    [n] No", curses.color_pair(5))

    win.refresh()

    while True:
        k = win.getch()
        if k in (ord("y"), ord("Y")):
            return True
        if k in (ord("n"), ord("N"), 27):
            return False


def draw(stdscr, items: List[core.Path], idx: int) -> None:
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    left_w = w // 2

    stdscr.addstr(0, 2, "Snapshots", curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(0, left_w + 2, "Metadata", curses.color_pair(1) | curses.A_BOLD)

    for i, snap in enumerate(items[: h - 4]):
        y = 2 + i
        if i == idx:
            stdscr.addstr(y, 2, snap.name.ljust(left_w - 4), curses.color_pair(2))
        else:
            stdscr.addstr(y, 2, snap.name)

    if items:
        meta = core.read_meta(items[idx])
        y = 2
        stdscr.addstr(
            y,
            left_w + 2,
            f"Created: {meta.get('created_at', '')}",
            curses.color_pair(3),
        )
        y += 2
        stdscr.addstr(
            y,
            left_w + 2,
            f"Tags: {', '.join(meta.get('tags', []))}",
            curses.color_pair(3),
        )
        y += 2
        stdscr.addstr(y, left_w + 2, "Note:", curses.A_BOLD)
        y += 1
        for line in (meta.get("note") or "").splitlines():
            stdscr.addstr(y, left_w + 4, line)
            y += 1

    stdscr.addstr(
        h - 2,
        2,
        "[↑↓] move  [b] backup  [r] restore  [t] restore-tag  [d] delete  [q] quit",
        curses.color_pair(5),
    )

    stdscr.refresh()


# ---------- main loop ----------


def main(stdscr) -> None:
    curses.curs_set(0)
    init_colors()

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
            snap = items[idx]
            if confirm(stdscr, "Restore snapshot", f"Restore {snap.name}?"):
                core.restore(snap)

        elif key == ord("d") and items:
            snap = items[idx]
            if confirm(stdscr, "Delete snapshot", f"Delete {snap.name}? This is permanent."):
                core.delete_snapshot(snap)
                idx = 0

        elif key == ord("t"):
            tag = prompt(stdscr, 1, "Restore tag: ")
            if confirm(stdscr, "Restore by tag", f"Restore latest snapshot tagged '{tag}'?"):
                core.restore_by_tag(tag)


if __name__ == "__main__":
    curses.wrapper(main)
