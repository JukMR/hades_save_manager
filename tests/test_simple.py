"""Simple integration tests that don't need file system mocking."""

from core.metadata_handler import read_meta, write_meta


def test_metadata_roundtrip(tmp_path):
    """Test that metadata write/read works correctly."""
    # Create test snapshot path
    snapshot_dir = tmp_path / "test_snapshot"
    snapshot_dir.mkdir()

    # Write metadata
    tags = ["test", "boss"]
    note = "Test checkpoint"
    write_meta(snapshot_dir, tags, note)

    # Read back and verify
    meta = read_meta(snapshot_dir)
    assert set(meta["tags"]) == set(tags)
    assert meta["note"] == note
    assert meta["created_at"] == snapshot_dir.name


def test_constants_import():
    """Test that constants can be imported."""
    from core.constants import BACKUP_SAVE_ROOT, SAVES_DIR

    assert BACKUP_SAVE_ROOT is not None
    assert SAVES_DIR is not None
