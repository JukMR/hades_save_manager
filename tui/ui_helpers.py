"""UI helper functions for the TUI."""

import curses
from typing import Any


def prompt(stdscr: Any, y: int, msg: str) -> str:
    """Display a prompt and get user input.

    Args:
        stdscr: The curses screen object
        y: Y coordinate for the prompt
        msg: Prompt message to display

    Returns:
        User input string
    """
    from .colors import ColorPairs

    curses.echo()
    stdscr.addstr(y, 2, msg, curses.color_pair(ColorPairs.YELLOW))
    stdscr.clrtoeol()
    val = stdscr.getstr(y, 2 + len(msg)).decode()
    curses.noecho()
    return val


def confirm(stdscr: Any, title: str, msg: str) -> bool:
    """Display a confirmation dialog.

    Args:
        stdscr: The curses screen object
        title: Dialog title
        msg: Confirmation message

    Returns:
        True if user confirms, False otherwise
    """
    from .colors import ColorPairs

    h, w = stdscr.getmaxyx()
    win_h, win_w = 7, max(len(msg) + 6, 44)

    win = curses.newwin(
        win_h,
        win_w,
        (h - win_h) // 2,
        (w - win_w) // 2,
    )
    win.keypad(True)

    selected = 0  # 0 = Yes, 1 = No

    while True:
        win.clear()
        win.box()
        win.addstr(1, 2, title, curses.color_pair(ColorPairs.RED) | curses.A_BOLD)
        win.addstr(3, 2, msg)

        yes_attr = curses.A_REVERSE if selected == 0 else curses.A_NORMAL
        no_attr = curses.A_REVERSE if selected == 1 else curses.A_NORMAL

        win.addstr(5, 8, " Yes ", yes_attr | curses.color_pair(ColorPairs.BLUE))
        win.addstr(5, 16, " No ", no_attr | curses.color_pair(ColorPairs.BLUE))
        win.refresh()

        k = win.getch()

        if k in (curses.KEY_LEFT, curses.KEY_RIGHT):
            selected = 1 - selected
        elif k in (10, 13):  # Enter
            return selected == 0
        elif k in (27,):  # Esc
            return False
