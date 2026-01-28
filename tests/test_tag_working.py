"""Simple working tests for tag manager."""


def test_add_tag_simple(patched_constants):
    """Test adding tags to snapshots."""
    root, tags, game_dir = patched_constants

    from core import tag_manager

    # Add a tag
    tag_manager.add_tag("test", "snapshot1")

    # Check tag file was created
    tag_file = tags / "test.json"
    assert tag_file.exists(), "Tag file should be created"

    # Check snapshot is in tag file
    from tests.conftest import read_tag_file

    snapshots = read_tag_file(tags, "test")
    assert "snapshot1" in snapshots, "Snapshot should be in tag file"


def test_list_tags_simple(patched_constants):
    """Test listing all tags."""
    root, tags, game_dir = patched_constants

    from core import tag_manager

    # Add some tags
    tag_manager.add_tag("tag1", "snap1")
    tag_manager.add_tag("tag2", "snap2")

    # List tags
    all_tags = tag_manager.list_tags()
    assert len(all_tags) == 2, f"Expected 2 tags, got {len(all_tags)}"
    assert "tag1" in all_tags, "tag1 should be in list"
    assert "tag2" in all_tags, "tag2 should be in list"


def test_snapshots_for_tag_simple(patched_constants):
    """Test getting snapshots for a specific tag."""
    root, tags, game_dir = patched_constants

    from core import tag_manager

    # Add snapshots to a tag
    tag_manager.add_tag("test", "snap1")
    tag_manager.add_tag("test", "snap2")

    # Get snapshots for tag
    snapshots = tag_manager.snapshots_for_tag("test")
    assert len(snapshots) == 2, f"Expected 2 snapshots, got {len(snapshots)}"
    assert "snap1" in snapshots, "snap1 should be in list"
    assert "snap2" in snapshots, "snap2 should be in list"


def test_get_tag_count_simple(patched_constants):
    """Test getting snapshot count for a tag."""
    root, tags, game_dir = patched_constants

    from core import tag_manager

    # Add snapshots to a tag
    tag_manager.add_tag("test", "snap1")
    tag_manager.add_tag("test", "snap2")
    tag_manager.add_tag("test", "snap3")

    # Get count
    count = tag_manager.get_tag_count("test")
    assert count == 3, f"Expected count 3, got {count}"


def test_add_multiple_snapshots_to_tag(patched_constants):
    """Test adding multiple snapshots to same tag."""
    root, tags, game_dir = patched_constants

    from core import tag_manager

    # Add multiple snapshots to the same tag
    tag_manager.add_tag("multi", "snap1")
    tag_manager.add_tag("multi", "snap2")
    tag_manager.add_tag("multi", "snap3")

    # Check all snapshots are in tag
    from tests.conftest import read_tag_file

    snapshots = read_tag_file(tags, "multi")
    assert len(snapshots) == 3, f"Expected 3 snapshots, got {len(snapshots)}"
    assert "snap1" in snapshots
    assert "snap2" in snapshots
    assert "snap3" in snapshots


def test_nonexistent_tag(patched_constants):
    """Test operations on non-existent tag."""
    root, tags, game_dir = patched_constants

    from core import tag_manager

    # Get snapshots for non-existent tag
    snapshots = tag_manager.snapshots_for_tag("nonexistent")
    assert len(snapshots) == 0, "Non-existent tag should return empty list"

    # Get count for non-existent tag
    count = tag_manager.get_tag_count("nonexistent")
    assert count == 0, "Non-existent tag should have count 0"
