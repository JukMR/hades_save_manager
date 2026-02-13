# Hades Save Backup Tool

A simplified backup and restore system for Hades save files with both CLI and TUI interfaces.

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
python3 -m cli.cli       # CLI
python3 -m tui.main      # TUI
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
# CLI - see all snapshots
./hades_cli.py list

# CLI - restore latest boss checkpoint
./hades_cli.py restore-tag boss

# TUI: Navigate with [↑↓], select with [Enter], restore with [r]
```

### Tag Management
```bash
# CLI - see all tags
./hades_cli.py list-tags

# CLI - rename tags
./hades_cli.py rename-tag "old_name" "new_name"

# CLI - delete tags
./hades_cli.py delete-tag "tag_name"

# TUI: Switch to tags pane with [Tab], create with [n], manage with shortcuts
```

## Key Features

- **Instant snapshots** of Hades save files
- **Simplified tag system** using directory structure
- **Notes embedded** in directory names
- **Multiple interfaces** (TUI and CLI)
- **Atomic operations** (corruption-resistant restores)
- **Comprehensive logging** of all operations

## File Structure

The tool uses a simplified directory structure:

```
~/.local/share/hades_backups_v2/
├── [tag_name_1]/
│   ├── [timestamp_note_1]/
│   └── [timestamp_note_2]/
├── [tag_name_2]/
│   └── [timestamp_note_3]/
├── config.json
└── hades.log
```

- Tags are directories containing snapshots
- Notes are embedded in directory names as `[timestamp]_[note]`
- No more complex JSON metadata files

## Interface Reference

### TUI Navigation

**Global Controls:**
- **[↑↓]** Navigate within active pane
- **[Tab]** Switch between panes (Snapshots ↔ Tags, skips Metadata)
- **[q]** Quit application

**Snapshots Pane:**
- **[s]** Save new snapshot (prompts for note)
- **[Enter/r]** Restore selected snapshot
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
./hades_cli.py list
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
  - Tag management (directory-based)
  - Minimal metadata handling
  - Configuration and logging
- **`cli/`** - Command-line interface
- **`tui/`** - Terminal user interface
  - Modular pane-based rendering
  - Input handling controllers
  - State management

## Simplified Design

### Cleaner Architecture
- **Directory-based tags**: Tags are simply directories
- **Embedded notes**: Notes are part of directory names
- **No JSON metadata**: Reduced complexity
- **Single source of truth**: File system is the canonical state

### Better User Experience
- **Simple launch**: `./hades_tui.py` and `./hades_cli.py`
- **Intuitive structure**: Browse saves directly in file system
- **Clear organization**: Tags are visible as directories
- **Robust operations**: Atomic restores prevent corruption

## Requirements

- Python 3.8+
- `curses` library (included with Python)
- Access to Hades save directory

## Installation

Clone and run from the project directory:
```bash
git clone <repository_url>
cd hades_save_manager
./hades_tui.py  # Launch TUI
```

The simplified version maintains all essential functionality while significantly reducing complexity and improving usability.