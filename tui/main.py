"""Refactored TUI main module."""

import curses
from typing import Any

import core

from .colors import init_colors
from .controllers import (
    NavigationController,
    SnapshotController,
    TagController,
    TagInputController,
)
from .drawer import TUIDrawer
from .ui_state import UIState


def main(stdscr: Any) -> None:
    """Main TUI application loop."""
    curses.curs_set(0)
    stdscr.keypad(True)

    init_colors()

    state = UIState()
    drawer = TUIDrawer()

    # Initialize with last used tag logic
    _initialize_tag_selection(state)

    while True:
        drawer.draw(stdscr, state)
        key = stdscr.getch()

        # Handle tag input mode (overrides everything)
        if state.creating_tag or state.renaming_tag:
            controller = TagInputController(stdscr, state)
            if controller.handle_input(key):
                continue  # Input handled, continue loop
            else:
                break  # Quit signal

        # Handle regular input based on active pane
        controller = _get_controller_for_pane(stdscr, state, key)
        result = controller.handle_input(key) if controller else True
        if result is False:  # Quit signal
            break

        # Decrease error message timer
        if state.error_timer > 0:
            state.error_timer -= 1


def _initialize_tag_selection(state: UIState) -> None:
    """Initialize tag selection with smart defaults."""
    all_snapshots = core.list_snapshots()

    # Initialize with last used tag
    if state.selected_tag and all_snapshots:
        tagged_snapshots = state.get_filtered_snapshots(all_snapshots)
        if not tagged_snapshots:
            # No snapshots with last tag, fall back to newest
            state.selected_tag = None
    elif not state.selected_tag and all_snapshots:
        # No last tag selected, try to find the most recently used tag
        tags = core.list_tags()
        if tags:
            latest_tag = _find_latest_tag(tags)
            if latest_tag:
                state.selected_tag = latest_tag


def _find_latest_tag(tags: list) -> str | None:
    """Find the tag with the most recent snapshot."""
    latest_tag = None
    latest_time = None

    for tag in tags:
        tag_snapshots = core.snapshots_for_tag(tag)
        if tag_snapshots:
            latest_snapshot = sorted(tag_snapshots)[-1]
            if latest_time is None or latest_snapshot > latest_time:
                latest_time = latest_snapshot
                latest_tag = tag

    return latest_tag


def _get_controller_for_pane(stdscr: Any, state: UIState, key: int) -> Any:
    """Get appropriate controller based on active pane."""
    # Navigation controller handles keys that work in any pane
    nav_controller = NavigationController(stdscr, state)
    if key in (9, curses.KEY_LEFT, curses.KEY_RIGHT, ord("q")):
        return nav_controller

    # Pane-specific controllers
    if state.active_pane == 0:
        return SnapshotController(stdscr, state)
    elif state.active_pane == 2:
        return TagController(stdscr, state)
    else:
        # Metadata pane has no specific controller
        return nav_controller
