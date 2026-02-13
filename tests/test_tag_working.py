"""Simple working tests for tag manager."""


def test_add_tag_simple(patched_constants):
    """Test adding tags to snapshots."""
    root, game_dir = patched_constants

    from core import tag_manager

    # Create a source tag directory and snapshot
    source_tag_dir = root / "source_tag"
    source_tag_dir.mkdir()
    snapshot_dir = source_tag_dir / "snapshot1"
    snapshot_dir.mkdir()
    (snapshot_dir / "mock_file.txt").write_text("mock content")
    
    # Add a tag
    tag_manager.add_tag("test", snapshot_dir)

    # Check tag directory was created
    tag_dir = root / "test"
    assert tag_dir.exists(), "Tag directory should be created"

    # Check snapshot exists in tag directory
    snapshot_in_tag = tag_dir / "snapshot1"
    assert snapshot_in_tag.exists(), "Snapshot should exist in tag directory"


def test_list_tags_simple(patched_constants):
    """Test listing all tags."""
    root, game_dir = patched_constants

    from core import tag_manager

    # Create initial tag directories with snapshots
    for tag_name, snap_name in [("tag1", "snap1"), ("tag2", "snap2")]:
        tag_dir = root / tag_name
        tag_dir.mkdir()
        snapshot_dir = tag_dir / snap_name
        snapshot_dir.mkdir()
        (snapshot_dir / "mock_file.txt").write_text("mock content")
    
    # Add additional tags to existing snapshots
    tag_manager.add_tag("tag3", root / "tag1" / "snap1")
    tag_manager.add_tag("tag4", root / "tag2" / "snap2")

    # List tags
    all_tags = tag_manager.list_tags()
    assert len(all_tags) >= 4, f"Expected at least 4 tags, got {len(all_tags)}"
    assert "tag1" in all_tags, "tag1 should be in list"
    assert "tag2" in all_tags, "tag2 should be in list"
    assert "tag3" in all_tags, "tag3 should be in list"
    assert "tag4" in all_tags, "tag4 should be in list"


def test_snapshots_for_tag_simple(patched_constants):
    """Test getting snapshots for a specific tag."""
    root, game_dir = patched_constants

    from core import tag_manager

    # Create a tag directory and add snapshots to it
    tag_dir = root / "test"
    tag_dir.mkdir()

    # Create snapshots in the tag directory
    for snap_name in ["snap1", "snap2"]:
        snapshot_dir = tag_dir / snap_name
        snapshot_dir.mkdir()
        (snapshot_dir / "mock_file.txt").write_text("mock content")

    # Get snapshots for tag
    snapshots = tag_manager.snapshots_for_tag("test")
    assert len(snapshots) == 2, f"Expected 2 snapshots, got {len(snapshots)}"
    assert "snap1" in snapshots, "snap1 should be in list"
    assert "snap2" in snapshots, "snap2 should be in list"


def test_get_tag_count_simple(patched_constants):
    """Test getting snapshot count for a tag."""
    root, game_dir = patched_constants

    from core import tag_manager

    # Create a tag directory and add snapshots to it
    tag_dir = root / "test"
    tag_dir.mkdir()

    # Create snapshots in the tag directory
    for snap_name in ["snap1", "snap2", "snap3"]:
        snapshot_dir = tag_dir / snap_name
        snapshot_dir.mkdir()
        (snapshot_dir / "mock_file.txt").write_text("mock content")

    # Get count
    count = tag_manager.get_tag_count("test")
    assert count == 3, f"Expected count 3, got {count}"


def test_add_multiple_snapshots_to_tag(patched_constants):
    """Test adding multiple snapshots to same tag."""
    root, game_dir = patched_constants

    from core import tag_manager

    # Create source snapshots in different tag directories
    for i, snap_name in enumerate(["snap1", "snap2", "snap3"]):
        tag_dir = root / f"source_tag_{i}"
        tag_dir.mkdir()
        snapshot_dir = tag_dir / snap_name
        snapshot_dir.mkdir()
        (snapshot_dir / "mock_file.txt").write_text("mock content")
    
    # Add multiple snapshots to the same tag
    tag_manager.add_tag("multi", root / "source_tag_0" / "snap1")
    tag_manager.add_tag("multi", root / "source_tag_1" / "snap2")
    tag_manager.add_tag("multi", root / "source_tag_2" / "snap3")

    # Check all snapshots are in tag
    snapshots = tag_manager.snapshots_for_tag("multi")
    assert len(snapshots) == 3, f"Expected 3 snapshots, got {len(snapshots)}"
    assert "snap1" in snapshots
    assert "snap2" in snapshots
    assert "snap3" in snapshots


def test_nonexistent_tag(patched_constants):
    """Test operations on non-existent tag."""
    root, game_dir = patched_constants

    from core import tag_manager

    # Get snapshots for non-existent tag
    snapshots = tag_manager.snapshots_for_tag("nonexistent")
    assert len(snapshots) == 0, "Non-existent tag should return empty list"

    # Get count for non-existent tag
    count = tag_manager.get_tag_count("nonexistent")
    assert count == 0, "Non-existent tag should have count 0"
