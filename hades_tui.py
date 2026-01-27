#!/usr/bin/env python3
"""Hades Save Backup Tool - TUI Wrapper

This script launches the terminal user interface for managing Hades save backups.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run TUI
from tui.main import main
import curses

def run_tui():
    """Run the TUI application."""
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"TUI Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_tui()