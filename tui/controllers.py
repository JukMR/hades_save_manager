"""Input handling controllers for TUI."""

from typing import Any

import curses
import core
from .ui_helpers import confirm, prompt


class BaseController:
    """Base controller for input handling."""
    
    def __init__(self, stdscr: Any, state: Any) -> None:
        self.stdscr = stdscr
        self.state = state
    
    def handle_input(self, key: int) -> bool:
        """Handle input key. Override in subclasses.
        
        Returns:
            True if application should continue, False if it should quit
        """
        return True


class NavigationController(BaseController):
    """Controller for navigation between panes."""
    
    def handle_input(self, key: int) -> bool:
        """Handle navigation keys."""
        if key == 9:  # Tab
            self._switch_pane()
            return True
        elif key in (curses.KEY_LEFT, curses.KEY_RIGHT) and self.state.active_pane != 1:
            self._arrow_navigation(key)
            return True

        elif key == ord("q"):  # Quit
            return False  # Signal to quit
        return super().handle_input(key)

    def _switch_pane(self) -> None:
        """Switch to next pane, skipping metadata."""
        self.state.active_pane = (self.state.active_pane + 1) % 3
        if self.state.active_pane == 1:  # Skip metadata pane
            self.state.active_pane = (self.state.active_pane + 1) % 3

    def _arrow_navigation(self, key: int) -> None:
        """Handle left/right arrow navigation."""
        if key == curses.KEY_LEFT:
            new_pane = self.state.active_pane - 1
        else:
            new_pane = self.state.active_pane + 1

        if new_pane == 1:  # Skip metadata pane
            new_pane = new_pane + (1 if key == curses.KEY_RIGHT else -1)

        self.state.active_pane = max(0, min(2, new_pane))


class SnapshotController(BaseController):
    """Controller for snapshots pane operations."""
    
    def handle_input(self, key: int) -> bool:
        """Handle snapshot-related input."""
        all_snapshots = core.list_snapshots()
        filtered_snapshots = self.state.get_filtered_snapshots(all_snapshots)
        
        if key == curses.KEY_UP and filtered_snapshots:
            self.state.snapshot_idx = max(0, self.state.snapshot_idx - 1)
            return True
        elif key == curses.KEY_DOWN and filtered_snapshots:
            self.state.snapshot_idx = min(len(filtered_snapshots) - 1, self.state.snapshot_idx + 1)
            return True
        elif key == ord("s"):
            self._handle_save()
            return True
        elif key == ord("r") and filtered_snapshots:
            self._handle_restore(filtered_snapshots)
            return True
        elif key in (10, 13) and filtered_snapshots:  # Enter - restore snapshot
            self._handle_restore(filtered_snapshots)
            return True
        elif key == ord("d") and filtered_snapshots:
            self._handle_delete(filtered_snapshots)
            return True
        
        return super().handle_input(key)

    def _handle_save(self) -> None:
        """Handle save operation."""
        curses.curs_set(1)
        note = prompt(self.stdscr, 1, "Note: ")
        curses.curs_set(0)

        tag_list = [self.state.selected_tag] if self.state.selected_tag else []
        confirm_text = f"Create snapshot{' with tag ' + self.state.selected_tag if self.state.selected_tag else ''}?"

        if confirm(self.stdscr, "Create backup", confirm_text):
            result, message = core.save(tag_list, note)
            if result:
                self.state.set_success(message)
                self.state.snapshot_idx = 0
            else:
                self.state.set_error(message)

    def _handle_restore(self, filtered_snapshots: list) -> None:
        """Handle restore operation."""
        snap = filtered_snapshots[self.state.snapshot_idx]
        if confirm(self.stdscr, "Restore snapshot", f"Restore {snap.name}? Current save will be replaced."):
            result, message = core.restore(snap)
            if result:
                self.state.set_success(message)
            else:
                self.state.set_error(message)

    def _handle_delete(self, filtered_snapshots: list) -> None:
        """Handle delete operation."""
        snap = filtered_snapshots[self.state.snapshot_idx]
        if confirm(self.stdscr, "Delete snapshot", f"Delete {snap.name}? This is permanent."):
            result, message = core.delete_snapshot(snap)
            if result:
                self.state.snapshot_idx = max(0, self.state.snapshot_idx - 1)
                self.state.set_success(message)
            else:
                self.state.set_error(message)


class TagController(BaseController):
    """Controller for tags pane operations."""
    
    def handle_input(self, key: int) -> bool:
        """Handle tag-related input."""
        tags = core.list_tags()
        
        if key == curses.KEY_UP:
            self.state.tag_idx = max(0, self.state.tag_idx - 1)
            return True
        elif key == curses.KEY_DOWN:
            self.state.tag_idx = min(len(tags), self.state.tag_idx + 1)
            return True
        elif key == ord("\n"):
            self._handle_enter(tags)
            return True
        elif key == ord("n"):
            self._handle_new_tag()
            return True
        elif key == ord("R") and tags:
            self._handle_rename_tag(tags)
            return True
        elif key == ord("D") and tags:
            self._handle_delete_tag(tags)
            return True
        elif key == ord("m") and tags:
            self._handle_merge_tags(tags)
            return True
        
        return super().handle_input(key)

    def _handle_enter(self, tags: list) -> None:
        """Handle enter key on tag selection."""
        if self.state.tag_idx == 0:  # New tag
            self.state.creating_tag = True
            self.state.tag_input = ""
            curses.curs_set(1)
        else:  # Select tag for filtering
            selected_tag = tags[self.state.tag_idx - 1]
            self.state.selected_tag = selected_tag
            core.set_last_tag(selected_tag)
            self.state.active_pane = 0
            self.state.snapshot_idx = 0

    def _handle_new_tag(self) -> None:
        """Handle new tag creation."""
        self.state.creating_tag = True
        self.state.tag_input = ""
        curses.curs_set(1)  # Show cursor

    def _handle_rename_tag(self, tags: list) -> None:
        """Handle tag renaming."""
        if self.state.tag_idx < len(tags):
            self.state.renaming_tag = True
            self.state.tag_input = tags[self.state.tag_idx]
            curses.curs_set(1)

    def _handle_delete_tag(self, tags: list) -> None:
        """Handle tag deletion."""
        tag = tags[self.state.tag_idx]
        if confirm(self.stdscr, "Delete tag", f"Delete tag '{tag}'? This will remove it from all snapshots."):
            result, message = core.delete_tag(tag)
            if result:
                if self.state.selected_tag == tag:
                    self.state.selected_tag = None
                    core.set_last_tag("")
                self.state.tag_idx = max(0, self.state.tag_idx - 1)
                self.state.set_success(message)
            else:
                self.state.set_error(message)

    def _handle_merge_tags(self, tags: list) -> None:
        """Handle tag merging."""
        if len(tags) > 1:
            source_tag = tags[self.state.tag_idx]
            target_idx = (self.state.tag_idx + 1) % len(tags)
            target_tag = tags[target_idx]

            if confirm(self.stdscr, "Merge tags", f"Merge '{source_tag}' into '{target_tag}'?"):
                result, message = core.merge_tags(source_tag, target_tag)
                if result:
                    if self.state.selected_tag == source_tag:
                        self.state.selected_tag = target_tag
                        core.set_last_tag(target_tag)
                    self.state.tag_idx = target_idx
                    self.state.set_success(message)
                else:
                    self.state.set_error(message)


class TagInputController(BaseController):
    """Controller for tag input modes (creation/renaming)."""
    
    def handle_input(self, key: int) -> bool:
        """Handle tag input keys."""
        if key in (27,):  # Esc
            self._cancel_input()
            return True
        elif key in (10, 13):  # Enter
            self._submit_input()
            return True
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            self.state.tag_input = self.state.tag_input[:-1]
            return True
        elif 32 <= key <= 126:  # Printable characters
            self.state.tag_input += chr(key)
            return True
        
        return super().handle_input(key)

    def _cancel_input(self) -> None:
        """Cancel tag input mode."""
        self.state.creating_tag = False
        self.state.renaming_tag = False
        self.state.tag_input = ""
        curses.curs_set(0)

    def _submit_input(self) -> None:
        """Submit tag input and create/rename tag."""
        name = self.state.tag_input.strip()
        if name:
            if self.state.creating_tag:
                self._create_tag(name)
            elif self.state.renaming_tag:
                self._rename_tag(name)

        self.state.creating_tag = False
        self.state.renaming_tag = False
        self.state.tag_input = ""
        curses.curs_set(0)

    def _create_tag(self, name: str) -> None:
        """Create a new tag."""
        import core
        from core.constants import TAGS_DIR
        
        core.TAGS_DIR.mkdir(parents=True, exist_ok=True)
        tag_file = core.TAGS_DIR / f"{name}.json"

        if tag_file.exists():
            self.state.set_error(f"Tag '{name}' already exists")
        else:
            tag_file.write_text("[]")
            self.state.set_success(f"Created tag '{name}'")

            # Auto-select newly created tag
            self.state.selected_tag = name
            core.set_last_tag(name)
            self.state.tag_idx = core.list_tags().index(name) + 1

    def _rename_tag(self, name: str) -> None:
        """Rename an existing tag."""
        tags = core.list_tags()
        if 0 < self.state.tag_idx <= len(tags):
            old_tag = tags[self.state.tag_idx - 1]
            result, message = core.rename_tag(old_tag, name)
            if result:
                if self.state.selected_tag == old_tag:
                    self.state.selected_tag = name
                    core.set_last_tag(name)
                self.state.set_success(message)
            else:
                self.state.set_error(message)