# =======================================================
# 🧩 Imports
# =======================================================
import json
import os
from pathlib import Path
from typing import Any, Dict

from oauth2client.service_account import \
    ServiceAccountCredentials  # type:ignore
from pydrive2.auth import GoogleAuth  # type:ignore
from pydrive2.drive import GoogleDrive  # type:ignore

from helpers import file_helper
from kraken_core import FolderType, PathsConfig, custom_logger


# =======================================================
# 🔑 Credentials Loading
# =======================================================
def load_service_account_creds(env_var: str) -> Dict[str, Any]:
    """Load JSON credentials from environment variable."""
    if env_var not in os.environ:
        msg = f"Environment variable '{env_var}' is not defined."
        custom_logger.error(msg)
        raise KeyError(msg)

    try:
        creds_json: Dict[str, Any] = json.loads(os.environ[env_var])
        return creds_json
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON in '{env_var}': {e}"
        custom_logger.error(msg)
        raise ValueError(msg) from e


# =======================================================
# 🔗 Google Drive Setup
# =======================================================
def setup_drive(creds_json: Dict[str, Any]) -> GoogleDrive:
    """Authenticate with Google Drive using service account."""
    gauth = GoogleAuth()
    scope = "https://www.googleapis.com/auth/drive"

    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(  # type: ignore
            creds_json, scope
        )
        gauth.credentials = credentials
        drive = GoogleDrive(gauth)
        return drive
    except ValueError as e:
        msg = f"Failed to create Google Drive credentials: {e}"
        custom_logger.error(msg)
        raise


# =======================================================
# 📄 File Download Logic
# =======================================================
def download_file(drive: GoogleDrive, file_id: str, output_path: Path) -> None:
    """Download file from Google Drive to output_path."""
    try:
        file = drive.CreateFile({"id": file_id})  # type: ignore
        file.GetContentFile(str(output_path))  # type: ignore
        custom_logger.info(f"✅ File downloaded to: {output_path}")
    except FileNotFoundError as e:
        msg = f"Output path not found: {output_path} — {e}"
        custom_logger.error(msg)
        raise
    except PermissionError as e:
        msg = f"No permission to write to {output_path} — {e}"
        custom_logger.error(msg)
        raise


# =======================================================
# 🏁 Main Execution
# =======================================================
def main() -> None:
    """Main script execution."""
    try:
        # Clear downloads directory
        file_helper.reset_dir(FolderType.DOWNLOADS)

        # Load credentials
        creds_json = load_service_account_creds("GOOGLE_DRIVE_JSON_KEY")

        # Authenticate with Google Drive
        drive = setup_drive(creds_json)

        # Download the target file
        file_id = "11_jmQS5RlPZzZt6zdwZHKWDon05ImWhX"
        download_file(drive, file_id, PathsConfig.KRAKEN_TRADES_PDF)

    except Exception as exc:
        custom_logger.exception(f"❌ Unexpected error in main(): {exc}")
        raise


# =======================================================
# 🔧 Entry Point
# =======================================================
if __name__ == "__main__":
    main()
