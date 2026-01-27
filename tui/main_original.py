from __future__ import annotations

import curses
from typing import List, Optional

import core

# ---------- colors ----------


def init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_CYAN, -1)  # headers
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)  # selected row
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # metadata
    curses.init_pair(4, curses.COLOR_RED, -1)  # warnings
    curses.init_pair(5, curses.COLOR_GREEN, -1)  # hints / actions
    curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_WHITE)  # active pane border
    curses.init_pair(7, curses.COLOR_MAGENTA, -1)  # tags
    curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_BLUE)  # active tag
    curses.init_pair(9, curses.COLOR_CYAN, -1)  # log messages


# ---------- UI helpers ----------


def prompt(stdscr, y: int, msg: str) -> str:
    curses.echo()
    stdscr.addstr(y, 2, msg, curses.color_pair(3))
    stdscr.clrtoeol()
    val = stdscr.getstr(y, 2 + len(msg)).decode()
    curses.noecho()
    return val


def confirm(stdscr, title: str, msg: str) -> bool:
    h, w = stdscr.getmaxyx()
    win_h, win_w = 7, max(len(msg) + 6, 44)

    win = curses.newwin(
        win_h,
        win_w,
        (h - win_h) // 2,
        (w - win_w) // 2,
    )
    win.keypad(True)

    selected = 0  # 0 = Yes, 1 = No

    while True:
        win.clear()
        win.box()
        win.addstr(1, 2, title, curses.color_pair(4) | curses.A_BOLD)
        win.addstr(3, 2, msg)

        yes_attr = curses.A_REVERSE if selected == 0 else curses.A_NORMAL
        no_attr = curses.A_REVERSE if selected == 1 else curses.A_NORMAL

        win.addstr(5, 8, " Yes ", yes_attr | curses.color_pair(5))
        win.addstr(5, 16, " No ", no_attr | curses.color_pair(5))
        win.refresh()

        k = win.getch()

        if k in (curses.KEY_LEFT, curses.KEY_RIGHT):
            selected = 1 - selected
        elif k in (10, 13):  # Enter
            return selected == 0
        elif k in (27,):  # Esc
            return False


# ---------- UI state ----------


class UIState:
    def __init__(self):
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
        self.show_logs = False  # Toggle log visibility

    def get_filtered_snapshots(self, all_snapshots: List[core.Path]) -> List[core.Path]:
        """Get snapshots filtered by selected tag"""
        if not self.selected_tag:
            return all_snapshots

        tagged_snapshots = core.snapshots_for_tag(self.selected_tag)
        return [s for s in all_snapshots if s.name in tagged_snapshots]


# ---------- drawing functions ----------


def draw(stdscr, state: UIState) -> None:
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    # Calculate pane widths
    snapshots_w = w // 3
    metadata_w = w // 3
    tags_w = w - snapshots_w - metadata_w - 4  # Account for borders

    # Draw pane separators and headers
    draw_pane_headers(stdscr, snapshots_w, metadata_w, tags_w, state.active_pane)

    # Get data
    all_snapshots = core.list_snapshots()
    filtered_snapshots = state.get_filtered_snapshots(all_snapshots)
    tags = core.list_tags()

    # Ensure indexes are valid
    if filtered_snapshots:
        state.snapshot_idx = max(0, min(state.snapshot_idx, len(filtered_snapshots) - 1))
    else:
        state.snapshot_idx = 0

    if tags:
        state.tag_idx = max(0, min(state.tag_idx, len(tags)))
    else:
        state.tag_idx = 0

    # Draw content in each pane
    draw_snapshots_pane(stdscr, filtered_snapshots, state, snapshots_w, h)
    draw_metadata_pane(stdscr, filtered_snapshots, state, snapshots_w, metadata_w, h)
    draw_tags_pane(stdscr, tags, state, snapshots_w + metadata_w, tags_w, h)

    # Draw help/status bar
    draw_help_bar(stdscr, h, w, state)

    stdscr.refresh()


def draw_pane_headers(stdscr, snapshots_w: int, metadata_w: int, tags_w: int, active_pane: int) -> None:
    """Draw pane headers with active pane highlighting"""
    # Determine header colors
    colors = [
        curses.color_pair(1) | curses.A_BOLD,  # default cyan
        curses.color_pair(1) | curses.A_BOLD,  # default cyan
        curses.color_pair(1) | curses.A_BOLD,  # default cyan
    ]

    if active_pane >= 0 and active_pane < 3:
        colors[active_pane] = curses.color_pair(6) | curses.A_BOLD  # active pane

    # Draw headers
    stdscr.addstr(0, 2, "Snapshots", colors[0])
    stdscr.addstr(0, snapshots_w + 3, "Metadata", colors[1])
    stdscr.addstr(0, snapshots_w + metadata_w + 4, "Tags", colors[2])

    # Draw vertical separators
    h, w = stdscr.getmaxyx()
    vline = "│"

    for y in range(1, h):
        stdscr.addch(y, snapshots_w + 1, ord(vline))
        stdscr.addch(y, snapshots_w + metadata_w + 2, ord(vline))


def draw_snapshots_pane(stdscr, snapshots: List[core.Path], state: UIState, pane_w: int, h: int) -> None:
    """Draw the snapshots list pane"""
    max_y = h - 3  # Leave space for header and help

    if not snapshots:
        if state.selected_tag:
            stdscr.addstr(2, 2, f"No snapshots with tag '{state.selected_tag}'", curses.color_pair(4))
        else:
            stdscr.addstr(2, 2, "No snapshots available", curses.color_pair(4))
        return

    for i, snap in enumerate(snapshots[:max_y]):
        y = 2 + i

        if i == state.snapshot_idx and state.active_pane == 0:
            # Active row in active pane
            stdscr.addstr(y, 2, snap.name.ljust(pane_w - 4), curses.color_pair(2))
        elif i == state.snapshot_idx:
            # Selected row but not active pane
            stdscr.addstr(y, 2, snap.name.ljust(pane_w - 4), curses.A_REVERSE)
        else:
            # Normal row
            stdscr.addstr(y, 2, snap.name[: pane_w - 4])


def draw_metadata_pane(stdscr, snapshots: List[core.Path], state: UIState, offset_x: int, pane_w: int, h: int) -> None:
    """Draw the metadata pane"""
    if not snapshots:
        stdscr.addstr(2, offset_x + 2, "No snapshots available", curses.color_pair(4))
        return

    snap = snapshots[state.snapshot_idx]
    meta = core.read_meta(snap)

    y = 2
    stdscr.addstr(
        y,
        offset_x + 2,
        f"Created: {meta.get('created_at', '')}",
        curses.color_pair(3),
    )
    y += 2
    stdscr.addstr(
        y,
        offset_x + 2,
        f"Tags: {', '.join(meta.get('tags', []))}",
        curses.color_pair(7),
    )
    y += 2
    stdscr.addstr(y, offset_x + 2, "Note:", curses.A_BOLD)
    y += 1
    for line in (meta.get("note") or "").splitlines()[: h - 7]:  # Limit lines
        if y < h - 2:
            stdscr.addstr(y, offset_x + 4, line[: pane_w - 6])
            y += 1


def draw_tags_pane(stdscr, tags: List[str], state: UIState, offset_x: int, pane_w: int, h: int) -> None:
    """Draw the tags management pane"""
    max_y = h - 3

    # Handle tag creation/editing modes
    if state.creating_tag or state.renaming_tag:
        draw_tag_input(stdscr, state, offset_x, pane_w)
        return

    if not tags:
        stdscr.addstr(2, offset_x + 2, "No tags available", curses.color_pair(4))
        stdscr.addstr(4, offset_x + 2, "Press [n] to create a tag", curses.color_pair(5))
        return

    display_tags = ["+ New tag"] + tags

    for i, item in enumerate(display_tags[:max_y]):
        y = 2 + i
        is_selected = i == state.tag_idx and state.active_pane == 2

        # ----- virtual row -----
        if item == "+ New tag":
            attr = curses.color_pair(5)
            if is_selected:
                attr |= curses.A_REVERSE
            stdscr.addstr(y, offset_x + 2, item.ljust(pane_w - 4), attr)
            continue

        # ----- real tag -----
        tag = item
        count = core.get_tag_count(tag)
        is_active = tag == state.selected_tag

        if is_selected:
            color = curses.color_pair(8 if is_active else 2)
        elif is_active:
            color = curses.color_pair(7) | curses.A_REVERSE
        else:
            color = curses.A_NORMAL

        stdscr.addstr(
            y,
            offset_x + 2,
            f"{tag} ({count})".ljust(pane_w - 4),
            color,
        )


def draw_tag_input(stdscr, state: UIState, offset_x: int, pane_w: int) -> None:
    """Draw tag input field for creation/renaming"""
    if state.creating_tag:
        prompt = "New tag: "
    else:
        prompt = "Rename to: "

    stdscr.addstr(2, offset_x + 2, prompt, curses.A_BOLD)
    input_field = state.tag_input + "_"
    stdscr.addstr(3, offset_x + 2, input_field.ljust(pane_w - 4), curses.color_pair(2))
    stdscr.addstr(5, offset_x + 2, "[Enter] confirm  [Esc] cancel", curses.color_pair(5))


def draw_logs(stdscr, state: UIState, offset_x: int, width: int, h: int) -> None:
    """Draw recent logs in a small panel"""
    if not state.show_logs:
        return

    # Get recent logs
    logs = core.logger.get_recent_logs(8)

    # Draw log border and header
    log_h = min(len(logs) + 2, h - 4)
    stdscr.addstr(h - log_h - 1, offset_x, "┌" + "─" * (width - 2) + "┐", curses.color_pair(1))
    stdscr.addstr(h - log_h, offset_x, "│ Logs ", curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(h - log_h, offset_x + len("│ Logs "), " " * (width - len("│ Logs ") - 1) + "│", curses.color_pair(1))

    # Draw log entries
    for i, log_line in enumerate(logs):
        y = h - log_h + 1 + i
        if y >= h - 1:
            break

        # Truncate log line if too long
        display_line = log_line[: width - 4]

        # Determine color based on log level
        if "ERROR" in log_line:
            color = curses.color_pair(4)
        elif "SUCCESS" in log_line:
            color = curses.color_pair(5)
        elif "WARNING" in log_line:
            color = curses.color_pair(3)
        else:
            color = curses.color_pair(9)

        stdscr.addstr(y, offset_x, f"│ {display_line.ljust(width - 4)} │", color)

    # Draw bottom border
    stdscr.addstr(h - 1, offset_x, "└" + "─" * (width - 2) + "┘", curses.color_pair(1))


def draw_help_bar(stdscr, h: int, w: int, state: UIState) -> None:
    """Draw the help/status bar"""
    # Draw logs if enabled
    if state.show_logs:
        draw_logs(stdscr, state, 2, w, h)

    # Draw error message if active
    if state.error_message and state.error_timer > 0:
        error_y = h - 3 if not state.show_logs else h - 2
        stdscr.addstr(error_y, 2, state.error_message[: w - 4], curses.color_pair(4))
        state.error_timer -= 1
        help_y = h - 2 if not state.show_logs else h - 3
    else:
        help_y = h - 2 if not state.show_logs else h - 3

    help_texts = {
        0: "[↑↓] move  [Tab] switch pane  [Enter] select  [s] save  [r] restore  [d] delete  [l] toggle logs  [q] quit",
        1: "[Tab] switch pane  [l] toggle logs  [q] quit",  # Metadata pane has fewer actions
        2: "[↑↓] move  [Tab] switch pane  [Enter] filter  [n] new  [R] rename  [D] delete  [m] merge  [l] toggle logs  [q] quit",
    }

    help_text = help_texts.get(state.active_pane, help_texts[0])

    # Add current filter info if any
    if state.selected_tag:
        filter_info = f" | Filter: {state.selected_tag}"
        if len(help_text) + len(filter_info) < w - 2:
            help_text += filter_info

    # Add logs toggle status
    logs_status = " | Logs: ON" if state.show_logs else ""
    if logs_status:
        help_text += logs_status

    stdscr.addstr(help_y, 2, help_text[: w - 4], curses.color_pair(5))


def set_error(state: UIState, message: str) -> None:
    """Set an error message to display"""
    state.error_message = message
    state.error_timer = 10  # Show for 10 frames


def set_success(state: UIState, message: str) -> None:
    """Set a success message to display"""
    state.error_message = message
    state.error_timer = 10  # Show for 10 frames


# ---------- main loop ----------


def main(stdscr) -> None:
    curses.curs_set(0)
    stdscr.keypad(True)  # ← YOU MUST HAVE THIS

    init_colors()

    state = UIState()

    all_snapshots = core.list_snapshots()

    # Initialize with last used tag
    if state.selected_tag and all_snapshots:
        tagged_snapshots = state.get_filtered_snapshots(all_snapshots)
        if not tagged_snapshots:
            # No snapshots with last tag, fall back to newest
            state.selected_tag = None
    elif not state.selected_tag and all_snapshots:
        # No last tag selected, try to find the most recently used tag
        tags = core.list_tags()
        if tags:
            # Find tag with most recent snapshot
            latest_tag = None
            latest_time = None
            for tag in tags:
                tag_snapshots = core.snapshots_for_tag(tag)
                if tag_snapshots:
                    # Get the most recent snapshot for this tag
                    latest_snapshot = sorted(tag_snapshots)[-1]
                    if latest_time is None or latest_snapshot > latest_time:
                        latest_time = latest_snapshot
                        latest_tag = tag

            if latest_tag:
                state.selected_tag = latest_tag

    while True:
        all_snapshots = core.list_snapshots()
        draw(stdscr, state)
        key = stdscr.getch()

        # ==========================================================
        # TAG INPUT MODE (OVERRIDES EVERYTHING)
        # ==========================================================
        if state.creating_tag or state.renaming_tag:
            if key in (27,):  # Esc
                state.creating_tag = False
                state.renaming_tag = False
                state.tag_input = ""
                curses.curs_set(0)

            elif key in (10, 13):  # Enter
                name = state.tag_input.strip()
                if name:
                    if state.creating_tag:
                        core.TAGS_DIR.mkdir(parents=True, exist_ok=True)
                        tag_file = core.TAGS_DIR / f"{name}.json"

                        if tag_file.exists():
                            set_error(state, f"Tag '{name}' already exists")
                        else:
                            tag_file.write_text("[]")
                            set_success(state, f"Created tag '{name}'")

                            # auto-select newly created tag
                            state.selected_tag = name
                            core.set_last_tag(name)
                            state.tag_idx = core.list_tags().index(name) + 1

                    else:  # renaming
                        tags = core.list_tags()
                        if 0 < state.tag_idx <= len(tags):
                            old = tags[state.tag_idx - 1]
                            result, message = core.rename_tag(old, name)
                            if result:
                                if state.selected_tag == old:
                                    state.selected_tag = name
                                    core.set_last_tag(name)
                                set_success(state, message)
                            else:
                                set_error(state, message)

                state.creating_tag = False
                state.renaming_tag = False
                state.tag_input = ""
                curses.curs_set(0)

            elif key in (curses.KEY_BACKSPACE, 127, 8):
                state.tag_input = state.tag_input[:-1]

            elif 32 <= key <= 126:
                state.tag_input += chr(key)

            continue  # 🔴 critical: block all other handling

        # ---------- PANE NAVIGATION ----------
        if key == 9:  # Tab
            state.active_pane = (state.active_pane + 1) % 3
            if state.active_pane == 1:  # Skip metadata pane for navigation
                state.active_pane = (state.active_pane + 1) % 3
            continue

        elif key in (curses.KEY_LEFT, curses.KEY_RIGHT) and state.active_pane != 1:
            # Left/right arrow navigation (skip metadata pane)
            if key == curses.KEY_LEFT:
                new_pane = state.active_pane - 1
            else:
                new_pane = state.active_pane + 1

            if new_pane == 1:  # Skip metadata pane
                new_pane = new_pane + (1 if key == curses.KEY_RIGHT else -1)

            state.active_pane = max(0, min(2, new_pane))

        # ---------- SNAPSHOT PANE ACTIONS ----------
        elif state.active_pane == 0:
            filtered_snapshots = state.get_filtered_snapshots(all_snapshots)

            if key == curses.KEY_UP and filtered_snapshots:
                state.snapshot_idx = max(0, state.snapshot_idx - 1)

            elif key == curses.KEY_DOWN and filtered_snapshots:
                state.snapshot_idx = min(len(filtered_snapshots) - 1, state.snapshot_idx + 1)

            elif key == ord("q"):
                break

            # ---------- BACKUP ----------
            elif key == ord("s"):
                curses.curs_set(1)
                note = prompt(stdscr, 1, "Note: ")
                curses.curs_set(0)

                tag_list = [state.selected_tag] if state.selected_tag else []

                if confirm(
                    stdscr,
                    "Create backup",
                    f"Create snapshot{' with tag ' + state.selected_tag if state.selected_tag else ''}?",
                ):
                    result, message = core.save(tag_list, note)

                    if result:
                        set_success(state, message)
                        state.snapshot_idx = 0
                    else:
                        set_error(state, message)

            # ---------- RESTORE ----------
            elif key == ord("r") and filtered_snapshots:
                snap = filtered_snapshots[state.snapshot_idx]
                if confirm(
                    stdscr,
                    "Restore snapshot",
                    f"Restore {snap.name}? Current save will be replaced.",
                ):
                    result, message = core.restore(snap)
                    if result:
                        set_success(state, message)
                    else:
                        set_error(state, message)

            # ---------- DELETE ----------
            elif key == ord("d") and filtered_snapshots:
                snap = filtered_snapshots[state.snapshot_idx]
                if confirm(
                    stdscr,
                    "Delete snapshot",
                    f"Delete {snap.name}? This is permanent.",
                ):
                    result, message = core.delete_snapshot(snap)
                    if result:
                        state.snapshot_idx = max(0, state.snapshot_idx - 1)
                        set_success(state, message)
                    else:
                        set_error(state, message)

            # ---------- TAGS PANE ACTIONS ----------
        elif state.active_pane == 2:
            tags = core.list_tags()

            if key == curses.KEY_UP:
                state.tag_idx = max(0, state.tag_idx - 1)

            elif key == curses.KEY_DOWN:
                state.tag_idx = min(len(tags), state.tag_idx + 1)

            elif key == ord("\n"):
                if state.tag_idx == 0:
                    state.creating_tag = True
                    state.tag_input = ""
                    curses.curs_set(1)
                else:
                    selected_tag = tags[state.tag_idx - 1]
                    state.selected_tag = selected_tag
                    core.set_last_tag(selected_tag)
                    state.active_pane = 0
                    state.snapshot_idx = 0

            elif key == ord("q"):
                break

            # ---------- NEW TAG ----------
            elif key == ord("n"):
                state.creating_tag = True
                state.tag_input = ""
                curses.curs_set(1)  # Show cursor

            # ---------- RENAME TAG ----------
            elif key == ord("R") and tags:
                state.renaming_tag = True
                state.tag_input = tags[state.tag_idx]
                curses.curs_set(1)  # Show cursor

            # ---------- DELETE TAG ----------
            elif key == ord("D") and tags:
                tag = tags[state.tag_idx]
                if confirm(
                    stdscr,
                    "Delete tag",
                    f"Delete tag '{tag}'? This will remove it from all snapshots.",
                ):
                    result, message = core.delete_tag(tag)
                    if result:
                        if state.selected_tag == tag:
                            state.selected_tag = None
                            core.set_last_tag("")
                        state.tag_idx = max(0, state.tag_idx - 1)
                        set_success(state, message)
                    else:
                        set_error(state, message)

            # ---------- MERGE TAG ----------
            elif key == ord("m") and tags:
                # Simplified merge: merge selected tag into most recent tag
                if len(tags) > 1:
                    source_tag = tags[state.tag_idx]
                    # Find target tag (next one in list, or first if at end)
                    target_idx = (state.tag_idx + 1) % len(tags)
                    target_tag = tags[target_idx]

                    if confirm(
                        stdscr,
                        "Merge tags",
                        f"Merge '{source_tag}' into '{target_tag}'?",
                    ):
                        result, message = core.merge_tags(source_tag, target_tag)
                        if result:
                            if state.selected_tag == source_tag:
                                state.selected_tag = target_tag
                                core.set_last_tag(target_tag)
                            state.tag_idx = target_idx
                            set_success(state, message)
                        else:
                            set_error(state, message)

        # ---------- TAG INPUT HANDLING ----------
        elif state.creating_tag or state.renaming_tag:
            if key == 27:  # Escape
                state.creating_tag = False
                state.renaming_tag = False
                state.tag_input = ""
                curses.curs_set(0)  # Hide cursor

            elif key == ord("\n"):  # Enter
                if state.tag_input.strip():
                    if state.creating_tag:
                        # Just create the tag (it will be empty until used)
                        core.TAGS_DIR.mkdir(parents=True, exist_ok=True)
                        tag_file = core.TAGS_DIR / f"{state.tag_input.strip()}.json"
                        if not tag_file.exists():
                            tag_file.write_text("[]")
                            set_success(state, f"Created tag '{state.tag_input.strip()}'")
                        else:
                            set_error(state, f"Tag '{state.tag_input.strip()}' already exists")
                    elif state.renaming_tag and state.tag_idx < len(core.list_tags()):
                        old_tag = core.list_tags()[state.tag_idx]
                        result, message = core.rename_tag(old_tag, state.tag_input.strip())
                        if result:
                            if state.selected_tag == old_tag:
                                state.selected_tag = state.tag_input.strip()
                                core.set_last_tag(state.selected_tag)
                            set_success(state, message)
                        else:
                            set_error(state, message)

                state.creating_tag = False
                state.renaming_tag = False
                state.tag_input = ""
                curses.curs_set(0)  # Hide cursor

            elif key == curses.KEY_BACKSPACE or key == 127:
                state.tag_input = state.tag_input[:-1]

            elif 32 <= key <= 126:  # Printable characters
                state.tag_input += chr(key)

        # ---------- LOGS TOGGLE ----------
        elif key == ord("l"):
            state.show_logs = not state.show_logs

        # ---------- QUIT ----------
        elif key == ord("q"):
            break


if __name__ == "__main__":
    curses.wrapper(main)
