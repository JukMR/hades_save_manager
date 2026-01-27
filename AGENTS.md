# AGENTS.md — Hades Save Backup Tool

## Purpose

This repository implements a **Hades save backup and restore tool** with modular architecture supporting multiple interfaces:

* **CLI** (`cli/`) — scriptable, automation-friendly
* **TUI** (`tui/`) — interactive curses-based UI  
* **Core** (`core/`) — single source of truth for all filesystem, tagging, metadata, and logging logic

The design goal is **zero duplication of business logic**: UI layers must delegate all state mutations to `core/` modules.

---

## Architecture Overview

```
┌─────────────┐
│   CLI/     │ ← Command-line interface
└─────┬─────┘
      │
┌─────▼─────┐
│   Core/    │ ← Single source of truth
└─────┬─────┘
      │
┌─────▼─────┐
│   TUI/     │ ← Terminal user interface
└───────────┘
```

### Core Design Principles

* **Filesystem is the canonical state** (snapshots, tags, metadata)
* **UI layers must never cache mutable filesystem state** 
* **All snapshot/tag mutations must maintain referential integrity**
* **Modular design** with clear separation of concerns

---

## Module Structure

### `core/` — Business Logic Layer

**Core modules with focused responsibilities:**

* **`constants.py`** — All paths, settings, and application constants
* **`logger.py`** — Logging system with in-memory and file persistence  
* **`metadata_handler.py`** — Snapshot metadata read/write operations (`meta.json`)
* **`config.py`** — Configuration management (last used tag, etc.)
* **`tag_manager.py`** — Tag CRUD operations and referential integrity
* **`snapshot_manager.py`** — Snapshot creation, restore, deletion operations
* **`__init__.py`** — Backward compatibility re-exports

**Key invariants (must always hold):**

1. Every snapshot directory listed in `tags/*.json` **must exist on disk**
2. Every tag listed in `meta.json` **must exist in `tags/`
3. Deleting a snapshot must remove all references to it
4. UI layers must never manipulate the filesystem directly

**Critical functions:**

* `save()` — create snapshot + metadata + tag references
* `restore()` / `restore_by_tag()` — atomic filesystem replace
* `delete_snapshot()` — MUST also clean tag references
* `rename_tag()`, `delete_tag()`, `merge_tags()` — maintain referential integrity

> ⚠️ If you add a new mutation path, ensure all invariants are preserved.

### `cli/` — Command-Line Interface

**Files:**
* **`cli.py`** — Main CLI implementation
* **`__init__.py`** — Package initialization

**Responsibilities:**
* Argument parsing with argparse
* Mapping subcommands → `core/` calls
* Human-readable output and error handling
* No filesystem access or persistence logic

**Key rules:**
* CLI is intentionally thin. If logic feels needed here, it belongs in `core/`
* No direct filesystem operations - always delegate to core

### `tui/` — Terminal User Interface

**Modular components:**
* **`main.py`** — Main TUI application loop
* **`drawer.py`** — Drawing coordinator and layout management
* **`panes.py`** — Individual UI pane components (SnapshotPane, MetadataPane, TagsPane, LogPane)
* **`controllers.py`** — Input handling controllers (Navigation, Snapshot, Tag, TagInput)
* **`colors.py`** — Color scheme definitions and utilities
* **`ui_helpers.py`** — UI utility functions (prompt, confirm dialogs)
* **`ui_state.py`** — State management and validation
* **`__init__.py`** — Package initialization

**Design patterns:**
* **Model-View-Controller** separation with controllers handling input
* **Component-based rendering** with reusable pane classes
* **State-driven architecture** with centralized state management

**Critical rules:**
* Never cache snapshot or tag lists across mutations
* Refresh data every frame using `core.list_snapshots()`
* UI bugs should not be fixed by data hacks - fix the data invariant

---

## Development Guidelines

### When Modifying Core Modules

**Before writing code, ask:**

* Does this change mutate filesystem state?
* If yes: what other files/components reference this state?

**Always update both sides of any relationship:**

| Relationship             | Update Both |
| ------------------------ | ----------- |
| snapshot ↔ tags          | yes         |
| tag ↔ metadata           | yes         |
| snapshot ↔ restore logic | yes         |

### When Modifying UI Modules

**CLI Guidelines:**
* Keep it thin and focused
* Only import from `core/` 
* Preserve backward compatibility
* Follow existing argument patterns

**TUI Guidelines:**
* Treat `core/` as a black box
* Never assume cached state is valid
* Always recompute snapshot/tag lists after mutations
* Follow existing component patterns (panes, controllers, etc.)
* Keep functions focused (< 25 lines when possible)

### When Adding New Features

**Preferred development order:**

1. **Core functionality** - Add business logic to appropriate core module
2. **CLI support** - Add command handling to `cli/cli.py`
3. **TUI support** - Add UI components to relevant TUI modules
4. **Testing** - Verify all interfaces work

**Never skip step 1** - core functionality must come first.

### Testing and Validation

**Required testing before merging:**

1. **Import testing:**
   ```bash
   python3 -c "import core; import cli.cli; import tui.main; print('✅ All imports work')"
   ```

2. **CLI functionality:**
   ```bash
   python3 cli/cli.py --help
   python3 cli/cli.py list
   python3 cli/cli.py list-tags
   ```

3. **TUI initialization:**
   ```bash
   python3 -m tui.main --help 2>/dev/null || echo "✅ TUI imports work"
   ```

4. **Backward compatibility:**
   ```bash
   # Test that existing usage patterns still work
   python3 hades_cli.py save --tag test --note "test"
   ```

---

## Launch Methods

The project supports multiple launch patterns for different use cases:

### **Universal Launcher** (Recommended for users)
```bash
./hades.py
```
*Interactive menu choice between TUI and CLI*

### **Direct Scripts** (For automation and power users)
```bash
./hades_cli.py        # Direct CLI
./hades_tui.py        # Direct TUI
```

### **Module Execution** (For development and packaging)
```bash
python3 -m cli.cli     # CLI as module
python3 -m tui.main    # TUI as module
```

---

## Common Development Tasks

### **Adding a New CLI Command**
1. Add argument parsing in `cli/cli.py`
2. Add command handling in the main function
3. Call appropriate `core/` functions
4. Test with `python3 cli/cli.py new-command --help`

### **Adding New TUI Features**
1. Identify if this affects drawing, input handling, or state
2. Modify relevant component class (pane, controller, drawer, etc.)
3. Update help text and navigation as needed
4. Test that state refreshes correctly

### **Extending Core Logic**
1. Choose appropriate module (snapshot_manager, tag_manager, etc.)
2. Add new functions maintaining invariants
3. Update `__init__.py` re-exports if public API
4. Add comprehensive error handling and logging
5. Test with both CLI and TUI

---

## Mental Model for Debugging

* **`core/` = database + transactions** - must maintain consistency
* **`cli/` + `tui/` = views** - should be stateless
* **Filesystem = truth** - what actually exists on disk
* **Anything cached can and will go stale** - always refresh after mutations

**Debugging approach:**
1. **Data issue?** Check core invariants and referential integrity
2. **UI issue?** Check state management and refresh patterns
3. **Both?** Look for invalid assumptions in either layer

---

## Recent Refactoring (2026)

### **Improvements Made:**
* **Modular architecture** - Split 1100+ lines into focused modules
* **SOLID principles** - Single responsibility, clear interfaces
* **Component-based TUI** - Reusable panes and controllers
* **Type safety** - Comprehensive type hints throughout
* **Error handling** - Centralized exception management
* **Backward compatibility** - All existing functionality preserved

### **Files Changed:**
* **Before:** `core.py` (421 lines), `tui.py` (685 lines), `cli.py` (117 lines)
* **After:** 15 modular files averaging 70-100 lines each
* **Result:** Better maintainability, testability, and extensibility

---

## Project Best Practices

1. **Always test both interfaces** - CLI and TUI should work equally well
2. **Maintain referential integrity** - Tags and snapshots must stay consistent  
3. **Never cache mutable state** - Refresh from filesystem after changes
4. **Follow Python best practices** - Type hints, docstrings, error handling
5. **Preserve backward compatibility** - Existing workflows should continue working

If something looks wrong in the UI, fix the **data invariant**, not the rendering.