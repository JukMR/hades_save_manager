"""Constants for Hades save backup tool."""

from pathlib import Path

# Game save directory
HADES_SAVE_DIR = Path(
    "/mnt/jupiter/SteamLibrary/steamapps/compatdata/1145360/pfx/drive_c/users/steamuser/Documents/Saved Games/Hades"
)

# Backup directories and files
BACKUP_SAVE_ROOT = Path.home() / ".local/share/hades_backups"
TAGS_DIR = BACKUP_SAVE_ROOT / "tags"
CONFIG_FILE = BACKUP_SAVE_ROOT / "config.json"
LOG_FILE = BACKUP_SAVE_ROOT / "hades.log"

# Application settings
MAX_LOG_ENTRIES = 50
ERROR_DISPLAY_DURATION = 10  # frames
