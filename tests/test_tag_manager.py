import pytest
import json
from core import tag_manager


@pytest.fixture
def temp_backup_root(tmp_path, monkeypatch):
    root = tmp_path / "backups"
    root.mkdir()

    # Monkeypatch constants in tag_manager
    monkeypatch.setattr("core.tag_manager.BACKUP_SAVE_ROOT", root)

    return root


def test_add_tag(temp_backup_root):
    root = temp_backup_root
    # Create a mock tag directory and snapshot
    source_tag_dir = root / "source_tag"
    source_tag_dir.mkdir()
    snapshot_dir = source_tag_dir / "snap1"
    snapshot_dir.mkdir()
    (snapshot_dir / "mock_file.txt").write_text("mock content")
    
    tag_manager.add_tag("test_tag", snapshot_dir)

    tag_dir = root / "test_tag"
    assert tag_dir.exists()
    snapshot_in_tag = tag_dir / "snap1"
    assert snapshot_in_tag.exists()


def test_list_tags(temp_backup_root):
    root = temp_backup_root
    # Create mock tag directories and snapshots
    for tag_name, snap_name in [("tag1", "snap1"), ("tag2", "snap2")]:
        tag_dir = root / tag_name
        tag_dir.mkdir()
        snapshot_dir = tag_dir / snap_name
        snapshot_dir.mkdir()
        (snapshot_dir / "mock_file.txt").write_text("mock content")
    
    # Add additional tags to existing snapshots
    tag_manager.add_tag("tag3", root / "tag1" / "snap1")
    tag_manager.add_tag("tag4", root / "tag2" / "snap2")

    assert sorted(tag_manager.list_tags()) == ["tag1", "tag2", "tag3", "tag4"]


def test_snapshots_for_tag(temp_backup_root):
    root = temp_backup_root
    # Create a tag directory and add snapshots to it
    tag_dir = root / "tag1"
    tag_dir.mkdir()
    
    # Create snapshots in the tag directory
    for snap_name in ["snap1", "snap2"]:
        snapshot_dir = tag_dir / snap_name
        snapshot_dir.mkdir()
        (snapshot_dir / "mock_file.txt").write_text("mock content")

    assert sorted(tag_manager.snapshots_for_tag("tag1")) == ["snap1", "snap2"]


def test_get_tag_count(temp_backup_root):
    root = temp_backup_root
    # Create a tag directory and add snapshots to it
    tag_dir = root / "tag1"
    tag_dir.mkdir()
    
    # Create snapshots in the tag directory
    for snap_name in ["snap1", "snap2"]:
        snapshot_dir = tag_dir / snap_name
        snapshot_dir.mkdir()
        (snapshot_dir / "mock_file.txt").write_text("mock content")

    assert tag_manager.get_tag_count("tag1") == 2
