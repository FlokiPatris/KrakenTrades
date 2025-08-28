# =============================================================================
# 🧰 Environment & Config
# =============================================================================
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import errno
from typing import Optional, Final

from kraken_core import FolderType, PathsConfig, custom_logger


# =============================================================================
# 🛠️ Constants
# =============================================================================
TREE_CMD_TIMEOUT: Final[int] = 5  # seconds


# =============================================================================
# 🧩 FileHelper Class
# =============================================================================
@dataclass
class FileHelper:
    """Singleton utility for safe file/folder operations and I/O."""

    downloads_dir: Path = PathsConfig.DOWNLOADS_DIR
    uploads_dir: Path = PathsConfig.UPLOADS_DIR
    reports_dir: Path = PathsConfig.REPORTS_DIR
    repo_root: Path = PathsConfig.REPO_ROOT

    _instance: FileHelper | None = None

    # ------------------------------------------------------------------------
    # Singleton Instantiation
    # ------------------------------------------------------------------------
    def __new__(cls) -> FileHelper:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__post_init__()
        return cls._instance

    def __post_init__(self) -> None:
        """Ensure all key folders exist at initialization."""
        for folder in [self.reports_dir, self.downloads_dir, self.uploads_dir]:
            self.ensure_dir(folder)

    # ------------------------------------------------------------------------
    # Directory Operations
    # ------------------------------------------------------------------------
    @staticmethod
    def ensure_dir(path: Path) -> Path:
        """Ensure a directory exists; create it if missing."""
        try:
            path.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            custom_logger.error(
                "❌ Permission denied creating directory %s: %s", path, e
            )
            raise
        except OSError as e:
            if e.errno != errno.EEXIST:
                custom_logger.error("❌ OS error creating directory %s: %s", path, e)
                raise
        return path

    def reset_dir(self, folder: FolderType) -> None:
        """Delete all files and subfolders in the specified folder."""
        path = self._get_folder_path(folder)
        if not path.exists():
            custom_logger.warning("⚠️ Folder does not exist: %s", path)
            return

        for entry in path.iterdir():
            try:
                if entry.is_file():
                    entry.unlink()
                    custom_logger.info("🗑️ Deleted file: %s", entry)
                elif entry.is_dir():
                    shutil.rmtree(entry)
                    custom_logger.info("🗑️ Deleted folder: %s", entry)
            except PermissionError as e:
                custom_logger.error("❌ Permission denied deleting %s: %s", entry, e)
                raise
            except OSError as e:
                custom_logger.error("❌ OS error deleting %s: %s", entry, e)
                raise

    def get_folder(self, folder: FolderType) -> Path:
        """Return the path for the given folder type."""
        return self._get_folder_path(folder)

    # ------------------------------------------------------------------------
    # Directory Tree Representation
    # ------------------------------------------------------------------------
    @staticmethod
    def get_tree_structure(root_path: Path, depth: int = 2) -> str:
        """Return a textual tree structure for a directory."""
        try:
            return subprocess.check_output(
                ["tree", "-L", str(depth), str(root_path)],
                text=True,
                timeout=TREE_CMD_TIMEOUT,
            )
        except subprocess.CalledProcessError as e:
            custom_logger.error("❌ 'tree' command failed for %s: %s", root_path, e)
            return ""
        except FileNotFoundError:
            custom_logger.error("❌ 'tree' command not found. Please install it.")
            return ""
        except subprocess.TimeoutExpired as e:
            custom_logger.warning("⚠️ 'tree' command timed out for %s: %s", root_path, e)
            return ""

    # ------------------------------------------------------------------------
    # Safe File I/O
    # ------------------------------------------------------------------------
    def safe_write(self, file_path: Path, content: str, mode: str = "a") -> None:
        """Safely write content to a file, creating parent directories if needed."""
        self.ensure_dir(file_path.parent)
        try:
            with file_path.open(mode, encoding="utf-8") as f:
                f.write(content)
            custom_logger.info("✅ Written to file: %s", file_path)
        except (OSError, PermissionError) as e:
            custom_logger.error("❌ Failed writing to %s: %s", file_path, e)
            raise

    def safe_read(self, file_path: Path, max_size: int) -> Optional[str]:
        """Safely read a file if smaller than max_size."""
        try:
            size = file_path.stat().st_size
            if size > max_size:
                custom_logger.warning(
                    "⏩ Skipping large file: %s (%d bytes)", file_path, size
                )
                return None
            return file_path.read_text(encoding="utf-8")
        except (OSError, PermissionError) as e:
            custom_logger.error("❌ Could not read %s: %s", file_path, e)
            return None

    # ------------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------------
    def _get_folder_path(self, folder: FolderType) -> Path:
        """Map FolderType enum to actual folder path."""
        mapping = {
            FolderType.DOWNLOADS: self.downloads_dir,
            FolderType.UPLOADS: self.uploads_dir,
            FolderType.REPORTS: self.reports_dir,
        }
        try:
            return mapping[folder]
        except KeyError as e:
            custom_logger.error("❌ Invalid folder type: %s", folder)
            raise ValueError(f"Unsupported folder type: {folder}") from e


# =============================================================================
# 🌟 Global Singleton Instance
# =============================================================================
file_helper = FileHelper()
