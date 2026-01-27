"""UI state management for the TUI."""

from typing import List, Optional

import core


class UIState:
    """Manages the current state of the TUI."""
    
    def __init__(self) -> None:
        self.active_pane = 0  # 0=snapshots, 1=metadata, 2=tags
        self.snapshot_idx = 0
        self.tag_idx = 0
        self.selected_tag = core.get_last_tag()
        self.creating_tag = False
        self.renaming_tag = False
        self.merging_tag = False
        self.tag_input = ""
        self.error_message = ""
        self.error_timer = 0


    def get_filtered_snapshots(self, all_snapshots: List[core.Path]) -> List[core.Path]:
        """Get snapshots filtered by selected tag.
        
        Args:
            all_snapshots: List of all available snapshots
            
        Returns:
            List of snapshots filtered by the selected tag
        """
        if not self.selected_tag:
            return all_snapshots

        tagged_snapshots = core.snapshots_for_tag(self.selected_tag)
        return [s for s in all_snapshots if s.name in tagged_snapshots]

    def set_error(self, message: str) -> None:
        """Set an error message to display.
        
        Args:
            message: Error message to display
        """
        import core
        from core.constants import ERROR_DISPLAY_DURATION
        
        self.error_message = message
        self.error_timer = ERROR_DISPLAY_DURATION

    def set_success(self, message: str) -> None:
        """Set a success message to display.
        
        Args:
            message: Success message to display
        """
        import core
        from core.constants import ERROR_DISPLAY_DURATION
        
        self.error_message = message
        self.error_timer = ERROR_DISPLAY_DURATION