# Hades Save Backup Tool

A comprehensive backup and restore system for Hades save files with both CLI and TUI interfaces.

## Quick Start

### Universal Launcher (Easiest)
```bash
./hades.py
# Interactive menu to choose between TUI and CLI
```

### Direct Launch

**Terminal Interface (Recommended):**
```bash
./hades_tui.py
```

**Command Line Interface:**
```bash
./hades_cli.py
```

**Python Module Execution:**
```bash
python3 -m tui.main      # TUI
python3 -m cli.cli       # CLI
```

## Common Workflows

### Save Progress with Tags
```bash
# CLI
./hades_cli.py save --tag "boss" --note "Reached Theseus with shield"

# TUI: Press [s] in snapshots pane, enter note when prompted
```

### List and Restore
```bash
# CLI - see all snapshots with metadata
./hades_cli.py list --meta

# CLI - restore latest boss checkpoint
./hades_cli.py restore-tag boss

# TUI: Navigate with [↑↓], select with [Enter], restore with [r]
```

### Tag Management
```bash
# CLI - see all tags
./hades_cli.py list-tags

# CLI - merge temporary tags
./hades_cli.py merge-tags "temp1" "main_run"

# TUI: Switch to tags pane with [Tab], create with [n], manage with shortcuts
```

## Key Features

- **Instant snapshots** of Hades save files
- **Tag system** for organizing checkpoints  
- **Metadata tracking** (creation time, notes, tags)
- **Multiple interfaces** (TUI and CLI)
- **Atomic operations** (corruption-resistant restores)
- **Comprehensive logging** of all operations

## Interface Reference

### TUI Navigation

**Global Controls:**
- **[↑↓]** Navigate within active pane
- **[Tab]** Switch between panes (Snapshots ↔ Tags, skips Metadata)
- **[l]** Toggle logs display on/off
- **[q]** Quit application

**Snapshots Pane:**
- **[s]** Save new snapshot (prompts for note)
- **[r]** Restore selected snapshot
- **[d]** Delete selected snapshot

**Tags Pane:**
- **[n]** Create new tag
- **[R]** Rename selected tag
- **[D]** Delete selected tag
- **[m]** Merge selected tag into next tag
- **[Enter]** Select tag to filter snapshots

### CLI Commands

**Snapshots:**
```bash
./hades_cli.py save [--tag <name>...] [--note "text"]
./hades_cli.py list [--meta]
./hades_cli.py restore <snapshot_name>
./hades_cli.py restore-tag <tag_name>
./hades_cli.py delete <snapshot_name>
```

**Tags:**
```bash
./hades_cli.py list-tags
./hades_cli.py rename-tag <old> <new>
./hades_cli.py delete-tag <tag>
./hades_cli.py merge-tags <source> <target>
```

**Other:**
```bash
./hades_cli.py logs
./hades_cli.py --help
```

## Architecture

The tool is organized into three main modules:

- **`core/`** - Business logic and data management
  - Snapshot CRUD operations
  - Tag management
  - Metadata handling
  - Configuration and logging
- **`cli/`** - Command-line interface
- **`tui/`** - Terminal user interface
  - Modular pane-based rendering
  - Input handling controllers
  - State management

## Recent Improvements

### Refactored for Maintainability
- **Modular design**: Split 421-line core.py into 6 focused modules
- **UI decomposition**: Split 685-line tui.py into 7 focused components  
- **SOLID principles**: Single responsibility, clear interfaces
- **Error handling**: Centralized exception management
- **Type safety**: Comprehensive type hints

### Backward Compatibility
- All original functionality preserved
- Same command-line interface structure
- No breaking changes to existing workflows

### Better User Experience
- **Simple launch**: `./hades_tui.py` and `./hades_cli.py`
- **Clear navigation**: Pane-based TUI with intuitive controls
- **Smart defaults**: Remembers last-used tag
- **Robust operations**: Atomic restores prevent corruption

## Requirements

- Python 3.8+
- `curses` library (included with Python)
- Access to Hades save directory

## Installation

Clone and run from the project directory:
```bash
git clone <repository_url>
cd hades_restore_savefile
./hades_tui.py  # Launch TUI
```

The refactored version maintains all original functionality while significantly improving code organization, readability, and maintainability.