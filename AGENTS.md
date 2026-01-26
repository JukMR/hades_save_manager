# AGENTS.md — Hades Save Backup Tool

## Purpose

This repository implements a **Hades save backup and restore tool** with three user interfaces sharing a single core:

* **CLI** (`cli.py`) — scriptable, automation-friendly
* **TUI** (`tui.py`) — interactive curses-based UI
* **Core** (`core.py`) — single source of truth for all filesystem, tagging, metadata, and logging logic

The design goal is **zero duplication of business logic**: UI layers must delegate all state mutations to `core.py`.

---

## High-level Architecture

```
            ┌──────────┐
            │  cli.py  │
            └────┬─────┘
                 │
            ┌────▼─────┐
            │  core.py │  ← source of truth
            └────┬─────┘
                 │
            ┌────▼─────┐
            │  tui.py  │
            └──────────┘
```

### Core principles

* **Filesystem is the canonical state** (snapshots, tags, metadata)
* UI code must never cache mutable filesystem state
* All snapshot/tag mutations must maintain **referential integrity**

---

## File Responsibilities

### `core.py` (CRITICAL)

**Responsibilities**:

* Snapshot creation, restore, deletion
* Metadata management (`meta.json` per snapshot)
* Tag persistence (`tags/*.json`)
* Referential integrity between snapshots and tags
* Logging (in-memory + file-backed)

**Key invariants (must always hold)**:

1. Every snapshot directory listed in `tags/*.json` **must exist on disk**
2. Every tag listed in `meta.json` **must exist in `tags/`**
3. Deleting a snapshot must remove all references to it
4. UI layers must never manipulate the filesystem directly

**Important functions**:

* `save()` — create snapshot + metadata + tag references
* `restore()` / `restore_by_tag()` — filesystem replace
* `delete_snapshot()` — MUST also clean tag references
* `rename_tag()`, `delete_tag()`, `merge_tags()` — update both tag files and snapshot metadata

> ⚠️ If you add a new mutation path, ensure all invariants are preserved.

---

### `cli.py`

**Responsibilities**:

* Argument parsing
* Mapping subcommands → `core.py` calls
* Human-readable output

**Rules**:

* No filesystem access
* No persistence logic
* No shared state

CLI is intentionally thin. If logic feels needed here, it probably belongs in `core.py`.

---

### `tui.py`

**Responsibilities**:

* Rendering panes (snapshots / metadata / tags)
* Input handling
* Calling `core.py` for all mutations

**Critical rule**:

> Never cache snapshot or tag lists across mutations.

#### Snapshot refresh rule

Snapshots **must be refreshed every frame**:

```python
while True:
    all_snapshots = core.list_snapshots()
    draw(stdscr, state)
    key = stdscr.getch()
```

This prevents UI drift after delete/save/restore.

#### Startup-only logic

One-time selection logic (e.g. selecting the last-used or most recent tag) may compute snapshots **once at startup**. That logic must not be reused during runtime.

---

## Bugs Found and Fixed (Historical Context)

### 1. Stale snapshot list in TUI

**Symptom**: Deleted snapshots still appeared in the UI

**Cause**: `all_snapshots` was computed once before the main loop

**Fix**: Refresh `core.list_snapshots()` every frame

---

### 2. Incorrect tag counts

**Symptom**: Tag counts increased even after deleting snapshots

**Cause**: `delete_snapshot()` removed directories but not tag references

**Fix**: `delete_snapshot()` now removes snapshot names from all related tag files

This restored referential integrity and fixed:

* TUI tag counts
* CLI `list-tags`
* `restore-by-tag`

---

## Modification Guidelines (for Future Agents)

### When modifying `core.py`

Ask:

* Does this change mutate filesystem state?
* If yes: what other files reference this state?

Always update **both sides** of any relationship:

| Relationship             | Update both |
| ------------------------ | ----------- |
| snapshot ↔ tags          | yes         |
| tag ↔ metadata           | yes         |
| snapshot ↔ restore logic | yes         |

---

### When modifying `tui.py`

* Treat `core.py` as a black box
* Never assume cached state is valid
* Always recompute snapshot/tag lists after mutations
* UI bugs should not be fixed by data hacks

---

### When adding features

Preferred order:

1. Add core functionality
2. Add CLI support
3. Add TUI support

Never skip step 1.

---

## Suggested Future Improvements (Optional)

* `core.fsck()` — repair tags vs snapshots on startup
* Make tags fully derived (no `tags/*.json`)
* Snapshot sorting by mtime instead of name
* Unit tests for referential integrity

---

## Mental Model

* `core.py` = database + transactions
* `cli.py` / `tui.py` = views
* Filesystem = truth
* Anything cached can and will go stale

If something looks wrong in the UI, fix the **data invariant**, not the rendering.
