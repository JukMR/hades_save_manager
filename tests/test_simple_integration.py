"""Simple integration tests with proper timing."""


def test_basic_workflow(patched_constants):
    """Test basic workflow: save -> list."""
    root, game_dir = patched_constants

    from core import snapshot_manager, tag_manager

    # Create snapshot
    snap_path, msg = snapshot_manager.save(tags=["basic"], note="basic test")
    assert snap_path is not None, f"Save failed: {msg}"

    # Verify tag assignment
    snapshots = tag_manager.snapshots_for_tag("basic")
    assert snap_path.name in snapshots, "Snapshot should be assigned to tag"

    # List snapshots
    all_snapshots = snapshot_manager.list_snapshots()
    assert len(all_snapshots) == 1, "Should have exactly one snapshot"


def test_error_handling(patched_constants):
    """Test error conditions."""
    root, game_dir = patched_constants

    from core import snapshot_manager

    # Test restore non-existent snapshot
    fake_path = root / "nonexistent"
    success, msg = snapshot_manager.restore(fake_path)
    assert not success, "Restore should fail for non-existent snapshot"
    assert "not found" in msg.lower() or "error" in msg.lower()


def test_import_isolation(patched_constants):
    """Test that imports work correctly with patching."""
    root, game_dir = patched_constants

    # Test importing after patching
    from core import snapshot_manager, tag_manager

    # Simple operation to test everything is working
    snap_path, msg = snapshot_manager.save(tags=["isolation"], note="test imports")
    assert snap_path is not None, f"Save failed: {msg}"

    # Verify tag was created
    tag_snapshots = tag_manager.snapshots_for_tag("isolation")
    assert snap_path.name in tag_snapshots, "Tag should contain snapshot"
