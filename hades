#!/usr/bin/env python3
"""Hades Save Backup Tool - Universal Launcher

Detects user preference or provides choice between TUI and CLI interfaces.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """Launch interface based on user preference."""

    # Simple interactive launcher
    print("Hades Save Backup Tool")
    print("=" * 25)
    print("1. Terminal UI (TUI) - Recommended")
    print("2. Command Line Interface (CLI)")
    print("3. Exit")
    print()

    try:
        choice = input("Choose interface [1-3]: ").strip()

        if choice == "1":
            print("Launching Terminal UI...")
            from tui.main import main
            import curses

            curses.wrapper(main)

        elif choice == "2":
            print("Launching CLI...")
            from cli.cli import main

            main()

        elif choice == "3":
            print("Goodbye!")

        else:
            print("Invalid choice. Please select 1, 2, or 3.")

    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
