# Hades Save Backup Tool

A simplified backup and restore system for Hades save files with both CLI and TUI interfaces.

## Quick Start

### Universal Launcher (Easiest)
```bash
./hades
# Interactive menu to choose between TUI and CLI
```

### Direct Launch

**Terminal Interface (Recommended):**
```bash
python3 -m tui.main
```

**Command Line Interface:**
```bash
python3 -m cli.cli
```

## Common Workflows

### Save Progress with Tags
```bash
# CLI
python3 -m cli.cli save --tag "boss" --note "Reached Theseus with shield"

# TUI: Press [s] in snapshots pane, enter note when prompted
```

### List and Restore
```bash
# CLI - see all snapshots
python3 -m cli.cli list

# CLI - restore latest boss checkpoint
python3 -m cli.cli restore-tag boss

# TUI: Navigate with [↑↓], select with [Enter], restore with [r]
```

### Tag Management
```bash
# CLI - see all tags
python3 -m cli.cli list-tags

# CLI - rename tags
python3 -m cli.cli rename-tag "old_name" "new_name"

# CLI - delete tags
python3 -m cli.cli delete-tag "tag_name"

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
python3 -m cli.cli save [--tag <name>...] [--note "text"]
python3 -m cli.cli list
python3 -m cli.cli restore <snapshot_name>
python3 -m cli.cli restore-tag <tag_name>
python3 -m cli.cli delete <snapshot_name>
```

**Tags:**
```bash
python3 -m cli.cli list-tags
python3 -m cli.cli rename-tag <old> <new>
python3 -m cli.cli delete-tag <tag>
python3 -m cli.cli merge-tags <source> <target>
```

**Other:**
```bash
python3 -m cli.cli logs
python3 -m cli.cli --help
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
- **Simple launch**: `./hades` or `python3 -m tui.main` / `python3 -m cli.cli`
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
./hades  # Launch universal menu
```

The simplified version maintains all essential functionality while significantly reducing complexity and improving usability.