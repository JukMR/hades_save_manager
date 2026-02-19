# AGENTS.md — Hades Save Backup Tool

## Purpose

This repository implements a **Hades save backup and restore tool** with modular architecture supporting multiple interfaces:

* **CLI** (`cli/`) — scriptable, automation-friendly
* **TUI** (`tui/`) — interactive curses-based UI  
* **Core** (`core/`) — single source of truth for all filesystem, tagging, metadata, and logging logic

The design goal is **zero duplication of business logic**: UI layers must delegate all state mutations to `core/` modules.

---

## Build, Lint, and Test Commands

### Development Environment Setup
```bash
# Install test dependencies
uv sync --dev  # Install development dependencies

# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_tag_manager.py -v

# Run tests with coverage
uv run pytest tests/ -v --cov=core --cov-report=term-missing
```

### Code Quality Commands
```bash
# Python syntax check
uv run python -m py_compile core/*.py cli/*.py tui/*.py

# Import testing
uv run python -c "import core; import cli.cli; import tui.main; print('✅ All imports work')"

# Functionality testing
uv run python -m cli.cli --help
uv run python -m cli.cli list
uv run python -m cli.cli list-tags
```

### Testing Strategy
1. **Unit Tests** (`tests/`) - Test individual core modules with mocking
2. **Integration Tests** - Test actual filesystem operations with temporary directories
3. **Import Tests** - Verify all modules can be imported without errors
4. **CLI Tests** - Test command-line interface functionality
5. **TUI Tests** - Verify TUI initialization (no interactive testing)

---

## Code Style Guidelines

### Import Organization
**Order:** Standard library → Third-party → Local imports
```python
import json
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

import core
from .colors import ColorPairs
from .constants import BACKUP_SAVE_ROOT
```

### Type Annotations
**Required for all public functions:**
```python
def save(tags: List[str], note: Optional[str]) -> Tuple[Optional[Path], str]:
    """Create a new snapshot."""
    pass

class BaseController:
    def handle_input(self, key: int) -> bool:
        """Handle input key. Returns False to quit."""
        return True
```

### Naming Conventions
- **Files:** `snake_case.py` (e.g., `snapshot_manager.py`)
- **Classes:** `PascalCase` (e.g., `SnapshotController`)  
- **Functions/Variables:** `snake_case` (e.g., `create_snapshot()`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `BACKUP_SAVE_ROOT`)
- **Private:** `_leading_underscore` (e.g., `_validate_indexes()`)

### Error Handling Patterns
**Always handle specific exceptions:**
```python
# Good
try:
    shutil.copytree(src, dest)
except PermissionError as e:
    logger.error(f"Permission denied: {e}")
    return False, str(e)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return False, str(e)

# Avoid generic catches except for cleanup
try:
    operation()
finally:
    cleanup()
```

### Function Length and Complexity
- **Preferred:** < 25 lines per function
- **Maximum:** < 50 lines per function
- **Split large functions** into smaller, focused helpers

### Documentation Style
**All public functions need docstrings:**
```python
def list_snapshots() -> List[Path]:
    """Get list of all snapshot directories.
    
    Returns:
        Sorted list of snapshot paths (newest first)
    """
    pass
```

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
- **Filesystem is canonical state** (snapshots, tags, metadata)
- **UI layers must never cache mutable filesystem state** 
- **All snapshot/tag mutations must maintain referential integrity**
- **Modular design** with clear separation of concerns

---

## Module Structure

### `core/` — Business Logic Layer
**Core modules with focused responsibilities:**
- `constants.py` — All paths, settings, and application constants
- `logger.py` — Logging system with in-memory and file persistence  
- `metadata_handler.py` — Snapshot metadata read/write operations (`meta.json`)
- `config.py` — Configuration management (last used tag, etc.)
- `tag_manager.py` — Tag CRUD operations and referential integrity
- `snapshot_manager.py` — Snapshot creation, restore, deletion operations
- `__init__.py` — Backward compatibility re-exports

### `cli/` — Command-Line Interface
- `cli.py` — Main CLI implementation
- `__init__.py` — Package initialization

### `tui/` — Terminal User Interface
- `main.py` — Main TUI application loop
- `drawer.py` — Drawing coordinator and layout management
- `panes.py` — Individual UI pane components (SnapshotPane, MetadataPane, TagsPane)
- `controllers.py` — Input handling controllers (Navigation, Snapshot, Tag, TagInput)
- `colors.py` — Color scheme definitions and utilities
- `ui_helpers.py` — UI utility functions (prompt, confirm dialogs)
- `ui_state.py` — State management and validation
- `__init__.py` — Package initialization

---

## Development Guidelines

### When Modifying Core Modules
**Before writing code, ask:**
- Does this change mutate filesystem state?
- If yes: what other files/components reference this state?

**Always update both sides of any relationship:**
| Relationship | Update Both |
| ----------- | ----------- |
| snapshot ↔ tags | yes |
| tag ↔ metadata | yes |
| snapshot ↔ restore logic | yes |

### When Modifying UI Modules
**CLI Guidelines:**
- Keep it thin and focused
- Only import from `core/` 
- Preserve backward compatibility
- Follow existing argument patterns

**TUI Guidelines:**
- Treat `core/` as a black box
- Never assume cached state is valid
- Always recompute snapshot/tag lists after mutations
- Follow existing component patterns (panes, controllers, etc.)
- Keep functions focused (< 25 lines when possible)
- **Index offsets:** When display lists include virtual items (like "+ New tag"), account for offsets in indexing

### When Adding New Features
**Preferred development order:**
1. **Core functionality** - Add business logic to appropriate core module
2. **CLI support** - Add command handling to `cli/cli.py`
3. **TUI support** - Add UI components to relevant TUI modules
4. **Testing** - Verify all interfaces work

**Never skip step 1** - core functionality must come first.

---

## Testing Requirements

### Required Testing Before Merging
1. **UV dependency management:**
   ```bash
   uv sync --dev  # Install development dependencies
   ```

2. **Run all tests:**
   ```bash
   uv run pytest tests/ -v
   ```

3. **Run specific test files:**
   ```bash
   uv run pytest tests/test_snapshot_working.py -v
   ```

4. **Coverage check:**
   ```bash
   uv run pytest tests/ --cov=core --cov-report=term-missing
   ```

5. **Test suite structure:**
   - `tests/conftest.py` - Shared test utilities and fixtures
   - `tests/test_simple.py` - Basic import and metadata tests
   - `tests/test_snapshot_working.py` - Snapshot manager unit tests
   - `tests/test_tag_working.py` - Tag manager unit tests  
   - `tests/test_simple_integration.py` - Integration workflow tests

6. **Test isolation:**
   - All tests use temporary directories via `patched_constants` fixture
   - Tests are isolated from real filesystem
   - Proper mocking of `BACKUP_SAVE_ROOT`, `TAGS_DIR`, `HADES_SAVE_DIR`

2. **Unit tests:**
   ```bash
   pytest tests/ -v
   ```

3. **CLI functionality:**
   ```bash
   python3 cli/cli.py --help
   python3 cli/cli.py list
   python3 cli/cli.py list-tags
   ```

4. **Coverage check:**
   ```bash
   uv run pytest tests/ --cov=core --cov-report=term-missing
   ```

### Test Organization
- **Unit tests** in `tests/test_*.py` with mocking for filesystem operations
- **Integration tests** for real filesystem operations with temporary directories
- **Fixtures** for common test setup (temporary directories, mocked constants)

---

## Launch Methods

### **Universal Launcher** (Recommended for users)
```bash
./hades
```

### **Module Execution** (For automation and power users)
```bash
python3 -m cli.cli     # CLI as module
python3 -m tui.main    # TUI as module
```

---

## Mental Model for Debugging

- **`core/` = database + transactions** - must maintain consistency
- **`cli/` + `tui/` = views** - should be stateless
- **Filesystem = truth** - what actually exists on disk
- **Anything cached can and will go stale** - always refresh after mutations

**Debugging approach:**
1. **Data issue?** Check core invariants and referential integrity
2. **UI issue?** Check state management and refresh patterns
3. **Both?** Look for invalid assumptions in either layer

---

## Project Best Practices

1. **Always test both interfaces** - CLI and TUI should work equally well
2. **Maintain referential integrity** - Tags and snapshots must stay consistent  
3. **Never cache mutable state** - Refresh from filesystem after changes
4. **Follow Python best practices** - Type hints, docstrings, error handling
5. **Preserve backward compatibility** - Existing workflows should continue working
6. **Run tests before committing** - Ensure all existing functionality remains intact

If something looks wrong in the UI, fix the **data invariant**, not the rendering.
