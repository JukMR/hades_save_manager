"""Simple working tests for snapshot manager."""

import pytest
from tests.conftest import patched_constants


def test_save_simple(patched_constants):
    """Test snapshot creation with simple approach."""
    root, tags, game_dir = patched_constants

    from core import snapshot_manager

    # Test creating a snapshot
    snap_path, msg = snapshot_manager.save(tags=["test"], note="hello")

    assert snap_path is not None, f"Save should succeed but got: {msg}"
    assert snap_path.exists(), "Snapshot directory should exist"

    # Check the save file was copied correctly
    saved_content = (snap_path / "Profile1.sav").read_text(
        encoding="utf-8", errors="replace"
    )
    assert saved_content == "dummy save", f"Content mismatch: {saved_content}"


def test_list_snapshots_simple(patched_constants):
    """Test listing snapshots."""
    root, tags, game_dir = patched_constants

    from core import snapshot_manager

    # Create one snapshot
    snapshot_manager.save(tags=[], note=None)

    # List snapshots
    snapshots = snapshot_manager.list_snapshots()
    assert len(snapshots) == 1, f"Expected 1 snapshot, got {len(snapshots)}"
    assert snapshots[0].exists(), "Snapshot should exist"


def test_restore_simple(patched_constants):
    """Test snapshot restore."""
    root, tags, game_dir = patched_constants

    from core import snapshot_manager

    # Create a snapshot
    snap_path, _ = snapshot_manager.save(tags=[], note=None)

    # Modify current save
    (game_dir / "Profile1.sav").write_text("new save")

    # Restore snapshot
    success, msg = snapshot_manager.restore(snap_path)
    assert success, f"Restore should succeed but got: {msg}"

    # Verify content was restored
    restored_content = (game_dir / "Profile1.sav").read_text(
        encoding="utf-8", errors="replace"
    )
    assert restored_content == "dummy save", (
        f"Content should be restored but got: {restored_content}"
    )


def test_delete_snapshot_simple(patched_constants):
    """Test snapshot deletion."""
    root, tags, game_dir = patched_constants

    from core import snapshot_manager

    # Create a snapshot
    snap_path, _ = snapshot_manager.save(tags=["test"], note=None)
    assert snap_path.exists(), "Snapshot should exist before deletion"

    # Delete snapshot
    success, msg = snapshot_manager.delete_snapshot(snap_path)
    assert success, f"Delete should succeed but got: {msg}"
    assert not snap_path.exists(), "Snapshot should not exist after deletion"


def test_save_error_handling(patched_constants):
    """Test error handling when game folder doesn't exist."""
    root, tags, game_dir = patched_constants

    # Remove game directory to simulate missing folder
    import shutil

    shutil.rmtree(game_dir)

    from core import snapshot_manager

    snap_path, msg = snapshot_manager.save(tags=["test"], note="test")
    assert snap_path is None, "Save should fail when game folder missing"
    assert "not found" in msg.lower() or "directory" in msg.lower(), (
        f"Error message should mention directory: {msg}"
    )
