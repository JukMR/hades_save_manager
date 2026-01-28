"""Test utilities and helpers for isolated test environments."""

import json
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_env(tmp_path: Path):
    """Create temporary environment for testing."""
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
    """Patch all constants with temporary environment."""
    root, tags, game_dir = temp_env

    with patch("core.constants.BACKUP_SAVE_ROOT", root):
        with patch("core.constants.TAGS_DIR", tags):
            with patch("core.constants.HADES_SAVE_DIR", game_dir):
                with patch("core.tag_manager.TAGS_DIR", tags):
                    with patch("core.tag_manager.BACKUP_SAVE_ROOT", root):
                        with patch("core.snapshot_manager.TAGS_DIR", tags):
                            with patch("core.snapshot_manager.BACKUP_SAVE_ROOT", root):
                                with patch(
                                    "core.snapshot_manager.HADES_SAVE_DIR", game_dir
                                ):
                                    yield root, tags, game_dir


def create_tag_file(tags_dir: Path, tag_name: str, snapshots: List[str]) -> None:
    """Create a tag file with given snapshots."""
    tag_file = tags_dir / f"{tag_name}.json"
    tag_file.write_text(json.dumps(sorted(snapshots), indent=2))


def read_tag_file(tags_dir: Path, tag_name: str) -> List[str]:
    """Read snapshots from tag file."""
    tag_file = tags_dir / f"{tag_name}.json"
    if tag_file.exists():
        return json.loads(tag_file.read_text())
    return []
