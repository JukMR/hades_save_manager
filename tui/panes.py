"""Pane drawing classes for the TUI."""

from typing import List, Any

import curses
import core
from .colors import ColorPairs


class BasePane:
    """Base class for all UI panes."""
    
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
    
    def draw(self, stdscr: Any, offset_x: int, state: Any, *args, **kwargs) -> None:
        """Draw the pane. Override in subclasses."""
        pass


class SnapshotPane(BasePane):
    """Pane for displaying and navigating snapshots."""
    
    def draw(self, stdscr: Any, offset_x: int, state: Any, snapshots: List[core.Path] | None = None) -> None:
        """Draw the snapshots list pane."""
        max_y = self.height - 3  # Leave space for header and help

        if not snapshots:
            self._draw_empty_state(stdscr, offset_x, state)
            return

        self._draw_snapshot_list(stdscr, offset_x, state, snapshots, max_y)

    def _draw_empty_state(self, stdscr: Any, offset_x: int, state: Any) -> None:
        """Draw empty state message."""
        if state.selected_tag:
            stdscr.addstr(
                2, offset_x + 2, 
                f"No snapshots with tag '{state.selected_tag}'", 
                curses.color_pair(ColorPairs.RED)
            )
        else:
            stdscr.addstr(
                2, offset_x + 2, 
                "No snapshots available", 
                curses.color_pair(ColorPairs.RED)
            )

    def _draw_snapshot_list(
        self, 
        stdscr: Any, 
        offset_x: int, 
        state: Any, 
        snapshots: List[core.Path], 
        max_y: int
    ) -> None:
        """Draw the list of snapshots."""
        for i, snap in enumerate(snapshots[:max_y]):
            y = 2 + i
            attr = self._get_snapshot_attr(i, state)
            text = snap.name.ljust(self.width - 4)
            stdscr.addstr(y, offset_x + 2, text, attr)

    def _get_snapshot_attr(self, index: int, state: Any) -> int:
        """Get attribute for snapshot row based on selection state."""
        if index == state.snapshot_idx and state.active_pane == 0:
            return curses.color_pair(ColorPairs.SELECTED)  # Active row in active pane
        elif index == state.snapshot_idx:
            return curses.A_REVERSE  # Selected row but not active pane
        else:
            return curses.A_NORMAL  # Normal row


class MetadataPane(BasePane):
    """Pane for displaying snapshot metadata."""
    
    def draw(self, stdscr: Any, offset_x: int, state: Any, snapshots: List[core.Path]) -> None:
        """Draw the metadata pane."""
        if not snapshots:
            stdscr.addstr(
                2, offset_x + 2, 
                "No snapshots available", 
                curses.color_pair(ColorPairs.RED)
            )
            return

        snap = snapshots[state.snapshot_idx]
        meta = core.read_meta(snap)
        self._draw_metadata_content(stdscr, offset_x, meta)

    def _draw_metadata_content(self, stdscr: Any, offset_x: int, meta: dict) -> None:
        """Draw the actual metadata content."""
        y = 2
        
        # Created date
        stdscr.addstr(
            y, offset_x + 2,
            f"Created: {meta.get('created_at', '')}",
            curses.color_pair(ColorPairs.YELLOW)
        )
        
        # Tags
        y += 2
        tags_text = ', '.join(meta.get('tags', []))
        stdscr.addstr(
            y, offset_x + 2,
            f"Tags: {tags_text}",
            curses.color_pair(ColorPairs.MAGENTA)
        )
        
        # Note
        y += 2
        stdscr.addstr(y, offset_x + 2, "Note:", curses.A_BOLD)
        y += 1
        
        note_lines = (meta.get("note") or "").splitlines()[: self.height - 7]
        for line in note_lines:
            if y < self.height - 2:
                stdscr.addstr(y, offset_x + 4, line[: self.width - 6])
                y += 1


class TagsPane(BasePane):
    """Pane for managing tags."""
    
    def draw(self, stdscr: Any, offset_x: int, state: Any) -> None:
        """Draw the tags management pane."""
        max_y = self.height - 3

        # Handle tag creation/editing modes
        if state.creating_tag or state.renaming_tag:
            self._draw_tag_input(stdscr, offset_x, state)
            return

        tags = core.list_tags()
        if not tags:
            self._draw_empty_tags_state(stdscr, offset_x)
            return

        self._draw_tags_list(stdscr, offset_x, state, tags, max_y)

    def _draw_tag_input(self, stdscr: Any, offset_x: int, state: Any) -> None:
        """Draw tag input field for creation/renaming."""
        from .ui_helpers import prompt
        
        if state.creating_tag:
            prompt_text = "New tag: "
        else:
            prompt_text = "Rename to: "

        stdscr.addstr(2, offset_x + 2, prompt_text, curses.A_BOLD)
        input_field = state.tag_input + "_"
        stdscr.addstr(
            3, offset_x + 2, 
            input_field.ljust(self.width - 4), 
            curses.color_pair(ColorPairs.SELECTED)
        )
        stdscr.addstr(
            5, offset_x + 2, 
            "[Enter] confirm  [Esc] cancel", 
            curses.color_pair(ColorPairs.GREEN)
        )

    def _draw_empty_tags_state(self, stdscr: Any, offset_x: int) -> None:
        """Draw empty tags state with hint."""
        stdscr.addstr(
            2, offset_x + 2, 
            "No tags available", 
            curses.color_pair(ColorPairs.RED)
        )
        stdscr.addstr(
            4, offset_x + 2, 
            "Press [n] to create a tag", 
            curses.color_pair(ColorPairs.GREEN)
        )

    def _draw_tags_list(
        self, 
        stdscr: Any, 
        offset_x: int, 
        state: Any, 
        tags: List[str], 
        max_y: int
    ) -> None:
        """Draw the list of tags."""
        display_tags = ["+ New tag"] + tags

        for i, item in enumerate(display_tags[:max_y]):
            y = 2 + i
            is_selected = i == state.tag_idx and state.active_pane == 2

            if item == "+ New tag":
                self._draw_new_tag_item(stdscr, offset_x, y, is_selected)
            else:
                self._draw_tag_item(stdscr, offset_x, y, item, state, is_selected)

    def _draw_new_tag_item(self, stdscr: Any, offset_x: int, y: int, is_selected: bool) -> None:
        """Draw the 'New tag' virtual item."""
        attr = curses.color_pair(ColorPairs.GREEN)
        if is_selected:
            attr |= curses.A_REVERSE
        stdscr.addstr(y, offset_x + 2, "+ New tag".ljust(self.width - 4), attr)

    def _draw_tag_item(
        self, 
        stdscr: Any, 
        offset_x: int, 
        y: int, 
        tag: str, 
        state: Any, 
        is_selected: bool
    ) -> None:
        """Draw a real tag item."""
        count = core.get_tag_count(tag)
        is_active = tag == state.selected_tag

        if is_selected:
            color = curses.color_pair(ColorPairs.ACTIVE_TAG if is_active else ColorPairs.SELECTED)
        elif is_active:
            color = curses.color_pair(ColorPairs.MAGENTA) | curses.A_REVERSE
        else:
            color = curses.A_NORMAL

        text = f"{tag} ({count})".ljust(self.width - 4)
        stdscr.addstr(y, offset_x + 2, text, color)


class LogPane(BasePane):
    """Pane for displaying recent logs."""
    
    def draw(self, stdscr: Any, offset_x: int, state: Any, show_logs: bool) -> None:
        """Draw recent logs in a small panel."""
        if not show_logs:
            return

        logs = core.logger.get_recent_logs(8)
        log_h = min(len(logs) + 2, self.height - 4)
        
        self._draw_log_border(stdscr, offset_x, log_h)
        self._draw_log_entries(stdscr, offset_x, logs, log_h)

    def _draw_log_border(self, stdscr: Any, offset_x: int, log_h: int) -> None:
        """Draw log window border and header."""
        h = self.height
        width = self.width
        
        stdscr.addstr(
            h - log_h - 1, offset_x, 
            "┌" + "─" * (width - 2) + "┐", 
            curses.color_pair(ColorPairs.CYAN)
        )
        stdscr.addstr(
            h - log_h, offset_x, 
            "│ Logs ", 
            curses.color_pair(ColorPairs.CYAN) | curses.A_BOLD
        )
        
        header_space = width - len("│ Logs ") - 1
        stdscr.addstr(
            h - log_h, offset_x + len("│ Logs "), 
            " " * header_space + "│", 
            curses.color_pair(ColorPairs.CYAN)
        )

    def _draw_log_entries(
        self, 
        stdscr: Any, 
        offset_x: int, 
        logs: List[str], 
        log_h: int
    ) -> None:
        """Draw individual log entries."""
        h = self.height
        width = self.width
        
        for i, log_line in enumerate(logs):
            y = h - log_h + 1 + i
            if y >= h - 1:
                break

            display_line = log_line[: width - 4]
            from .colors import get_log_color
            color = get_log_color(log_line)
            
            stdscr.addstr(
                y, offset_x, 
                f"│ {display_line.ljust(width - 4)} │", 
                curses.color_pair(color)
            )

    def _draw_bottom_border(self, stdscr: Any, offset_x: int) -> None:
        """Draw the bottom border of the log pane."""
        h = self.height
        width = self.width
        
        stdscr.addstr(
            h - 1, offset_x, 
            "└" + "─" * (width - 2) + "┘", 
            curses.color_pair(ColorPairs.CYAN)
        )