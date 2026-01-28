#!/usr/bin/env python3
"""Hades Save Backup Tool - CLI Wrapper

This script provides the command-line interface for managing Hades save backups.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run CLI
from cli.cli import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"CLI Error: {e}")
        sys.exit(1)
