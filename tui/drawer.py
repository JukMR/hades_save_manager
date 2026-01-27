"""Main drawing coordinator for TUI."""

from typing import Any

import curses
import core
from .colors import ColorPairs
from .panes import LogPane, MetadataPane, SnapshotPane, TagsPane


class TUIDrawer:
    """Main drawing coordinator for the TUI."""
    
    def __init__(self) -> None:
        self.snapshot_pane = None
        self.metadata_pane = None
        self.tags_pane = None
        self.log_pane = None
    
    def draw(self, stdscr: Any, state: Any) -> None:
        """Draw the entire TUI interface."""
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        # Calculate pane widths
        snapshots_w = w // 3
        metadata_w = w // 3
        tags_w = w - snapshots_w - metadata_w - 4

        # Get data first
        all_snapshots = core.list_snapshots()
        filtered_snapshots = state.get_filtered_snapshots(all_snapshots)
        tags = core.list_tags()

        # Initialize panes with correct dimensions
        self.initialize_panes(snapshots_w, metadata_w, tags_w, h)

        # Validate indexes
        self.validate_indexes(state, filtered_snapshots, tags)

        # Draw pane headers
        self.draw_pane_headers(stdscr, snapshots_w, metadata_w, tags_w, state.active_pane)

        # Validate indexes
        self.validate_indexes(state, filtered_snapshots, tags)

        # Draw content in each pane
        if self.snapshot_pane and self.metadata_pane and self.tags_pane:
            self.snapshot_pane.draw(stdscr, 0, state, filtered_snapshots)
            self.metadata_pane.draw(stdscr, snapshots_w + 3, state, filtered_snapshots)
            self.tags_pane.draw(stdscr, snapshots_w + metadata_w + 4, state)
        
        # Draw help/status bar
        self.draw_help_bar(stdscr, h, w, state)
        
        # Draw logs if enabled
        if state.show_logs and self.log_pane:
            # Calculate log pane position and size
            snapshots_w = w // 3
            metadata_w = w // 3
            tags_w = w - snapshots_w - metadata_w - 4
            offset_x = snapshots_w + metadata_w + 4
            
            self.log_pane.draw(stdscr, offset_x, state, state.show_logs)

    def draw_pane_headers(
        self, 
        stdscr: Any, 
        snapshots_w: int, 
        metadata_w: int, 
        tags_w: int, 
        active_pane: int
    ) -> None:
        """Draw pane headers with active pane highlighting."""
        # Determine header colors
        colors = [
            curses.color_pair(ColorPairs.CYAN) | curses.A_BOLD,
            curses.color_pair(ColorPairs.CYAN) | curses.A_BOLD,
            curses.color_pair(ColorPairs.CYAN) | curses.A_BOLD,
        ]

        if 0 <= active_pane < 3:
            colors[active_pane] = curses.color_pair(ColorPairs.ACTIVE_PANE) | curses.A_BOLD

        # Draw headers
        stdscr.addstr(0, 2, "Snapshots", colors[0])
        stdscr.addstr(0, snapshots_w + 3, "Metadata", colors[1])
        stdscr.addstr(0, snapshots_w + metadata_w + 4, "Tags", colors[2])

        # Draw vertical separators
        h, w = stdscr.getmaxyx()
        vline = "│"

        for y in range(1, h):
            stdscr.addch(y, snapshots_w + 1, ord(vline))
            stdscr.addch(y, snapshots_w + metadata_w + 2, ord(vline))

    def validate_indexes(self, state: Any, filtered_snapshots: list, tags: list) -> None:
        """Ensure selection indexes are valid."""
        if filtered_snapshots:
            state.snapshot_idx = max(0, min(state.snapshot_idx, len(filtered_snapshots) - 1))
        else:
            state.snapshot_idx = 0

        if tags:
            state.tag_idx = max(0, min(state.tag_idx, len(tags)))
        else:
            state.tag_idx = 0

    def initialize_panes(self, snapshots_w: int, metadata_w: int, tags_w: int, h: int) -> None:
        """Initialize pane objects with correct dimensions."""
        pane_height = h
        
        # Always initialize panes
        self.snapshot_pane = SnapshotPane(snapshots_w - 2, pane_height)
        self.metadata_pane = MetadataPane(metadata_w - 2, pane_height)
        self.tags_pane = TagsPane(tags_w - 2, pane_height)
        self.log_pane = LogPane(tags_w - 2, pane_height)

    def draw_help_bar(self, stdscr: Any, h: int, w: int, state: Any) -> None:
        """Draw help/status bar."""
        help_y = h - 2 if not state.show_logs else h - 3
        
        help_texts = {
            0: "[↑↓] move  [Tab] switch pane  [Enter] select  [s] save  [r] restore  [d] delete  [l] toggle logs  [q] quit",
            1: "[Tab] switch pane  [l] toggle logs  [q] quit",
            2: "[↑↓] move  [Tab] switch pane  [Enter] filter  [n] new  [R] rename  [D] delete  [m] merge  [l] toggle logs  [q] quit",
        }

        help_text = help_texts.get(state.active_pane, help_texts[0])
        help_text = self._add_context_info(help_text, state, w)

        stdscr.addstr(help_y, 2, help_text[: w - 4], curses.color_pair(ColorPairs.GREEN))

    def _add_context_info(self, help_text: str, state: Any, w: int) -> str:
        """Add context information to help text."""
        # Add current filter info if any
        if state.selected_tag:
            filter_info = f" | Filter: {state.selected_tag}"
            if len(help_text) + len(filter_info) < w - 2:
                help_text += filter_info

        # Add logs toggle status
        logs_status = " | Logs: ON" if state.show_logs else ""
        if logs_status:
            help_text += logs_status

        return help_text