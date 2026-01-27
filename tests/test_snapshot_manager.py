import pytest
import shutil
from pathlib import Path
from unittest.mock import patch
from core import snapshot_manager

@pytest.fixture
def temp_env(tmp_path):
    root = tmp_path / "backups"
    root.mkdir()
    tags = root / "tags"
    tags.mkdir()
    
    game_dir = tmp_path / "Hades"
    game_dir.mkdir()
    (game_dir / "Profile1.sav").write_text("dummy save")
    
    return root, tags, game_dir

@pytest.fixture
def patched_constants(temp_env):
    root, tags, game_dir = temp_env
    
    with patch('core.constants.BACKUP_SAVE_ROOT', root):
        with patch('core.constants.TAGS_DIR', tags):
            with patch('core.constants.HADES_SAVE_DIR', game_dir):
                yield root, tags, game_dir

def test_save(patched_constants):
    root, tags, game_dir = patched_constants
    snap_path, msg = snapshot_manager.save(tags=["test"], note="hello")
    
    assert snap_path is not None
    assert snap_path.exists()
    assert (snap_path / "Profile1.sav").read_text() == "dummy save"
    assert (tags / "test.json").exists()

def test_list_snapshots(patched_constants):
    root, tags, game_dir = patched_constants
    snapshot_manager.save(tags=[], note=None)
    snapshots = snapshot_manager.list_snapshots()
    assert len(snapshots) == 1

def test_restore(patched_constants):
    root, tags, game_dir = patched_constants
    snap_path, _ = snapshot_manager.save(tags=[], note=None)
    
    # Modify current save
    (game_dir / "Profile1.sav").write_text("new save")
    
    success, msg = snapshot_manager.restore(snap_path)
    assert success
    assert (game_dir / "Profile1.sav").read_text() == "dummy save"

def test_delete_snapshot(patched_constants):
    root, tags, game_dir = patched_constants
    snap_path, _ = snapshot_manager.save(tags=["test"], note=None)
    
    success, msg = snapshot_manager.delete_snapshot(snap_path)
    assert success
    assert not snap_path.exists()
    # Check tag reference removed
    import json
    tag_data = json.loads((tags / "test.json").read_text())
    assert snap_path.name not in tag_data
