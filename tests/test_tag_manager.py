import pytest
import json
from core import tag_manager


@pytest.fixture
def temp_backup_root(tmp_path, monkeypatch):
    root = tmp_path / "backups"
    root.mkdir()
    tags = root / "tags"
    tags.mkdir()

    # Monkeypatch constants in tag_manager
    monkeypatch.setattr("core.tag_manager.TAGS_BASE_DIR", tags)
    monkeypatch.setattr("core.tag_manager.BACKUP_SAVE_ROOT", root)

    return root, tags


def test_add_tag(temp_backup_root):
    root, tags = temp_backup_root
    # Create a mock snapshot directory for testing
    snapshot_dir = root / "snap1"
    snapshot_dir.mkdir()
    (snapshot_dir / "mock_file.txt").write_text("mock content")
    
    tag_manager.add_tag("test_tag", "snap1")

    tag_dir = tags / "test_tag"
    assert tag_dir.exists()
    snapshot_link = tag_dir / "snap1"
    assert snapshot_link.exists()


def test_list_tags(temp_backup_root):
    root, tags = temp_backup_root
    # Create mock snapshot directories for testing
    for snap_name in ["snap1", "snap2"]:
        snapshot_dir = root / snap_name
        snapshot_dir.mkdir()
        (snapshot_dir / "mock_file.txt").write_text("mock content")
    
    tag_manager.add_tag("tag1", "snap1")
    tag_manager.add_tag("tag2", "snap2")

    assert sorted(tag_manager.list_tags()) == ["tag1", "tag2"]


def test_snapshots_for_tag(temp_backup_root):
    root, tags = temp_backup_root
    # Create mock snapshot directories for testing
    for snap_name in ["snap1", "snap2"]:
        snapshot_dir = root / snap_name
        snapshot_dir.mkdir()
        (snapshot_dir / "mock_file.txt").write_text("mock content")
    
    tag_manager.add_tag("tag1", "snap1")
    tag_manager.add_tag("tag1", "snap2")

    assert sorted(tag_manager.snapshots_for_tag("tag1")) == ["snap1", "snap2"]


def test_get_tag_count(temp_backup_root):
    root, tags = temp_backup_root
    # Create mock snapshot directories for testing
    for snap_name in ["snap1", "snap2"]:
        snapshot_dir = root / snap_name
        snapshot_dir.mkdir()
        (snapshot_dir / "mock_file.txt").write_text("mock content")
    
    tag_manager.add_tag("tag1", "snap1")
    tag_manager.add_tag("tag1", "snap2")

    assert tag_manager.get_tag_count("tag1") == 2
