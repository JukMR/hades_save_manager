import pytest
import json
from core import tag_manager


@pytest.fixture
def temp_backup_root(tmp_path, monkeypatch):
    root = tmp_path / "backups"
    root.mkdir()
    saves = root / "saves"
    saves.mkdir()

    # Monkeypatch constants in tag_manager
    monkeypatch.setattr("core.tag_manager.BACKUP_SAVE_ROOT", root)
    monkeypatch.setattr("core.snapshot_manager.SAVES_DIR", saves)

    return root, saves


def test_add_tag(temp_backup_root):
    root, saves = temp_backup_root
    # Create a mock snapshot directory for testing in the saves directory
    snapshot_dir = saves / "snap1"
    snapshot_dir.mkdir()
    (snapshot_dir / "mock_file.txt").write_text("mock content")
    
    tag_manager.add_tag("test_tag", snapshot_dir)

    tag_dir = root / "test_tag"
    assert tag_dir.exists()
    snapshot_in_tag = tag_dir / "snap1"
    assert snapshot_in_tag.exists()


def test_list_tags(temp_backup_root):
    root, saves = temp_backup_root
    # Create mock snapshot directories for testing in the saves directory
    for snap_name in ["snap1", "snap2"]:
        snapshot_dir = saves / snap_name
        snapshot_dir.mkdir()
        (snapshot_dir / "mock_file.txt").write_text("mock content")
    
    tag_manager.add_tag("tag1", saves / "snap1")
    tag_manager.add_tag("tag2", saves / "snap2")

    assert sorted(tag_manager.list_tags()) == ["tag1", "tag2"]


def test_snapshots_for_tag(temp_backup_root):
    root, saves = temp_backup_root
    # Create mock snapshot directories for testing in the saves directory
    for snap_name in ["snap1", "snap2"]:
        snapshot_dir = saves / snap_name
        snapshot_dir.mkdir()
        (snapshot_dir / "mock_file.txt").write_text("mock content")
    
    tag_manager.add_tag("tag1", saves / "snap1")
    tag_manager.add_tag("tag1", saves / "snap2")

    assert sorted(tag_manager.snapshots_for_tag("tag1")) == ["snap1", "snap2"]


def test_get_tag_count(temp_backup_root):
    root, saves = temp_backup_root
    # Create mock snapshot directories for testing in the saves directory
    for snap_name in ["snap1", "snap2"]:
        snapshot_dir = saves / snap_name
        snapshot_dir.mkdir()
        (snapshot_dir / "mock_file.txt").write_text("mock content")
    
    tag_manager.add_tag("tag1", saves / "snap1")
    tag_manager.add_tag("tag1", saves / "snap2")

    assert tag_manager.get_tag_count("tag1") == 2
