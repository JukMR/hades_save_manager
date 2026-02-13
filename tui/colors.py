"""Color definitions for TUI."""

import curses


class ColorPairs:
    """Color pair definitions for the TUI."""

    # Color pair constants
    CYAN = 1  # headers
    SELECTED = 2  # selected row (black on cyan)
    YELLOW = 3  # metadata
    RED = 4  # warnings
    BLUE = 5  # hints / actions (changed from green to blue)
    ACTIVE_PANE = 6  # active pane border (black on white)
    MAGENTA = 7  # tags
    ACTIVE_TAG = 8  # active tag (white on blue)
    LOG = 9  # log messages (changed from cyan to purple)


def init_colors() -> None:
    """Initialize color pairs for the TUI."""
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(ColorPairs.CYAN, curses.COLOR_CYAN, -1)
    curses.init_pair(ColorPairs.SELECTED, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(ColorPairs.YELLOW, curses.COLOR_YELLOW, -1)
    curses.init_pair(ColorPairs.RED, curses.COLOR_RED, -1)
    curses.init_pair(ColorPairs.BLUE, curses.COLOR_BLUE, -1)  # Changed from green to blue
    curses.init_pair(ColorPairs.ACTIVE_PANE, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(ColorPairs.MAGENTA, curses.COLOR_MAGENTA, -1)
    curses.init_pair(ColorPairs.ACTIVE_TAG, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(ColorPairs.LOG, curses.COLOR_MAGENTA, -1)  # Changed from cyan to magenta (purple-like)


def get_log_color(log_line: str) -> int:
    """Get color for a log line based on its content.

    Args:
        log_line: The log line to color

    Returns:
        Color pair constant for the log line
    """
    if "ERROR" in log_line:
        return curses.color_pair(ColorPairs.RED)
    elif "SUCCESS" in log_line:
        return curses.color_pair(ColorPairs.BLUE)  # Changed from GREEN to BLUE
    elif "WARNING" in log_line:
        return curses.color_pair(ColorPairs.YELLOW)
    else:
        return curses.color_pair(ColorPairs.LOG)
